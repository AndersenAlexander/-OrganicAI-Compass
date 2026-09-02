import { MoodboardCard } from "./MoodboardCard";
import { StudioCanvas } from "./StudioCanvas";

export function VisualCoCreationStudio() {
  return (
    <section className="space-y-5">
      <div className="grid gap-4 md:grid-cols-3">
        {["Organic forms", "Leaf + circuit motifs", "Prompt suggestions"].map((item) => <MoodboardCard key={item} title={item} />)}
      </div>
      <StudioCanvas />
      <button type="button" onClick={() => window.print()} className="rounded-full bg-teal px-5 py-3 text-sm font-semibold text-white">Export / Print</button>
    </section>
  );
}
