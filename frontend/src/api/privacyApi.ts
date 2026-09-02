import { apiClient } from "./client";
import type {
  CategoryDeletionPreview,
  PrivacyConsentEvent,
  PrivacyExportArtifact,
  PrivacyInventory,
  PrivacyPreferences,
  PrivacyProvider,
  PrivacyRequestRecord,
  PrivacyResearchSummary,
  PrivacySummary,
} from "../types/privacy";

export async function getPrivacySummary() {
  const { data } = await apiClient.get<PrivacySummary>("/privacy/summary");
  return data;
}

export async function getPrivacyInventory() {
  const { data } = await apiClient.get<PrivacyInventory>("/privacy/inventory");
  return data;
}

export async function getPrivacyPreferences() {
  const { data } = await apiClient.get<PrivacyPreferences>("/privacy/preferences");
  return data;
}

export async function updatePrivacyPreferences(payload: Partial<PrivacyPreferences>) {
  const { data } = await apiClient.put<PrivacyPreferences>("/privacy/preferences", payload);
  return data;
}

export async function getPrivacyConsents() {
  const { data } = await apiClient.get<PrivacyConsentEvent[]>("/privacy/consents");
  return data;
}

export async function getPrivacyRequests() {
  const { data } = await apiClient.get<PrivacyRequestRecord[]>("/privacy/requests");
  return data;
}

export async function getPrivacyProviders() {
  const { data } = await apiClient.get<PrivacyProvider[]>("/privacy/providers");
  return data;
}

export async function getPrivacyResearch() {
  const { data } = await apiClient.get<PrivacyResearchSummary>("/privacy/research");
  return data;
}

export async function reauthenticatePrivacy(password: string) {
  const { data } = await apiClient.post<{ recentAuthentication: boolean }>("/privacy/reauthenticate", { password });
  return data;
}

export async function createPrivacyExport() {
  const { data } = await apiClient.post<PrivacyExportArtifact>("/privacy/exports");
  return data;
}

export async function getPrivacyExports() {
  const { data } = await apiClient.get<PrivacyExportArtifact[]>("/privacy/exports");
  return data;
}

export async function downloadPrivacyExport(artifactId: string) {
  const { data } = await apiClient.get<Blob>(`/privacy/exports/${artifactId}/download`, { responseType: "blob" });
  return data;
}

export async function deletePrivacyExport(artifactId: string) {
  await apiClient.delete(`/privacy/exports/${artifactId}`);
}

export async function previewCategoryDeletion(categoryKey: string) {
  const { data } = await apiClient.get<CategoryDeletionPreview>(`/privacy/deletion/categories/${categoryKey}/preview`);
  return data;
}

export async function deletePrivacyCategory(categoryKey: string) {
  const { data } = await apiClient.post<{ categoryKey: string; deletedRows: Record<string, number>; providerStatus: string }>(
    `/privacy/deletion/categories/${categoryKey}`,
    { confirmation: categoryKey },
  );
  return data;
}

export async function requestAccountDeletion() {
  const { data } = await apiClient.post<{ requestId: string; status: string; graceUntil: string }>("/privacy/account-deletion", {
    confirmation: "DELETE MY ORGANICAI ACCOUNT",
  });
  return data;
}

export async function cancelAccountDeletion(requestId: string) {
  const { data } = await apiClient.post<{ requestId: string; status: string }>(`/privacy/account-deletion/${requestId}/cancel`);
  return data;
}

export async function withdrawResearchParticipation() {
  const { data } = await apiClient.post<{ researchParticipationEnabled: boolean; futureResearchCollection: string; identifiableCleanup: string }>("/privacy/research/withdraw");
  return data;
}
