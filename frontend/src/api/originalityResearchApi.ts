import { apiClient } from "./client";
import type {
  AdaptiveExperimentAlternative,
  AdaptiveExperimentRecommendation,
  AdaptiveExperimentRun,
  EvidenceGapDiscovery,
  FairnessAudit,
  FairnessTestSuite,
  RecommendationProvenance,
  RecommendationSystemCard,
  RobustnessRun,
  TransitionPreset,
  TransitionSimulation,
} from "../types/originalityResearch";

export async function analyseAdaptiveExperiments(profileId: string, payload: Record<string, unknown> = {}) {
  const { data } = await apiClient.post<AdaptiveExperimentRun>(`/v1/profiles/${profileId}/adaptive-experiments/analyse`, payload);
  return data;
}

export async function getAdaptiveExperiments(profileId: string) {
  const { data } = await apiClient.get<AdaptiveExperimentRecommendation[]>(`/v1/profiles/${profileId}/adaptive-experiments`);
  return data;
}

export async function getEvidenceGaps(profileId: string) {
  const { data } = await apiClient.get<EvidenceGapDiscovery>(`/v1/profiles/${profileId}/evidence-gaps`);
  return data;
}

export async function acceptAdaptiveExperiment(recommendationId: string, payload: Record<string, unknown> = {}) {
  const { data } = await apiClient.post<AdaptiveExperimentRecommendation>(`/v1/adaptive-experiments/${recommendationId}/accept`, payload);
  return data;
}

export async function saveAdaptiveExperiment(recommendationId: string, payload: Record<string, unknown> = {}) {
  const { data } = await apiClient.post<AdaptiveExperimentRecommendation>(`/v1/adaptive-experiments/${recommendationId}/save`, payload);
  return data;
}

export async function rejectAdaptiveExperiment(recommendationId: string, payload: Record<string, unknown> = {}) {
  const { data } = await apiClient.post<AdaptiveExperimentRecommendation>(`/v1/adaptive-experiments/${recommendationId}/reject`, payload);
  return data;
}

export async function startAdaptiveExperiment(recommendationId: string, payload: Record<string, unknown> = {}) {
  const { data } = await apiClient.post<AdaptiveExperimentRecommendation>(`/v1/adaptive-experiments/${recommendationId}/start`, payload);
  return data;
}

export async function recordAdaptiveExperimentOutcome(recommendationId: string, payload: Record<string, unknown> = {}) {
  const { data } = await apiClient.post<AdaptiveExperimentRecommendation>(`/v1/adaptive-experiments/${recommendationId}/outcome`, payload);
  return data;
}

export async function transitionAdaptiveExperimentLifecycle(recommendationId: string, payload: Record<string, unknown> = {}) {
  const { data } = await apiClient.post<AdaptiveExperimentRecommendation>(`/v1/adaptive-experiments/${recommendationId}/lifecycle`, payload);
  return data;
}

export async function getAdaptiveEvidenceCapture(recommendationId: string) {
  const { data } = await apiClient.get<Record<string, unknown>>(`/v1/adaptive-experiments/${recommendationId}/evidence-capture`);
  return data;
}

export async function reviewAdaptiveEvidenceCapture(recommendationId: string, payload: Record<string, unknown>) {
  const { data } = await apiClient.post<AdaptiveExperimentRecommendation>(`/v1/adaptive-experiments/${recommendationId}/evidence-capture/review`, payload);
  return data;
}

export async function getAdaptiveExperimentAlternatives(recommendationId: string) {
  const { data } = await apiClient.get<AdaptiveExperimentAlternative[]>(`/v1/adaptive-experiments/${recommendationId}/alternatives`);
  return data;
}

export async function getTransitionPresets() {
  const { data } = await apiClient.get<TransitionPreset[]>("/v1/transition-simulations/presets");
  return data;
}

export async function createTransitionSimulation(profileId: string, payload: Record<string, unknown> = {}) {
  const { data } = await apiClient.post<TransitionSimulation>(`/v1/profiles/${profileId}/transition-simulations`, payload);
  return data;
}

export async function getTransitionSimulations(profileId: string) {
  const { data } = await apiClient.get<TransitionSimulation[]>(`/v1/profiles/${profileId}/transition-simulations`);
  return data;
}

export async function runTransitionSimulation(simulationId: string, payload: Record<string, unknown> = {}) {
  const { data } = await apiClient.post<TransitionSimulation>(`/v1/transition-simulations/${simulationId}/run`, payload);
  return data;
}

export async function compareTransitionScenarios(simulationId: string, payload: Record<string, unknown> = {}) {
  const { data } = await apiClient.post<Record<string, unknown>>(`/v1/transition-simulations/${simulationId}/compare`, payload);
  return data;
}

export async function updateTransitionSimulationConstraints(simulationId: string, payload: Record<string, unknown> = {}) {
  const { data } = await apiClient.post<Record<string, unknown>>(`/v1/transition-simulations/${simulationId}/constraints`, payload);
  return data;
}

export async function archiveTransitionSimulation(simulationId: string, payload: Record<string, unknown> = {}) {
  const { data } = await apiClient.post<TransitionSimulation>(`/v1/transition-simulations/${simulationId}/archive`, payload);
  return data;
}

export async function addTransitionPathToDecisionJournal(pathId: string, payload: Record<string, unknown> = {}) {
  const { data } = await apiClient.post<Record<string, unknown>>(`/v1/transition-paths/${pathId}/decision-journal`, payload);
  return data;
}

export async function proposeTransitionPathRoadmap(pathId: string, payload: Record<string, unknown> = {}) {
  const { data } = await apiClient.post<Record<string, unknown>>(`/v1/transition-paths/${pathId}/propose-roadmap`, payload);
  return data;
}

export async function runRecommendationRobustness(profileId: string, payload: Record<string, unknown> = {}) {
  const { data } = await apiClient.post<RobustnessRun>(`/v1/profiles/${profileId}/recommendation-robustness`, payload);
  return data;
}

export async function getRecommendationRobustness(profileId: string) {
  const { data } = await apiClient.get<RobustnessRun[]>(`/v1/profiles/${profileId}/recommendation-robustness`);
  return data;
}

export async function getRecommendationProvenance(targetType: string, targetId: string) {
  const { data } = await apiClient.get<RecommendationProvenance>(`/v1/recommendation-provenance/${targetType}/${targetId}`);
  return data;
}

export async function getFairnessTestSuites() {
  const { data } = await apiClient.get<FairnessTestSuite[]>("/v1/research/fairness-test-suites");
  return data;
}

export async function resetFairnessAuditFixtures(payload: Record<string, unknown> = { demo_only: true }) {
  const { data } = await apiClient.post<Record<string, unknown>>("/v1/research/fairness-audits/reset", payload);
  return data;
}

export async function runFairnessAudit(payload: Record<string, unknown> = {}) {
  const { data } = await apiClient.post<FairnessAudit>("/v1/research/fairness-audits", payload);
  return data;
}

export async function getFairnessAudits() {
  const { data } = await apiClient.get<FairnessAudit[]>("/v1/research/fairness-audits");
  return data;
}

export async function getRecommendationSystemCard() {
  const { data } = await apiClient.get<RecommendationSystemCard>("/v1/recommendation-system-card");
  return data;
}
