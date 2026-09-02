import { useState } from "react";
import { BookOpen, Check, ChevronDown, Map, MessageCircle, Play, Star, X } from "lucide-react";
import type { Recommendation } from "../../types/recommendation";
import { acceptRecommendation, addRecommendationToRoadmap, completeRecommendation, rateRecommendation, rejectRecommendation, updateRecommendation } from "../../api/recommendationsApi";
import { RecommendationExplanationPanel } from "./RecommendationExplanationPanel";
import { useCoach } from "../../hooks/useCoach";
import { useAppActions } from "../../hooks/useAppActions";

const reasons = ["not relevant", "already know this", "too difficult", "too basic", "too much time", "not interested", "ethical concern", "other"];

export function RecommendationCard({ item, onChange }: { item: Recommendation; onChange: (next: Recommendation) => void }) {
  const [expanded, setExpanded] = useState(false);
  const [rejecting, setRejecting] = useState(false);
  const [reason, setReason] = useState("not relevant");
  const [feedback, setFeedback] = useState("");
  const [busy, setBusy] = useState(false);
  const coach = useCoach();
  const actions = useAppActions();
  const confidence = item.confidence >= .75 ? "High context confidence" : item.confidence >= .5 ? "Moderate context confidence" : "Limited context confidence";

  async function act(action: () => Promise<Recommendation>) {
    setBusy(true);
    try { onChange(await action()); } finally { setBusy(false); }
  }

  async function addToRoadmap() {
    setBusy(true);
    try { const data = await addRecommendationToRoadmap(item.id); onChange(data.recommendation); } finally { setBusy(false); }
  }

  return <article className="glass-card p-5" data-testid="recommendation-card" data-recommendation-id={item.id}>
    <div className="flex flex-wrap items-start justify-between gap-3">
      <div className="min-w-0 flex-1"><div className="flex flex-wrap gap-2 text-xs"><span className="organic-chip px-2 py-1">{item.category.replace(/_/g, " ")}</span><span className="organic-chip px-2 py-1">{item.status}</span><span className="organic-chip px-2 py-1">{item.rag_sources.length ? "RAG grounded" : "Profile grounded"}</span></div><h3 className="mt-3 font-display text-2xl font-semibold theme-text">{item.title}</h3><p className="mt-2 text-sm leading-6 theme-muted">{item.summary}</p></div>
      <div className="text-right"><p className="text-2xl font-bold text-[color:var(--teal)]">{Math.round(item.relevance_score * 100)}</p><p className="max-w-28 text-xs theme-muted" title="This score reflects platform matching rules and available profile signals. It is not a psychometric or predictive certainty.">OrganicAI relevance indicator</p></div>
    </div>
    <div className="mt-4 flex flex-wrap gap-3 text-xs theme-muted"><span>{item.time_horizon.replace(/_/g, " ")}</span><span>Effort: {item.effort}</span><span>Impact: {item.impact}</span><span>{confidence}</span></div>
    <button type="button" aria-expanded={expanded} onClick={() => setExpanded(value => !value)} className="organic-action-link mt-4 flex items-center gap-1 text-sm font-bold">{expanded ? "Collapse" : "Expand"}<ChevronDown className={expanded ? "rotate-180" : ""} size={16} /></button>
    {expanded ? <RecommendationExplanationPanel item={item} /> : null}
    <div className="mt-5 flex flex-wrap gap-2">
      {item.status === "suggested" ? <><button disabled={busy} type="button" onClick={() => void act(() => acceptRecommendation(item.id))} className="organic-button"><Check size={16} /> Accept</button><button disabled={busy} type="button" onClick={() => setRejecting(true)} className="organic-button-secondary"><X size={16} /> Not relevant</button></> : null}
      {["accepted", "suggested"].includes(item.status) ? <button disabled={busy} type="button" onClick={() => void addToRoadmap()} className="organic-button-secondary"><Map size={16} /> Add to roadmap</button> : null}
      {item.status === "accepted" ? <button type="button" onClick={() => void act(() => updateRecommendation(item.id, { status: "in_progress" }))} className="organic-button-secondary"><Play size={16} /> Start</button> : null}
      {item.status === "in_progress" ? <button type="button" onClick={() => void act(() => completeRecommendation(item.id))} className="organic-button"><Check size={16} /> Mark complete</button> : null}
      <button type="button" onClick={() => { coach.setSelectedRecommendationId(item.id); actions.openCoach(); void coach.sendTextMessage(`Explain recommendation ${item.id}: why was this recommended and what should remain human-led?`); }} className="organic-button-secondary"><MessageCircle size={16} /> Ask AI Coach</button>
      {item.rag_sources[0] ? <a href="/knowledge-base" className="organic-button-secondary"><BookOpen size={16} /> View source</a> : null}
    </div>
    {["accepted", "in_progress", "completed"].includes(item.status) ? <div className="mt-4 flex items-center gap-2"><span className="text-xs theme-muted">Rate:</span>{[1, 2, 3, 4, 5].map(value => <button type="button" aria-label={`Rate ${value} out of 5`} key={value} onClick={() => void rateRecommendation(item.id, value, feedback).then(() => onChange({ ...item, user_rating: value }))} className={value <= (item.user_rating || 0) ? "text-[color:var(--color-accent-action-muted)]" : "text-slate-300"}><Star size={18} fill="currentColor" /></button>)}</div> : null}
    {rejecting ? <div className="mt-4 rounded-2xl border border-[color:var(--border-soft)] p-4"><label className="text-sm font-bold theme-text">Why is this not relevant?<select value={reason} onChange={event => setReason(event.target.value)} className="organic-input mt-2">{reasons.map(value => <option key={value}>{value}</option>)}</select></label><label className="mt-3 block text-sm font-bold theme-text">Optional feedback<textarea value={feedback} onChange={event => setFeedback(event.target.value)} className="organic-input mt-2" rows={2} /></label><div className="mt-3 flex gap-2"><button type="button" onClick={() => void act(() => rejectRecommendation(item.id, { reason_code: reason, feedback_text: feedback })).then(() => setRejecting(false))} className="organic-button">Submit</button><button type="button" onClick={() => setRejecting(false)} className="organic-button-secondary">Cancel</button></div></div> : null}
  </article>;
}
