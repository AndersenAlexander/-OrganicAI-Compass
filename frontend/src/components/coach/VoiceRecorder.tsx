import { useEffect, useRef, useState } from "react";
import { Mic, Square } from "lucide-react";
import { Button } from "../shared/Button";
import { ErrorState } from "../shared/ErrorState";

type VoiceRecorderProps = {
  onRecordingComplete: (blob: Blob) => void;
  disabled?: boolean;
};

function formatSeconds(seconds: number) {
  const minutes = Math.floor(seconds / 60).toString().padStart(2, "0");
  const remainder = (seconds % 60).toString().padStart(2, "0");
  return `${minutes}:${remainder}`;
}

export function VoiceRecorder({ onRecordingComplete, disabled = false }: VoiceRecorderProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [seconds, setSeconds] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);
  const streamRef = useRef<MediaStream | null>(null);

  useEffect(() => {
    if (!isRecording) return;
    const intervalId = window.setInterval(() => setSeconds((current) => current + 1), 1000);
    return () => window.clearInterval(intervalId);
  }, [isRecording]);

  useEffect(() => {
    return () => {
      streamRef.current?.getTracks().forEach((track) => track.stop());
    };
  }, []);

  async function startRecording() {
    setError(null);
    if (!navigator.mediaDevices?.getUserMedia) {
      setError("Voice recording is not supported in this browser. You can still use text chat.");
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      chunksRef.current = [];
      const mimeType = MediaRecorder.isTypeSupported("audio/webm") ? "audio/webm" : "";
      const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data);
      };
      recorder.onstop = () => {
        const type = recorder.mimeType || "audio/webm";
        const blob = new Blob(chunksRef.current, { type });
        stream.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
        if (blob.size > 0) onRecordingComplete(blob);
      };

      recorderRef.current = recorder;
      recorder.start();
      setSeconds(0);
      setIsRecording(true);
    } catch {
      setError("Microphone access was blocked. You can still use text chat.");
    }
  }

  function stopRecording() {
    if (recorderRef.current?.state === "recording") {
      recorderRef.current.stop();
    }
    setIsRecording(false);
  }

  return (
    <div className="space-y-3">
      {error ? <ErrorState message={error} /> : null}
      <div className="flex flex-wrap items-center gap-3">
        {!isRecording ? (
          <Button type="button" variant="secondary" onClick={startRecording} disabled={disabled}>
            <Mic size={18} /> Start voice message
          </Button>
        ) : (
          <Button type="button" onClick={stopRecording} disabled={disabled}>
            <Square size={17} /> Stop recording
          </Button>
        )}
        <span className={`rounded-full px-3 py-1 text-sm font-semibold ${isRecording ? "bg-red-50 text-red-700" : "bg-white/70 text-slate-600"}`}>
          {isRecording ? `Recording ${formatSeconds(seconds)}` : "Ready to record"}
        </span>
      </div>
    </div>
  );
}
