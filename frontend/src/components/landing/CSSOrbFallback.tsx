import { Compass } from "lucide-react";

export function CSSOrbFallback() {
  return (
    <div className="hero-human-ai-orb hero-human-ai-orb-fallback" aria-hidden="true">
      <span className="hero-human-ai-orb-ring" />
      <span className="hero-human-ai-orb-ring hero-human-ai-orb-ring-alt" />
      <span className="hero-human-ai-orb-core">
        <Compass className="h-9 w-9 text-[#99f6e4]" />
        <span className="mt-2 text-center text-sm font-black leading-4 tracking-[0.22em]">
          HUMAN
          <br />+<br />
          AI
        </span>
      </span>
    </div>
  );
}
