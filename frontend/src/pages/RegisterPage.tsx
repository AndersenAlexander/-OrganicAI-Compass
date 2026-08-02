import { FormEvent, useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { UserPlus } from "lucide-react";
import { Button } from "../components/shared/Button";
import { Card } from "../components/shared/Card";
import { ErrorState } from "../components/shared/ErrorState";
import { useAuth } from "../context/AuthContext";

export function RegisterPage() {
  const { register, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (isAuthenticated) return <Navigate to="/my-journey" replace />;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    setIsSubmitting(true);
    try {
      await register({ name, email, password });
      navigate("/my-journey");
    } catch {
      setError("Account creation failed. The email may already be used or the password is too short.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-xl py-10">
      <Card className="space-y-6">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-teal">Create your account</p>
          <h1 className="mt-3 font-display text-4xl font-bold text-navy">Start your saved journey</h1>
          <p className="mt-3 text-sm leading-6 text-slate-600">
            Save diagnostics, conversations, roadmaps, and human-AI collaboration progress in one place.
          </p>
        </div>
        {error ? <ErrorState message={error} /> : null}
        <form onSubmit={handleSubmit} className="space-y-4">
          <label className="block">
            <span className="text-sm font-semibold text-slate-700">Name</span>
            <input
              required
              value={name}
              onChange={(event) => setName(event.target.value)}
              className="mt-2 w-full rounded-2xl border border-slate-200 bg-white/90 p-4 text-sm outline-none ring-teal/20 focus:ring-4"
            />
          </label>
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
          <label className="block">
            <span className="text-sm font-semibold text-slate-700">Confirm password</span>
            <input
              type="password"
              required
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
              className="mt-2 w-full rounded-2xl border border-slate-200 bg-white/90 p-4 text-sm outline-none ring-teal/20 focus:ring-4"
            />
          </label>
          <Button type="submit" disabled={isSubmitting}>
            <UserPlus size={18} /> {isSubmitting ? "Creating account..." : "Create account"}
          </Button>
        </form>
        <p className="text-sm text-slate-600">
          Already have an account?{" "}
          <Link to="/login" className="font-semibold text-teal">
            Log in
          </Link>
        </p>
      </Card>
    </div>
  );
}
