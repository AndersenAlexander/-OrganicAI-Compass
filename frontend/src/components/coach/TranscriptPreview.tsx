import { useState } from "react";
import { RotateCcw, Send, X } from "lucide-react";
import { Button } from "../shared/Button";
import { ErrorState } from "../shared/ErrorState";

type TranscriptPreviewProps = {
  transcript: string;
  onConfirm: (editedTranscript: string) => void;
  onRetry: () => void;
  onCancel: () => void;
};

export function TranscriptPreview({ transcript, onConfirm, onRetry, onCancel }: TranscriptPreviewProps) {
  const [editedTranscript, setEditedTranscript] = useState(transcript);
  const [error, setError] = useState<string | null>(null);

  function handleConfirm() {
    const trimmed = editedTranscript.trim();
    if (!trimmed) {
      setError("The transcript is empty. Please record again or type your message.");
      return;
    }
    onConfirm(trimmed);
  }

  return (
    <div className="space-y-4 rounded-[1.5rem] border border-white/70 bg-white/75 p-4 shadow-sm backdrop-blur">
      <div>
        <p className="text-sm font-bold text-teal">We heard:</p>
        <p className="mt-1 text-xs leading-5 text-slate-500">
          Review the transcript before sending it to the AI Coach.
        </p>
      </div>
      {error ? <ErrorState message={error} /> : null}
      <textarea
        value={editedTranscript}
        onChange={(event) => setEditedTranscript(event.target.value)}
        rows={4}
        className="w-full rounded-2xl border border-slate-200 bg-white/90 p-4 text-sm leading-6 outline-none ring-[color:var(--color-accent-action-soft)] focus:ring-4"
      />
      <div className="flex flex-wrap gap-2">
        <Button type="button" onClick={handleConfirm}>
          <Send size={17} /> Send to AI Coach
        </Button>
        <Button type="button" variant="secondary" onClick={onRetry}>
          <RotateCcw size={17} /> Record again
        </Button>
        <Button type="button" variant="ghost" onClick={onCancel}>
          <X size={17} /> Cancel
        </Button>
      </div>
    </div>
  );
}
