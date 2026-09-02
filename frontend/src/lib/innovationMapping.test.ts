import { describe, expect, it } from "vitest";
import {
  advisorCommentStatus,
  advisorPermissionSummary,
  captureNeedsReview,
  careerFamilyCounts,
  extensionCapturePayload,
  journalStateSummary,
  normalisePanelFeedback,
  tokenExpiryLabel,
} from "./innovationMapping";
import type { AdvisorComment, AdvisorShare, BrowserJobCapture, CareerRoleProfile, DecisionJournalEntry, PanelSession } from "../types/innovationExtension";

describe("innovation extension mapping", () => {
  it("maps extension capture payloads to backend snake_case without passive scraping flags", () => {
    const payload = extensionCapturePayload({
      sourceUrl: "https://jobs.example.test/role/123",
      pageTitle: "AI Product Designer - Example",
      capturedText: "Mandatory requirements include UX and responsible AI.",
      selectedText: "UX and responsible AI",
    });

    expect(payload.source_domain).toBe("jobs.example.test");
    expect(payload.capture_method).toBe("user_triggered_browser_extension");
    expect(payload.requested_action).toBe("save_and_analyse");
    expect(JSON.stringify(payload)).not.toContain("history");
  });

  it("guards capture review states when arrays or title data are missing", () => {
    const capture = {
      status: "Captured",
      quality_warnings: [],
      detected_title: "",
    } as unknown as BrowserJobCapture;

    expect(captureNeedsReview(capture)).toBe(true);
    expect(captureNeedsReview({ ...capture, detected_title: "Designer", status: "Analysed" })).toBe(false);
  });

  it("summarises advisor permissions and comment statuses", () => {
    const share = {
      permission_level: "Suggest changes",
      allowed_sections: ["Evidence Passport", "Job Analysis"],
      allowed_actions: ["view", "comment", "suggest_changes", "validate_selected_evidence"],
      export_allowed: false,
    } as AdvisorShare;
    const comment = { status: "accepted" } as AdvisorComment;

    expect(advisorPermissionSummary(share)).toMatchObject({ canComment: true, canValidateEvidence: true, canExport: false, selectedSectionCount: 2 });
    expect(advisorCommentStatus(comment)).toEqual({ tone: "success", label: "Accepted adviser suggestion" });
  });

  it("normalises panel feedback without introducing opaque scoring", () => {
    const session = {
      no_single_opaque_score: true,
      feedback: {
        personas: [{ persona_id: "recruiter" }, { persona_id: "technical_lead" }],
        unsupported_claims: ["unsupported production claim"],
        repeated_gaps: ["used relevant evidence"],
      },
    } as unknown as PanelSession;

    expect(normalisePanelFeedback(session)).toMatchObject({ personaCount: 2, unsupportedClaimCount: 1, repeatedGapCount: 1, hasOpaqueScore: false });
    expect(normalisePanelFeedback(session).prohibitedInferenceText).toContain("emotion");
  });

  it("counts career families and journal states with missing-array-safe records", () => {
    const roles = [
      { career_family: "AI and software" },
      { career_family: "AI and software" },
      { career_family: "Design and product" },
    ] as CareerRoleProfile[];
    const entries = [
      { status: "active", outcome_status: "", adviser_comment_ids: [], reminder_status: "due", roadmap_mutation_allowed: false },
      { status: "outcome_recorded", outcome_status: "recorded", adviser_comment_ids: ["comment-1"], reminder_status: "scheduled", roadmap_mutation_allowed: false },
      { status: "reconsidered", outcome_status: "recorded", adviser_comment_ids: [], reminder_status: "not_scheduled", roadmap_mutation_allowed: false },
    ] as DecisionJournalEntry[];

    expect(careerFamilyCounts(roles)).toEqual({ "AI and software": 2, "Design and product": 1 });
    expect(journalStateSummary(entries)).toMatchObject({ active: 1, outcomes: 2, reconsidered: 1, adviserRelated: 1, dueReviews: 1, roadmapMutations: 0 });
  });

  it("displays token expiry labels relative to a stable date", () => {
    const now = new Date("2026-07-24T12:00:00Z");

    expect(tokenExpiryLabel("2026-07-24T18:00:00Z", now)).toBe("Expires today");
    expect(tokenExpiryLabel("2026-07-25T12:00:00Z", now)).toBe("Expires tomorrow");
    expect(tokenExpiryLabel("2026-07-30T12:00:00Z", now)).toBe("Expires in 6 days");
    expect(tokenExpiryLabel("2026-07-20T12:00:00Z", now)).toBe("Expired");
  });
});
