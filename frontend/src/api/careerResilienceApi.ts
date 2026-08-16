import { apiClient } from "./client";
import type {
  CareerExperimentSession,
  CareerExperimentTemplate,
  CareerResilienceDashboard,
  EvidencePassport,
  ImmediateActionPlan,
  JobLossProfile,
  SupportBrief,
  SupportScreening,
  SupportedPathRun,
} from "../types/careerResilience";

export async function getCareerResilienceDashboard(profileId: string) {
  const { data } = await apiClient.get<CareerResilienceDashboard>(`/v1/profiles/${profileId}/career-resilience`);
  return data;
}

export async function getCareerExperimentTemplates(roleFamily?: string) {
  const { data } = await apiClient.get<CareerExperimentTemplate[]>("/v1/career-experiments", {
    params: roleFamily ? { role_family: roleFamily } : undefined,
  });
  return data;
}

export async function getCareerExperimentTemplate(experimentId: string) {
  const { data } = await apiClient.get<CareerExperimentTemplate>(`/v1/career-experiments/${experimentId}`);
  return data;
}

export async function createCareerExperiment(
  profileId: string,
  payload: { experiment_template_id?: string; career_match_id?: string | null; mode?: string; user_confirmed?: boolean; add_to_roadmap?: boolean }
) {
  const { data } = await apiClient.post<CareerExperimentSession>(`/v1/profiles/${profileId}/career-experiments`, payload);
  return data;
}

export async function getProfileCareerExperiments(profileId: string) {
  const { data } = await apiClient.get<CareerExperimentSession[]>(`/v1/profiles/${profileId}/career-experiments`);
  return data;
}

export async function getCareerExperimentSession(sessionId: string) {
  const { data } = await apiClient.get<CareerExperimentSession>(`/v1/career-experiment-sessions/${sessionId}`);
  return data;
}

export async function startCareerExperiment(sessionId: string) {
  const { data } = await apiClient.post<CareerExperimentSession>(`/v1/career-experiment-sessions/${sessionId}/start`);
  return data;
}

export async function submitCareerExperiment(
  sessionId: string,
  payload: {
    text_response?: string;
    project_url?: string;
    repository_url?: string;
    portfolio_url?: string;
    document_metadata?: Record<string, unknown>;
    completion_notes: string;
    time_spent_minutes?: number;
    ai_tools_used?: string[];
    assistance_level?: string;
    self_rated_difficulty?: number;
    self_rated_enjoyment?: number;
    confidence_before?: number;
    confidence_after?: number;
    reflection?: Record<string, unknown>;
  }
) {
  const { data } = await apiClient.post<CareerExperimentSession>(`/v1/career-experiment-sessions/${sessionId}/submit`, payload);
  return data;
}

export async function selfReviewCareerExperiment(
  sessionId: string,
  payload: { reflection: string; self_rated_difficulty?: number; self_rated_enjoyment?: number; confidence_before?: number; confidence_after?: number }
) {
  const { data } = await apiClient.post<CareerExperimentSession>(`/v1/career-experiment-sessions/${sessionId}/self-review`, payload);
  return data;
}

export async function evaluateCareerExperiment(sessionId: string) {
  const { data } = await apiClient.post<CareerExperimentSession>(`/v1/career-experiment-sessions/${sessionId}/evaluate`);
  return data;
}

export async function getEvidencePassport(profileId: string) {
  const { data } = await apiClient.get<EvidencePassport>(`/v1/profiles/${profileId}/evidence-passport`);
  return data;
}

export async function recalibrateCareer(profileId: string, experimentResultId?: string) {
  const { data } = await apiClient.post(`/v1/profiles/${profileId}/career-recalibration`, {
    experiment_result_id: experimentResultId,
  });
  return data;
}

export async function createSupportedPaths(profileId: string) {
  const { data } = await apiClient.post<SupportedPathRun>(`/v1/profiles/${profileId}/supported-paths`);
  return data;
}

export async function getSupportedPaths(profileId: string) {
  const { data } = await apiClient.get<SupportedPathRun>(`/v1/profiles/${profileId}/supported-paths`);
  return data;
}

export async function saveJobLossProfile(
  profileId: string,
  payload: {
    consent_accepted: boolean;
    country_of_residence?: string;
    country_of_employment?: string;
    municipality_or_region?: string;
    last_working_date?: string;
    contract_termination_type?: string;
    employment_status?: string;
    reduction_in_working_hours?: number;
    jobseeker_registration_status?: string;
    current_benefits?: string[];
    work_permit_or_residency_status?: string;
    education?: string;
    training_interest?: string;
    availability_for_work?: string;
    relocation_preferences?: string;
  }
) {
  const { data } = await apiClient.post<JobLossProfile>(`/v1/profiles/${profileId}/job-loss-profile`, payload);
  return data;
}

export async function getJobLossProfile(profileId: string) {
  const { data } = await apiClient.get<JobLossProfile | null>(`/v1/profiles/${profileId}/job-loss-profile`);
  return data;
}

export async function createImmediateActionPlan(profileId: string) {
  const { data } = await apiClient.post<ImmediateActionPlan>(`/v1/profiles/${profileId}/immediate-action-plan`);
  return data;
}

export async function getImmediateActionPlan(profileId: string) {
  const { data } = await apiClient.get<ImmediateActionPlan | null>(`/v1/profiles/${profileId}/immediate-action-plan`);
  return data;
}

export async function runSupportScreening(profileId: string, values: Record<string, unknown> = {}) {
  const { data } = await apiClient.post<SupportScreening>(`/v1/profiles/${profileId}/support-screening`, { values });
  return data;
}

export async function getSupportScreening(profileId: string) {
  const { data } = await apiClient.get<SupportScreening | null>(`/v1/profiles/${profileId}/support-screening`);
  return data;
}

export async function createSupportBrief(profileId: string) {
  const { data } = await apiClient.post<SupportBrief>(`/v1/profiles/${profileId}/support-brief`);
  return data;
}

export async function getSupportBrief(profileId: string) {
  const { data } = await apiClient.get<SupportBrief | null>(`/v1/profiles/${profileId}/support-brief`);
  return data;
}
