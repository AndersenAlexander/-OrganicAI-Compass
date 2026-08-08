import { DiagnosticWizard } from "../components/diagnostic/DiagnosticWizard";
import { EmergingProfileSidebar } from "../components/diagnostic/EmergingProfileSidebar";

export function DiagnosticPage() {
  return (
    <div className="organic-page">
      <div className="organic-section">
        <p className="organic-badge">Human Diagnostic</p>
        <h1 className="mt-4 font-display text-4xl font-bold theme-text sm:text-5xl">Discover the signal beneath your talents, fears, and future choices.</h1>
        <p className="mt-4 max-w-3xl text-lg leading-8 theme-muted">
          A 5-step journey to discover what drives you, what holds you back, and how you can grow with AI as your partner.
        </p>
      </div>
      <div className="grid gap-6 xl:grid-cols-[1fr_22rem]">
        <DiagnosticWizard />
        <EmergingProfileSidebar />
      </div>
    </div>
  );
}
