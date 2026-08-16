import { useEffect, useRef, useState } from "react";
import { Pause, Play, RotateCcw } from "lucide-react";
import { Button } from "../shared/Button";

type VoiceResponsePlayerProps = {
  audioUrl?: string;
  autoPlay?: boolean;
};

export function VoiceResponsePlayer({ audioUrl, autoPlay = false }: VoiceResponsePlayerProps) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);

  useEffect(() => {
    if (!audioUrl || !autoPlay) return;
    const audio = audioRef.current;
    audio?.play().then(() => setIsPlaying(true)).catch(() => setIsPlaying(false));
  }, [audioUrl, autoPlay]);

  useEffect(() => {
    return () => {
      if (audioUrl?.startsWith("blob:")) URL.revokeObjectURL(audioUrl);
    };
  }, [audioUrl]);

  if (!audioUrl) return null;

  function togglePlayback() {
    const audio = audioRef.current;
    if (!audio) return;
    if (audio.paused) {
      audio.play().then(() => setIsPlaying(true)).catch(() => setIsPlaying(false));
    } else {
      audio.pause();
      setIsPlaying(false);
    }
  }

  function replay() {
    const audio = audioRef.current;
    if (!audio) return;
    audio.currentTime = 0;
    audio.play().then(() => setIsPlaying(true)).catch(() => setIsPlaying(false));
  }

  return (
    <div className="mt-3 rounded-2xl border border-teal/15 bg-mist/70 p-3">
      <p className="text-xs font-bold uppercase tracking-[0.16em] text-teal">AI voice response</p>
      <audio ref={audioRef} src={audioUrl} onEnded={() => setIsPlaying(false)} className="hidden">
        <track kind="captions" />
      </audio>
      <div className="mt-3 flex flex-wrap gap-2">
        <Button type="button" variant="secondary" onClick={togglePlayback}>
          {isPlaying ? <Pause size={17} /> : <Play size={17} />} {isPlaying ? "Pause" : "Listen to response"}
        </Button>
        <Button type="button" variant="ghost" onClick={replay}>
          <RotateCcw size={17} /> Replay
        </Button>
      </div>
    </div>
  );
}
