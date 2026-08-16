export interface DiagnosticPayload {
  interests: string[];
  natural_activities: string[];
  problems_noticed: string[];
  preferred_orientation: string[];
  career_interests: Record<string, number>;
  fears: string[];
  fear_intensity: number;
  ai_threat_or_opportunity: string;
  unclear_future: string;
  desired_world: string;
  values: string[];
  contribution_if_supported: string;
  skills: string[];
  preferred_learning_style: string[];
  cognitive_style: string[];
  ai_experience: string;
  ai_tools_used: string[];
  ai_confidence: number;
  ai_help_goals: string[];
  preferred_interaction: "text" | "voice" | "both";
  raw_answers: Record<string, string>;
}

export interface DiagnosticResponse {
  diagnostic_id: string;
  profile_id: string;
}
