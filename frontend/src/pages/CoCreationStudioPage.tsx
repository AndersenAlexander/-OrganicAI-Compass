import { VisualCoCreationStudio } from "../components/studio/VisualCoCreationStudio";

export function CoCreationStudioPage() {
  return (
    <div className="space-y-8">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-teal">Studio</p>
        <h1 className="mt-3 font-display text-4xl font-bold text-navy">Visual Co-Creation Studio</h1>
      </div>
      <VisualCoCreationStudio />
    </div>
  );
}
