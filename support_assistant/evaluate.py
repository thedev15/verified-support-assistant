from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import get_settings
from .knowledge import load_documents
from .models import EvaluationCase, EvaluationMetrics, EvaluationReport
from .retrieval import TfidfRetriever
from .service import SupportService


def evaluate_detailed(
    dataset_path: Path, service: SupportService | None = None
) -> EvaluationReport:
    if service is None:
        settings = get_settings()
        service = SupportService(TfidfRetriever(load_documents(settings.knowledge_path)), settings)
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    examples = dataset["examples"]
    retrieval_hits = 0
    refusal_hits = 0
    keyword_scores: list[float] = []
    cases: list[EvaluationCase] = []
    for index, example in enumerate(examples, start=1):
        response = service.answer(example["question"])
        cited_ids = {citation.document_id for citation in response.citations}
        expected_id = example.get("expected_document_id")
        retrieval_correct = expected_id is None or expected_id in cited_ids
        refusal_correct = response.refused == (not example["answerable"])
        retrieval_hits += int(retrieval_correct)
        refusal_hits += int(refusal_correct)
        keywords = [word.lower() for word in example.get("required_keywords", [])]
        keyword_coverage = 1.0
        if keywords and example["answerable"]:
            text = response.answer.lower()
            keyword_coverage = sum(word in text for word in keywords) / len(keywords)
            keyword_scores.append(keyword_coverage)
        passed = retrieval_correct and refusal_correct and keyword_coverage == 1.0
        cases.append(
            EvaluationCase(
                case=index,
                question=example["question"],
                expected_answerable=example["answerable"],
                observed_refused=response.refused,
                expected_document_id=expected_id,
                observed_citation_ids=sorted(cited_ids),
                retrieval_correct=retrieval_correct,
                refusal_correct=refusal_correct,
                keyword_coverage=round(keyword_coverage, 4),
                answer=response.answer,
                passed=passed,
            )
        )

    count = len(examples)
    passed_cases = sum(case.passed for case in cases)
    return EvaluationReport(
        dataset_version=dataset["version"],
        metrics=EvaluationMetrics(
            examples=count,
            retrieval_accuracy=round(retrieval_hits / count, 4),
            refusal_accuracy=round(refusal_hits / count, 4),
            keyword_coverage=round(sum(keyword_scores) / len(keyword_scores), 4),
        ),
        passed_cases=passed_cases,
        failed_cases=count - passed_cases,
        cases=cases,
    )


def evaluate(dataset_path: Path) -> dict[str, float | int]:
    return evaluate_detailed(dataset_path).metrics.model_dump()


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
