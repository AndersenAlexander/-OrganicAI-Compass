import { apiClient } from "./client";
import type {
  AssessmentDefinition,
  AssessmentMode,
  AssessmentPrefill,
  AssessmentResponse,
  AssessmentResults,
  AssessmentSession,
  CareerComparison,
  CareerMatch,
} from "../types/assessment";

const assessmentId = "human-potential-career-assessment";

export async function getAssessmentDefinition(mode?: AssessmentMode) {
  const { data } = await apiClient.get<AssessmentDefinition>(`/v1/assessments/${assessmentId}`, { params: mode ? { mode } : undefined });
  return data;
}

export async function getCurrentAssessmentSession(profileId: string) {
  const { data } = await apiClient.get<{ session: AssessmentSession | null; definition: AssessmentDefinition; disclaimer: string; prefill?: AssessmentPrefill }>(
    `/v1/profiles/${profileId}/assessment-sessions/current`
  );
  return data;
}

export async function createAssessmentSession(profileId: string, mode: AssessmentMode, consentAccepted: boolean) {
  const { data } = await apiClient.post<{ session: AssessmentSession; definition: AssessmentDefinition; disclaimer: string; prefill?: AssessmentPrefill }>(
    `/v1/profiles/${profileId}/assessment-sessions`,
    { mode, consent_accepted: consentAccepted }
  );
  return data;
}

export async function saveAssessmentResponses(
  sessionId: string,
  responses: Array<{ item_id: string; module_id?: string; response_type?: string; value: unknown; excluded_from_recommendations?: boolean }>
) {
  const { data } = await apiClient.post<{ status: string; responses: AssessmentResponse[]; session: AssessmentSession }>(
    `/v1/assessment-sessions/${sessionId}/responses`,
    { responses }
  );
  return data;
}

export async function completeAssessmentSession(sessionId: string) {
  const { data } = await apiClient.post<{
    status: string;
    missing_required_items?: string[];
    session: AssessmentSession;
    results?: AssessmentResults;
    career_matches?: CareerMatch[];
  }>(`/v1/assessment-sessions/${sessionId}/complete`);
  return data;
}

export async function getAssessmentResults(profileId: string) {
  const { data } = await apiClient.get<AssessmentResults>(`/v1/profiles/${profileId}/assessment-results`);
  return data;
}

export async function confirmAssessmentResults(
  profileId: string,
  payload: { summary?: string; corrections?: Record<string, unknown>; reflection_answers?: Record<string, unknown>; confirmation_status?: string }
) {
  const { data } = await apiClient.post(`/v1/profiles/${profileId}/assessment-results/confirm`, payload);
  return data;
}

export async function getCareerMatches(profileId: string, includeRejected = false) {
  const { data } = await apiClient.get<CareerMatch[]>(`/v1/profiles/${profileId}/career-matches`, {
    params: includeRejected ? { include_rejected: true } : undefined,
  });
  return data;
}

export async function saveCareerMatch(matchId: string, payload?: { feedback_text?: string; user_priority?: number }) {
  const { data } = await apiClient.post<CareerMatch>(`/v1/career-matches/${matchId}/save`, payload || {});
  return data;
}

export async function rejectCareerMatch(matchId: string, payload?: { feedback_text?: string; reason_code?: string }) {
  const { data } = await apiClient.post<CareerMatch>(`/v1/career-matches/${matchId}/reject`, payload || {});
  return data;
}

export async function requestCareerAlternative(matchId: string, payload?: { feedback_text?: string }) {
  const { data } = await apiClient.post<{ status: string; career_match: CareerMatch; alternatives: CareerMatch[] }>(
    `/v1/career-matches/${matchId}/request-alternative`,
    payload || {}
  );
  return data;
}

export async function createCareerRoadmapDraft(matchId: string) {
  const { data } = await apiClient.post<{ roadmap_id: string; career_match: CareerMatch; actions: Array<{ id: string; title: string; horizon: string; status: string }> }>(
    `/v1/career-matches/${matchId}/create-roadmap-draft`
  );
  return data;
}

export async function createCareerComparison(
  profileId: string,
  matchIds: string[],
  criteriaWeights?: Record<string, number>,
  decisionPriorities?: Record<string, unknown>
) {
  const { data } = await apiClient.post<CareerComparison>(`/v1/profiles/${profileId}/career-comparisons`, {
    match_ids: matchIds,
    criteria_weights: criteriaWeights || {},
    decision_priorities: decisionPriorities || {},
  });
  return data;
}

export async function deleteAssessmentData(profileId: string) {
  const { data } = await apiClient.delete<{ status: string; deleted: Record<string, number> }>(`/v1/profiles/${profileId}/assessment-data`);
  return data;
}
