import { X } from "lucide-react";

export function ComingSoonDialog({ open, feature, description, onClose }: { open: boolean; feature: string; description: string; onClose: () => void }) {
  if (!open) return null;
  return <div className="fixed inset-0 z-[100] grid place-items-center bg-[#06101d]/65 p-4" role="presentation" onMouseDown={onClose}><div role="dialog" aria-modal="true" aria-labelledby="coming-soon-title" onMouseDown={(event) => event.stopPropagation()} className="glass-card relative max-w-md p-6"><button type="button" aria-label="Close dialog" onClick={onClose} className="absolute right-4 top-4 grid h-9 w-9 place-items-center rounded-full border border-[color:var(--border-soft)]"><X size={17} /></button><p className="organic-badge">Coming Soon</p><h2 id="coming-soon-title" className="mt-4 pr-10 font-display text-2xl font-bold theme-text">{feature}</h2><p className="mt-3 leading-6 theme-muted">{description}</p><button type="button" onClick={onClose} className="organic-button mt-6">Close</button></div></div>;
}
