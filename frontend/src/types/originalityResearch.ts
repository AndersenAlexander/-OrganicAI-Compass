export type AdaptiveScoreComponent = {
  value: number;
  weight: number;
};

export type AdaptiveExperimentRecommendation = {
  id: string;
  run_id: string;
  profile_id: string;
  experiment_template_id?: string | null;
  career_experiment_session_id?: string | null;
  title: string;
  experiment_type: string;
  priority_band: string;
  score_band: string;
  score_internal: number;
  rank_position: number;
  related_hypotheses: Array<Record<string, unknown>>;
  uncertainty: Record<string, unknown>;
  skills_tested: string[];
  evidence_expected: string[];
  expected_evidence_gain: Record<string, unknown>;
  linked_evidence_gap_ids?: string[];
  linked_job_requirement_ids?: string[];
  linked_market_signal_ids?: string[];
  actual_evidence_gain: Record<string, unknown>;
  estimated_duration: string;
  estimated_effort: string;
  estimated_cost: string;
  market_relevance: string;
  cross_path_usefulness: string;
  accessibility_considerations: string[];
  support_options: string[];
  limitations: string[];
  score_components: {
    version?: string;
    weight_version?: string;
    positive?: Record<string, AdaptiveScoreComponent>;
    negative?: Record<string, AdaptiveScoreComponent>;
    normalised_score?: number;
    score_precision_note?: string;
  };
  alternatives: AdaptiveExperimentAlternative[];
  data_quality_warnings: string[];
  explanation: string;
  status: string;
  user_confirmation_status: string;
  rejection_reason: string;
  rejection_feedback: Record<string, unknown>;
  roadmap_confirmation_status: string;
  scoring_version: string;
  weight_version: string;
  decision_support_snapshot?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type EvidenceGap = {
  id: string;
  profile_id: string;
  skill_id: string;
  gap_type: string;
  severity: number;
  source_types: string[];
  linked_hypothesis_ids: string[];
  linked_experiment_template_ids: string[];
  linked_job_requirement_ids: string[];
  linked_market_signal_ids: string[];
  expected_evidence_type: string;
  missing_input: boolean;
  data_quality_note: string;
  limitation: string;
  version: string;
};

export type EvidenceGapDiscovery = {
  profile_id: string;
  status: string;
  version: string;
  gaps: EvidenceGap[];
  summary: Record<string, unknown>;
  decision_support_snapshot: Record<string, unknown>;
};

export type AdaptiveExperimentAlternative = {
  type: string;
  title: string;
  experiment_template_id: string;
  reason: string;
  tradeoff: string;
};

export type AdaptiveExperimentRun = {
  id: string;
  profile_id: string;
  status: string;
  input_snapshot: Record<string, unknown>;
  scoring_version: string;
  weight_version: string;
  weights: Record<string, unknown>;
  source_versions: Record<string, unknown>;
  data_coverage: Record<string, unknown>;
  limitations: string[];
  uncertainty_summary: Record<string, unknown>;
  decision_support_snapshot?: Record<string, unknown>;
  evidence_gaps?: EvidenceGap[];
  missing_inputs?: string[];
  recommendations: AdaptiveExperimentRecommendation[];
  created_at: string;
};

export type TransitionPath = {
  id: string;
  simulation_id: string;
  profile_id: string;
  title: string;
  role_slug: string;
  path_type: string;
  objectives: Record<string, number>;
  normalised_objectives: Record<string, number>;
  objective_directions: Record<string, "min" | "max" | string>;
  is_pareto_optimal: boolean;
  dominated_by: Array<Record<string, unknown>>;
  dominated_explanation: string;
  feasibility_status?: string;
  recommendation_eligible?: boolean;
  constraint_results?: Array<Record<string, unknown>>;
  hard_constraint_violations?: Array<Record<string, unknown>>;
  tradeoff_summary?: Array<Record<string, unknown>>;
  existing_assets: string[];
  missing_assets: string[];
  required_experiments: string[];
  required_learning: string[];
  transition_stages: string[];
  relevant_jobs: string[];
  support_opportunities: string[];
  assumptions: string[];
  uncertainties: string[];
  reversibility: string;
  next_action: string;
  user_selection_status: string;
};

export type TransitionSimulation = {
  id: string;
  profile_id: string;
  scenario_name: string;
  preset: string;
  status: string;
  controls: Record<string, unknown>;
  objective_config: Record<string, unknown>;
  input_snapshot: Record<string, unknown>;
  decision_support_snapshot?: Record<string, unknown>;
  pareto_front: Array<Record<string, unknown>>;
  paths: TransitionPath[];
  scenario_comparisons: Array<Record<string, unknown>>;
  explanation: string;
  objective_version: string;
  data_coverage: Record<string, unknown>;
  limitations: string[];
  saved: boolean;
  created_at: string;
};

export type TransitionPreset = {
  id: string;
  label: string;
  objective_priorities: Record<string, number>;
};

export type RobustnessRun = {
  id: string;
  profile_id: string;
  status: string;
  input_snapshot: Record<string, unknown>;
  decision_support_snapshot?: Record<string, unknown>;
  scenario_results?: Array<Record<string, unknown>>;
  baseline: Array<Record<string, unknown>>;
  variations: Array<Record<string, unknown>>;
  stability_results: Array<Record<string, unknown>>;
  sensitivity_matrix: Array<Record<string, unknown>>;
  dependency_flags: Array<Record<string, unknown>>;
  metrics: Record<string, unknown>;
  data_coverage: Record<string, unknown>;
  limitations: string[];
  scoring_version: string;
  what_could_change: string[];
  created_at: string;
};

export type FairnessAudit = {
  id: string;
  status: string;
  audit_type: string;
  synthetic_only: boolean;
  fixtures: Array<Record<string, unknown>>;
  results: Array<Record<string, unknown>>;
  summary: Record<string, unknown>;
  system_card_version: string;
  reproducibility: Record<string, unknown>;
  limitations: string[];
  created_at: string;
};

export type FairnessTestSuite = {
  suite_id: string;
  label: string;
  synthetic_only: boolean;
  cases: Array<Record<string, unknown>>;
  limitations: string[];
};

export type RecommendationProvenance = {
  target_type: string;
  target_id: string;
  profile_id?: string;
  input_trace: Record<string, unknown>;
  decision_support_snapshot: Record<string, unknown>;
  algorithm_version: string;
  rule_set_version: string;
  source_versions: Record<string, unknown>;
  weights?: Record<string, unknown>;
  change_explanation: string;
  available_actions: string[];
  limitations: string[];
};

export type RecommendationSystemCard = {
  version: string;
  system_purpose: string;
  intended_users: string[];
  excluded_uses: string[];
  input_categories: string[];
  output_categories: string[];
  deterministic_services: string[];
  ai_assisted_components: string[];
  scoring_versions: Record<string, string>;
  known_limitations: string[];
  data_dependencies: string[];
  fairness_considerations: string[];
  human_oversight: string[];
  privacy: string[];
  validation_status: string;
  unresolved_risks: string[];
};
