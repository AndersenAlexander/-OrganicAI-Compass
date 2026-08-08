import { AudioWaveform, Database, Download, Eye, LockKeyhole, RotateCcw, ShieldCheck, Trash2 } from "lucide-react";
import type { LucideIcon } from "lucide-react";

type PrivacyItem = [string, LucideIcon, string];

const processItems: PrivacyItem[] = [
  ["Diagnostic responses", ShieldCheck, "Available in MVP"],
  ["Conversation text", LockKeyhole, "Available in MVP"],
  ["Concerns and goals", Eye, "Available in MVP"],
  ["Known profile data", Database, "Available in MVP"],
  ["Ratings and progress", ShieldCheck, "Available in MVP"],
  ["Optional voice recordings", AudioWaveform, "Available in MVP"],
];

const controlItems: PrivacyItem[] = [
  ["Whether voice is used", AudioWaveform, "Available in MVP"],
  ["Whether information is stored", Database, "Available in MVP"],
  ["Ability to export data", Download, "Planned production control"],
  ["Ability to delete conversations", Trash2, "Planned production control"],
  ["Ability to redo the diagnostic", RotateCcw, "Available in MVP"],
  ["Ability to opt out", ShieldCheck, "Planned production control"],
];

export function PrivacyControlSection() {
  return (
    <section className="how-page-section privacy-control-section" aria-labelledby="privacy-title">
      <header className="how-section-heading">
        <p>PRIVACY AND CONTROL</p>
        <h2 id="privacy-title">Privacy and control stay visible</h2>
        <span>MVP capabilities and planned production controls are separated instead of presented as the same state.</span>
      </header>
      <div className="privacy-control-grid">
        <PrivacyPanel title="What OrganicAI may process" items={processItems} />
        <PrivacyPanel title="What the user controls" items={controlItems} />
      </div>
    </section>
  );
}

function PrivacyPanel({
  title,
  items,
}: {
  title: string;
  items: PrivacyItem[];
}) {
  return (
    <article className="privacy-panel">
      <h3>{title}</h3>
      <ul>
        {items.map(([label, Icon, status]) => (
          <li key={label}>
            <span className="privacy-icon">
              <Icon size={18} />
            </span>
            <span>{label}</span>
            <b className={status.includes("Planned") ? "planned" : "available"}>{status}</b>
          </li>
        ))}
      </ul>
    </article>
  );
}
