export interface CareerExperimentTemplate {
  id: string;
  title: string;
  target_role_family: string;
  purpose: string;
  real_world_scenario: string;
  user_instructions: string[];
  expected_deliverables: string[];
  estimated_duration_minutes: number;
  difficulty: string;
  required_skills: string[];
  skills_being_evaluated: string[];
  optional_prerequisites: string[];
  allowed_tools: string[];
  ai_assistance_policy: string;
  reflection_questions: string[];
  completion_criteria: string[];
  evidence_generated: string[];
  version: string;
  source_metadata: Record<string, unknown>;
  active: boolean;
  evaluation_rubric?: {
    id: string | null;
    version: string;
    rating_scale: Array<{ rating: number; label: string }>;
    criteria: Array<{
      id: string;
      criterion_id: string;
      skill_id: string;
      description: string;
      weight: number;
      evidence_requirement: string;
    }>;
  };
}

export interface CareerExperimentRecommendation {
  version: string;
  state?: "experiment_recommended" | "evidence_sufficient";
  rank: number | null;
  score: number | null;
  score_breakdown: Record<string, number>;
  targeted_gap_skill_ids: string[];
  unresolved_gap_skill_ids: string[];
  already_practically_verified_skill_ids: string[];
  rationale: string[];
  next_options?: string[];
  ranked_template_ids: string[];
  ranked_candidates?: Array<{
    template_id: string;
    score: number;
    score_breakdown: Record<string, number>;
    targeted_gap_skill_ids: string[];
    already_verified_skill_ids: string[];
    duplicate_reason: string;
  }>;
}

export interface CareerEvidenceSufficientState {
  status: "evidence_sufficient";
  profile_id: string;
  career_match_id?: string | null;
  hypothesis_id?: string | null;
  user_confirmed: boolean;
  expected_evidence_gain: "None";
  recommendation: CareerExperimentRecommendation;
}

export interface CareerExperimentSession {
  id: string;
  profile_id: string;
  career_match_id?: string | null;
  experiment_template_id: string;
  roadmap_action_id?: string | null;
  hypothesis_id?: string | null;
  evidence_gap_id?: string | null;
  mode: string;
  status: string;
  user_confirmed: boolean;
  confidence_label: string;
  expected_evidence_gain?: string;
  recommendation?: CareerExperimentRecommendation | null;
  created_at: string;
  updated_at: string;
  started_at?: string | null;
  submitted_at?: string | null;
  evaluated_at?: string | null;
  template?: CareerExperimentTemplate | null;
  submission?: Record<string, unknown> | null;
  result?: {
    id: string;
    overall_score: number;
    overall_label: string;
    criteria_scores: Array<{ criterion_id: string; skill_id: string; rating: number; weight: number; interpretation: string }>;
    skills_evaluated: string[];
    strengths: string[];
    improvement_areas: string[];
    evidence_created: Array<{ skill_id: string; skill_label: string; evidence_id: string; confidence_label: string; strength_label: string }>;
    persistence?: {
      status: string;
      review_id?: string;
      source_type?: string;
      evidence_ids?: string[];
    };
    linked_gap?: {
      intended_gap?: { id: string; skill_id: string; skill_label: string; status: string } | null;
      assessed_skill_ids?: string[];
      generated_skill_ids?: string[];
      directly_assessed?: boolean;
      remaining_unresolved?: boolean;
      message?: string;
    };
    evidence_not_created?: Array<{ skill_id: string; skill_label: string; deterministic_score?: number | null; reason: string }>;
    provenance?: {
      canonical_direction_id?: string | null;
      career_match_id?: string | null;
      hypothesis_id?: string | null;
      experiment_session_id?: string;
      submission_id?: string;
      deterministic_review_id?: string;
      experiment_template_id?: string;
    };
  } | null;
  reviews: Array<Record<string, unknown>>;
}

