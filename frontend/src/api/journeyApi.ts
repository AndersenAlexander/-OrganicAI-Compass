import { apiClient } from "./client";

export type JourneySummary = {
  diagnostics: Array<{ id: string; created_at: string; payload: Record<string, unknown> }>;
  profiles: Array<{ id: string; created_at: string; data: Record<string, unknown> }>;
  roadmaps: Array<{ id: string; created_at: string; data: Record<string, unknown> }>;
};

export async function getJourneySummary(): Promise<JourneySummary> {
  const [diagnostics, profiles, roadmaps] = await Promise.all([
    apiClient.get<JourneySummary["diagnostics"]>("/diagnostics"),
    apiClient.get<JourneySummary["profiles"]>("/profiles"),
    apiClient.get<JourneySummary["roadmaps"]>("/roadmap"),
  ]);

  return {
    diagnostics: diagnostics.data,
    profiles: profiles.data,
    roadmaps: roadmaps.data,
  };
}
