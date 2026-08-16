export function AICollaborationStyleCard({ style }: { style: string }) {
  return (
    <article className="glass-card p-5">
      <h3 className="font-display text-xl font-bold text-navy">AI Collaboration Style</h3>
      <p className="mt-4 text-lg font-semibold text-teal">{style}</p>
      <p className="mt-3 text-sm leading-6 text-slate-600">You thrive with AI as a creative partner that amplifies ideas while keeping your judgment central.</p>
    </article>
  );
}
