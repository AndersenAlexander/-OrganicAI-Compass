import type { ReactNode } from "react";

export function DiagnosticQuestionCard({ title, subtitle, children }: { title: string; subtitle?: string; children: ReactNode }) {
  return (
    <article className="rounded-[1.5rem] border border-[color:var(--border-soft)] bg-[color:var(--bg-glass)] p-5 backdrop-blur-xl">
      <h3 className="font-semibold theme-text">{title}</h3>
      {subtitle ? <p className="mt-1 text-sm theme-muted">{subtitle}</p> : null}
      <div className="mt-4">{children}</div>
    </article>
  );
}
