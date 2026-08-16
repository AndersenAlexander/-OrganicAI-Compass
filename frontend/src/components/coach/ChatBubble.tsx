import { Mic } from "lucide-react";
import type { ChatMessage } from "../../types/chat";
import { VoiceResponsePlayer } from "./VoiceResponsePlayer";
import { RagFeedback } from "../shared/RagFeedback";

type ChatBubbleProps = {
  message: ChatMessage;
  autoPlay?: boolean;
  isLatestAudio?: boolean;
};

export function ChatBubble({ message, autoPlay = false, isLatestAudio = false }: ChatBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div className={`max-w-[88%] rounded-2xl p-4 text-sm leading-6 shadow-[0_14px_45px_rgba(15,23,42,0.1)] ${isUser ? "ml-auto bg-gradient-to-r from-[#0f766e] to-[#0891b2] text-white" : "border border-[color:var(--border-soft)] bg-[color:var(--bg-glass)] theme-muted backdrop-blur-xl"}`}>
      <div className={`mb-2 flex items-center gap-2 text-xs font-bold uppercase tracking-[0.14em] ${isUser ? "text-white/80" : "theme-muted"}`}>
        {message.inputMode === "voice" ? <Mic size={14} /> : null}
        {isUser ? "You" : "OrganicAI Coach"}
      </div>
      <p>{message.content}</p>
      {!isUser ? <p className="mt-3 text-xs font-bold uppercase tracking-[0.12em] text-[color:var(--teal)]">{message.sourcesUsed?.length ? "Grounded answer" : message.groundingStatus === "profile_grounded" ? "Profile-grounded guidance" : "General AI answer"}</p> : null}
      {!isUser && message.sourcesUsed?.length ? (
        <div className="mt-3 rounded-2xl border border-[color:var(--border-soft)] bg-[color:var(--bg-glass)] p-3">
          <p className="text-xs font-bold uppercase tracking-[0.14em] text-[color:var(--teal)]">Grounded answer</p>
          <p className="mt-1 text-xs theme-muted">Based on OrganicAI Knowledge Base</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {message.sourcesUsed.map((source) => (
              <span key={source.id} className="organic-chip px-2.5 py-1 text-xs font-semibold">
                {source.document_name.replace(/_/g, " ")}
              </span>
            ))}
          </div>
        </div>
      ) : null}
      {!isUser && message.profileSignals?.length ? <details className="mt-3 rounded-xl border border-[color:var(--border-soft)] p-2 text-xs"><summary className="cursor-pointer font-bold theme-text">Why this fits your profile</summary><div className="mt-2 flex flex-wrap gap-2">{message.profileSignals.map(signal=><span key={signal} className="organic-chip px-2 py-1 text-[10px]">{signal}</span>)}</div><p className="mt-2 theme-muted">Final choices, personal values, and ethical responsibility should remain human-led.</p></details> : null}
      {!isUser && message.retrievalStatus ? <details className="mt-2 text-xs"><summary className="cursor-pointer font-semibold">Why this answer?</summary><pre className="mt-2 overflow-auto whitespace-pre-wrap rounded-xl bg-black/5 p-2 dark:bg-white/5">{JSON.stringify(message.retrievalStatus, null, 2)}</pre></details> : null}
      {!isUser && message.confidenceNote ? (
        <p className="mt-3 text-xs theme-muted">{message.confidenceNote}</p>
      ) : null}
      {!isUser && message.ethicalNote ? (
        <p className="mt-2 rounded-xl border border-[color:var(--border-soft)] bg-[color:var(--color-surface-secondary)] p-2 text-xs theme-muted">{message.ethicalNote}</p>
      ) : null}
      {!isUser && typeof message.retrievalStatus?.context_quality==="string" ? <span className={`rag-quality ${message.retrievalStatus.context_quality}`}>Context quality: {String(message.retrievalStatus.context_quality)}</span>:null}
      {!isUser && typeof message.retrievalStatus?.rag_run_id==="string" ? <RagFeedback runId={message.retrievalStatus.rag_run_id}/>:null}
      {!isUser ? <VoiceResponsePlayer audioUrl={message.audioUrl} autoPlay={autoPlay && isLatestAudio} /> : null}
    </div>
  );
}
