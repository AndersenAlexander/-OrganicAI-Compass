import { useState } from "react";
import { Button } from "../shared/Button";

export function ProjectBuilder() {
  const [domain, setDomain] = useState("AI Literacy");
  const [goal, setGoal] = useState("I want to help non-technical people understand AI.");
  return (
    <div className="rounded-2xl border border-white/80 bg-white/75 p-5">
      <div className="grid gap-4 md:grid-cols-2">
        <label className="block">
          <span className="text-sm font-semibold text-slate-700">Domain</span>
          <input value={domain} onChange={(event) => setDomain(event.target.value)} className="mt-2 w-full rounded-2xl border border-slate-200 bg-white p-3 text-sm" />
        </label>
        <label className="block">
          <span className="text-sm font-semibold text-slate-700">Goal</span>
          <input value={goal} onChange={(event) => setGoal(event.target.value)} className="mt-2 w-full rounded-2xl border border-slate-200 bg-white p-3 text-sm" />
        </label>
      </div>
      <Button type="button" className="mt-4">Generate project brief</Button>
    </div>
  );
}
