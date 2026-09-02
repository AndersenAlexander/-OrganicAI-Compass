import { Compass, Linkedin, Send, Twitter, Youtube } from "lucide-react";
import { Link } from "react-router-dom";
import { useAppActions } from "../../hooks/useAppActions";

export function PublicFooter() {
  const { activeProfileId } = useAppActions();
  const coachPath = activeProfileId ? `/coach/${activeProfileId}` : "/diagnostic";

  return (
    <footer className="public-footer" data-testid="public-footer">
      <div className="footer-brand">
        <Link to="/" className="footer-logo">
          <span className="footer-logo__compass-anchor" data-living-compass-anchor="footer" aria-hidden="true">
            <Compass size={24} />
          </span>
          <strong>OrganicAI Compass</strong>
        </Link>
        <p>A human-centred compass for the age of AI.</p>
        <div className="footer-social" aria-label="Social links">
          <a href="https://www.linkedin.com" aria-label="LinkedIn">
            <Linkedin size={15} />
          </a>
          <a href="https://x.com" aria-label="X">
            <Twitter size={15} />
          </a>
          <a href="https://www.youtube.com" aria-label="YouTube">
            <Youtube size={15} />
          </a>
        </div>
      </div>
      <div>
        <span>Platform</span>
        <Link to="/how-it-works">How It Works</Link>
        <Link to="/careers">Careers</Link>
        <Link to="/dashboard">Workspace</Link>
        <Link to="/research">Research</Link>
      </div>
      <div>
        <span>Resources</span>
        <Link to="/blog">Blog / Insights</Link>
        <Link to="/principles">Principles</Link>
        <Link to="/about/recommendation-system-card">System Card</Link>
        <Link to="/project-roadmap">Project Roadmap</Link>
      </div>
      <div>
        <span>Support</span>
        <Link to={coachPath}>OrganicAI Coach</Link>
        <Link to="/knowledge-base">Knowledge Base</Link>
        <Link to="/privacy">Privacy Center</Link>
        <Link to="/about">About</Link>
      </div>
      <div className="footer-newsletter">
        <span>Stay in the loop</span>
        <p>Get updates on research, insights, and new features.</p>
        <label>
          <span className="sr-only">Email address</span>
          <input type="email" placeholder="Enter your email" disabled />
          <button type="button" disabled aria-label="Newsletter signup coming soon">
            <Send size={15} />
          </button>
        </label>
      </div>
      <small>OrganicAI Compass - Master's Dissertation Research Prototype</small>
    </footer>
  );
}
