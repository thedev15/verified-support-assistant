import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { getPolicies } from "../api/client";

export function PoliciesPage() {
  const [query, setQuery] = useState("");
  const policies = useQuery({
    queryKey: ["policies"],
    queryFn: ({ signal }) => getPolicies(signal),
  });
  const visible = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) return policies.data ?? [];
    return (policies.data ?? []).filter((policy) =>
      [policy.document_id, policy.title, policy.excerpt].some((value) =>
        value.toLowerCase().includes(needle),
      ),
    );
  }, [policies.data, query]);

  return (
    <div className="page-shell">
      <header className="page-hero policy-hero">
        <div>
          <p className="eyebrow">Versioned evidence boundary</p>
          <h1>Policy library</h1>
          <p className="lede">
            Explore the complete synthetic corpus that the assistant is allowed to cite. Search by
            topic, identifier, or policy language.
          </p>
        </div>
        <div className="hero-stat">
          <strong>{policies.data?.length ?? "—"}</strong>
          <span>versioned policies</span>
        </div>
      </header>

      <div className="toolbar">
        <label className="search-field">
          <span className="sr-only">Search policies</span>
          <span aria-hidden="true">⌕</span>
          <input
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search refunds, shipping, security…"
          />
        </label>
        <span className="result-count">{visible.length} results</span>
      </div>

      {policies.isPending && <div className="loading-card">Loading the versioned corpus…</div>}
      {policies.isError && (
        <div className="error-card">
          <h2>Policy library unavailable</h2>
          <p>{policies.error.message}</p>
          <button type="button" className="secondary-button" onClick={() => policies.refetch()}>
            Try again
          </button>
        </div>
      )}
      {policies.isSuccess && visible.length === 0 && (
        <div className="empty-state">
          <h2>No policy matched “{query}”</h2>
          <p>Try a broader phrase or clear the search to browse all evidence.</p>
          <button type="button" className="secondary-button" onClick={() => setQuery("")}>Clear search</button>
        </div>
      )}

      <div className="policy-grid">
        {visible.map((policy) => (
          <Link className="policy-card" to={`/policies/${policy.document_id}`} key={policy.document_id}>
            <div className="policy-card-head">
              <span className="policy-id">{policy.document_id}</span>
              <span aria-hidden="true">↗</span>
            </div>
            <h2>{policy.title}</h2>
            <p>{policy.excerpt}</p>
            <span className="policy-card-link">Read policy <b>→</b></span>
          </Link>
        ))}
      </div>
    </div>
  );
}