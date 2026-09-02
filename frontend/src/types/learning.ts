export interface LearningProvider {
  id: string;
  provider_name: string;
  display_name: string;
  provider_type: string;
  base_url?: string | null;
  active: boolean;
  supports_external_search: boolean;
  api_enabled: boolean;
  metadata: Record<string, unknown>;
}

export interface LearningResource {
  id: string;
  provider_id: string;
  external_id?: string | null;
  title: string;
  canonical_url: string;
  description: string;
  resource_type: string;
  resource_type_label: string;
  level: string;
  language: string;
  subtitles: string[];
  duration_minutes?: number | null;
  cost_type: string;
  displayed_price?: number | null;
  currency?: string | null;
  instructor_organization?: string | null;
  rating?: number | null;
  review_count?: number | null;
  publication_date?: string | null;
  last_updated_date?: string | null;
  last_verified_at?: string | null;
  prerequisites: string[];
  certificate_available?: boolean | null;
  practical_exercises: boolean;
  project_included: boolean;
  quality_status: string;
  source_provenance: string;
  active: boolean;
  affiliate: boolean;
  affiliate_disclosure: string;
  notes_limitations: string;
  metadata_version: string;
  skills?: Array<{ skill_id: string; coverage_level: string; target_level: string; weight: number }>;
  objective_keys?: string[];
}

export interface LearningPreferences {
  id: string;
  profile_id: string;
  preferred_language: string;
  acceptable_secondary_languages: string[];
  free_only: boolean;
  max_budget_per_course?: number | null;
  monthly_learning_budget?: number | null;
  available_hours_per_week: number;
  preferred_content_formats: string[];
  preferred_session_length_minutes?: number | null;
  theory_practice_preference: string;
  certificate_importance: string;
  preferred_difficulty: string;
  target_completion_date?: string | null;
  accessibility_preferences: string[];
  subtitles_required: boolean;
  mobile_friendly: boolean;
  offline_availability: boolean;
  provider_exclusions: string[];
  strict_duration_limit_minutes?: number | null;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface SkillGapItem {
  id: string;
  analysis_id: string;
  skill_id: string;
  skill_label: string;
  current_level: number;
  current_level_label: string;
  target_level: number;
  target_level_label: string;
  gap_size: number;
  importance: number;
  evidence_level: string;
  required: boolean;
  ai_augmentable: boolean;
  prerequisite_skill_ids: string[];
  missing_prerequisites: string[];
  status: string;
  priority_label: string;
  priority_score_internal: number;
  dependency_order: number;
  explanation: string;
}

export interface LearningObjective {
  id: string;
  analysis_id: string;
  gap_item_id: string;
  objective_key: string;
  skill_id: string;
  target_level: number;
  target_level_label: string;
  description: string;
  prerequisite_ids: string[];
  estimated_effort_minutes: number;
  evidence_expected: string;
  role_relevance: string;
  priority: string;
  objective_version: string;
  status: string;
}

export interface PracticalProject {
  id: string;
  profile_id?: string | null;
  career_match_id?: string | null;
  skill_gap_item_id?: string | null;
  title: string;
  description: string;
  skills_demonstrated: string[];
  estimated_effort_minutes: number;
  suggested_deliverables: string[];
  completion_criteria: string[];
  portfolio_value: string;
  prerequisites: string[];
  status: string;
}

export interface SkillGapAnalysis {
  id?: string;
  profile_id?: string;
  career_match_id?: string | null;
  role_template_id?: string | null;
  analysis_version?: string;
  status: string;
  message?: string;
  summary?: string;
  hard_filters?: Array<Record<string, unknown>>;
  context?: Record<string, unknown>;
  items?: SkillGapItem[];
  objectives?: LearningObjective[];
  practical_projects?: PracticalProject[];
  created_at?: string;
  updated_at?: string;
}

export interface LearningRecommendationFactor {
  id: string;
  factor_type: string;
  factor_value: number;
  weight: number;
  explanation: string;
}

export interface LearningRecommendation {
  id: string;
  run_id: string;
  profile_id: string;
  career_match_id?: string | null;
  skill_gap_item_id?: string | null;
  learning_objective_id?: string | null;
  learning_resource_id: string;
  alignment_label: string;
  ranking_score_internal: number;
  rank_position: number;
  status: string;
  explanation: string;
  limitations: string[];
  recommendation_version: string;
  resource: LearningResource;
  skill_gap?: SkillGapItem | null;
  objective?: LearningObjective | null;
  factors: LearningRecommendationFactor[];
  created_at: string;
  updated_at: string;
}

export interface LearningRecommendationRun {
  id?: string;
  profile_id?: string;
  career_match_id?: string | null;
  skill_gap_analysis_id?: string | null;
  preferences_id?: string | null;
  recommendation_version?: string;
  status: string;
  message?: string;
  provider_status?: Array<Record<string, string>>;
  hard_filters?: Array<{ resource_id: string; skill_gap_id: string; reasons: string[] }>;
  ranking_weights?: Record<string, number>;
  recommendations: LearningRecommendation[];
  grouped_by_skill_gap?: Record<string, LearningRecommendation[]>;
  created_at?: string;
}

export interface LearningResourceComparison {
  id: string;
  profile_id: string;
  recommendation_ids: string[];
  resource_ids: string[];
  criteria_weights: Record<string, number>;
  matrix: {
    items: Array<{
      recommendation_id: string;
      resource_id: string;
      title: string;
      provider: string;
      resource_type: string;
      alignment_label: string;
      level: string;
      duration_minutes?: number | null;
      price?: number | null;
      cost_type: string;
      language: string;
      certificate_available?: boolean | null;
      project_component: boolean;
      last_verification?: string | null;
      prerequisites: string[];
      strengths: string[];
      limitations: string[];
      criteria: Record<string, number>;
    }>;
  };
  created_at: string;
}

export interface LearningPathItem {
  id: string;
  learning_path_id: string;
  phase_id: string;
  recommendation_id?: string | null;
  learning_resource_id?: string | null;
  learning_objective_id?: string | null;
  title: string;
  status: string;
  progress_percentage: number;
  user_reported_progress: string;
  completion_date?: string | null;
  evidence_url?: string | null;
  reflection: string;
  difficulty_feedback?: string | null;
  relevance_feedback?: string | null;
  expected_evidence: string;
  created_at: string;
  updated_at: string;
}

export interface LearningPathPhase {
  id: string;
  phase_index: number;
  title: string;
  description: string;
  objectives: string[];
  estimated_duration_minutes: number;
  weekly_effort_hours: number;
  completion_evidence: string;
  dependencies: number[];
  items: LearningPathItem[];
}

export interface LearningPath {
  id?: string;
  profile_id?: string;
  career_match_id?: string | null;
  recommendation_run_id?: string | null;
  title?: string;
  summary?: string;
  status: string;
  weekly_effort_hours?: number;
  phases: LearningPathPhase[];
  created_at?: string;
  updated_at?: string;
}
