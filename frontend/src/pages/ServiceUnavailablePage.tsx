export function ServiceUnavailablePage() {
  const timestamp = new Date().toISOString();
  const requestId = new URLSearchParams(window.location.search).get("requestId") || "unavailable";

  return (
    <main className="min-h-screen bg-[var(--color-bg)] px-6 py-16 text-[var(--color-text)]">
      <section className="mx-auto max-w-2xl">
        <p className="text-sm font-semibold uppercase tracking-[0.12em] text-[var(--color-accent)]">Service unavailable</p>
        <h1 className="mt-4 text-3xl font-semibold">OrganicAI Compass is temporarily unavailable. Please try again shortly.</h1>
        <dl className="mt-8 grid gap-3 text-sm">
          <div>
            <dt className="font-semibold">Request ID</dt>
            <dd className="break-all text-[var(--color-muted)]">{requestId}</dd>
          </div>
          <div>
            <dt className="font-semibold">Timestamp</dt>
            <dd className="text-[var(--color-muted)]">{timestamp}</dd>
          </div>
          <div>
            <dt className="font-semibold">Status code</dt>
            <dd className="text-[var(--color-muted)]">503</dd>
          </div>
        </dl>
      </section>
    </main>
  );
}
