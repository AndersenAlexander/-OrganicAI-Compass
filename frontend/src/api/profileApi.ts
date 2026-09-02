import { apiClient } from "./client";
import type { ArchetypeResult, CollaborationStyleResult, ContributionDomainResult, FearTransform, HumanPotentialProfile, LearningPathResult, ProfileUserFeedback, StrengthResult, ValueResult } from "../types/profile";
import type { Roadmap } from "../types/roadmap";

export type OwnedProfileSummary = { id: string; created_at: string; data: Record<string, unknown> };

export async function listProfiles() {
  const { data } = await apiClient.get<OwnedProfileSummary[]>("/profiles");
  return data;
}

export async function getProfile(id: string) {
  const { data } = await apiClient.get<Record<string, unknown>>(`/profiles/${id}`);
  return normalizeProfile(data);
}

const archetype = (value: unknown, fallback: string): ArchetypeResult => typeof value === "object" && value ? value as ArchetypeResult : { name: String(value || fallback), summary: "Your answers suggest this exploratory tendency.", confidence: 0.6, signals: [] };
const strings = (value: unknown) => Array.isArray(value) ? value.map(String) : value ? [String(value)] : [];
const strengths = (value: unknown): StrengthResult[] => (Array.isArray(value) ? value : []).map((item, index) => typeof item === "object" && item ? item as StrengthResult : { name: String(item), score: Math.max(55, 78 - index * 5), explanation: "Derived from your diagnostic answers.", evidence: [] });
const values = (value: unknown): ValueResult[] => (Array.isArray(value) ? value : []).map((item, index) => typeof item === "object" && item ? item as ValueResult : { name: String(item), score: Math.max(55, 76 - index * 4), evidence: [] });
const domains = (value: unknown): ContributionDomainResult[] => (Array.isArray(value) ? value : []).map((item, index) => typeof item === "object" && item ? item as ContributionDomainResult : { name: String(item), score: Math.max(55, 76 - index * 5), explanation: "Suggested by your interests and values." });
const learning = (value: unknown): LearningPathResult[] => (Array.isArray(value) ? value : []).map((item) => typeof item === "object" && item ? item as LearningPathResult : { name: String(item), level: "All levels", duration: "Self-paced", reason: "Supports your profile direction." });

export function normalizeProfile(data: Record<string, unknown>): HumanPotentialProfile {
  const collaboration = data.ai_collaboration_style;
  const style: CollaborationStyleResult = typeof collaboration === "object" && collaboration ? collaboration as CollaborationStyleResult : { name: String(collaboration || "Co-Creator"), summary: "AI may support exploration while decisions remain human-led.", strengths: [], cautions: ["Verify important outputs"], recommended_uses: ["Ideation"], human_led_decisions: ["Final decisions", "Values", "Ethical responsibility"] };
  return { id: String(data.id), diagnostic_id: String(data.diagnostic_id || ""), natural_discovery_snapshot: data.natural_discovery_snapshot as Record<string, unknown> | undefined, assessment_prefill: data.assessment_prefill as HumanPotentialProfile["assessment_prefill"], human_potential_sections: data.human_potential_sections as Record<string, string> | undefined, primary_archetype: archetype(data.primary_archetype, "Curious Explorer"), secondary_archetype: archetype(data.secondary_archetype, "Reflective Co-Creator"), strengths: strengths(data.strengths), values: values(data.values), fears: strings(data.fears), creative_tendencies: strings(data.creative_tendencies), ai_collaboration_style: style, contribution_domains: domains(data.contribution_domains), recommended_learning_paths: learning(data.recommended_learning_paths), uncertainties: strings(data.uncertainties), risk_notes: strings(data.risk_notes), ethical_note: String(data.ethical_note || "You can confirm or adjust this interpretation."), user_feedback: data.user_feedback as ProfileUserFeedback | undefined, created_at: String(data.created_at || "") };
}

export async function getProfileFeedback(profileId: string) {
  const { data } = await apiClient.get<ProfileUserFeedback>(`/profiles/${profileId}/feedback`);
  return data;
}

export async function updateProfileFeedback(profileId: string, feedback: ProfileUserFeedback) {
  const { data } = await apiClient.patch<ProfileUserFeedback>(`/profiles/${profileId}/feedback`, feedback);
  return data;
}

export async function transformFear(profileId: string, fear: string) {
  const { data } = await apiClient.post<FearTransform>("/fear-transform", {
    profile_id: profileId,
    fear
  });
  return data;
}

export async function getReport(profileId: string) {
  const { data } = await apiClient.get<{
    profile: Record<string, unknown>;
    fear_transforms: FearTransform[];
    roadmap: Roadmap | null;
  }>(`/report/${profileId}`);
  return { ...data, profile: normalizeProfile(data.profile) };
}
