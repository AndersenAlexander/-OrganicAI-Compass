export type ArchetypeResult = { name: string; summary: string; confidence: number; signals: string[] };
export type StrengthResult = { name: string; score: number; explanation: string; evidence: string[] };
export type ValueResult = { name: string; score: number; evidence: string[] };
export type CollaborationStyleResult = { name: string; summary: string; strengths: string[]; cautions: string[]; recommended_uses: string[]; human_led_decisions: string[] };
export type ContributionDomainResult = { name: string; score: number; explanation: string };
export type LearningPathResult = { name: string; level: string; duration: string; reason: string };

export interface ProfileUserFeedback {
  confirmed_nodes: string[];
  hidden_recommendations: string[];
  strength_adjustments: Record<string, number>;
  archetype_override: string | null;
  user_notes: Record<string, string>;
}

export interface HumanPotentialProfile {
  id: string;
  diagnostic_id: string;
  natural_discovery_snapshot?: Record<string, unknown>;
  assessment_prefill?: { responses?: Record<string, unknown>; notes?: Record<string, string>; [key: string]: unknown };
  human_potential_sections?: Record<string, string>;
  primary_archetype: ArchetypeResult;
  secondary_archetype: ArchetypeResult;
  strengths: StrengthResult[];
  values: ValueResult[];
  fears: string[];
  creative_tendencies: string[];
  ai_collaboration_style: CollaborationStyleResult;
  contribution_domains: ContributionDomainResult[];
  recommended_learning_paths: LearningPathResult[];
  uncertainties: string[];
  risk_notes: string[];
  ethical_note: string;
  user_feedback?: ProfileUserFeedback;
  created_at: string;
}

export interface FearTransform {
  id: string; profile_id: string; input_fear: string;
  output: { fear_summary: string; validation?: string; what_is_real: string; what_is_uncertain: string; what_the_user_can_control: string[]; what_user_can_control?: string[]; creative_reframe: string; ai_collaboration_opportunities: string[]; collaboration_opportunity?: string; fifteen_minute_action?: string; ethical_cautions: string[]; ethical_note?: string; seven_day_action: string; };
  created_at: string;
}
