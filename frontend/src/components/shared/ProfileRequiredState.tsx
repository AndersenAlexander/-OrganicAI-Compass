import { Link } from "react-router-dom";

export function ProfileRequiredState({
  title = "Create your profile to continue.",
  message = "This workspace area needs an owned profile. Start Natural Discovery to create or select your profile.",
}: {
  title?: string;
  message?: string;
}) {
  return (
    <section className="organic-section" role="status" aria-live="polite">
      <p className="organic-badge">Profile required</p>
      <h1 className="mt-4 font-display text-4xl font-semibold theme-text">{title}</h1>
      <p className="mt-4 max-w-2xl text-lg leading-8 theme-muted">{message}</p>
      <Link className="organic-button mt-6" to="/diagnostic">
        Start Natural Discovery
      </Link>
    </section>
  );
}
