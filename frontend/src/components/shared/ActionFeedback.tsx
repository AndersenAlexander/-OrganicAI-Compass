import { useEffect, useState } from "react";
import { CheckCircle2, X } from "lucide-react";
import { useLocation } from "react-router-dom";

export const ACTION_FEEDBACK_KEY="organicai_action_feedback";

export function ActionFeedback(){const location=useLocation();const [message,setMessage]=useState("");useEffect(()=>{const next=sessionStorage.getItem(ACTION_FEEDBACK_KEY);if(!next)return;sessionStorage.removeItem(ACTION_FEEDBACK_KEY);setMessage(next);const timer=window.setTimeout(()=>setMessage(""),4200);return()=>window.clearTimeout(timer)},[location.key]);if(!message)return null;return <div role="status" aria-live="polite" className="fixed bottom-6 left-1/2 z-[110] flex max-w-[calc(100vw-2rem)] -translate-x-1/2 items-center gap-3 rounded-full border border-[color:var(--color-accent-success-soft)] bg-white/95 px-5 py-3 text-sm font-semibold text-[#102033] shadow-[0_18px_55px_rgba(15,23,42,0.2)] backdrop-blur dark:border-[color:var(--color-accent-success-soft)] dark:bg-[#071527]/95 dark:text-white"><CheckCircle2 className="text-[color:var(--color-accent-success)]" size={18}/><span>{message}</span><button type="button" aria-label="Dismiss notification" onClick={()=>setMessage("")}><X size={16}/></button></div>}
