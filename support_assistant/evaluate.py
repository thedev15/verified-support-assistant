from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import get_settings
from .knowledge import load_documents
from .retrieval import TfidfRetriever
from .service import SupportService


def evaluate(dataset_path: Path) -> dict[str, float | int]:
    settings = get_settings()
    service = SupportService(
        TfidfRetriever(load_documents(settings.knowledge_path)), settings
    )
    examples = json.loads(dataset_path.read_text(encoding="utf-8"))["examples"]

    retrieval_hits = 0
    refusal_hits = 0
    keyword_scores: list[float] = []
    for example in examples:
        response = service.answer(example["question"])
        cited_ids = {citation.document_id for citation in response.citations}
        expected_id = example.get("expected_document_id")
        retrieval_hits += int(expected_id is None or expected_id in cited_ids)
        refusal_hits += int(response.refused == (not example["answerable"]))
        keywords = [word.lower() for word in example.get("required_keywords", [])]
        if keywords and example["answerable"]:
            text = response.answer.lower()
            keyword_scores.append(sum(word in text for word in keywords) / len(keywords))

    count = len(examples)
    return {
        "examples": count,
        "retrieval_accuracy": round(retrieval_hits / count, 4),
        "refusal_accuracy": round(refusal_hits / count, 4),
        "keyword_coverage": round(sum(keyword_scores) / len(keyword_scores), 4),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=Path("data/eval_set.json"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--min-retrieval", type=float, default=0.95)
    parser.add_argument("--min-refusal", type=float, default=0.95)
    parser.add_argument("--min-keyword-coverage", type=float, default=0.85)
    args = parser.parse_args()
    metrics = evaluate(args.dataset)
    rendered = json.dumps(metrics, indent=2, sort_keys=True)
    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")

    failures = []
    if metrics["retrieval_accuracy"] < args.min_retrieval:
        failures.append("retrieval_accuracy")
    if metrics["refusal_accuracy"] < args.min_refusal:
        failures.append("refusal_accuracy")
    if metrics["keyword_coverage"] < args.min_keyword_coverage:
        failures.append("keyword_coverage")
    if failures:
        raise SystemExit(f"Evaluation gate failed: {', '.join(failures)}")


if __name__ == "__main__":
    main()