import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, Compass } from "lucide-react";
import { getJourneySummary, type JourneySummary } from "../api/journeyApi";
import { Button } from "../components/shared/Button";
import { Card } from "../components/shared/Card";
import { ErrorState } from "../components/shared/ErrorState";
import { LoadingState } from "../components/shared/LoadingState";
import { useAuth } from "../context/AuthContext";
import { getProfileRecommendations } from "../api/recommendationsApi";
import type { Recommendation } from "../types/recommendation";
import { getRoadmap } from "../api/roadmapApi";
import type { Roadmap, RoadmapCheckIn } from "../types/roadmap";
import { getRoadmapCheckIns } from "../api/roadmapApi";

export function MyJourneyPage() {
  const { user } = useAuth();
  const [summary, setSummary] = useState<JourneySummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [roadmap, setRoadmap] = useState<Roadmap | null>(null);
  const [latestCheckIn, setLatestCheckIn] = useState<RoadmapCheckIn | null>(null);

  useEffect(() => {
    getJourneySummary()
      .then((data) => { setSummary(data); const profileId=data.profiles[0]?.id; if(profileId) { void getProfileRecommendations(profileId).then(setRecommendations); void getRoadmap(profileId).then(item => { setRoadmap(item); if (item) void getRoadmapCheckIns(item.id).then(rows => setLatestCheckIn(rows[0] || null)); }); } })
      .catch(() => setError("Your saved journey could not be loaded."))
      .finally(() => setIsLoading(false));
  }, []);

  if (isLoading) return <LoadingState label="Loading your saved journey..." />;

  const isEmpty =
    !summary || (summary.diagnostics.length === 0 && summary.profiles.length === 0 && summary.roadmaps.length === 0);

  return (
    <div className="space-y-8" data-testid="my-journey-page">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-teal">My Journey</p>
        <h1 className="mt-3 font-display text-4xl font-bold text-navy">{user?.name ?? "Your"} OrganicAI Compass</h1>
        <p className="mt-3 max-w-3xl text-slate-600">
          A saved view of your diagnostics, talent maps, roadmap direction, and AI Coach conversations.
        </p>
      </div>

      {error ? <ErrorState message={error} /> : null}

      {isEmpty ? (
        <Card className="space-y-5">
          <div className="grid h-14 w-14 place-items-center rounded-2xl bg-teal text-white">
            <Compass size={24} />
          </div>
          <h2 className="font-display text-2xl font-bold text-navy">Your journey is empty.</h2>
          <p className="max-w-2xl leading-7 text-slate-600">Start with the Human Diagnostic to create your first talent map and roadmap.</p>
          <Link to="/diagnostic">
            <Button type="button">
              Start Diagnostic <ArrowRight size={18} />
            </Button>
          </Link>
        </Card>
      ) : (<>
        <div className="grid gap-6 lg:grid-cols-4">
          <Card>
            <h2 className="font-display text-xl font-bold text-navy">Diagnostics</h2>
            <p className="mt-3 text-4xl font-black text-teal">{summary?.diagnostics.length ?? 0}</p>
            <p className="mt-2 text-sm text-slate-600">Saved diagnostic sessions.</p>
          </Card>
          <Card>
            <h2 className="font-display text-xl font-bold text-navy">Recommendations</h2>
            <p className="mt-3 text-4xl font-black text-teal">{recommendations.filter(item=>["accepted","in_progress","completed"].includes(item.status)).length}</p>
            <p className="mt-2 text-sm text-slate-600">Accepted, active, or completed suggestions.</p>
            {summary?.profiles[0]?.id ? <Link to={`/recommendations/${summary.profiles[0].id}`} className="mt-4 inline-flex text-sm font-bold text-teal">View recommendations <ArrowRight size={16}/></Link> : null}
          </Card>
          <Card>
            <h2 className="font-display text-xl font-bold text-navy">Talent maps</h2>
            <p className="mt-3 text-4xl font-black text-teal">{summary?.profiles.length ?? 0}</p>
            <p className="mt-2 text-sm text-slate-600">Generated human potential profiles.</p>
          </Card>
          <Card>
            <h2 className="font-display text-xl font-bold text-navy">Roadmaps</h2>
            <p className="mt-3 text-4xl font-black text-teal">{roadmap?.progress.completion_percentage ?? 0}%</p>
            <p className="mt-2 text-sm text-slate-600">{roadmap ? `${roadmap.progress.completed_actions} completed · ${roadmap.progress.in_progress_actions} active` : "Personal human-AI action plans."}</p>
            {summary?.profiles[0]?.id && roadmap ? <Link to={`/roadmap/${summary.profiles[0].id}`} className="mt-4 inline-flex text-sm font-bold text-teal">Open roadmap <ArrowRight size={16}/></Link> : null}
          </Card>
        </div>
        {roadmap ? <div className="grid gap-6 lg:grid-cols-2"><Card><h2 className="font-display text-xl font-bold text-navy">Latest check-in</h2><p className="mt-3 text-sm text-slate-600">{latestCheckIn ? `Energy ${latestCheckIn.energy_level} · ${latestCheckIn.main_blocker || latestCheckIn.what_worked}` : "No check-in yet."}</p></Card><Card><h2 className="font-display text-xl font-bold text-navy">Recent recalibration</h2><p className="mt-3 text-sm text-slate-600">{roadmap.last_recalibrated_at ? `Roadmap version ${roadmap.version} · ${new Date(roadmap.last_recalibrated_at).toLocaleDateString()}` : "No recalibration applied yet."}</p></Card></div> : null}
      </>)}
    </div>
  );
}
