import { describe, expect, it } from "vitest";

import { parseEventBlock } from "./client";

describe("parseEventBlock", () => {
  it("parses a streaming result event", () => {
    expect(parseEventBlock('event: result\ndata: {"refused":false}')).toEqual({
      event: "result",
      data: '{"refused":false}',
    });
  });

  it("joins multiline event data", () => {
    expect(parseEventBlock("event: stage\ndata: first\ndata: second")).toEqual({
      event: "stage",
      data: "first\nsecond",
    });
  });

  it("ignores incomplete blocks", () => {
    expect(parseEventBlock("data: pending")).toBeNull();
  });
});