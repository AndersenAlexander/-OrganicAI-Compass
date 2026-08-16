import { useState } from "react";
import type { RoadmapAction } from "../../types/roadmap";

type Props = {
  action: RoadmapAction;
  onUpdate: (patch: Partial<RoadmapAction>) => void;
  onStart: () => void;
  onComplete: (outcome: string) => void;
  onSkip: (reason: string) => void;
  onPostpone: () => void;
  onRemove: () => void;
  onCoach: () => void;
};

export function RoadmapActionCard({
  action,
  onUpdate,
  onStart,
  onComplete,
  onSkip,
  onPostpone,
  onRemove,
  onCoach,
}: Props) {
  const [open, setOpen] = useState(false);
  const [note, setNote] = useState("");
  const [edit, setEdit] = useState(false);
  const [source, setSource] = useState(action.title);

  return (
    <article className="rounded-2xl border border-[color:var(--border-soft)] bg-[color:var(--surface)] p-4">
      <div className="flex gap-3">
        <input
          aria-label={`Mark ${action.title} complete`}
          type="checkbox"
          checked={action.status === "completed"}
          onChange={(event) => (event.target.checked ? onComplete(note) : onUpdate({ status: "not_started", progress_percentage: 0 }))}
          className="mt-1 h-4 w-4"
          style={{ accentColor: "var(--color-accent-success)" }}
        />

        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="font-bold theme-text">{action.title}</h3>
            <span className="rounded-full bg-[color:var(--teal-soft)] px-2 py-0.5 text-xs font-semibold text-[color:var(--teal)]">
              {action.source_type.replace(/_/g, " ")}
            </span>
            <span className="text-xs theme-muted">
              Priority {action.priority} - {action.estimated_minutes ?? "-"} min - {action.status.replace(/_/g, " ")}
            </span>
          </div>

          <p className="mt-1 text-sm theme-muted">First step: {action.first_step || "Choose a small first step."}</p>

          <div className="mt-3 flex flex-wrap gap-2">
            <button type="button" className="organic-action-link text-xs font-bold" onClick={() => setOpen(!open)}>
              {open ? "Hide details" : "Expand"}
            </button>
            {action.status !== "completed" ? (
              <button type="button" className="organic-action-link text-xs font-bold" onClick={onStart}>
                Start
              </button>
            ) : null}
            <button type="button" className="organic-action-link text-xs font-bold" onClick={onPostpone}>
              Postpone
            </button>
            <button type="button" className="text-xs font-bold text-[color:var(--teal)]" onClick={onCoach}>
              Ask AI Coach
            </button>
            <button type="button" className="organic-action-link text-xs font-bold" onClick={() => setEdit(!edit)}>
              Edit
            </button>
          </div>

          {open ? (
            <div className="mt-3 space-y-2 border-t border-[color:var(--border-soft)] pt-3 text-sm theme-muted">
              <p>{action.description}</p>
              <p>
                <strong>Why:</strong> {action.reason || "It supports your selected direction."}
              </p>
              <p>
                <strong>Complete when:</strong> {action.success_criteria || "You record an outcome."}
              </p>
              <textarea
                value={note}
                onChange={(event) => setNote(event.target.value)}
                aria-label="Completion note"
                placeholder="Optional outcome or learning"
                className="organic-input rounded-lg p-2"
              />
              <button type="button" className="text-xs font-bold text-[color:var(--color-accent-success)]" onClick={() => onComplete(note)}>
                Mark complete
              </button>
              <button
                type="button"
                className="ml-3 text-xs font-bold text-[color:var(--color-accent-action-muted)]"
                onClick={() => onSkip(prompt("Why are you skipping it? (not relevant, too difficult, no time...)") || "other")}
              >
                Skip
              </button>
              <button type="button" className="ml-3 text-xs text-red-600" onClick={onRemove}>
                Remove
              </button>
            </div>
          ) : null}

          {edit ? (
            <div className="mt-3 flex gap-2">
              <input value={source} onChange={(event) => setSource(event.target.value)} className="organic-input min-w-0 flex-1 rounded-lg p-2 text-sm" />
              <button
                type="button"
                className="organic-action-link text-sm font-bold"
                onClick={() => {
                  onUpdate({ title: source });
                  setEdit(false);
                }}
              >
                Save
              </button>
            </div>
          ) : null}
        </div>
      </div>
    </article>
  );
}
