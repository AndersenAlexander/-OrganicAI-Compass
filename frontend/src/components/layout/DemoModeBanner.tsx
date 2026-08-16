import { useEffect, useRef, useState } from "react";
import { LogOut, RotateCcw, X } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { resetDemoData } from "../../api/demoApi";
import { useAuth } from "../../context/AuthContext";

export function DemoModeBanner() {
  const { isDemo, logout } = useAuth();
  const navigate = useNavigate();
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [isResetting, setIsResetting] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (dialogRef.current?.open) dialogRef.current.querySelector<HTMLButtonElement>("button")?.focus();
  }, [isResetting]);

  if (!isDemo) return null;

  function openDialog() { dialogRef.current?.showModal(); }
  function closeDialog() { if (!isResetting) dialogRef.current?.close(); }
  async function reset() {
    setIsResetting(true); setMessage("");
    try {
      const result = await resetDemoData();
      localStorage.setItem("organicai_active_profile_id", result.active_profile_id);
      dialogRef.current?.close();
      setMessage("Demo data restored successfully.");
      window.dispatchEvent(new CustomEvent("organicai:demo-reset"));
      navigate(`/profile/${result.active_profile_id}`);
    } catch { setMessage("Demo data could not be restored. Please try again."); }
    finally { setIsResetting(false); }
  }
  function exitDemo() { logout(); localStorage.removeItem("organicai_active_profile_id"); navigate("/login"); }

  return <>
    <aside aria-label="Demo Mode" className="relative mx-auto mt-3 flex max-w-[1320px] flex-wrap items-center justify-between gap-3 rounded-2xl border border-[color:var(--oa-border-strong)] bg-[color:var(--oa-surface-strong)] px-4 py-3 text-[color:var(--oa-text)] shadow-[var(--oa-glow)]">
      <div><strong className="text-sm">Demo Mode</strong><span className="ml-2 text-sm text-[color:var(--oa-text-secondary)]">You are exploring demonstration data.</span></div>
      <div className="flex gap-2"><button type="button" onClick={openDialog} className="inline-flex min-h-11 items-center gap-2 rounded-full border border-[color:var(--oa-border-strong)] px-4 text-sm font-bold focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[color:var(--color-accent-action)]"><RotateCcw size={15}/>Reset Demo</button><button type="button" onClick={exitDemo} className="inline-flex min-h-11 items-center gap-2 rounded-full px-4 text-sm font-bold text-[color:var(--oa-text-secondary)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[color:var(--color-accent-action)]"><LogOut size={15}/>Exit Demo</button></div>
    </aside>
    <p className="sr-only" aria-live="polite">{message}</p>
    <dialog ref={dialogRef} aria-labelledby="demo-reset-title" aria-describedby="demo-reset-description" onCancel={(event)=>{event.preventDefault();closeDialog()}} className="m-auto w-[min(92vw,520px)] rounded-[2rem] border border-[color:var(--oa-border-strong)] bg-[color:var(--oa-surface-strong)] p-6 text-[color:var(--oa-text)] shadow-2xl backdrop:bg-slate-950/60">
      <div className="flex items-start justify-between gap-4"><div><h2 id="demo-reset-title" className="font-display text-3xl font-bold">Reset demonstration data?</h2><p id="demo-reset-description" className="mt-3 text-sm leading-6 text-[color:var(--oa-text-secondary)]">This restores the diagnostic, profile, recommendations, roadmap, and sample conversations to their original state.</p></div><button type="button" aria-label="Close reset dialog" onClick={closeDialog} className="grid h-11 w-11 shrink-0 place-items-center rounded-full focus-visible:outline focus-visible:outline-2 focus-visible:outline-[color:var(--color-accent-action)]"><X size={18}/></button></div>
      <div className="mt-6 flex justify-end gap-3"><button type="button" disabled={isResetting} onClick={closeDialog} className="min-h-11 rounded-full px-5 font-bold">Cancel</button><button type="button" disabled={isResetting} onClick={()=>void reset()} className="organic-button disabled:opacity-70">{isResetting?"Resetting...":"Reset Demo"}</button></div>
    </dialog>
  </>;
}
