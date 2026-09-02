import { mockConstitution } from "../../data/mockConstitution";
import { ConstitutionPrincipleCard } from "./ConstitutionPrincipleCard";
import { ConstitutionWizard } from "./ConstitutionWizard";

export function PersonalAIConstitution() {
  return (
    <section className="space-y-5">
      <ConstitutionWizard />
      <div className="grid gap-5 lg:grid-cols-2">
        <ConstitutionPrincipleCard title="My values" items={mockConstitution.values} />
        <ConstitutionPrincipleCard title="My boundaries" items={mockConstitution.boundaries} />
        <ConstitutionPrincipleCard title="My verification rules" items={mockConstitution.verificationRules} />
        <ConstitutionPrincipleCard title="My creative principles" items={mockConstitution.creativePrinciples} />
        <ConstitutionPrincipleCard title="My contribution promise" items={mockConstitution.contributionPromise} />
        <ConstitutionPrincipleCard title="My ethical cautions" items={mockConstitution.ethicalCautions} />
      </div>
      <button type="button" onClick={() => window.print()} className="rounded-full bg-teal px-5 py-3 text-sm font-semibold text-white">Export Charter</button>
    </section>
  );
}
