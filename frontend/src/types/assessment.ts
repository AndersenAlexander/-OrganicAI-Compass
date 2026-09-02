export type AssessmentMode = "quick" | "complete" | "evidence_based";
export type AssessmentStatus = "not_started" | "in_progress" | "completed" | "needs_review" | "unavailable" | "error";

export interface AssessmentModeInfo {
  id: AssessmentMode;
  title: string;
  estimated_minutes: string;
  description: string;
}

export interface AssessmentModuleDefinition {
  id: string;
  title: string;
  description: string;
  order: number;
}

export interface AssessmentItemDefinition {
  id: string;
  module_id: string;
  prompt: string;
  item_type: "likert" | "value_rating" | "skill_level" | "single_select" | "text" | "long_text";
  dimension?: string | null;
  reverse_scored: boolean;
  required: boolean;
  quick_mode: boolean;
  metadata: Record<string, unknown>;
}

export interface AssessmentDefinition {
  id: string;
  title: string;
  version: string;
  scoring_version: string;
  disclaimer: string;
  methodology_note: string;
  modes: AssessmentModeInfo[];
  modules: AssessmentModuleDefinition[];
  items: AssessmentItemDefinition[];
  likert_options: Array<{ value: number; label: string }>;
  skill_levels: Array<{ value: string; score: number; label: string }>;
  evidence_statuses: Array<{ value: string; label: string }>;
}

export interface AssessmentResponse {
  id: string;
  session_id: string;
  profile_id: string;
  module_id: string;
  item_id: string;
  response_type: string;
  value: unknown;
  numeric_value?: number | null;
  text_value?: string | null;
  option_value?: string | null;
  payload?: Record<string, unknown>;
  excluded_from_recommendations: boolean;
  confirmation_status: string;
  source_type: string;
  created_at: string;
  updated_at: string;
}

export interface AssessmentSession {
  id: string;
  profile_id: string;
  mode: AssessmentMode;
  status: AssessmentStatus;
  consent_accepted: boolean;
  assessment_version: string;
  scoring_version: string;
  completion_time_seconds?: number | null;
  last_confirmed_at?: string | null;
  source_type: string;
  demo_marker: boolean;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  completed_at?: string | null;
  responses?: AssessmentResponse[];
}

export interface AssessmentScore {
  id: string;
  score_type: string;
  dimension: string;
  raw_score: number;
  normalized_score: number;
  label: string;
  interpretation: string;
  source_type: string;
  confirmation_status: string;
  metadata: Record<string, unknown>;
}

export interface AssessmentResults {
  status: AssessmentStatus;
  disclaimer: string;
  methodology_note: string;
  assessment_version: string;
  scoring_version: string;
  session: AssessmentSession | null;
  scores: AssessmentScore[];
  grouped_scores: Record<string, Record<string, AssessmentScore>>;
  summary: {
    combined_interest_profile?: string;
    top_work_values?: Array<{ value: string; label: string; raw_score: number; normalized_score: number }>;
    ai_literacy_level?: string;
    ai_readiness_level?: string;
    change_readiness?: string;
    skills?: Array<{ id: string; skill_id: string; label: string; category: string; level: number; level_label: string; evidence_status: string; evidence_note: string }>;
  };
  reflection_prompts: string[];
}

export interface AssessmentPrefill {
  source: string;
  source_profile_id: string;
  responses: Record<string, unknown>;
  notes: Record<string, string>;
  strategy: string;
}

export interface CareerMatchFactor {
  id: string;
  factor_type: string;
  label: string;
  raw_value: number;
  normalized_value: number;
  weight: number;
  polarity: string;
  evidence: Record<string, unknown>;
}

export interface CareerMatch {
  id: string;
  session_id?: string | null;
  profile_id: string;
  role_template_id?: string | null;
  canonical_direction_id?: string;
  category: string;
  title: string;
  role_family: string;
  description: string;
  alignment_score: number;
  alignment_label: string;
  explanation: string;
  supporting_factors: string[];
  conflicting_factors: string[];
  missing_skills: string[];
  transferable_skills: Array<Record<string, unknown>>;
  ai_opportunities: string[];
  next_step: string;
  transition_difficulty: string;
  time_horizon: string;
  status: string;
  user_feedback?: string | null;
  user_priority?: number | null;
  assumptions: string[];
  limitations: string[];
  source_metadata: Record<string, unknown>;
  hypothesis_dimensions?: {
    scores?: Record<string, number>;
    labels?: Record<string, string>;
    explanations?: Record<string, string>;
    rule_set?: string;
    rule_set_version?: string;
    weights?: Record<string, number>;
    market_fit?: Record<string, unknown>;
    support_fit?: Record<string, unknown>;
  };
  dimension_scores?: Record<string, number>;
  dimension_labels?: Record<string, string>;
  dimension_explanations?: Record<string, string>;
  factors: CareerMatchFactor[];
  created_at: string;
  updated_at: string;
}

export interface CareerComparison {
  id: string;
  profile_id: string;
  match_ids: string[];
  criteria_weights: Record<string, number>;
  decision_priorities: Record<string, unknown>;
  matrix: {
    items: Array<{
      match_id: string;
      title: string;
      alignment_label: string;
      strengths: string[];
      challenges: string[];
      uncertainties: string[];
      next_experiment: string;
      evidence_required: string[];
      criteria: Record<string, number>;
    }>;
  };
  created_at: string;
  updated_at: string;
}
