import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { getEvaluation, type EvaluationCase } from "../api/client";

type Filter = "all" | "passed" | "failed" | "answerable" | "refusal";

export function formatPercent(value: number) {
  return `${Math.round(value * 100)}%`;
}

function matchesFilter(item: EvaluationCase, filter: Filter) {
  if (filter === "passed") return item.passed;
  if (filter === "failed") return !item.passed;
  if (filter === "answerable") return item.expected_answerable;
  if (filter === "refusal") return !item.expected_answerable;
  return true;
}

export function EvaluationsPage() {
  const [filter, setFilter] = useState<Filter>("all");
  const [query, setQuery] = useState("");
  const evaluation = useQuery({
    queryKey: ["evaluation", "latest"],
    queryFn: ({ signal }) => getEvaluation(signal),
    staleTime: 60_000,
  });
  const visible = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return (evaluation.data?.cases ?? []).filter(
      (item) =>
        matchesFilter(item, filter) &&
        (!needle ||
          item.question.toLowerCase().includes(needle) ||
          item.answer.toLowerCase().includes(needle) ||
          item.expected_document_id?.toLowerCase().includes(needle)),
    );
  }, [evaluation.data, filter, query]);

  if (evaluation.isPending) return <div className="page-shell loading-card">Running the deterministic quality view…</div>;
  if (evaluation.isError) {
    return (
      <div className="page-shell error-card">
        <h1>Evaluation results unavailable</h1>
        <p>{evaluation.error.message}</p>
        <button className="secondary-button" type="button" onClick={() => evaluation.refetch()}>Try again</button>
      </div>
    );
  }

  const { metrics } = evaluation.data;
  const metricCards = [
    ["Retrieval accuracy", metrics.retrieval_accuracy, "Expected policy cited"],
    ["Refusal accuracy", metrics.refusal_accuracy, "Correct answer/refusal decision"],
    ["Keyword coverage", metrics.keyword_coverage, "Required answer facts present"],
  ] as const;

  return (
    <div className="page-shell">
      <header className="page-hero evaluation-hero">
        <div>
          <p className="eyebrow">Inspectable quality gate</p>
          <h1>Evaluation dashboard</h1>
          <p className="lede">Every benchmark case is visible—expected behavior, observed citations, answer text, and pass state.</p>
        </div>
        <div className="release-badge">
          <span className="live-dot" />
          Dataset {evaluation.data.dataset_version}
        </div>
      </header>

      <section className="metric-grid" aria-label="Evaluation metrics">
        {metricCards.map(([label, value, detail]) => (
          <article className="metric-card" key={label}>
            <div className="metric-title"><span>{label}</span><strong>{formatPercent(value)}</strong></div>
            <div className="metric-track"><span style={{ width: formatPercent(value) }} /></div>
            <p>{detail}</p>
          </article>
        ))}
        <article className="metric-card pass-card">
          <div className="metric-title"><span>Case gate</span><strong>{evaluation.data.passed_cases}/{metrics.examples}</strong></div>
          <div className="metric-track"><span style={{ width: formatPercent(evaluation.data.passed_cases / metrics.examples) }} /></div>
          <p>{evaluation.data.failed_cases === 0 ? "Every case passes" : `${evaluation.data.failed_cases} cases need attention`}</p>
        </article>
      </section>

      <section className="evaluation-table-card">
        <div className="table-toolbar">
          <div className="filter-tabs" role="group" aria-label="Filter evaluation cases">
            {(["all", "passed", "failed", "answerable", "refusal"] as Filter[]).map((value) => (
              <button className={filter === value ? "active" : ""} type="button" key={value} onClick={() => setFilter(value)}>
                {value[0].toUpperCase() + value.slice(1)}
              </button>
            ))}
          </div>
          <label className="compact-search">
            <span className="sr-only">Search evaluation cases</span>
            <input type="search" placeholder="Search cases…" value={query} onChange={(event) => setQuery(event.target.value)} />
          </label>
        </div>
        <p className="result-count evaluation-count">Showing {visible.length} of {metrics.examples} cases</p>
        <div className="case-list">
          {visible.map((item) => (
            <details className="case-row" key={item.case}>
              <summary>
                <span className="case-number">{String(item.case).padStart(2, "0")}</span>
                <span className="case-question">{item.question}</span>
                <span className={`case-mode ${item.expected_answerable ? "answer" : "refusal"}`}>
                  {item.expected_answerable ? "Answer" : "Refuse"}
                </span>
                <span className={item.passed ? "case-status pass" : "case-status fail"}>
                  {item.passed ? "Pass" : "Fail"}
                </span>
              </summary>
              <div className="case-detail">
                <div><span>Observed output</span><p>{item.answer}</p></div>
                <dl>
                  <div><dt>Expected policy</dt><dd>{item.expected_document_id ?? "None"}</dd></div>
                  <div><dt>Observed citations</dt><dd>{item.observed_citation_ids.join(", ") || "None"}</dd></div>
                  <div><dt>Retrieval</dt><dd>{item.retrieval_correct ? "Correct" : "Incorrect"}</dd></div>
                  <div><dt>Refusal decision</dt><dd>{item.refusal_correct ? "Correct" : "Incorrect"}</dd></div>
                  <div><dt>Keyword coverage</dt><dd>{formatPercent(item.keyword_coverage)}</dd></div>
                </dl>
              </div>
            </details>
          ))}
        </div>
      </section>
    </div>
  );
}