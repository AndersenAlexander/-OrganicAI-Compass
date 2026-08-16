export function QuizCard({ question }: { question: string }) {
  return (
    <div className="rounded-2xl border border-white/80 bg-white/75 p-5">
      <p className="text-sm font-semibold text-teal">Reflection quiz</p>
      <p className="mt-3 text-sm leading-6 text-slate-600">{question}</p>
    </div>
  );
}
