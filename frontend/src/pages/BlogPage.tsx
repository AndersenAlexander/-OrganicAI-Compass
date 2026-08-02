import { Link } from "react-router-dom";

export function BlogPage() {
  return <div className="organic-section mx-auto max-w-3xl text-center"><p className="organic-badge">Coming Soon</p><h1 className="mt-4 font-display text-4xl font-bold theme-text">OrganicAI Journal</h1><p className="mt-4 theme-muted">Future articles will explore responsible AI, human creativity, and meaningful collaboration.</p><Link className="organic-button-secondary mt-6" to="/">Return home</Link></div>;
}
