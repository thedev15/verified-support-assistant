"use strict";

const elements = {
  form: document.querySelector("#question-form"),
  question: document.querySelector("#question"),
  button: document.querySelector("#ask"),
  response: document.querySelector("#response"),
  answer: document.querySelector("#answer"),
  status: document.querySelector("#status"),
  meta: document.querySelector("#response-meta"),
  citationSection: document.querySelector("#citation-section"),
  citations: document.querySelector("#citations"),
  actions: document.querySelector("#response-actions"),
  copy: document.querySelector("#copy-answer"),
  askAnother: document.querySelector("#ask-another"),
  count: document.querySelector("#character-count"),
  runtime: document.querySelector("#runtime-status"),
  theme: document.querySelector("#theme-toggle"),
};

function updateCharacterCount() {
  elements.count.textContent = `${elements.question.value.length.toLocaleString()} / 2,000`;
}

function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  const nextTheme = theme === "dark" ? "light" : "dark";
  elements.theme.setAttribute("aria-label", `Use ${nextTheme} theme`);
  elements.theme.title = `Use ${nextTheme} theme`;
}

function initializeTheme() {
  const saved = localStorage.getItem("vsa-theme");
  const preferred = window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";
  applyTheme(saved || preferred);
}

function addCitation(citation) {
  const row = document.createElement("article");
  row.className = "citation";

  const icon = document.createElement("span");
  icon.className = "doc-icon";
  icon.setAttribute("aria-hidden", "true");
  icon.textContent = "▤";

  const copy = document.createElement("div");
  const title = document.createElement("strong");
  title.textContent = `${citation.document_id} · ${citation.title}`;
  const source = document.createElement("a");
  source.href = citation.source;
  source.target = "_blank";
  source.rel = "noopener";
  source.textContent = `Open policy source · ${citation.source}`;
  copy.append(title, source);

  const score = document.createElement("span");
  score.className = "score";
  score.textContent = `${Math.round(citation.score * 100)}% match`;
  row.append(icon, copy, score);
  elements.citations.append(row);
}

function beginRequest() {
  delete elements.response.dataset.complete;
  delete elements.response.dataset.refused;
  elements.response.hidden = false;
  elements.status.className = "status checking";
  elements.status.textContent = "● Checking policies";
  elements.meta.textContent = "Retrieving evidence…";
  elements.answer.className = "";
  elements.answer.textContent = "Checking the versioned policy corpus…";
  elements.citations.replaceChildren();
  elements.citationSection.hidden = true;
  elements.actions.hidden = true;
  elements.button.disabled = true;
  elements.button.querySelector("span").textContent = "Verifying…";
}

function renderResult(data) {
  elements.answer.textContent = data.answer;
  const timing = Number.isFinite(data.latency_ms) ? ` · ${Math.round(data.latency_ms)} ms` : "";
  if (data.refused) {
    elements.status.className = "status refused";
    elements.status.textContent = "◆ Safely refused";
    elements.meta.textContent = `${data.backend} backend · no unsupported claim${timing}`;
  } else {
    elements.status.className = "status verified";
    elements.status.textContent = "✓ Verified answer";
    const sourceLabel = data.citations.length === 1 ? "policy source" : "policy sources";
    elements.meta.textContent = `${data.backend} backend · ${data.citations.length} ${sourceLabel}${timing}`;
    data.citations.forEach(addCitation);
    elements.citationSection.hidden = false;
  }
  elements.actions.hidden = false;
  elements.response.dataset.complete = "true";
  elements.response.dataset.refused = String(data.refused);
  elements.response.tabIndex = -1;
  elements.response.focus({preventScroll: true});
}

function renderError(error) {
  const timedOut = error.name === "AbortError";
  elements.status.className = "status refused";
  elements.status.textContent = "! Verification unavailable";
  elements.meta.textContent = "Nothing was submitted or changed";
  elements.answer.className = "error";
  elements.answer.textContent = timedOut
    ? "The verification request timed out. Please try again."
    : "The policy service could not verify this question. Please try again.";
  elements.response.dataset.complete = "error";
  console.error("VSA request failed", error);
}

async function submitQuestion() {
  const question = elements.question.value.trim();
  if (!question || !elements.form.reportValidity()) return;
  beginRequest();
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 30_000);
  try {
    const apiResponse = await fetch("/api/ask", {
      method: "POST",
      headers: {"Content-Type": "application/json", "Accept": "application/json"},
      body: JSON.stringify({question}),
      signal: controller.signal,
    });
    if (!apiResponse.ok) throw new Error(`Request failed with HTTP ${apiResponse.status}`);
    renderResult(await apiResponse.json());
  } catch (error) {
    renderError(error);
  } finally {
    window.clearTimeout(timeout);
    elements.button.disabled = false;
    elements.button.querySelector("span").textContent = "Verify answer";
  }
}

elements.form.addEventListener("submit", event => {
  event.preventDefault();
  submitQuestion();
});

elements.question.addEventListener("input", updateCharacterCount);
elements.question.addEventListener("keydown", event => {
  if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
    event.preventDefault();
    elements.form.requestSubmit();
  }
});

document.querySelectorAll(".example-chip").forEach(button => {
  button.addEventListener("click", () => {
    elements.question.value = button.textContent;
    updateCharacterCount();
    elements.question.focus();
  });
});

elements.copy.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(elements.answer.textContent);
    elements.copy.textContent = "Copied";
    window.setTimeout(() => { elements.copy.textContent = "Copy answer"; }, 1_500);
  } catch {
    elements.copy.textContent = "Copy unavailable";
  }
});

elements.askAnother.addEventListener("click", () => {
  elements.response.hidden = true;
  elements.question.select();
  elements.question.focus();
});

elements.theme.addEventListener("click", () => {
  const theme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  localStorage.setItem("vsa-theme", theme);
  applyTheme(theme);
});

async function loadRuntimeMetadata() {
  try {
    const response = await fetch("/api/meta", {headers: {"Accept": "application/json"}});
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const metadata = await response.json();
    elements.runtime.textContent = `${metadata.document_count} policies online · ${metadata.backend} backend · v${metadata.version}`;
  } catch {
    elements.runtime.textContent = "Policy service status unavailable";
  }
}

initializeTheme();
updateCharacterCount();
loadRuntimeMetadata();