from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import sys
import time
from dataclasses import replace
from pathlib import Path

import wandb

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from support_assistant.config import get_settings  # noqa: E402
from support_assistant.knowledge import load_documents  # noqa: E402
from support_assistant.retrieval import TfidfRetriever  # noqa: E402
from support_assistant.service import SupportService  # noqa: E402

CITATION_PATTERN = re.compile(r"\[([A-Z][A-Z0-9_-]+)\]")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a bounded hosted-model evaluation.")
    parser.add_argument("--entity", required=True)
    parser.add_argument("--project", default="verified-support-assistant")
    parser.add_argument("--model", required=True)
    parser.add_argument("--max-paid-calls", type=int, default=25)
    parser.add_argument("--max-tokens", type=int, default=220)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--limit", type=int, default=40)
    parser.add_argument("--weave", action="store_true")
    return parser.parse_args()


def percentile_95(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(0.95 * len(ordered)))]


def main() -> None:
    args = parse_args()
    os.environ["WANDB_ENTITY"] = args.entity
    os.environ["WANDB_PROJECT"] = args.project

    examples = json.loads((ROOT / "data/eval_set.json").read_text())["examples"][: args.limit]
    base_settings = get_settings()
    documents = load_documents(ROOT / "data/knowledge_base.json")
    retriever = TfidfRetriever(documents)
    baseline = SupportService(retriever, replace(base_settings, llm_backend="extractive"))
    planned_paid_calls = sum(not baseline.answer(item["question"]).refused for item in examples)
    if planned_paid_calls > args.max_paid_calls:
        raise SystemExit(
            f"Refusing to run: {planned_paid_calls} model calls exceed "
            f"--max-paid-calls={args.max_paid_calls}."
        )

    settings = replace(
        base_settings,
        llm_backend="inference",
        inference_model=args.model,
        inference_max_tokens=args.max_tokens,
        inference_temperature=args.temperature,
    )
    service = SupportService(retriever, settings)
    answer = service.answer
    if args.weave:
        import weave

        weave.init(f"{args.entity}/{args.project}")
        answer = weave.op()(answer)

    safe_model = re.sub(r"[^a-z0-9]+", "-", args.model.lower()).strip("-")
    config: dict[str, object] = {
        "model": args.model,
        "retriever": "tfidf_word_ngrams_1_2",
        "top_k": settings.top_k,
        "min_retrieval_score": settings.min_retrieval_score,
        "temperature": args.temperature,
        "max_tokens_per_call": args.max_tokens,
        "max_paid_calls": args.max_paid_calls,
        "planned_paid_calls": planned_paid_calls,
        "evaluation_examples": len(examples),
        "github_repository": "thedev15/verified-support-assistant",
    }
    thread_id = os.environ.get("WANDB_ARIA_THREAD_ID")
    turn_id = os.environ.get("WANDB_ARIA_TURN_ID")
    if thread_id and turn_id:
        config["_wb_agent"] = {"thread_id": thread_id, "turn_id": turn_id}

    columns = [
        "question",
        "answerable",
        "expected_document_id",
        "answer",
        "refused",
        "response_document_ids",
        "answer_citation_ids",
        "latency_seconds",
        "prompt_tokens",
        "completion_tokens",
        "retrieval_correct",
        "refusal_correct",
        "citation_valid",
        "keyword_coverage",
        "error",
    ]
    table = wandb.Table(columns=columns)
    counters = {
        "retrieval": 0,
        "refusal": 0,
        "citation_valid": 0,
        "citation_eligible": 0,
        "errors": 0,
        "prompt_tokens": 0,
        "completion_tokens": 0,
    }
    keyword_scores: list[float] = []
    latencies: list[float] = []

    with wandb.init(
        entity=args.entity,
        project=args.project,
        name=f"live-eval-{safe_model}",
        job_type="evaluation",
        tags=["live-model", "rag", "evaluation", "portfolio"],
        config=config,
    ) as run:
        for index, example in enumerate(examples):
            started = time.perf_counter()
            error = ""
            try:
                response = answer(example["question"])
            except Exception as exc:  # Preserve the partial experiment for diagnosis.
                counters["errors"] += 1
                error = f"{type(exc).__name__}: {exc}"
                table.add_data(
                    example["question"], example["answerable"],
                    example.get("expected_document_id"), "", None, "", "",
                    time.perf_counter() - started, None, None, False, False,
                    False, None, error,
                )
                continue

            latency = time.perf_counter() - started
            latencies.append(latency)
            response_ids = [citation.document_id for citation in response.citations]
            answer_ids = CITATION_PATTERN.findall(response.answer)
            expected_id = example.get("expected_document_id")
            retrieval_correct = expected_id is None or expected_id in response_ids
            refusal_correct = response.refused == (not example["answerable"])
            citation_valid = True
            if example["answerable"] and not response.refused:
                counters["citation_eligible"] += 1
                citation_valid = bool(answer_ids) and set(answer_ids).issubset(set(response_ids))
                counters["citation_valid"] += int(citation_valid)
            counters["retrieval"] += int(retrieval_correct)
            counters["refusal"] += int(refusal_correct)
            counters["prompt_tokens"] += response.prompt_tokens or 0
            counters["completion_tokens"] += response.completion_tokens or 0

            keywords = [word.lower() for word in example.get("required_keywords", [])]
            keyword_coverage = None
            if keywords and example["answerable"] and not response.refused:
                keyword_coverage = sum(word in response.answer.lower() for word in keywords) / len(keywords)
                keyword_scores.append(keyword_coverage)

            table.add_data(
                example["question"], example["answerable"], expected_id,
                response.answer, response.refused, ", ".join(response_ids),
                ", ".join(answer_ids), latency, response.prompt_tokens,
                response.completion_tokens, retrieval_correct, refusal_correct,
                citation_valid, keyword_coverage, error,
            )
            run.log({"progress/completed_examples": index + 1})

        completed = len(examples) - counters["errors"]
        metrics = {
            "eval/examples": len(examples),
            "eval/errors": counters["errors"],
            "eval/retrieval_accuracy": counters["retrieval"] / completed if completed else 0,
            "eval/refusal_accuracy": counters["refusal"] / completed if completed else 0,
            "eval/citation_validity": (
                counters["citation_valid"] / counters["citation_eligible"]
                if counters["citation_eligible"] else 0
            ),
            "eval/keyword_coverage": statistics.mean(keyword_scores) if keyword_scores else 0,
            "usage/prompt_tokens": counters["prompt_tokens"],
            "usage/completion_tokens": counters["completion_tokens"],
            "latency/mean_seconds": statistics.mean(latencies) if latencies else 0,
            "latency/p95_seconds": percentile_95(latencies),
        }
        run.log({**metrics, "eval/cases": table})
        run.summary.update(metrics)
        print(f"run_url={run.url}")
        print(json.dumps(metrics, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()