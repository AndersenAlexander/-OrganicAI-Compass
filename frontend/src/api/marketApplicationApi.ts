import { apiClient } from "./client";
import type {
  ApplicationDocument,
  JobAnalysis,
  JobApplication,
  MarketJob,
  MarketRadar,
  MarketRadarPreference,
  ProviderStatusResponse,
  ResearchEvaluation,
} from "../types/marketApplication";

export async function getMarketProviderStatus() {
  const { data } = await apiClient.get<ProviderStatusResponse>("/v1/market/providers/status");
  return data;
}

export async function syncDemoMarketProvider() {
  const { data } = await apiClient.post("/v1/market/providers/demo/sync");
  return data;
}

export async function getMarketRadar(profileId: string, params: Record<string, unknown> = {}) {
  const { data } = await apiClient.get<MarketRadar>(`/v1/profiles/${profileId}/market-radar`, { params });
  return data;
}

export async function updateMarketPreferences(profileId: string, payload: Record<string, unknown>) {
  const { data } = await apiClient.put<MarketRadarPreference>(`/v1/profiles/${profileId}/market-preferences`, payload);
  return data;
}

export async function getMarketJobs(profileId: string, params: Record<string, unknown> = {}) {
  const { data } = await apiClient.get<MarketJob[]>(`/v1/profiles/${profileId}/jobs`, { params });
  return data;
}

export async function saveMarketJob(profileId: string, jobId: string) {
  const { data } = await apiClient.post<JobApplication>(`/v1/profiles/${profileId}/jobs/${jobId}/save`);
  return data;
}

export async function getJobAnalyses(profileId: string) {
  const { data } = await apiClient.get<JobAnalysis[]>(`/v1/profiles/${profileId}/job-analyses`);
  return data;
}

export async function getJobAnalysis(profileId: string, analysisId: string) {
  const { data } = await apiClient.get<JobAnalysis>(`/v1/profiles/${profileId}/job-analyses/${analysisId}`);
  return data;
}

export async function createJobAnalysis(profileId: string, payload: Record<string, unknown>) {
  const { data } = await apiClient.post<JobAnalysis>(`/v1/profiles/${profileId}/job-analyses`, payload);
  return data;
}

export async function matchJobAnalysis(profileId: string, analysisId: string) {
  const { data } = await apiClient.post(`/v1/profiles/${profileId}/job-analyses/${analysisId}/match`);
  return data;
}

export async function calculateJobAnalysisReadiness(profileId: string, analysisId: string) {
  const { data } = await apiClient.post<JobAnalysis["readiness"]>(`/v1/profiles/${profileId}/job-analyses/${analysisId}/readiness`);
  return data;
}

export async function updateJobRequirement(profileId: string, requirementId: string, payload: Record<string, unknown>) {
  const { data } = await apiClient.patch(`/v1/profiles/${profileId}/job-requirements/${requirementId}`, payload);
  return data;
}

export async function getMasterCareerProfile(profileId: string) {
  const { data } = await apiClient.get(`/v1/profiles/${profileId}/master-career-profile`);
  return data;
}

export async function getApplicationDocuments(profileId: string) {
  const { data } = await apiClient.get<ApplicationDocument[]>(`/v1/profiles/${profileId}/application-documents`);
  return data;
}

export async function createApplicationDocument(profileId: string, payload: Record<string, unknown>) {
  const { data } = await apiClient.post<ApplicationDocument>(`/v1/profiles/${profileId}/application-documents`, payload);
  return data;
}

export async function updateDocumentClaim(profileId: string, claimId: string, payload: Record<string, unknown>) {
  const { data } = await apiClient.patch(`/v1/profiles/${profileId}/document-claims/${claimId}`, payload);
  return data;
}

export async function saveDocumentVersion(profileId: string, documentId: string, reason: string) {
  const { data } = await apiClient.post(`/v1/profiles/${profileId}/application-documents/${documentId}/versions`, { reason });
  return data;
}

export async function exportApplicationDocument(profileId: string, documentId: string, confirmBlockedClaimExport = false) {
  const { data } = await apiClient.post(`/v1/profiles/${profileId}/application-documents/${documentId}/export`, {
    confirm_blocked_claim_export: confirmBlockedClaimExport,
    export_format: "html_json",
  });
  return data;
}

export async function getApplications(profileId: string) {
  const { data } = await apiClient.get<JobApplication[]>(`/v1/profiles/${profileId}/applications`);
  return data;
}

export async function createApplication(profileId: string, payload: Record<string, unknown>) {
  const { data } = await apiClient.post<JobApplication>(`/v1/profiles/${profileId}/applications`, payload);
  return data;
}

export async function addApplicationStage(profileId: string, applicationId: string, payload: Record<string, unknown>) {
  const { data } = await apiClient.post(`/v1/profiles/${profileId}/applications/${applicationId}/stages`, payload);
  return data;
}

export async function recordApplicationOutcome(profileId: string, applicationId: string, payload: Record<string, unknown>) {
  const { data } = await apiClient.post(`/v1/profiles/${profileId}/applications/${applicationId}/outcome`, payload);
  return data;
}

export async function recalibrateApplication(profileId: string, applicationId: string) {
  const { data } = await apiClient.post(`/v1/profiles/${profileId}/applications/${applicationId}/recalibrate`);
  return data;
}

export async function getResearchEvaluation(profileId: string) {
  const { data } = await apiClient.get<ResearchEvaluation>(`/v1/profiles/${profileId}/research-evaluation`);
  return data;
}

export async function consentToResearch(studyId: string, profileId: string, consentScope: string[] = ["survey", "workflow_metrics", "pseudonymous_export"]) {
  const { data } = await apiClient.post(`/v1/research/studies/${studyId}/profiles/${profileId}/consent`, {
    consent_given: true,
    consent_scope: consentScope,
  });
  return data;
}

export async function withdrawResearchConsent(studyId: string, profileId: string) {
  const { data } = await apiClient.post(`/v1/research/studies/${studyId}/profiles/${profileId}/withdraw`);
  return data;
}

export async function createResearchSession(studyId: string, profileId: string, workflowStage: string, workflow = "experimental") {
  const { data } = await apiClient.post(`/v1/research/studies/${studyId}/profiles/${profileId}/sessions`, {
    workflow_stage: workflowStage,
    workflow,
  });
  return data;
}

export async function submitResearchResponses(profileId: string, sessionId: string, responses: Array<Record<string, unknown>>) {
  const { data } = await apiClient.post(`/v1/profiles/${profileId}/research-sessions/${sessionId}/responses`, {
    responses,
    complete_session: true,
  });
  return data;
}

export async function submitResearchMetrics(profileId: string, sessionId: string, metrics: Array<Record<string, unknown>>) {
  const { data } = await apiClient.post(`/v1/profiles/${profileId}/research-sessions/${sessionId}/metrics`, {
    metrics,
  });
  return data;
}

export async function createResearchExport(studyId: string, includeDemo = false) {
  const { data } = await apiClient.post(`/v1/research/studies/${studyId}/exports`, {
    include_demo: includeDemo,
    export_format: "json_csv",
  });
  return data;
}
