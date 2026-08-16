export type ChatRole = "user" | "assistant";

export type ChatMessage = {
  id: string;
  role: ChatRole;
  content: string;
  createdAt: string;
  inputMode?: "text" | "voice";
  audioUrl?: string;
  isLoading?: boolean;
  error?: string;
  audio_url?: string | null;
  created_at?: string;
  sourcesUsed?: RagSource[];
  confidenceNote?: string;
  ethicalNote?: string;
  intent?: string;
  profileSignals?: string[];
  groundingStatus?: "grounded" | "profile_grounded" | "general";
  retrievalStatus?: Record<string, unknown>;
  timing?: Record<string, number>;
  ragRunId?: string;
  contextQuality?: "strong"|"partial"|"insufficient";
  eventId?: string | number | null;
  appConversationId?: string | null;
};

export type RagSource = {
  id: string;
  document_name: string;
  section_title: string;
  score: number;
};

export interface ChatResponse {
  answer: string;
  suggested_actions?: string[];
  confidence_note?: string;
  sources_used?: RagSource[];
  ethical_note?: string;
  conversation_id?: string;
  conversationId?: string;
  message_id?: string;
  messageId?: string;
  intent?: string;
  executed_command?: { name: string; parameters: Record<string, unknown> } | null;
  profile_signals_used?: string[];
  grounding_status?: "grounded" | "profile_grounded" | "general";
  audio_available?: boolean;
  retrieval_status?: Record<string, unknown>;
  timing?: Record<string, number>;
  rag_run_id?: string;
  context_quality?: "strong"|"partial"|"insufficient";
  insufficient_context?: boolean;
}
