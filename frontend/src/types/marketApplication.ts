export type ProviderStatus = {
  provider_name: string;
  display_name: string;
  provider_type: string;
  enabled: boolean;
  configured: boolean;
  reachable: boolean;
  status: string;
  degraded_reason: string;
  documentation_url: string;
  documentation_checked_date: string;
  metadata: Record<string, unknown>;
  updated_at: string;
};

export type ProviderStatusResponse = {
  providers: ProviderStatus[];
  active_provider: string;
  live_enabled: boolean;
  warning: string;
};

export type MarketSignal = {
  id: string;
  signal_type: string;
  label: string;
  trend_label: string;
  observation_count: number;
  comparison_count: number;
  confidence_label: string;
  limitations: string[];
  factor: Record<string, unknown>;
};

export type MarketRadarPreference = {
  id: string;
  profile_id: string;
  country: string;
  county: string;
  municipality: string;
  commuting_area: string;
  radius_km?: number | null;
  work_modes: string[];
  preferred_languages: string[];
  employment_types: string[];
  full_time_part_time: string[];
  career_families: string[];
  selected_hypothesis_id?: string | null;
  minimum_publication_date?: string | null;
  experience_level: string;
  excluded_employers: string[];
  excluded_keywords: string[];
  relocation_preference: string;
  user_confirmed_storage: boolean;
  updated_at: string;
};

export type EvidenceCoverage = {
  covered_count: number;
  missing_count: number;
  total_count: number;
  covered_skills: string[];
  missing_skills: string[];
  label: string;
};

export type MarketJob = {
  id: string;
  provider: string;
  external_job_id: string;
  source_url: string;
  title: string;
  employer: string;
  location: string;
  municipality: string;
  country: string;
  publication_time?: string | null;
  expiry_time?: string | null;
  is_active: boolean;
  inactive_reason: string;
  work_mode: string;
  employment_type: string;
  full_time_part_time: string;
  languages: string[];
  skills: string[];
  career_families: string[];
  coverage?: EvidenceCoverage;
  recommendation?: {
    readiness_label: string;
    reason: string;
    missing_skills: string[];
    covered_skills: string[];
  };
  source_metadata: Record<string, unknown>;
};

export type MarketRadar = {
  profile_id: string;
  provider_status: ProviderStatusResponse;
  preferences: MarketRadarPreference | null;
  active_jobs: MarketJob[];
  saved_filters: Record<string, unknown>;
  signal_run: {
    id: string;
    status: string;
    coverage_label: string;
    source_metadata: Record<string, unknown>;
    created_at: string;
  };
  recurring_requirements: MarketSignal[];
  emerging_observed_requirements: MarketSignal[];
  location_language: {
    municipalities: Array<{ label: string; count: number }>;
    languages: Array<{ label: string; count: number }>;
  };
  limitations: string[];
};

export type RequirementMatch = {
  id: string;
  requirement_id: string;
  evidence_id?: string | null;
  evidence_type: string;
  evidence_strength: string;
  match_category: string;
  recency_label: string;
  gap: string;
  transferable_evidence: string[];
  recommended_action: string;
  deterministic_reason: string;
};

export type JobRequirement = {
  id: string;
  requirement_text: string;
  requirement_category: string;
  requirement_type: string;
  source_excerpt: string;
  source_location: string;
  extraction_method: string;
  confidence: string;
  user_confirmation_state: string;
  normalised_skill_id?: string | null;
  esco_uri?: string | null;
  status: string;
  matches: RequirementMatch[];
};

export type JobAnalysis = {
  id: string;
  profile_id: string;
  job_id?: string | null;
  input_type: string;
  source_url?: string | null;
  title: string;
  organisation: string;
  location: string;
  deadline?: string | null;
  raw_text_excerpt: string;
  structured_output: Record<string, unknown>;
  uncertainties: string[];
  ambiguous_statements: string[];
  status: string;
  extraction_version: string;
  requirements: JobRequirement[];
  readiness?: {
    id: string;
    readiness_label: string;
    reasons: string[];
    blockers: string[];
    recommended_actions: string[];
    deterministic_version: string;
    created_at: string;
  } | null;
  job?: MarketJob | null;
  updated_at: string;
};

export type DocumentClaim = {
  id: string;
  document_id: string;
  section_id?: string | null;
  claim_text: string;
  claim_type: string;
  status: string;
  safer_alternative: string;
  deterministic_reason: string;
  user_confirmation_state: string;
  blocked_for_export: boolean;
  evidence_links: Array<{ id: string; evidence_id?: string | null; relationship: string; confidence: string }>;
};

export type ApplicationDocument = {
  id: string;
  profile_id: string;
  job_analysis_id?: string | null;
  job_application_id?: string | null;
  document_type: "cv" | "cover_letter" | string;
  title: string;
  language: string;
  variant: string;
  status: string;
  evidence_lock_status: string;
  readiness_status: string;
  export_warning_acknowledged: boolean;
  sections: Array<{ id: string; section_type: string; title: string; content: string; include_in_export: boolean; order_index: number }>;
  claims: DocumentClaim[];
  versions: Array<{ id: string; version_number: number; warnings: string[]; created_at: string }>;
  source_metadata: Record<string, unknown>;
  updated_at: string;
};

export type JobApplication = {
  id: string;
  profile_id: string;
  job_id?: string | null;
  job_analysis_id?: string | null;
  cv_document_id?: string | null;
  cover_letter_document_id?: string | null;
  title: string;
  organisation: string;
  source: string;
  application_date?: string | null;
  deadline?: string | null;
  status: string;
  contacts: Array<Record<string, unknown>>;
  notes: string;
  next_action: string;
  auto_submitted: boolean;
  events: Array<{ id: string; event_type: string; from_status: string; to_status: string; description: string; created_at: string }>;
  stages: Array<{ id: string; stage_type: string; result: string; feedback: string; probable_questions: string[]; created_at: string }>;
  outcome?: {
    id: string;
    outcome: string;
    outcome_date?: string | null;
    employer_feedback: string;
    feedback_confirmed: boolean;
    user_interpretation: string;
    ai_interpretation: string;
    observed_data: Record<string, unknown>;
  } | null;
  recalibration?: {
    id: string;
    status: string;
    observed_data: Record<string, unknown>;
    suggestions: Array<{ suggestion_type: string; label: string; requires_user_confirmation: boolean }>;
    roadmap_changes_require_confirmation: boolean;
  } | null;
  job?: MarketJob | null;
  updated_at: string;
};

export type ResearchEvaluation = {
  study: {
    id: string;
    title: string;
    status: string;
    consent_version: string;
    export_schema_version: string;
    protocol: Record<string, unknown>;
    questions: Array<{ id: string; construct: string; prompt: string; instrument_type: string; scale_min: number; scale_max: number; order_index: number }>;
  };
  summary: Record<string, unknown>;
  consent_template: Record<string, unknown>;
  profile_id: string;
};
