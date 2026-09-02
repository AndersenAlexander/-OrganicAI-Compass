export type BrowserExtensionConnection = {
  id: string;
  profile_id: string;
  display_name: string;
  status: string;
  permissions: string[];
  expires_at: string;
  last_used_at?: string | null;
  revoked_at?: string | null;
  connection_token?: string;
  token_visible_once?: boolean;
  last_capture?: BrowserJobCapture | null;
  created_at: string;
};

export type BrowserExtensionSettings = {
  profile_id: string;
  feature_name: string;
  connections: BrowserExtensionConnection[];
  connected: boolean;
  installation_instructions: string[];
  privacy_explanation: string;
  privacy: {
    user_triggered_only: boolean;
    automatic_background_scraping: boolean;
    raw_html_storage: boolean;
    permissions: string[];
  };
};

export type BrowserJobCapture = {
  id: string;
  profile_id: string;
  job_analysis_id?: string | null;
  source_url: string;
  page_title: string;
  detected_title: string;
  detected_employer: string;
  source_domain: string;
  sanitised_text: string;
  captured_text_preview: string;
  selected_text: string;
  confirmed_fields: Record<string, unknown>;
  capture_method: string;
  requested_action: string;
  status: string;
  quality_warnings: string[];
  extension_version: string;
  captured_at: string;
  updated_at: string;
  duplicate_of?: string;
};

export type AdvisorComment = {
  id: string;
  share_id: string;
  profile_id: string;
  adviser_display_name: string;
  adviser_role: string;
  target_type: string;
  target_id: string;
  suggestion_type: string;
  comment_text: string;
  evidence_validation: string;
  supporting_reference: string;
  status: "pending" | "accepted" | "rejected" | string;
  user_response: string;
  provenance: string;
  created_at: string;
  updated_at: string;
};

export type AdvisorShare = {
  id: string;
  profile_id: string;
  adviser_display_name: string;
  adviser_role: string;
  purpose: string;
  permission_level: string;
  allowed_sections: string[];
  allowed_actions: string[];
  export_allowed: boolean;
  status: string;
  expires_at: string;
  access_attempts: number;
  max_access_attempts: number;
  last_accessed_at?: string | null;
  comments: AdvisorComment[];
  sections?: Array<{ name: string; items: unknown[]; limitations?: string[]; excluded?: string[] }>;
  limitations: string[];
  share_token?: string;
  review_url?: string;
  token_visible_once?: boolean;
  created_at: string;
};

export type PanelPersona = {
  persona_id: string;
  role_label: string;
  purpose: string;
  question_categories: string[];
  expected_depth: string;
  follow_up_style: string;
  terminology_level: string;
  allowed_evidence_focus: string[];
  maximum_question_count: number;
  voice_configuration?: Record<string, unknown>;
};

export type PanelQuestion = {
  id: string;
  question_text: string;
  category: string;
  source_type: string;
  related_job_requirement?: string;
  persona_id: string;
  persona_label: string;
  turn_index: number;
};

export type PanelTurn = {
  id: string;
  question_id?: string | null;
  question_text: string;
  answer_text: string;
  follow_up_questions: string[];
  rubric: Array<{ criterion: string; score: number }>;
  persona_id: string;
  persona_label: string;
  category: string;
  source: string;
  related_requirement: string;
  prohibited_inferences: string[];
};

export type PanelSession = {
  id: string;
  interview_id: string;
  profile_id: string;
  mode: string;
  delivery_mode: string;
  persona: string;
  status: string;
  panel_config: Record<string, unknown>;
  questions: PanelQuestion[];
  turns: PanelTurn[];
  feedback: Record<string, unknown>;
  rubric_results: Array<Record<string, unknown>>;
  no_single_opaque_score: boolean;
  updated_at: string;
};

export type CareerRoleProfile = {
  id: string;
  role_id: string;
  slug: string;
  title: string;
  aliases: string[];
  career_family: string;
  summary: string;
  profile: Record<string, unknown>;
  status: string;
  source_metadata: Record<string, unknown>;
  last_reviewed_date: string;
  version: string;
  updated_at: string;
};

export type CareerRoleComparison = {
  profile_id: string;
  career_slug: string;
  career_title: string;
  fit_dimensions: Record<string, { label: string; reason?: string; covered_skills?: string[]; missing_skills?: string[]; linked_applications?: unknown[] }>;
  evidence_passport_links: unknown[];
  recommended_experiments: string[];
  learning_objectives: string[];
  status: string;
};

export type DecisionJournalEntry = {
  id: string;
  profile_id: string;
  title: string;
  decision_type: string;
  status: string;
  decision_summary: string;
  context: string;
  selected_option: string;
  options: Array<Record<string, unknown>>;
  assumptions: Array<Record<string, unknown>>;
  uncertainty: Record<string, unknown>;
  confidence: string;
  reversibility: string;
  evidence_links: Array<Record<string, unknown>>;
  source_attributions: Array<Record<string, unknown>>;
  system_suggestions: Array<Record<string, unknown>>;
  ai_explanations: Array<Record<string, unknown>>;
  evidence_observations: Array<Record<string, unknown>>;
  adviser_inputs: Array<Record<string, unknown>>;
  user_reasoning: string;
  adviser_comment_ids: string[];
  career_slug?: string | null;
  job_analysis_id?: string | null;
  application_id?: string | null;
  privacy_scope: string;
  review_date?: string | null;
  outcome_status: string;
  outcome: Record<string, unknown>;
  reconsideration_reason: string;
  roadmap_mutation_allowed: boolean;
  version_number: number;
  reminder_status: string;
  versions?: Array<{ id: string; version_number: number; snapshot: Record<string, unknown>; change_reason: string; created_at: string }>;
  created_at: string;
  updated_at: string;
};
