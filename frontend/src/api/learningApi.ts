import { apiClient } from "./client";
import type {
  LearningPath,
  LearningPreferences,
  LearningRecommendation,
  LearningProvider,
  LearningRecommendationRun,
  LearningResource,
  LearningResourceComparison,
  SkillGapAnalysis,
} from "../types/learning";

function asArray<T>(value: T[] | null | undefined): T[] {
  return Array.isArray(value) ? value : [];
}

function asRecord<T = unknown>(value: Record<string, T> | null | undefined): Record<string, T> {
  return value && typeof value === "object" && !Array.isArray(value) ? value : {};
}

function normalizeLearningResource(resource: LearningResource | null | undefined): LearningResource {
  const fallback: LearningResource = {
    id: "unknown-resource",
    provider_id: "unknown",
    external_id: null,
    title: "Learning resource",
    canonical_url: "#",
    description: "",
    resource_type: "resource",
    resource_type_label: "Resource",
    level: "not_specified",
    language: "en",
    subtitles: [],
    duration_minutes: null,
    cost_type: "unknown",
    displayed_price: null,
    currency: null,
    instructor_organization: null,
    rating: null,
    review_count: null,
    publication_date: null,
    last_updated_date: null,
    last_verified_at: null,
    prerequisites: [],
    certificate_available: null,
    practical_exercises: false,
    project_included: false,
    quality_status: "Unverified",
    source_provenance: "Not provided",
    active: true,
    affiliate: false,
    affiliate_disclosure: "No affiliate relationship is used for ranking.",
    notes_limitations: "",
    metadata_version: "unknown",
    skills: [],
    objective_keys: [],
  };
  if (!resource) return fallback;
  return {
    ...fallback,
    ...resource,
    subtitles: asArray(resource.subtitles),
    prerequisites: asArray(resource.prerequisites),
    skills: asArray(resource.skills),
    objective_keys: asArray(resource.objective_keys),
    language: resource.language || "en",
    resource_type_label: resource.resource_type_label || resource.resource_type?.replace(/_/g, " ") || "Resource",
    quality_status: resource.quality_status || "Unverified",
    source_provenance: resource.source_provenance || "Not provided",
    affiliate_disclosure: resource.affiliate_disclosure || "No affiliate relationship is used for ranking.",
  };
}

function normalizeLearningRecommendation(item: LearningRecommendation): LearningRecommendation {
  return {
    ...item,
    limitations: asArray(item.limitations),
    factors: asArray(item.factors),
    resource: normalizeLearningResource(item.resource),
  };
}

function normalizeLearningPreferences(preferences: LearningPreferences): LearningPreferences {
  return {
    ...preferences,
    preferred_language: preferences.preferred_language || "en",
    acceptable_secondary_languages: asArray(preferences.acceptable_secondary_languages),
    preferred_content_formats: asArray(preferences.preferred_content_formats),
    accessibility_preferences: asArray(preferences.accessibility_preferences),
    provider_exclusions: asArray(preferences.provider_exclusions),
    metadata: asRecord(preferences.metadata),
  };
}

function normalizeSkillGapAnalysis(analysis: SkillGapAnalysis): SkillGapAnalysis {
  return {
    ...analysis,
    hard_filters: asArray(analysis.hard_filters),
    context: asRecord(analysis.context),
    items: asArray(analysis.items),
    objectives: asArray(analysis.objectives),
    practical_projects: asArray(analysis.practical_projects),
  };
}

function normalizeLearningRecommendationRun(run: LearningRecommendationRun): LearningRecommendationRun {
  const recommendations = asArray(run.recommendations).map(normalizeLearningRecommendation);
  return {
    ...run,
    status: run.status || "not_started",
    provider_status: asArray(run.provider_status),
    hard_filters: asArray(run.hard_filters),
    ranking_weights: asRecord(run.ranking_weights),
    recommendations,
    grouped_by_skill_gap: asRecord(run.grouped_by_skill_gap),
  };
}

export async function getLearningProviders() {
  const { data } = await apiClient.get<LearningProvider[]>("/v1/learning/providers");
  return data;
}

export async function getLearningResources(params?: { provider?: string; skill_id?: string; active_only?: boolean }) {
  const { data } = await apiClient.get<LearningResource[]>("/v1/learning/resources", { params });
  return data.map(normalizeLearningResource);
}

export async function getLearningResource(resourceId: string) {
  const { data } = await apiClient.get<LearningResource>(`/v1/learning/resources/${resourceId}`);
  return normalizeLearningResource(data);
}

export async function getLearningPreferences(profileId: string) {
  const { data } = await apiClient.get<LearningPreferences>(`/v1/profiles/${profileId}/learning-preferences`);
  return normalizeLearningPreferences(data);
}

export async function updateLearningPreferences(profileId: string, payload: Partial<LearningPreferences>) {
  const { data } = await apiClient.put<LearningPreferences>(`/v1/profiles/${profileId}/learning-preferences`, payload);
  return normalizeLearningPreferences(data);
}

