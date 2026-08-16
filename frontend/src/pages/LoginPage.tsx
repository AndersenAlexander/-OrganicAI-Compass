import { FormEvent, useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { LogIn, Sparkles } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { Button } from "../components/shared/Button";
import { Card } from "../components/shared/Card";
import { ErrorState } from "../components/shared/ErrorState";

export function LoginPage() {
  const { login, loginDemo, isAuthenticated, isDemo } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDemoLoading, setDemoLoading] = useState(false);

  if (isAuthenticated) return <Navigate to={isDemo ? `/profile/${localStorage.getItem("organicai_active_profile_id") || "demo-profile"}` : "/my-journey"} replace />;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await login({ email, password });
      navigate("/my-journey");
    } catch {
      setError("Login failed. Check your email and password.");
    } finally {
      setIsSubmitting(false);
    }
  }
  async function handleDemo(){setError(null);setDemoLoading(true);try{const profileId=await loginDemo();navigate(`/profile/${profileId}`)}catch{setError("The demo account could not be prepared. Enable demo mode on the server and try again.")}finally{setDemoLoading(false)}}

  return (
    <div className="mx-auto max-w-xl py-10">
      <Card className="space-y-6">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-teal">Welcome back</p>
          <h1 className="mt-3 font-display text-4xl font-bold text-navy">Log in</h1>
          <p className="mt-3 text-sm leading-6 text-slate-600">
            Continue your OrganicAI Compass journey and keep your roadmap connected to your account.
          </p>
        </div>
        {error ? <ErrorState message={error} /> : null}
        <form onSubmit={handleSubmit} className="space-y-4">
          <label className="block">
            <span className="text-sm font-semibold text-slate-700">Email</span>
            <input
              type="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              className="mt-2 w-full rounded-2xl border border-slate-200 bg-white/90 p-4 text-sm outline-none ring-[color:var(--color-accent-action-soft)] focus:ring-4"
            />
          </label>
          <label className="block">
            <span className="text-sm font-semibold text-slate-700">Password</span>
            <input
              type="password"
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className="mt-2 w-full rounded-2xl border border-slate-200 bg-white/90 p-4 text-sm outline-none ring-[color:var(--color-accent-action-soft)] focus:ring-4"
            />
          </label>
          <Button type="submit" disabled={isSubmitting}>
            <LogIn size={18} /> {isSubmitting ? "Logging in..." : "Log in"}
          </Button>
        </form>
        <div className="flex items-center gap-3 text-xs font-bold uppercase tracking-[0.16em] text-[color:var(--oa-text-muted)]"><span className="h-px flex-1 bg-[color:var(--oa-border)]"/>or<span className="h-px flex-1 bg-[color:var(--oa-border)]"/></div>
        <section className="rounded-2xl border border-[color:var(--oa-border-strong)] bg-[color:var(--oa-surface-strong)] p-4 text-[color:var(--oa-text)]"><div className="flex items-center gap-2"><Sparkles size={18} className="text-[color:var(--oa-teal)]"/><h2 className="font-display text-2xl font-bold">Explore Demo</h2></div><p className="mt-2 text-sm text-[color:var(--oa-text-secondary)]">Explore the complete OrganicAI Compass experience using demonstration data. Changes can be reset at any time.</p><Button type="button" className="mt-4 min-h-11 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[color:var(--color-accent-action)]" disabled={isDemoLoading} onClick={()=>void handleDemo()}><Sparkles size={17}/>{isDemoLoading?"Preparing demo...":"Explore Demo"}</Button></section>
        <p className="text-sm text-slate-600">
          <Link to="/forgot-password" className="font-semibold organic-action-link">
            Forgot password?
          </Link>
          <span className="mx-2 text-slate-300">|</span>
          New here?{" "}
          <Link to="/register" className="font-semibold organic-action-link">
            Create account
          </Link>
        </p>
      </Card>
    </div>
  );
}
