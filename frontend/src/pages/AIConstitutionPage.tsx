import { PersonalAIConstitution } from "../components/constitution/PersonalAIConstitution";

export function AIConstitutionPage() {
  return (
    <div className="space-y-8">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-teal">Charter</p>
        <h1 className="mt-3 font-display text-4xl font-bold text-navy">My Human-AI Collaboration Charter</h1>
      </div>
      <PersonalAIConstitution />
    </div>
  );
}
