import { useState } from "react";
import { Button } from "../shared/Button";

const questions = [
  "How do I want to use AI?",
  "What should I never fully delegate to AI?",
  "What values do I want to protect?",
  "How will I verify AI outputs?",
  "How will I keep my creativity alive?",
  "How will I use AI for good, not only for efficiency?"
];

export function ConstitutionWizard() {
  const [step, setStep] = useState(0);
  return (
    <div className="rounded-2xl border border-white/80 bg-white/75 p-5">
      <p className="text-sm font-semibold text-teal">Question {step + 1} of {questions.length}</p>
      <p className="mt-3 font-display text-xl font-bold text-navy">{questions[step]}</p>
      <textarea className="mt-4 w-full rounded-2xl border border-slate-200 bg-white p-4 text-sm" rows={3} />
      <Button type="button" className="mt-4" onClick={() => setStep((current) => Math.min(current + 1, questions.length - 1))}>Next</Button>
    </div>
  );
}
