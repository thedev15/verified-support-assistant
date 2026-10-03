import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AssistantPage } from "./AssistantPage";

const response = {
  request_id: "1234567890abcdef1234567890abcdef",
  latency_ms: 4.2,
  answer: "Card refunds usually appear in 5 to 10 business days. [REF-001]",
  citations: [
    {
      document_id: "REF-001",
      title: "Refund processing times",
      source: "/policies/REF-001",
      score: 0.84,
    },
  ],
  refused: false,
  backend: "extractive",
  model: null,
  finish_reason: null,
  prompt_tokens: null,
  completion_tokens: null,
};

afterEach(() => {
  vi.restoreAllMocks();
  window.localStorage.clear();
});

describe("AssistantPage", () => {
  it("submits through the stream and preserves the browser evidence hooks", async () => {
    const stream = [
      'event: stage\ndata: {"step":"retrieving","message":"Ranking versioned policies"}\n\n',
      `event: result\ndata: ${JSON.stringify(response)}\n\n`,
    ].join("");
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(stream, { status: 200, headers: { "Content-Type": "text/event-stream" } }),
      ),
    );

    render(
      <MemoryRouter>
        <AssistantPage />
      </MemoryRouter>,
    );
    await userEvent.click(screen.getByRole("button", { name: /verify answer/i }));

    expect(await screen.findByText("✓ Verified answer")).toBeInTheDocument();
    expect(screen.getByText(/5 to 10 business days/)).toBeInTheDocument();
    expect(screen.getAllByText(/REF-001/)).toHaveLength(2);
    await waitFor(() => expect(document.querySelector("#response")).toHaveAttribute("data-complete", "true"));
    expect(document.querySelector(".app-shell")).toBeInTheDocument();
  });
});