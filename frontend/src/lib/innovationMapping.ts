import type { AdvisorComment, AdvisorShare, BrowserJobCapture, CareerRoleProfile, DecisionJournalEntry, PanelSession } from "../types/innovationExtension";

export function extensionCapturePayload(input: {
  sourceUrl: string;
  pageTitle?: string;
  capturedText?: string;
  selectedText?: string;
  requestedAction?: string;
}) {
  const url = new URL(input.sourceUrl);
  return {
    source_url: input.sourceUrl,
    page_title: input.pageTitle ?? "",
    captured_text: input.capturedText ?? "",
    selected_text: input.selectedText ?? "",
    source_domain: url.hostname,
    capture_method: "user_triggered_browser_extension",
    requested_action: input.requestedAction ?? "save_and_analyse",
    extension_version: "frontend-simulation",
  };
}

export function tokenExpiryLabel(expiresAt?: string | null, now = new Date()) {
  if (!expiresAt) return "No expiry";
  const expires = new Date(expiresAt);
  if (Number.isNaN(expires.getTime())) return "Invalid expiry";
  const today = Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate());
  const expiryDay = Date.UTC(expires.getUTCFullYear(), expires.getUTCMonth(), expires.getUTCDate());
  const days = Math.round((expiryDay - today) / 86_400_000);
  if (days < 0) return "Expired";
  if (days === 0) return "Expires today";
  if (days === 1) return "Expires tomorrow";
  return `Expires in ${days} days`;
}

export function captureNeedsReview(capture?: BrowserJobCapture | null) {
  if (!capture) return false;
  return capture.status === "Needs review" || capture.quality_warnings.length > 0 || !capture.detected_title;
}

export function advisorPermissionSummary(share: Pick<AdvisorShare, "permission_level" | "allowed_sections" | "allowed_actions" | "export_allowed">) {
  return {
    canComment: share.allowed_actions.includes("comment") || share.allowed_actions.includes("suggest_changes"),
    canValidateEvidence: share.allowed_actions.includes("validate_selected_evidence"),
    canExport: share.export_allowed && share.allowed_actions.includes("export"),
    selectedSectionCount: share.allowed_sections.length,
    label: `${share.permission_level} across ${share.allowed_sections.length} selected section${share.allowed_sections.length === 1 ? "" : "s"}`,
  };
}

export function advisorCommentStatus(comment: AdvisorComment) {
  if (comment.status === "accepted") return { tone: "success" as const, label: "Accepted adviser suggestion" };
  if (comment.status === "rejected") return { tone: "danger" as const, label: "Rejected adviser suggestion" };
  return { tone: "warning" as const, label: "Pending user response" };
}

export function normalisePanelFeedback(session?: PanelSession | null) {
  const feedback = session?.feedback ?? {};
  const personas = Array.isArray(feedback.personas) ? feedback.personas : [];
  const unsupported = Array.isArray(feedback.unsupported_claims) ? feedback.unsupported_claims : [];
  const repeatedGaps = Array.isArray(feedback.repeated_gaps) ? feedback.repeated_gaps : [];
  return {
    personaCount: personas.length,
    unsupportedClaimCount: unsupported.length,
    repeatedGapCount: repeatedGaps.length,
    hasOpaqueScore: session?.no_single_opaque_score === false || feedback.no_single_opaque_score === false,
    prohibitedInferenceText: ["emotion", "personality", "honesty", "employability", "accent quality"],
  };
}

export function careerFamilyCounts(roles: CareerRoleProfile[]) {
  return roles.reduce<Record<string, number>>((accumulator, role) => {
    accumulator[role.career_family] = (accumulator[role.career_family] ?? 0) + 1;
    return accumulator;
  }, {});
}

export function journalStateSummary(entries: DecisionJournalEntry[]) {
  return {
    active: entries.filter((entry) => entry.status === "active").length,
    outcomes: entries.filter((entry) => Boolean(entry.outcome_status)).length,
    reconsidered: entries.filter((entry) => entry.status === "reconsidered").length,
    adviserRelated: entries.filter((entry) => entry.adviser_comment_ids.length > 0).length,
    dueReviews: entries.filter((entry) => entry.reminder_status === "due").length,
    roadmapMutations: entries.filter((entry) => entry.roadmap_mutation_allowed).length,
  };
}
