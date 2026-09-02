import { useState } from "react";
import { Check, Edit3, Save, X } from "lucide-react";
import type { ProfileUserFeedback } from "../../types/profile";

export type PotentialNodeDetail = { id:string; title:string; interpretation:string; confidence?:number; signals:string[]; evidence:string[]; actions:string[]; caution:string };
const unique = (items:string[]) => [...new Set(items)];

export function PotentialNodeDetailPanel({ node, feedback, onSave }:{ node:PotentialNodeDetail; feedback:ProfileUserFeedback; onSave:(feedback:ProfileUserFeedback)=>Promise<void> }) {
  const [editing,setEditing]=useState(false);
  const [note,setNote]=useState(feedback.user_notes[node.id] || "");
  const [saving,setSaving]=useState(false);
  const confirmed=feedback.confirmed_nodes.includes(node.id);
  async function persist(next:ProfileUserFeedback) { setSaving(true); try { await onSave(next); } finally { setSaving(false); } }
  const list = (items:string[], fallback:string) => unique(items).length ? unique(items).map((item,index) => <li key={`${item}-${index}`}>• {item}</li>) : <li>{fallback}</li>;
  return <section className="glass-card p-6" aria-live="polite">
    <div className="flex flex-wrap items-start justify-between gap-3"><div><p className="text-xs font-bold uppercase tracking-wider text-[color:var(--teal)]">Selected interpretation</p><h2 className="mt-2 font-display text-3xl font-semibold theme-text">{node.title}</h2></div>{node.confidence != null ? <span className="organic-chip text-xs">Confidence {Math.round(node.confidence*100)}%</span> : <span className="organic-chip text-xs">Not enough data yet</span>}</div>
    <p className="mt-4 leading-7 theme-muted">{node.interpretation}</p>
    <div className="mt-5 grid gap-4 md:grid-cols-2"><div><h3 className="font-bold theme-text">Signals used</h3><ul className="mt-2 space-y-1 text-sm theme-muted">{list(node.signals,"Not enough explicit signals yet")}</ul></div><div><h3 className="font-bold theme-text">Evidence from diagnostic</h3><ul className="mt-2 space-y-1 text-sm theme-muted">{list(node.evidence,"Evidence will grow as you add reflections")}</ul></div><div><h3 className="font-bold theme-text">Recommended actions</h3><ul className="mt-2 space-y-1 text-sm theme-muted">{list(node.actions,"No actions suggested yet")}</ul></div><div><h3 className="font-bold theme-text">Keep human-led</h3><p className="mt-2 text-sm theme-muted">{node.caution}</p></div></div>
    {editing ? <div className="mt-5 rounded-2xl border border-[color:var(--border-soft)] p-4"><label className="block"><span className="text-sm font-semibold theme-text">Personal note or adjustment</span><textarea value={note} onChange={event=>setNote(event.target.value)} rows={3} className="organic-input mt-2" /></label><div className="mt-3 flex gap-2"><button type="button" disabled={saving} onClick={()=>void persist({...feedback,user_notes:{...feedback.user_notes,[node.id]:note}}).then(()=>setEditing(false))} className="organic-button"><Save size={16}/> Save adjustment</button><button type="button" onClick={()=>setEditing(false)} className="organic-button-secondary"><X size={16}/> Cancel</button></div></div> : null}
    <div className="mt-6 flex flex-wrap gap-3"><button type="button" disabled={confirmed||saving} onClick={()=>void persist({...feedback,confirmed_nodes:[...new Set([...feedback.confirmed_nodes,node.id])]})} className="organic-button disabled:opacity-60"><Check size={17}/> {confirmed ? "Interpretation confirmed" : "Confirm interpretation"}</button><button type="button" onClick={()=>setEditing(true)} className="organic-button-secondary"><Edit3 size={17}/> Adjust interpretation</button></div>
    <p className="mt-5 text-xs theme-muted">These are exploratory OrganicAI Compass indicators, not clinical or psychometric measurements.</p>
  </section>;
}