export async function createSkillGapAnalysis(profileId: string, careerMatchId?: string) {
  const { data } = await apiClient.post<SkillGapAnalysis>(`/v1/profiles/${profileId}/skill-gap-analysis`, {
    career_match_id: careerMatchId,
  });
  return normalizeSkillGapAnalysis(data);
}

export async function getSkillGapAnalysis(profileId: string, careerMatchId?: string) {
  const { data } = await apiClient.get<SkillGapAnalysis>(`/v1/profiles/${profileId}/skill-gap-analysis`, {
    params: careerMatchId ? { career_match_id: careerMatchId } : undefined,
  });
  return normalizeSkillGapAnalysis(data);
}

export async function generateLearningRecommendations(profileId: string, careerMatchId?: string) {
  const { data } = await apiClient.post<LearningRecommendationRun>(`/v1/profiles/${profileId}/learning-recommendations`, {
    career_match_id: careerMatchId,
  });
  return normalizeLearningRecommendationRun(data);
}

export async function getLearningRecommendations(profileId: string, careerMatchId?: string) {
  const { data } = await apiClient.get<LearningRecommendationRun>(`/v1/profiles/${profileId}/learning-recommendations`, {
    params: careerMatchId ? { career_match_id: careerMatchId } : undefined,
  });
  return normalizeLearningRecommendationRun(data);
}

export async function saveLearningRecommendation(recommendationId: string) {
  const { data } = await apiClient.post<LearningRecommendation>(`/v1/learning-recommendations/${recommendationId}/save`);
  return normalizeLearningRecommendation(data);
}

export async function rejectLearningRecommendation(recommendationId: string, payload?: { reason_code?: string; feedback_text?: string }) {
  const { data } = await apiClient.post<LearningRecommendation>(`/v1/learning-recommendations/${recommendationId}/reject`, payload || {});
  return normalizeLearningRecommendation(data);
}

export async function sendLearningFeedback(
  recommendationId: string,
  payload: { reason_code?: string; rating?: number; relevant?: boolean; feedback_text?: string }
) {
  const { data } = await apiClient.post<{ status: string; feedback_id: string; effect: Record<string, unknown> }>(
    `/v1/learning-recommendations/${recommendationId}/feedback`,
    payload
  );
  return data;
}

export async function requestLearningAlternative(recommendationId: string, reasonCode?: string) {
  const { data } = await apiClient.post<{ status: string; alternatives: LearningRecommendation[] }>(
    `/v1/learning-recommendations/${recommendationId}/alternative`,
    { reason_code: reasonCode || "alternative_requested" }
  );
  return { ...data, alternatives: asArray(data.alternatives).map(normalizeLearningRecommendation) };
}

export async function addLearningRecommendationToRoadmap(
  recommendationId: string,
  payload: {
    roadmap_title?: string;
    learning_objective?: string;
    start_date?: string;
    target_completion_date?: string;
    weekly_commitment?: string;
    priority?: number;
    expected_evidence?: string;
    associated_practical_project?: string;
    notes?: string;
  }
) {
  const { data } = await apiClient.post<{ status: string; roadmap_id: string; action_id: string; roadmap_learning_action_id: string }>(
    `/v1/learning-recommendations/${recommendationId}/add-to-roadmap`,
    payload
  );
  return data;
}

export async function createLearningComparison(profileId: string, recommendationIds: string[], criteriaWeights?: Record<string, number>) {
  const { data } = await apiClient.post<LearningResourceComparison>(`/v1/profiles/${profileId}/learning-resource-comparisons`, {
    recommendation_ids: recommendationIds,
    criteria_weights: criteriaWeights || {},
  });
  return data;
}

export async function getLearningComparisons(profileId: string) {
  const { data } = await apiClient.get<LearningResourceComparison[]>(`/v1/profiles/${profileId}/learning-resource-comparisons`);
  return data;
}

export async function getLearningPath(profileId: string) {
  const { data } = await apiClient.get<LearningPath>(`/v1/profiles/${profileId}/learning-path`);
  return data;
}

export async function generateLearningPath(profileId: string, runId?: string) {
  const { data } = await apiClient.post<LearningPath>(`/v1/profiles/${profileId}/learning-path/generate`, { run_id: runId });
  return data;
}

export async function updateLearningPath(profileId: string, payload: Partial<LearningPath>) {
  const { data } = await apiClient.put<LearningPath>(`/v1/profiles/${profileId}/learning-path`, payload);
  return data;
}

export async function updateLearningProgress(
  itemId: string,
  payload: {
    status?: string;
    progress_percentage?: number;
    user_reported_progress?: string;
    completion_date?: string;
    evidence_url?: string;
    reflection?: string;
    difficulty_feedback?: string;
    relevance_feedback?: string;
  }
) {
  const { data } = await apiClient.post(`/v1/learning-path-items/${itemId}/progress`, payload);
  return data;
}

export async function deleteLearningData(profileId: string) {
  const { data } = await apiClient.delete<{ status: string; deleted: Record<string, number> }>(`/v1/profiles/${profileId}/learning-data`);
  return data;
}
