import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, Compass } from "lucide-react";
import { getJourneySummary, getProfileJourneyState, type JourneySummary, type ProfileJourneyState } from "../api/journeyApi";
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
import { getCareerResilienceDashboard } from "../api/careerResilienceApi";
import type { CareerResilienceDashboard } from "../types/careerResilience";
import { useAppActions } from "../hooks/useAppActions";

export function MyJourneyPage() {
  const { user } = useAuth();
  const { activeProfileId } = useAppActions();
  const [summary, setSummary] = useState<JourneySummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [roadmap, setRoadmap] = useState<Roadmap | null>(null);
  const [latestCheckIn, setLatestCheckIn] = useState<RoadmapCheckIn | null>(null);
  const [careerDashboard, setCareerDashboard] = useState<CareerResilienceDashboard | null>(null);
  const [employmentJourney, setEmploymentJourney] = useState<ProfileJourneyState | null>(null);
  const [journeyProfileId, setJourneyProfileId] = useState("");

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setIsLoading(true);
      setError(null);
      try {
        const data = await getJourneySummary();
        const profileId = data.profiles.some((item) => item.id === activeProfileId)
          ? activeProfileId
          : data.profiles.length === 1 ? data.profiles[0].id : "";
        let recommendationData: Recommendation[] = [];
        let roadmapData: Roadmap | null = null;
        let careerData: CareerResilienceDashboard | null = null;
        let employmentData: ProfileJourneyState | null = null;
        if (profileId) {
          [recommendationData, roadmapData, careerData, employmentData] = await Promise.all([
            getProfileRecommendations(profileId).catch(() => [] as Recommendation[]),
            getRoadmap(profileId).catch(() => null),
            getCareerResilienceDashboard(profileId).catch(() => null),
            getProfileJourneyState(profileId).catch(() => null),
          ]);
        }
        const checkIns = roadmapData ? await getRoadmapCheckIns(roadmapData.id).catch(() => []) : [];
        if (cancelled) return;
        setSummary(data);
        setJourneyProfileId(profileId);
        setRecommendations(recommendationData);
        setRoadmap(roadmapData);
        setLatestCheckIn(checkIns[0] || null);
        setCareerDashboard(careerData);
        setEmploymentJourney(employmentData);
      } catch {
        if (!cancelled) setError("Your saved journey could not be loaded.");
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }
    void load();
    return () => { cancelled = true; };
  }, [activeProfileId]);

  if (isLoading) return <LoadingState label="Loading your saved journey..." />;

  const isEmpty =
    !summary || (summary.diagnostics.length === 0 && summary.profiles.length === 0 && summary.roadmaps.length === 0);
  const evidenceStates = careerDashboard?.evidence_states || [];
  const sufficientEvidenceStates = evidenceStates.filter((item) => item.state === "evidence_sufficient");
  // My Journey is a read-only projection: show a direction only when the
  // persisted read model identifies one unambiguous hypothesis.
  const evidenceState = sufficientEvidenceStates.length === 1
    ? sufficientEvidenceStates[0]
    : evidenceStates.length === 1 ? evidenceStates[0] : null;
  const currentHypothesis = evidenceState
    ? careerDashboard?.career_hypotheses.find((item) => item.id === evidenceState.hypothesis_id) || null
    : null;
  const experimentStatus = currentHypothesis
    ? careerDashboard?.active_experiments.find((item) => item.hypothesis_id === currentHypothesis.id)?.status || "no experiment record"
    : "no experiment record";

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
            {journeyProfileId ? <Link to={`/recommendations/${journeyProfileId}`} className="mt-4 inline-flex text-sm font-bold text-teal">View recommendations <ArrowRight size={16}/></Link> : null}
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
            {journeyProfileId && roadmap ? <Link to={`/roadmap/${journeyProfileId}`} className="mt-4 inline-flex text-sm font-bold text-teal">Open roadmap <ArrowRight size={16}/></Link> : null}
          </Card>
        </div>
        {careerDashboard && currentHypothesis ? (
          <Card data-testid="journey-career-evidence">
            <h2 className="font-display text-xl font-bold text-navy">Current career evidence</h2>
            <p className="mt-3 font-semibold text-navy" data-testid="journey-current-direction">{currentHypothesis.title}</p>
            <p className="mt-2 text-sm text-slate-600" data-testid="journey-evidence-state">Evidence state: {evidenceState?.state?.replace(/_/g, " ") || "not available"}</p>
            <p className="mt-1 text-sm text-slate-600">Experiment status: {experimentStatus.replace(/_/g, " ")}</p>
            <p className="mt-1 text-sm text-slate-600">Unresolved priority gaps: {evidenceState?.recommendation.unresolved_gap_skill_ids.length ?? careerDashboard.evidence_gaps.length}</p>
            <p className="mt-1 text-sm text-slate-600">Next action: {careerDashboard.next_recommended_action}</p>
            <p className="mt-3 text-xs text-slate-500">Evidence and roadmap changes remain separate; no roadmap update is applied here.</p>
          </Card>
        ) : null}
        {employmentJourney?.employment_summary ? (
          <Card data-testid="journey-employment-summary">
            <h2 className="font-display text-xl font-bold text-navy">Employment journey</h2>
            <p className="mt-3 text-sm text-slate-600">Applications: {employmentJourney.employment_summary.application_count} · Interviews: {employmentJourney.employment_summary.interview_count} · Completed interviews: {employmentJourney.employment_summary.completed_interview_count} · Offer reviews: {employmentJourney.employment_summary.offer_review_count}</p>
            <p className="mt-1 text-sm text-slate-600">Current next action: {employmentJourney.interview_summary?.next_action || "Create or select an interview when you are ready."}</p>
            <p className="mt-3 text-xs text-slate-500">Interview and offer events do not mutate the roadmap automatically.</p>
          </Card>
        ) : null}
        {roadmap ? <div className="grid gap-6 lg:grid-cols-2"><Card><h2 className="font-display text-xl font-bold text-navy">Latest check-in</h2><p className="mt-3 text-sm text-slate-600">{latestCheckIn ? `Energy ${latestCheckIn.energy_level} · ${latestCheckIn.main_blocker || latestCheckIn.what_worked}` : "No check-in yet."}</p></Card><Card><h2 className="font-display text-xl font-bold text-navy">Recent recalibration</h2><p className="mt-3 text-sm text-slate-600">{roadmap.last_recalibrated_at ? `Roadmap version ${roadmap.version} · ${new Date(roadmap.last_recalibrated_at).toLocaleDateString()}` : "No recalibration applied yet."}</p></Card></div> : null}
      </>)}
    </div>
  );
}
