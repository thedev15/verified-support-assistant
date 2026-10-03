import { describe, expect, it } from "vitest";

import { formatPercent } from "./EvaluationsPage";

describe("formatPercent", () => {
  it("renders evaluation ratios as readable percentages", () => {
    expect(formatPercent(1)).toBe("100%");
    expect(formatPercent(0.954)).toBe("95%");
    expect(formatPercent(0)).toBe("0%");
  });
});