import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import { forgotPassword } from "../api/authApi";

export function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    await forgotPassword(email);
    setSent(true);
  }

  return (
    <section className="mx-auto grid min-h-[70vh] max-w-md place-items-center px-6 py-16 text-slate-100">
      <form onSubmit={submit} className="grid w-full gap-4 rounded-2xl border border-white/10 bg-slate-950/70 p-6">
        <h1 className="text-2xl font-semibold">Forgot Password</h1>
        <label className="grid gap-2 text-sm font-semibold">
          Email
          <input className="rounded-lg border border-white/15 bg-white/10 px-3 py-2" type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
        </label>
        <button className="rounded-lg bg-teal-300 px-4 py-2 font-semibold text-slate-950" type="submit">Send Reset Link</button>
        {sent ? <p className="text-sm text-teal-100">If an account exists, password reset instructions have been sent.</p> : null}
        <Link className="text-sm text-teal-100" to="/login">Back to login</Link>
      </form>
    </section>
  );
}
