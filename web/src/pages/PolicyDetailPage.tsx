import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";

import { getPolicy } from "../api/client";

export function PolicyDetailPage() {
  const { documentId = "" } = useParams();
  const policy = useQuery({
    queryKey: ["policy", documentId],
    queryFn: ({ signal }) => getPolicy(documentId, signal),
    enabled: Boolean(documentId),
  });

  if (policy.isPending) return <div className="page-shell loading-card">Loading policy evidence…</div>;
  if (policy.isError) {
    return (
      <div className="page-shell error-card">
        <p className="eyebrow">Policy unavailable</p>
        <h1>{documentId}</h1>
        <p>{policy.error.message}</p>
        <Link className="secondary-button inline-button" to="/policies">Return to policy library</Link>
      </div>
    );
  }

  return (
    <article className="document-page">
      <Link className="back-link" to="/policies">← Policy library</Link>
      <p className="eyebrow">Versioned support policy · {policy.data.document_id}</p>
      <h1>{policy.data.title}</h1>
      <div className="policy-metadata">
        <span>Evidence status</span><strong>Active</strong>
        <span>Source route</span><code>{policy.data.source}</code>
      </div>
      <p className="policy-copy">{policy.data.text}</p>
      <footer className="page-footer">
        <Link to="/assistant">Ask the assistant</Link>
        <Link to="/evaluations">Inspect quality results</Link>
      </footer>
    </article>
  );
}