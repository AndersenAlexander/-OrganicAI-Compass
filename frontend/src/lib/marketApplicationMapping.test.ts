import { describe, expect, it } from "vitest";
import { analysisCanCreateDocuments, buildLikertResponses, providerWarning, readinessTone } from "./marketApplicationMapping";
import type { JobAnalysis, ResearchEvaluation } from "../types/marketApplication";

describe("marketApplicationMapping", () => {
  it("maps readiness labels to deterministic UI tones", () => {
    expect(readinessTone("Apply now")).toBe("success");
    expect(readinessTone("Prepare first")).toBe("warning");
    expect(readinessTone("Low current feasibility")).toBe("danger");
    expect(readinessTone("Insufficient information")).toBe("muted");
  });

  it("surfaces provider fallback warnings without exposing credentials", () => {
    expect(providerWarning(null)).toContain("unavailable");
    expect(providerWarning({ active_provider: "demo", live_enabled: false, warning: "", providers: [] })).toContain("fallback");
    expect(providerWarning({ active_provider: "nav_stilling_feed", live_enabled: true, warning: "", providers: [] })).toContain("enabled");
  });

  it("creates bounded research responses without raw free text", () => {
    const research = {
      study: {
        questions: [
          { id: "q1", instrument_type: "custom_likert" },
          { id: "sus-1", instrument_type: "sus" },
        ],
      },
    } as ResearchEvaluation;
    const responses = buildLikertResponses(research, "post_test");
    expect(responses).toEqual([
      { question_id: "q1", numeric_response: 4, text_response: "", workflow_stage: "post_test", response_time_ms: 1200 },
      { question_id: "sus-1", numeric_response: 3, text_response: "", workflow_stage: "post_test", response_time_ms: 1270 },
    ]);
  });

  it("requires extracted requirements before document generation", () => {
    expect(analysisCanCreateDocuments(null)).toBe(false);
    expect(analysisCanCreateDocuments({ requirements: [], status: "analysed" } as unknown as JobAnalysis)).toBe(false);
    expect(analysisCanCreateDocuments({ requirements: [{ id: "r1" }], status: "analysed" } as unknown as JobAnalysis)).toBe(true);
    expect(analysisCanCreateDocuments({ requirements: [{ id: "r1" }], status: "failed" } as unknown as JobAnalysis)).toBe(false);
  });
});
