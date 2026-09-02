import { useState } from "react";
import { transcribeAudio } from "../../api/voiceApi";
import { ErrorState } from "../shared/ErrorState";
import { LoadingState } from "../shared/LoadingState";
import { TranscriptPreview } from "./TranscriptPreview";
import { VoiceRecorder } from "./VoiceRecorder";
import { VoiceResponsePlayer } from "./VoiceResponsePlayer";

type VoiceChatControlsProps = {
  profileId?: string;
  onTranscriptConfirmed: (message: string) => Promise<void>;
  lastAudioUrl?: string;
  autoPlay?: boolean;
};

export function VoiceChatControls({ profileId, onTranscriptConfirmed, lastAudioUrl, autoPlay = false }: VoiceChatControlsProps) {
  const [transcript, setTranscript] = useState<string | null>(null);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [isConfirming, setIsConfirming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleRecordingComplete(blob: Blob) {
    setTranscript(null);
    setError(null);
    setIsTranscribing(true);
    try {
      const response = await transcribeAudio(blob);
      if (!response.transcript.trim()) {
        setError("We could not transcribe the audio. Please try again or type your message.");
        return;
      }
      setTranscript(response.transcript);
    } catch {
      setError("We could not transcribe the audio. Please try again or type your message.");
    } finally {
      setIsTranscribing(false);
    }
  }

  async function handleConfirm(editedTranscript: string) {
    setIsConfirming(true);
    setError(null);
    try {
      await onTranscriptConfirmed(editedTranscript);
      setTranscript(null);
    } finally {
      setIsConfirming(false);
    }
  }

  return (
    <div className="space-y-4">
      <div>
        <h2 className="font-display text-xl font-bold text-navy">Talk with OrganicAI Coach</h2>
        <p className="mt-2 text-sm leading-6 text-slate-600">
          Speak naturally. The platform will transcribe your voice, let you confirm the text, and respond with a calm AI voice.
        </p>
      </div>

      {error ? <ErrorState message={error} /> : null}
      {isTranscribing ? <LoadingState label="Transcribing your voice message..." /> : null}

      {transcript ? (
        <TranscriptPreview
          transcript={transcript}
          onConfirm={handleConfirm}
          onRetry={() => setTranscript(null)}
          onCancel={() => setTranscript(null)}
        />
      ) : (
        <VoiceRecorder onRecordingComplete={handleRecordingComplete} disabled={!profileId || isTranscribing || isConfirming} />
      )}

      {isConfirming ? <LoadingState label="Sending confirmed transcript to AI Coach..." /> : null}
      <VoiceResponsePlayer audioUrl={lastAudioUrl} autoPlay={autoPlay} />
    </div>
  );
}
