import { type FormEvent, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";

import { askQuestionStream, type AskResponse, type StreamStage } from "../api/client";
import { useConversationHistory } from "../hooks/useConversationHistory";

const EXAMPLES = [
  "How long does a card refund take?",
  "Can I change my shipping address after checkout?",
  "Should I share my one-time code with support?",
];

export function AssistantPage() {
  const [question, setQuestion] = useState(EXAMPLES[0]);
  const [result, setResult] = useState<AskResponse>();
  const [stage, setStage] = useState<StreamStage>();
  const [error, setError] = useState<string>();
  const [pending, setPending] = useState(false);
  const [copied, setCopied] = useState(false);
  const controller = useRef<AbortController | undefined>(undefined);
  const responseRef = useRef<HTMLElement>(null);
  const { history, add, clear } = useConversationHistory();

  useEffect(() => () => controller.current?.abort(), []);

  async function submit(event: FormEvent) {
    event.preventDefault();
    const normalized = question.trim();
    if (normalized.length < 3) return;
    controller.current?.abort();
    controller.current = new AbortController();
    setPending(true);
    setResult(undefined);
    setError(undefined);
    setStage({ step: "connecting", message: "Opening verification stream" });
    const timeout = window.setTimeout(() => controller.current?.abort(), 30_000);
    try {
      const response = await askQuestionStream(normalized, setStage, controller.current.signal);
      setResult(response);
      add(normalized, response);
      window.setTimeout(() => responseRef.current?.focus({ preventScroll: true }), 0);
    } catch (caught) {
      if ((caught as Error).name === "AbortError") {
        setError("The verification request timed out or was cancelled. Please try again.");
      } else {
        setError((caught as Error).message || "The policy service could not verify this question.");
      }
    } finally {
      window.clearTimeout(timeout);
      setPending(false);
    }
  }

  function restore(item: (typeof history)[number]) {
    setQuestion(item.question);
    setResult(item.response);
    setError(undefined);
    setStage(undefined);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  async function copyAnswer() {
    if (!result) return;
    await navigator.clipboard.writeText(result.answer);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1_500);
  }

  const complete = result ? "true" : error ? "error" : undefined;

  return (
    <div className="app-shell">
      <section className="assistant-card" aria-labelledby="page-title">
        <p className="eyebrow">Citation-first customer support</p>
        <h1 id="page-title">
          Answers you can verify,
          <br />
          <span>not just trust.</span>
        </h1>
        <p className="lede">
          Ask about shipping, returns, refunds, warranties, payments, gift cards, or account
          security. Supported answers disclose the exact policy used; unsupported requests are
          refused.
        </p>

        <div className="examples" aria-label="Example questions">
          <span>Try an example</span>
          {EXAMPLES.map((example) => (
            <button key={example} className="example-chip" type="button" onClick={() => setQuestion(example)}>
              {example}
            </button>
          ))}
        </div>

        <form id="question-form" onSubmit={submit}>
          <div className="field-heading">
            <label htmlFor="question">Your support question</label>
            <span aria-live="polite">{question.length.toLocaleString()} / 2,000</span>
          </div>
          <textarea
            id="question"
            name="question"
            required
            minLength={3}
            maxLength={2_000}
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
                event.preventDefault();
                event.currentTarget.form?.requestSubmit();
              }
            }}
            aria-describedby="scope-note keyboard-note"
          />
          <div className="form-bottom">
            <div>
              <span id="scope-note" className="scope">
                No account access · No transactions · Policy answers only
              </span>
              <span id="keyboard-note" className="keyboard-note">
                Ctrl/⌘ + Enter to verify
              </span>
            </div>
            <button id="ask" className="primary-button" type="submit" disabled={pending}>
              <span>{pending ? "Verifying…" : "Verify answer"}</span>
              <b aria-hidden="true">→</b>
            </button>
          </div>
        </form>

        <section
          id="response"
          ref={responseRef}
          className="response"
          aria-live="polite"
          aria-atomic="false"
          hidden={!pending && !result && !error}
          data-complete={complete}
          data-refused={result ? String(result.refused) : undefined}
          tabIndex={-1}
        >
          <div className="response-head">
            <span className={`status ${pending ? "checking" : result?.refused || error ? "refused" : "verified"}`}>
              {pending ? "● Verifying evidence" : error ? "! Verification unavailable" : result?.refused ? "◆ Safely refused" : "✓ Verified answer"}
            </span>
            <span className="response-meta">
              {pending
                ? stage?.message
                : result
                  ? `${result.backend} · ${Math.round(result.latency_ms ?? 0)} ms · ${(result.request_id ?? "pending").slice(0, 8)}`
                  : "Nothing was submitted or changed"}
            </span>
          </div>

          {pending && (
            <div className="verification-progress" aria-label="Verification progress">
              <span />
              <p>{stage?.message ?? "Checking the versioned policy corpus…"}</p>
            </div>
          )}
          {error && <p className="answer error">{error}</p>}
          {result && (
            <>
              <p className="answer">{result.answer}</p>
              <div className="response-actions">
                <button className="secondary-button" type="button" onClick={copyAnswer}>
                  {copied ? "Copied" : "Copy answer"}
                </button>
                <button
                  className="secondary-button"
                  type="button"
                  onClick={() => {
                    setResult(undefined);
                    setQuestion("");
                    document.querySelector<HTMLTextAreaElement>("#question")?.focus();
                  }}
                >
                  Ask another
                </button>
              </div>
              {result.citations.length > 0 && (
                <div className="citation-section">
                  <div className="section-heading">
                    <p className="citations-title">Verified policy sources</p>
                    <Link to="/policies">Browse all policies</Link>
                  </div>
                  <div className="citation-list">
                    {result.citations.map((citation) => (
                      <article className="citation" key={citation.document_id}>
                        <span className="doc-icon" aria-hidden="true">▤</span>
                        <div>
                          <strong>{citation.document_id} · {citation.title}</strong>
                          <Link to={citation.source}>Open versioned policy</Link>
                        </div>
                        <span className="score">{Math.round(citation.score * 100)}% match</span>
                      </article>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </section>
      </section>

      <aside className="studio-sidebar" aria-label="Verification and conversation history">
        <section className="verification-panel">
          <div className="panel-head">
            <div className="shield" aria-hidden="true">◆</div>
            <p className="eyebrow">Trust architecture</p>
            <h2>Verification built in</h2>
            <p>The assistant answers only when the versioned corpus provides sufficient evidence.</p>
          </div>
          <div className="checks">
            <div className="check"><b>1</b><div><strong>Scope checked</strong><span>Private actions and unsafe requests are refused.</span></div></div>
            <div className="check"><b>2</b><div><strong>Evidence ranked</strong><span>Transparent retrieval finds relevant policy text.</span></div></div>
            <div className="check"><b>3</b><div><strong>Sources disclosed</strong><span>Supported answers link to their actual evidence.</span></div></div>
          </div>
          <div className="panel-links">
            <Link to="/about">How it works <span>→</span></Link>
            <Link to="/evaluations">See quality results <span>→</span></Link>
          </div>
        </section>

        <section className="history-panel">
          <div className="section-heading">
            <div>
              <p className="eyebrow">This browser only</p>
              <h2>Recent questions</h2>
            </div>
            {history.length > 0 && <button className="text-button" type="button" onClick={clear}>Clear</button>}
          </div>
          {history.length === 0 ? (
            <p className="empty-copy">Verified answers will appear here. History never leaves this browser.</p>
          ) : (
            <ol className="history-list">
              {history.slice(0, 5).map((item) => (
                <li key={item.id}>
                  <button type="button" onClick={() => restore(item)}>
                    <span className={item.response.refused ? "history-state refused" : "history-state verified"}>
                      {item.response.refused ? "Refused" : "Verified"}
                    </span>
                    <strong>{item.question}</strong>
                    <small>{new Date(item.createdAt).toLocaleString()}</small>
                  </button>
                </li>
              ))}
            </ol>
          )}
        </section>
      </aside>
    </div>
  );
}