import { useState } from "react";
import { Button } from "../shared/Button";

export function CollaborationStyleQuiz({ onSelect }: { onSelect: (title: string) => void }) {
  const [answer, setAnswer] = useState("I want help seeing my own thinking more clearly.");
  const options = [
    "I want help seeing my own thinking more clearly.",
    "I want to build ideas together.",
    "I want faster research and synthesis.",
    "I want structured guidance.",
    "I want help building practical outputs.",
    "I want my assumptions challenged."
  ];
  const map: Record<string, string> = {
    [options[0]]: "AI as Mirror",
    [options[1]]: "AI as Co-Creator",
    [options[2]]: "AI as Research Assistant",
    [options[3]]: "AI as Mentor",
    [options[4]]: "AI as Builder Assistant",
    [options[5]]: "AI as Ethical Challenger"
  };

  return (
    <div className="rounded-2xl border border-white/80 bg-white/75 p-5">
      <label className="block">
        <span className="text-sm font-semibold text-slate-700">What do you want most from AI?</span>
        <select value={answer} onChange={(event) => setAnswer(event.target.value)} className="mt-2 w-full rounded-2xl border border-slate-200 bg-white p-3 text-sm">
          {options.map((option) => <option key={option}>{option}</option>)}
        </select>
      </label>
      <Button type="button" className="mt-4" onClick={() => onSelect(map[answer])}>Identify style</Button>
    </div>
  );
}