export interface EvidencePassport {
  profile_id: string;
  version: string;
  methodology: string;
  skills: Array<{
    skill_id: string;
    skill_label: string;
    category: string;
    declared_level: number;
    target_level: number;
    evidence_confidence: string;
    strongest_evidence_label: string;
    evidence_sources: Array<{
      id: string;
      type: string;
      title: string;
      description: string;
      url?: string | null;
      confidence: string;
      strength: string;
      sources?: Array<{
        id: string;
        source_type: string;
        provenance_label: string;
        deterministic_score?: number;
        deterministic_review_id?: string;
        experiment_session_id?: string;
        submission_id?: string;
      }>;
    }>;
    recency: {
      status: string;
      evidence_age_days?: number | null;
      refresh_recommendation: string;
    };
    status: string;
    related_roles: string[];
    outstanding_verification_needs: string[];
  }>;
}

export interface SupportedPathRun {
  id?: string;
  status: string;
  results: Array<{
    id: string;
    career_match_id?: string | null;
    role_family: string;
    title: string;
    personal_fit: string;
    capability_fit: string;
    market_fit: string;
    support_fit: string;
    transition_difficulty: string;
    estimated_preparation_range: string;
    main_strengths: string[];
    main_gaps: string[];
    main_uncertainties: string[];
    required_experiment_id?: string | null;
    required_experiment_title: string;
    possible_public_support: Array<Record<string, unknown>>;
    next_best_action: string;
    official_assessment_required: boolean;
  }>;
}

export interface JobLossProfile {
  id: string;
  profile_id: string;
  consent_accepted: boolean;
  country_of_residence: string;
  country_of_employment: string;
  municipality_or_region: string;
  last_working_date?: string | null;
  contract_termination_type: string;
  employment_status: string;
  reduction_in_working_hours?: number | null;
  jobseeker_registration_status: string;
  current_benefits: string[];
  training_interest: string;
  availability_for_work: string;
  sensitive_explanations: Record<string, string>;
}

export interface ImmediateActionPlan {
  id: string;
  status: string;
  items: Array<{
    id: string;
    title: string;
    reason: string;
    urgency: string;
    official_source: { title: string; url: string; last_checked_date: string };
    status: string;
    due_date?: string | null;
    user_confirmation: boolean;
  }>;
}

export interface SupportScreening {
  id: string;
  status: string;
  country: string;
  unknown_fields: string[];
  preliminary_result: {
    programmes: Array<{
      programme_id: string;
      programme_name: string;
      preliminary_label: string;
      explanation: string;
      unknown_fields: string[];
      official_source: { title: string; url: string; last_checked_date: string };
      human_assessment_required: boolean;
    }>;
    limitations: string[];
  };
  rule_version: string;
}

export interface SupportBrief {
  id: string;
  content: Record<string, unknown>;
  disclaimer: string;
  official_source_references: Array<{ programme_id?: string; title: string; url: string; last_checked_date: string }>;
  unresolved_questions: string[];
}

export interface CareerResilienceDashboard {
  profile_id: string;
  workflow: string[];
  life_event: JobLossProfile | null;
  urgent_actions: ImmediateActionPlan["items"];
  career_hypotheses: Array<{
    id: string;
    career_match_id?: string | null;
    canonical_direction_id?: string;
    title: string;
    role_family: string;
    statement: string;
    uncertainty_label: string;
    status: string;
    missing_evidence?: Array<{ gap_id: string; capability: string; status: string; gap_kind: string; reason: string }>;
  }>;
  active_experiments: CareerExperimentSession[];
  evidence_updates: EvidencePassport["skills"];
  evidence_gaps: Array<{ skill_id: string; capability_label?: string; status: string }>;
  evidence_states?: Array<{
    hypothesis_id: string;
    career_match_id: string;
    canonical_direction_id: string;
    state: "experiment_recommended" | "evidence_sufficient";
    recommendation: CareerExperimentRecommendation;
  }>;
  best_supported_paths: SupportedPathRun["results"];
  potential_programmes: Array<Record<string, unknown>>;
  next_recommended_action: string;
}
