import type { JobAnalysis, ProviderStatusResponse, ResearchEvaluation } from "../types/marketApplication";

export function readinessTone(label?: string | null): "success" | "warning" | "danger" | "muted" {
  if (!label) return "muted";
  if (label === "Apply now") return "success";
  if (label === "Apply with positioning" || label === "Prepare first") return "warning";
  if (label === "Low current feasibility") return "danger";
  return "muted";
}

export function providerWarning(status: ProviderStatusResponse | null): string {
  if (!status) return "Provider status is unavailable.";
  if (status.warning) return status.warning;
  return status.live_enabled ? "Live provider mode is enabled." : "Demo or fallback provider mode is active.";
}

export function buildLikertResponses(research: ResearchEvaluation, stage = "post_test") {
  return research.study.questions.slice(0, 8).map((question, index) => ({
    question_id: question.id,
    numeric_response: question.instrument_type === "sus" ? 3 : 4,
    text_response: "",
    workflow_stage: stage,
    response_time_ms: 1200 + index * 70,
  }));
}

export function analysisCanCreateDocuments(analysis: JobAnalysis | null): boolean {
  return Boolean(analysis && analysis.requirements.length > 0 && analysis.status !== "failed");
}
