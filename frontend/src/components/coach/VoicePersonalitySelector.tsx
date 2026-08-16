const personalities = ["Calm Guide", "Creative Mentor", "Practical Coach", "Reflective Companion", "Energetic Builder"];

export function VoicePersonalitySelector({ value, onChange }: { value: string; onChange: (value: string) => void }) {
  return (
    <label className="block">
      <span className="text-xs font-semibold uppercase tracking-[0.16em] text-teal">Voice personality</span>
      <select value={value} onChange={(event) => onChange(event.target.value)} className="mt-2 w-full rounded-2xl border border-slate-200 bg-white p-3 text-sm">
        {personalities.map((item) => <option key={item}>{item}</option>)}
      </select>
    </label>
  );
}
