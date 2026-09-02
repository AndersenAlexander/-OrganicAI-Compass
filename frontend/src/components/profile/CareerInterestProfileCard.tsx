import { Compass } from "lucide-react";
import { Link } from "react-router-dom";
import type { RiasecCareerInterestProfile } from "../../lib/riasecCareerInterests";
import { riasecStatusCopy } from "../../lib/riasecCareerInterests";

export function CareerInterestProfileCard({ profile }: { profile: RiasecCareerInterestProfile | null }) {
  const ready = profile && profile.status !== "insufficient_information";
  return (
    <section className="glass-card p-5" aria-labelledby="riasec-career-interests-title">
      <div className="flex items-start gap-3">
        <span className="organic-icon-orb h-11 w-11">
          <Compass size={20} />
        </span>
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.14em] text-[color:var(--teal)]">Career Interests</p>
          <h2 id="riasec-career-interests-title" className="font-display text-lg font-bold theme-text">
            RIASEC-inspired Career Interests
          </h2>
        </div>
      </div>
      <p className="mt-3 text-sm theme-muted">{riasecStatusCopy(profile)}</p>
      {ready ? (
        <>
          {profile.topPattern ? (
            <p className="mt-3 text-sm font-semibold theme-text">
              Current interest pattern: <span className="text-[color:var(--teal)]">{profile.topPattern}</span>
            </p>
          ) : null}
          {profile.closeScoreNotice ? <p className="mt-2 text-xs theme-muted">{profile.closeScoreNotice}</p> : null}
          <div className="mt-4 space-y-3">
            {profile.dimensions.map((dimension) => {
              const score = dimension.score ?? 0;
              return (
                <div key={dimension.key}>
                  <div className="flex items-center justify-between gap-3 text-sm">
                    <span className="font-semibold theme-text">
                      {dimension.label} <span className="theme-muted">({dimension.code})</span>
                    </span>
                    <span className="theme-muted">{dimension.band}</span>
                  </div>
                  <div className="mt-1 h-2 rounded-full bg-[color:var(--bg-elevated)]" aria-hidden="true">
                    <div className="h-2 rounded-full bg-[color:var(--teal)]" style={{ width: `${Math.max(0, Math.min(100, score))}%` }} />
                  </div>
                  <p className="sr-only">
                    {dimension.label} score {dimension.score ?? "not enough information"}, {dimension.band}.
                  </p>
                </div>
              );
            })}
          </div>
          <p className="mt-4 text-xs theme-muted">
            Interest is kept separate from capability, evidence strength, transition feasibility, market fit, and support fit.
          </p>
        </>
      ) : null}
      <Link to="/diagnostic" className="organic-button-secondary mt-4 w-full">
        Review Natural Discovery
      </Link>
    </section>
  );
}
