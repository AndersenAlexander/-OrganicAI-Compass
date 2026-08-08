import { ArrowRight, Globe2, Sprout, Users } from "lucide-react";
import { Link } from "react-router-dom";

export function QuoteStatsStrip() {
  return (
    <section id="quote" className="landing-page-container landing-quote-strip grid items-center gap-5 px-[22px] py-[14px] lg:grid-cols-[0.42fr_0.36fr_0.22fr]">
      <div className="flex items-center gap-4">
        <span className="grid h-12 w-12 shrink-0 place-items-center rounded-full bg-gradient-to-br from-[#ecfeff] to-[#84cc16]/20 text-[color:var(--teal)] shadow-glow">
          <Sprout size={24} />
        </span>
        <p className="landing-quote-text theme-text">
          The future is not about humans or AI.<br className="hidden sm:block" />
          It is about humans and AI, <span className="text-[color:var(--teal)]">together.</span>
        </p>
      </div>
      <div className="grid grid-cols-3 gap-2">
        <div className="organic-chip h-16 justify-center rounded-2xl px-3 py-2"><Users size={17} /> <span><b>124+</b><br /><span className="text-[11px] theme-muted">Early Explorers</span></span></div>
        <div className="organic-chip h-16 justify-center rounded-2xl px-3 py-2"><Globe2 size={17} /> <span><b>18</b><br /><span className="text-[11px] theme-muted">Countries</span></span></div>
        <div className="organic-chip h-16 justify-center rounded-2xl px-3 py-2"><Sprout size={17} /> <span><b>1 Goal</b><br /><span className="text-[11px] theme-muted">Meaningful future</span></span></div>
      </div>
      <Link to="/register" className="organic-button h-11 w-[170px] justify-self-end whitespace-nowrap px-4">Join the Movement <ArrowRight size={17} /></Link>
    </section>
  );
}
