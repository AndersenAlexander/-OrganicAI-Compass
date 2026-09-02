const modes = [
  "Explain simply",
  "Ask me reflective questions",
  "Help me structure my thoughts",
  "Help me create",
  "Challenge me ethically",
  "Build a small action plan"
];

export function ConversationModeSelector({ value, onChange }: { value: string; onChange: (value: string) => void }) {
  return (
    <label className="block">
      <span className="text-xs font-semibold uppercase tracking-[0.16em] text-teal">Conversation mode</span>
      <select value={value} onChange={(event) => onChange(event.target.value)} className="mt-2 w-full rounded-2xl border border-slate-200 bg-white p-3 text-sm">
        {modes.map((item) => <option key={item}>{item}</option>)}
      </select>
    </label>
  );
}
