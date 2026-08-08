import { FormEvent, useState } from "react";
import { Mic, Send } from "lucide-react";

type ChatInputProps = {
  onSend: (message: string) => Promise<void> | void;
  onStartVoice: () => void;
  disabled?: boolean;
};

export function ChatInput({ onSend, onStartVoice, disabled = false }: ChatInputProps) {
  const [message, setMessage] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = message.trim();
    if (!trimmed) return;
    await onSend(trimmed);
    setMessage("");
  }

  return (
    <form onSubmit={handleSubmit} className="flex items-center gap-2 border-t border-[color:var(--border-soft)] bg-[color:var(--bg-glass)] p-3">
      <input
        value={message}
        onChange={(event) => setMessage(event.target.value)}
        placeholder="Write to OrganicAI Coach..."
        className="min-h-11 flex-1 rounded-full border border-[color:var(--border-soft)] bg-[color:var(--bg-glass)] px-4 text-sm outline-none focus:ring-4 focus:ring-[color:var(--color-accent-action-soft)] theme-text"
      />
      <button
        type="button"
        onClick={onStartVoice}
        disabled={disabled}
        className="grid h-11 w-11 place-items-center rounded-full border border-[color:var(--border-soft)] bg-[color:var(--bg-glass)] text-[color:var(--teal)] transition hover:-translate-y-0.5 disabled:opacity-50"
        title="Start voice message"
      >
        <Mic size={18} />
      </button>
      <button
        type="submit"
        disabled={disabled || !message.trim()}
        className="grid h-11 w-11 place-items-center rounded-full bg-[color:var(--color-accent-action)] text-[color:var(--color-accent-action-text)] shadow-[var(--shadow-action)] transition hover:-translate-y-0.5 hover:bg-[color:var(--color-accent-action-hover)] disabled:opacity-50"
        title="Send"
      >
        <Send size={18} />
      </button>
    </form>
  );
}
