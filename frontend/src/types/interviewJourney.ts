export type InterviewStage =
  | "recruiter_screening"
  | "first_interview"
  | "hiring_manager"
  | "behavioural"
  | "technical"
  | "case_study"
  | "portfolio"
  | "panel"
  | "final"
  | "reference_check"
  | "offer_discussion"
  | "salary_negotiation"
  | "custom";

export type Interview = {
  id: string;
  profile_id: string;
  application_id?: string | null;
  job_analysis_id?: string | null;
  organisation: string;
  role: string;
  stage_type: InterviewStage | string;
  stage_label: string;
  stage_order: number;
  scheduled_at?: string | null;
  timezone: string;
  location_or_platform: string;
  interview_format: string;
  expected_duration_minutes?: number | null;
  participants: Array<{ role: string; name?: string; user_confirmed?: boolean }>;
  preparation_status: string;
  mock_session_status: string;
  confidence_before?: number | null;
  confidence_after?: number | null;
  interview_result: string;
  follow_up_status: string;
  notes: string;
  source: string;
  user_confirmed: boolean;
  question_count: number;
  mock_session_count: number;
  has_preparation: boolean;
  has_reflection: boolean;
  application_status: string;
  updated_at: string;
};

export type InterviewDashboard = {
  profile_id: string;
  upcoming_interviews: Interview[];
  active_preparation: Interview[];
  saved_star_stories: StarStory[];
  readiness_checklist: string[];
  recent_mock_sessions: MockInterviewSession[];
  unresolved_evidence_gaps: Array<{ label: string; count: number }>;
  pending_reflections: Interview[];
  application_stage_links: Array<{ interview_id: string; application_id?: string | null; application_status: string }>;
  next_recommended_action: string;
  source_notes: string[];
};

export type PreparationBrief = {
  id: string;
  interview_id: string;
  sections: Record<string, { confirmed_facts?: unknown[]; likely_stage_expectations?: unknown[]; ai_generated_suggestions?: unknown[]; user_assumptions?: unknown[]; missing_information?: unknown[]; source?: string; uncertainty_note?: string }>;
  readiness_checklist: Array<{ label: string; status: string; optional?: boolean }>;
  source_notes: string[];
  language: string;
  status: string;
  user_confirmed: boolean;
};

export type InterviewQuestion = {
  id: string;
  interview_id: string;
  category: string;
  stage: string;
  question_text: string;
  why_it_may_be_asked: string;
  related_job_requirement_id?: string | null;
  related_job_requirement: string;
  related_evidence: Array<Record<string, unknown>>;
  answer_objective: string;
  risk_level: string;
  difficulty: string;
  source_type: string;
  origin: string;
  saved_by_user: boolean;
};

export type AnswerBuilder = {
  id: string;
  question_id: string;
  answer_objective: string;
  selected_evidence: Array<Record<string, unknown>>;
  suggested_structure: string[];
  possible_opening: string;
  possible_closing: string;
  risk_areas: string[];
  unsupported_claims: Array<Record<string, unknown>>;
  claim_statuses: Array<{ claim_text: string; status: string; safer_alternative?: string; deterministic_reason?: string }>;
  user_draft: string;
  revised_draft: string;
  user_confirmed: boolean;
};

export type StarStory = {
  id: string;
  profile_id: string;
  title: string;
  situation: string;
  task: string;
  action: string;
  result: string;
  reflection: string;
  skills_demonstrated: string[];
  evidence_links: Array<Record<string, unknown>>;
  confidentiality_status: string;
  claim_statuses: Array<Record<string, unknown>>;
  suitable_stages: string[];
  tags: string[];
  quality_status: string;
  quality: Record<string, unknown>;
  status: string;
  updated_at: string;
};

export type MockInterviewTurn = {
  id: string;
  question_text: string;
  answer_text: string;
  corrected_transcript: string;
  estimated_word_count: number;
  response_duration_seconds?: number | null;
  follow_up_questions: string[];
  rubric: Array<{ criterion: string; score: number }>;
  feedback: Record<string, unknown>;
};

export type MockInterviewSession = {
  id: string;
  interview_id: string;
  mode: string;
  delivery_mode: string;
  persona: string;
  status: string;
  feedback: {
    strengths?: string[];
    needs_improvement?: string[];
    missing_evidence?: string[];
    unsupported_or_unclear_claims?: string[];
    suggested_next_practice?: string;
    no_single_opaque_score?: boolean;
    voice_fallback?: string;
  };
  rubric_results: Array<{ criterion: string; average_score: number; attempts: number }>;
  turns: MockInterviewTurn[];
};

export type InterviewReflection = {
  id: string;
  interview_id: string;
  stage_completed: string;
  completed_date?: string | null;
  questions_remembered: string[];
  strong_answers: string[];
  weak_answers: string[];
  unexpected_topics: string[];
  confirmed_interviewer_feedback: string;
  user_interpretation: string;
  ai_interpretation: Record<string, unknown>;
  next_step: string;
  follow_up_deadline?: string | null;
  confidence_before?: number | null;
  confidence_after?: number | null;
  additional_evidence_needed: string[];
  outcome_status: string;
  user_confirmed: boolean;
};

export type FollowUpDraft = {
  id: string;
  draft_type: string;
  subject: string;
  body: string;
  source_facts: Array<{ label: string; value: string }>;
  status: string;
  auto_sent: boolean;
};

export type OfferReview = {
  id: string;
  profile_id: string;
  application_id?: string | null;
  interview_id?: string | null;
  organisation: string;
  role: string;
  offer_items: Record<string, unknown>;
  user_priorities: string[];
  review: {
    confirmed_offer_facts?: Array<{ field: string; value: unknown }>;
    missing_information?: string[];
    questions_to_clarify?: string[];
    negotiation_priorities?: Array<{ priority: string; draft_point: string }>;
    draft_negotiation_points?: string[];
    acceptance_considerations?: string[];
    unresolved_risks?: string[];
    legal_or_financial_advice?: boolean;
  };
  status: string;
};

export type VoiceStatus = {
  enabled: boolean;
  provider: string;
  configured: boolean;
  default_language: string;
  session_timeout_seconds: number;
  max_session_minutes: number;
  transcript_retention_enabled: boolean;
  raw_audio_retention_enabled: boolean;
  text_mode_available: boolean;
  status: string;
  privacy_notes: string[];
};
