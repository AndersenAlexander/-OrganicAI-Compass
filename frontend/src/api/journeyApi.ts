import { apiClient } from "./client";

export type JourneySummary = {
  diagnostics: Array<{ id: string; created_at: string; payload: Record<string, unknown> }>;
  profiles: Array<{ id: string; created_at: string; data: Record<string, unknown> }>;
  roadmaps: Array<{ id: string; created_at: string; data: Record<string, unknown> }>;
};

export type ProfileJourneyState = {
  profile_id: string;
  has_market_activity: boolean;
  has_application_activity: boolean;
  has_interview_activity: boolean;
  employment_summary: {
    application_count: number;
    interview_count: number;
    completed_interview_count: number;
    offer_review_count: number;
    roadmap_mutated: boolean;
  };
  interview_summary: {
    id: string;
    lifecycle_status: string;
    stage_type: string;
    has_reflection: boolean;
    outcome: string;
    next_action: string;
  } | null;
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

export async function getProfileJourneyState(profileId: string): Promise<ProfileJourneyState> {
  const { data } = await apiClient.get<ProfileJourneyState>(`/profiles/${profileId}/journey-state`);
  return data;
}
