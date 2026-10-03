import { Link } from "react-router-dom";

const STEPS = [
  ["01", "Validate the request", "Pydantic rejects malformed input while scope rules block private actions, secrets, unsafe instructions, and unsupported domains."],
  ["02", "Retrieve evidence", "A transparent TF-IDF index ranks the versioned policy corpus. Weak evidence triggers refusal rather than speculation."],
  ["03", "Generate within bounds", "The deterministic baseline or optional Forge model receives only relevant policies and must cite the evidence used."],
  ["04", "Return a typed result", "FastAPI validates the final answer, citations, refusal state, latency, and request ID before React renders it."],
];

export function AboutPage() {
  return (
    <div className="page-shell about-page">
      <header className="page-hero about-hero">
        <div>
          <p className="eyebrow">Trustworthy by construction</p>
          <h1>Support answers with an inspectable evidence trail.</h1>
          <p className="lede">Verified Support Studio demonstrates how retrieval, typed contracts, explicit authority boundaries, and measurable evaluations can make an AI interface safer and easier to audit.</p>
          <div className="hero-actions">
            <Link className="primary-button inline-button" to="/assistant">Try the assistant <b>→</b></Link>
            <Link className="secondary-button inline-button" to="/evaluations">View evaluation results</Link>
          </div>
        </div>
        <div className="architecture-orbit" aria-label="React, FastAPI, Pydantic, and Python architecture">
          <span className="orbit-core">VSA</span>
          <span className="orbit-node node-react">React</span>
          <span className="orbit-node node-fastapi">FastAPI</span>
          <span className="orbit-node node-pydantic">Pydantic</span>
          <span className="orbit-node node-python">Python</span>
        </div>
      </header>

      <section className="about-section">
        <p className="eyebrow">Request lifecycle</p>
        <h2>How verification works</h2>
        <div className="process-grid">
          {STEPS.map(([number, title, description]) => (
            <article className="process-card" key={number}>
              <span>{number}</span><h3>{title}</h3><p>{description}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="boundary-section">
        <div>
          <p className="eyebrow">Explicit limitations</p>
          <h2>What this system will not do</h2>
          <p>The demo has no customer accounts, order database, payment authority, or transaction tools. It cannot inspect private records or perform actions.</p>
        </div>
        <ul>
          <li><span>×</span>Reveal passwords, one-time codes, or payment details</li>
          <li><span>×</span>Access, change, place, or cancel customer orders</li>
          <li><span>×</span>Invent answers when policy evidence is weak</li>
          <li><span>×</span>Follow instructions that override its safety boundary</li>
        </ul>
      </section>

      <section className="stack-section">
        <div className="stack-card"><strong>React + TypeScript</strong><p>Accessible product interface, streaming state, local history, policy search, and evaluation exploration.</p></div>
        <div className="stack-card"><strong>FastAPI + Pydantic</strong><p>OpenAPI-first typed contracts, validation, SSE progress, security headers, and production serving.</p></div>
        <div className="stack-card"><strong>Python retrieval</strong><p>Inspectable ranking, deterministic safety decisions, optional Forge Inference, and Weave traces.</p></div>
      </section>
    </div>
  );
}