import { FormEvent, useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { Copy, LogIn, Sparkles } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { Button } from "../components/shared/Button";
import { Card } from "../components/shared/Card";
import { ErrorState } from "../components/shared/ErrorState";

export function LoginPage() {
  const { login, loginDemo, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDemoLoading, setDemoLoading] = useState(false);
  const demoEnabled = import.meta.env.VITE_DEMO_MODE === "true";

  if (isAuthenticated) return <Navigate to="/my-journey" replace />;

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
  const copy=(value:string)=>void navigator.clipboard?.writeText(value);

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
              className="mt-2 w-full rounded-2xl border border-slate-200 bg-white/90 p-4 text-sm outline-none ring-teal/20 focus:ring-4"
            />
          </label>
          <label className="block">
            <span className="text-sm font-semibold text-slate-700">Password</span>
            <input
              type="password"
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className="mt-2 w-full rounded-2xl border border-slate-200 bg-white/90 p-4 text-sm outline-none ring-teal/20 focus:ring-4"
            />
          </label>
          <Button type="submit" disabled={isSubmitting}>
            <LogIn size={18} /> {isSubmitting ? "Logging in..." : "Log in"}
          </Button>
        </form>
        {demoEnabled ? <section className="rounded-2xl border border-teal/20 bg-teal/5 p-4"><div className="flex items-center gap-2"><Sparkles size={18} className="text-teal"/><h2 className="font-display text-2xl font-bold text-navy">Explore the Demo</h2></div><p className="mt-2 text-sm text-slate-600">Experience a completed diagnostic, Human Potential Map, AI Coach history, and personalized roadmap.</p><Button type="button" className="mt-4" disabled={isDemoLoading} onClick={()=>void handleDemo()}><Sparkles size={17}/>{isDemoLoading?"Preparing demo...":"Continue with Demo Account"}</Button><details className="mt-4 text-xs text-slate-600"><summary className="cursor-pointer font-semibold">Demo credentials</summary><div className="mt-2 grid gap-2"><span>Email: demo@organicai.local <button aria-label="Copy demo email" onClick={()=>copy("demo@organicai.local")}><Copy size={13}/></button></span><span>Password: OrganicAI-Demo-2026! <button aria-label="Copy demo password" onClick={()=>copy("OrganicAI-Demo-2026!")}><Copy size={13}/></button></span></div></details></section> : null}
        <p className="text-sm text-slate-600">
          New here?{" "}
          <Link to="/register" className="font-semibold text-teal">
            Create account
          </Link>
        </p>
      </Card>
    </div>
  );
}
