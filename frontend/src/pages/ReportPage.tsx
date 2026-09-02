import { Printer } from "lucide-react";
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getRoadmapCheckIns } from "../api/roadmapApi";
import { getReport } from "../api/profileApi";
import type { FearTransform, HumanPotentialProfile } from "../types/profile";
import type { Roadmap, RoadmapCheckIn } from "../types/roadmap";

type ReportData = { profile:HumanPotentialProfile; fear_transforms:FearTransform[]; roadmap:Roadmap|null };

export function ReportPage() {
  const { profileId } = useParams();
  const [data, setData] = useState<ReportData | null>(null);
  const [latestCheckIn, setLatestCheckIn] = useState<RoadmapCheckIn | null>(null);
  const [error, setError] = useState("");
  useEffect(() => { if (profileId) getReport(profileId).then(result => { setData(result); if (result.roadmap) void getRoadmapCheckIns(result.roadmap.id).then(rows => setLatestCheckIn(rows[0] || null)); }).catch(() => setError("The report could not be loaded.")); }, [profileId]);
  if (error) return <div className="organic-section text-red-600">{error}</div>;
  if (!data) return <div className="organic-section theme-muted">Loading report...</div>;
  const actions = data.roadmap ? Object.values(data.roadmap.horizons).flat() : [];
  const completed = actions.filter(item => item.status === "completed");
  const remaining = actions.filter(item => item.status !== "completed" && item.status !== "archived");
  const recommendationActions = actions.filter(item => item.source_type === "recommendation");
  return <div className="organic-page mx-auto max-w-5xl" data-testid="report-page">
    <div className="organic-section flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between"><div><p className="organic-badge">Final Report</p><h1 className="mt-4 font-display text-4xl font-bold theme-text">Human Potential Profile</h1></div><button type="button" onClick={() => window.print()} className="organic-button-secondary"><Printer size={18} /> Print / Export Report</button></div>
    <section className="glass-card p-6"><h2 className="font-display text-2xl font-bold theme-text">Talent Map Summary</h2><p className="mt-4 theme-muted">{data.profile.primary_archetype.name} with {data.profile.secondary_archetype.name} tendencies. Possible strengths: {data.profile.strengths.map(item => item.name).join(", ")}.</p></section>
    <section className="glass-card p-6"><h2 className="font-display text-2xl font-bold theme-text">Personal Roadmap</h2><p className="mt-4 theme-muted">{data.roadmap?.contribution_direction || "Generate your roadmap to add it to this report."}</p>{data.roadmap && <><p className="mt-2 text-sm theme-muted">Version {data.roadmap.version} · {data.roadmap.progress.completion_percentage}% complete · {completed.length} completed actions · {remaining.length} active or remaining actions.</p><p className="mt-2 text-sm theme-muted">Last recalibration: {data.roadmap.last_recalibrated_at ? new Date(data.roadmap.last_recalibrated_at).toLocaleDateString() : "Not yet recalibrated"}.</p><p className="mt-2 text-sm theme-muted">Recommendation-derived actions: {recommendationActions.length}.</p></>}</section>
    <section className="glass-card p-6"><h2 className="font-display text-2xl font-bold theme-text">Latest check-in summary</h2><p className="mt-4 theme-muted">{latestCheckIn ? `Energy ${latestCheckIn.energy_level}, confidence ${latestCheckIn.confidence_level}, perceived progress ${latestCheckIn.perceived_progress}. ${latestCheckIn.what_worked} ${latestCheckIn.main_blocker}` : "No check-in submitted yet."}</p></section>
    <section className="glass-card p-6"><h2 className="font-display text-2xl font-bold theme-text">AI Collaboration Style</h2><p className="mt-4 theme-muted"><strong>{data.profile.ai_collaboration_style.name}.</strong> {data.profile.ai_collaboration_style.summary}</p></section>
    <section className="glass-card p-6"><h2 className="font-display text-2xl font-bold theme-text">Ethical Reflection</h2><p className="mt-4 theme-muted">{data.profile.risk_notes.join(" ")} {data.profile.ethical_note}</p></section>
  </div>;
}
