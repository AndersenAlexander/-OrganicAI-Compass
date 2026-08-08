import { Compass, Linkedin, Mail, Send, Twitter, Youtube } from "lucide-react";
import { Link } from "react-router-dom";

export function PublicFooter() {
  return (
    <footer className="public-footer">
      <div className="footer-brand">
        <Link to="/" className="footer-logo">
          <Compass size={24} />
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
          <Link to="/contact" aria-label="Contact">
            <Mail size={15} />
          </Link>
        </div>
      </div>
      <div>
        <span>Platform</span>
        <Link to="/how-it-works">How It Works</Link>
        <Link to="/principles">Principles</Link>
        <Link to="/project-roadmap">Roadmap</Link>
        <Link to="/research">Research</Link>
      </div>
      <div>
        <span>Resources</span>
        <Link to="/blog">Blog</Link>
        <Link to="/knowledge-base">Knowledge Base</Link>
        <Link to="/learning-paths">Guides & Tools</Link>
        <Link to="/faq">FAQ</Link>
      </div>
      <div>
        <span>Company</span>
        <Link to="/about">About</Link>
        <Link to="/privacy">Privacy</Link>
        <Link to="/terms">Terms of Use</Link>
        <Link to="/contact">Contact</Link>
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
