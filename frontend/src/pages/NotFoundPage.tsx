import { Link } from "react-router-dom";

export function NotFoundPage() {
  return <div className="organic-section mx-auto max-w-3xl text-center"><p className="organic-badge">404</p><h1 className="mt-4 font-display text-4xl font-bold theme-text">Page not found</h1><p className="mt-3 theme-muted">The requested OrganicAI Compass page does not exist.</p><Link className="organic-button mt-6" to="/">Return home</Link></div>;
}
