import { apiClient } from "./client";
import type {
  AdvisorComment,
  AdvisorShare,
  BrowserExtensionConnection,
  BrowserExtensionSettings,
  BrowserJobCapture,
  CareerRoleComparison,
  CareerRoleProfile,
  DecisionJournalEntry,
  PanelPersona,
  PanelSession,
  PanelTurn,
} from "../types/innovationExtension";

export async function getBrowserExtensionSettings(profileId: string) {
  const { data } = await apiClient.get<BrowserExtensionSettings>(`/v1/profiles/${profileId}/browser-extension/settings`);
  return data;
}

export async function createBrowserExtensionConnection(profileId: string, payload: Record<string, unknown> = {}) {
  const { data } = await apiClient.post<BrowserExtensionConnection>(`/v1/profiles/${profileId}/browser-extension/connection`, payload);
  return data;
}

export async function revokeBrowserExtensionConnection(profileId: string, connectionId: string) {
  const { data } = await apiClient.delete<BrowserExtensionConnection>(`/v1/profiles/${profileId}/browser-extension/connection/${connectionId}`);
  return data;
}

export async function getJobCaptures(profileId: string) {
  const { data } = await apiClient.get<BrowserJobCapture[]>(`/v1/profiles/${profileId}/job-captures`);
  return data;
}

export async function createJobCapture(profileId: string, payload: Record<string, unknown>, extensionToken?: string) {
  const { data } = await apiClient.post<BrowserJobCapture>(`/v1/profiles/${profileId}/job-captures`, payload, {
    headers: extensionToken ? { "X-OrganicAI-Extension-Token": extensionToken } : undefined,
  });
  return data;
}

export async function confirmJobCapture(profileId: string, captureId: string, payload: Record<string, unknown>) {
  const { data } = await apiClient.post<BrowserJobCapture>(`/v1/profiles/${profileId}/job-captures/${captureId}/confirm`, payload);
  return data;
}

export async function getAdvisorShares(profileId: string) {
  const { data } = await apiClient.get<AdvisorShare[]>(`/v1/profiles/${profileId}/advisor-shares`);
  return data;
}

export async function createAdvisorShare(profileId: string, payload: Record<string, unknown>) {
  const { data } = await apiClient.post<AdvisorShare>(`/v1/profiles/${profileId}/advisor-shares`, payload);
  return data;
}

export async function getAdvisorShare(profileId: string, shareId: string) {
  const { data } = await apiClient.get<AdvisorShare>(`/v1/profiles/${profileId}/advisor-shares/${shareId}`);
  return data;
}

export async function revokeAdvisorShare(profileId: string, shareId: string) {
  const { data } = await apiClient.delete<AdvisorShare>(`/v1/profiles/${profileId}/advisor-shares/${shareId}`);
  return data;
}

export async function respondToAdvisorComment(profileId: string, commentId: string, payload: Record<string, unknown>) {
  const { data } = await apiClient.patch<AdvisorComment>(`/v1/profiles/${profileId}/advisor-comments/${commentId}`, payload);
  return data;
}

export async function getAdvisorReview(shareToken: string, pin?: string) {
  const { data } = await apiClient.get<AdvisorShare>(`/v1/advisor-review/${shareToken}`, { params: pin ? { pin } : undefined });
  return data;
}

export async function submitAdvisorReviewComment(shareToken: string, payload: Record<string, unknown>) {
  const { data } = await apiClient.post<AdvisorComment>(`/v1/advisor-review/${shareToken}/comments`, payload);
  return data;
}

export async function getPanelPersonas() {
  const { data } = await apiClient.get<PanelPersona[]>("/v1/interviews/panel-personas");
  return data;
}

export async function createPanelSimulation(interviewId: string, payload: Record<string, unknown>) {
  const { data } = await apiClient.post<PanelSession>(`/v1/interviews/${interviewId}/panel-simulation`, payload);
  return data;
}

export async function getPanelSimulation(sessionId: string) {
  const { data } = await apiClient.get<PanelSession>(`/v1/mock-sessions/${sessionId}/panel`);
  return data;
}

export async function addPanelTurn(sessionId: string, payload: Record<string, unknown>) {
  const { data } = await apiClient.post<PanelTurn>(`/v1/mock-sessions/${sessionId}/panel-turns`, payload);
  return data;
}

export async function completePanelSimulation(sessionId: string, payload: Record<string, unknown>) {
  const { data } = await apiClient.post<PanelSession>(`/v1/mock-sessions/${sessionId}/panel-complete`, payload);
  return data;
}

export async function getCareerRoles(params: Record<string, unknown> = {}) {
  const { data } = await apiClient.get<CareerRoleProfile[]>("/v1/careers", { params });
  return data;
}

export async function getCareerRole(slug: string) {
  const { data } = await apiClient.get<CareerRoleProfile>(`/v1/careers/${slug}`);
  return data;
}

export async function getProfileCareerRoles(profileId: string, params: Record<string, unknown> = {}) {
  const { data } = await apiClient.get<CareerRoleProfile[]>(`/v1/profiles/${profileId}/career-encyclopedia`, { params });
  return data;
}

export async function getCareerRoleComparison(profileId: string, slug: string) {
  const { data } = await apiClient.get<CareerRoleComparison>(`/v1/profiles/${profileId}/career-encyclopedia/${slug}/compare`);
  return data;
}

export async function saveCareerRoleHypothesis(profileId: string, slug: string) {
  const { data } = await apiClient.post(`/v1/profiles/${profileId}/career-encyclopedia/${slug}/hypothesis`);
  return data;
}

export async function startCareerRoleExperiment(profileId: string, slug: string) {
  const { data } = await apiClient.post(`/v1/profiles/${profileId}/career-encyclopedia/${slug}/experiment`);
  return data;
}

export async function getDecisionJournal(profileId: string) {
  const { data } = await apiClient.get<DecisionJournalEntry[]>(`/v1/profiles/${profileId}/decision-journal`);
  return data;
}

export async function createDecisionJournalEntry(profileId: string, payload: Record<string, unknown>) {
  const { data } = await apiClient.post<DecisionJournalEntry>(`/v1/profiles/${profileId}/decision-journal`, payload);
  return data;
}

export async function updateDecisionJournalEntry(profileId: string, entryId: string, payload: Record<string, unknown>) {
  const { data } = await apiClient.put<DecisionJournalEntry>(`/v1/profiles/${profileId}/decision-journal/${entryId}`, payload);
  return data;
}

export async function recordDecisionJournalOutcome(profileId: string, entryId: string, payload: Record<string, unknown>) {
  const { data } = await apiClient.post<DecisionJournalEntry>(`/v1/profiles/${profileId}/decision-journal/${entryId}/outcome`, payload);
  return data;
}

export async function getDecisionJournalResearchExport(profileId: string) {
  const { data } = await apiClient.get<Record<string, unknown>>(`/v1/profiles/${profileId}/decision-journal/research-export`);
  return data;
}
