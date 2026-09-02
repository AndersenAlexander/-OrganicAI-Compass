import { Star } from "lucide-react";

export function TrustChips() {
  return (
    <div className="landing-hero-trust-row">
      <div className="landing-trust-explorers">
        <div className="landing-trust-avatars">
          {["#d9c0ad", "#6d8575", "#d6dce7", "#b7d8cf", "#f3d0a5"].map((color) => (
            <span key={color} style={{ backgroundColor: color }} />
          ))}
        </div>
        <span>Trusted by early explorers and innovators worldwide</span>
      </div>
      <div className="landing-trust-divider" />
      <div className="landing-trust-rating">
        <div>{Array.from({ length: 5 }).map((_, index) => <Star key={index} size={17} fill="currentColor" />)}</div>
        <p><strong>4.9</strong> / 5 from 124 beta users</p>
      </div>
    </div>
  );
}
