import { FormEvent, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowRight, MessageCircle, Route } from "lucide-react";
import { transformFear } from "../api/profileApi";
import { Button } from "../components/shared/Button";
import { Card } from "../components/shared/Card";
import { ErrorState } from "../components/shared/ErrorState";
import type { FearTransform } from "../types/profile";
import { FearToCreativityEngine } from "../components/fear/FearToCreativityEngine";

export function FearTransformerPage() {
  const { profileId } = useParams();
  const [fear, setFear] = useState("");
  const [result, setResult] = useState<FearTransform | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!profileId) return;
    setError(null);
    setIsLoading(true);

    try {
      const response = await transformFear(profileId, fear);
      setResult(response);
    } catch {
      setError("The fear transformation could not be generated. Check the backend API and try again.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="organic-page mx-auto max-w-6xl">
      <div className="organic-section">
        <p className="organic-badge">Fear-to-Creativity Engine</p>
        <h1 className="mt-4 font-display text-4xl font-bold theme-text sm:text-5xl">Transform uncertainty about AI into clarity, agency, and creative action.</h1>
        <p className="mt-4 max-w-3xl text-lg leading-8 theme-muted">
          Write one concrete concern about AI, automation, robots, or the future.
        </p>
      </div>

      {error ? <ErrorState message={error} /> : null}

      <div className="glass-card p-6">
        <form onSubmit={handleSubmit} className="space-y-4">
          <label className="block">
            <span className="text-sm font-semibold theme-text">What fear or uncertainty about AI would you like to transform?</span>
            <textarea
              required
              rows={5}
              value={fear}
              onChange={(event) => setFear(event.target.value)}
              className="organic-input mt-2"
            />
          </label>
          <Button type="submit" disabled={isLoading}>
            {isLoading ? "Transforming..." : "Transform fear"} <ArrowRight size={18} />
          </Button>
        </form>
      </div>

      {result ? (
        <>
          <FearToCreativityEngine result={result} />
          <div className="flex flex-wrap gap-3">
            <Link className="organic-button-secondary" to={`/coach/${profileId}`}>
              <MessageCircle size={18} /> Discuss with coach
            </Link>
            <Link className="organic-button" to={`/roadmap/${profileId}`}>
              <Route size={18} /> Build roadmap
            </Link>
          </div>
        </>
      ) : null}
    </div>
  );
}
