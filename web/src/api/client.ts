import type { components } from "./schema";

export type AskResponse = components["schemas"]["AskResponse"];
export type RuntimeMetadata = components["schemas"]["RuntimeMetadata"];
export type PolicySummary = components["schemas"]["PolicySummary"];
export type PolicyDetail = components["schemas"]["PolicyDetail"];
export type EvaluationReport = components["schemas"]["EvaluationReport"];
export type EvaluationCase = components["schemas"]["EvaluationCase"];

export interface StreamStage {
  step: string;
  message: string;
}

async function errorMessage(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: string | Array<{ msg?: string }> };
    if (typeof body.detail === "string") return body.detail;
    if (Array.isArray(body.detail)) return body.detail.map((item) => item.msg).join("; ");
  } catch {
    // The generic HTTP message below is safe even for non-JSON upstream failures.
  }
  return `Request failed with HTTP ${response.status}`;
}

export async function fetchJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(path, {
    headers: { Accept: "application/json" },
    signal,
  });
  if (!response.ok) throw new Error(await errorMessage(response));
  return (await response.json()) as T;
}

export const getMetadata = (signal?: AbortSignal) =>
  fetchJson<RuntimeMetadata>("/api/meta", signal);

export const getPolicies = (signal?: AbortSignal) =>
  fetchJson<PolicySummary[]>("/api/policies", signal);

export const getPolicy = (documentId: string, signal?: AbortSignal) =>
  fetchJson<PolicyDetail>(`/api/policies/${encodeURIComponent(documentId)}`, signal);

export const getEvaluation = (signal?: AbortSignal) =>
  fetchJson<EvaluationReport>("/api/evaluations/latest", signal);

interface ParsedEvent {
  event: string;
  data: string;
}

export function parseEventBlock(block: string): ParsedEvent | null {
  const lines = block.split("\n");
  const event = lines.find((line) => line.startsWith("event:"))?.slice(6).trim();
  const data = lines
    .filter((line) => line.startsWith("data:"))
    .map((line) => line.slice(5).trimStart())
    .join("\n");
  return event && data ? { event, data } : null;
}

export async function askQuestionStream(
  question: string,
  onStage: (stage: StreamStage) => void,
  signal?: AbortSignal,
): Promise<AskResponse> {
  const response = await fetch("/api/ask/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
    body: JSON.stringify({ question }),
    signal,
  });
  if (!response.ok) throw new Error(await errorMessage(response));
  if (!response.body) throw new Error("Streaming response body was unavailable");

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let result: AskResponse | undefined;

  while (true) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value, { stream: !done }).replaceAll("\r\n", "\n");
    const blocks = buffer.split("\n\n");
    buffer = blocks.pop() ?? "";
    for (const block of blocks) {
      const parsed = parseEventBlock(block);
      if (!parsed) continue;
      if (parsed.event === "stage") onStage(JSON.parse(parsed.data) as StreamStage);
      if (parsed.event === "result") result = JSON.parse(parsed.data) as AskResponse;
    }
    if (done) break;
  }

  const trailing = parseEventBlock(buffer);
  if (trailing?.event === "result") result = JSON.parse(trailing.data) as AskResponse;
  if (!result) throw new Error("The verification stream ended without a result");
  return result;
}