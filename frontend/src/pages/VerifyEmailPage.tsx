import { FormEvent, useLayoutEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { verifyEmail } from "../api/authApi";
import { captureTokenAndCleanSearch } from "../lib/urlTokenCleanup";

export function VerifyEmailPage() {
  const [, setParams] = useSearchParams();
  const captured = useRef(captureTokenAndCleanSearch(window.location.search));
  const [token, setToken] = useState(captured.current.token);
  const [verified, setVerified] = useState(false);
  const hasUrlToken = Boolean(captured.current.token);

  useLayoutEffect(() => {
    if (hasUrlToken) setParams(new URLSearchParams(captured.current.cleanedSearch), { replace: true });
  }, [hasUrlToken, setParams]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    await verifyEmail(token);
    setVerified(true);
  }

  return (
    <section className="mx-auto grid min-h-[70vh] max-w-md place-items-center px-6 py-16 text-slate-100">
      <form onSubmit={submit} className="grid w-full gap-4 rounded-2xl border border-white/10 bg-slate-950/70 p-6">
        <h1 className="text-2xl font-semibold">Verify Email</h1>
        {!hasUrlToken ? (
          <label className="grid gap-2 text-sm font-semibold">
            Verification token
            <input className="rounded-lg border border-white/15 bg-white/10 px-3 py-2" value={token} onChange={(event) => setToken(event.target.value)} required />
          </label>
        ) : null}
        <button className="rounded-lg bg-teal-300 px-4 py-2 font-semibold text-slate-950" type="submit">Verify Email</button>
        {verified ? <p className="text-sm text-teal-100">Email verification completed.</p> : null}
        <Link className="text-sm text-teal-100" to="/settings">Back to settings</Link>
      </form>
    </section>
  );
}
