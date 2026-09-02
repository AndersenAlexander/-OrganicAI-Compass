import { AudioWaveform, Map, Mic, Sparkles, UserRound } from "lucide-react";
import { motion } from "motion/react";
import { fadeUp, staggerContainer } from "../../lib/animations";
import { Link } from "react-router-dom";
import { useAppActions } from "../../hooks/useAppActions";

const steps = [
  { title: "Onboarding", description: "Welcome & set your intention", icon: UserRound, tone: "text-emerald-600 bg-emerald-50 dark:bg-emerald-400/10" },
  { title: "Diagnostic", description: "Voice conversation + deep listening", icon: AudioWaveform, tone: "text-sky-500 bg-sky-50 dark:bg-sky-400/10" },
  { title: "Insights", description: "AI generates personal insights", icon: Sparkles, tone: "text-violet-500 bg-violet-50 dark:bg-violet-400/10" },
  { title: "Roadmap", description: "Personalized steps for your growth", icon: Map, tone: "text-green-600 bg-green-50 dark:bg-green-400/10" }
];

export function MVPFlow() {
  const { activeProfileId, openCoach } = useAppActions();
  return (
    <section id="flow" className="landing-detail-card landing-mvp-card scroll-mt-28">
      <div className="flex items-center justify-between gap-4">
        <h2 className="font-serif text-[19px] font-semibold theme-text">MVP Flow</h2>
        <Link to="/how-it-works" className="text-xs theme-muted hover:text-[color:var(--color-accent-action-muted)]">Explore the journey</Link>
      </div>

      <motion.div variants={staggerContainer} initial="hidden" whileInView="visible" viewport={{ once: true, amount: 0.2 }} className="landing-mvp-flow relative grid grid-cols-4 gap-3">
        {steps.map((step, index) => {
          const Icon = step.icon;
          return (
            <motion.article key={step.title} variants={fadeUp} className="relative z-10 text-center">
              <div className={`mx-auto grid h-[52px] w-[52px] place-items-center rounded-full border border-[color:var(--border-soft)] shadow-[0_10px_26px_rgba(15,23,42,0.08)] ${step.tone}`}>
                <Icon size={20} />
              </div>
              <span className="mt-3 block text-[11px] font-black text-[color:var(--teal)]">{index + 1}. {step.title}</span>
              <p className="mx-auto mt-1 max-w-[8rem] text-[10px] leading-[1.35] theme-muted">{step.description}</p>
            </motion.article>
          );
        })}
      </motion.div>
      <button type="button" aria-label="Open OrganicAI Coach" onClick={() => openCoach()} className="mt-5 flex h-[54px] w-full items-center justify-between gap-4 rounded-[1.15rem] border border-[color:var(--border-soft)] bg-white/35 px-4 text-left text-sm theme-muted transition hover:border-[color:var(--color-accent-action-border)] focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[color:var(--color-accent-action-soft)] dark:bg-white/5">
        <div className="flex items-center gap-3">
          <Mic size={21} className="text-[color:var(--teal)]" />
          <span>
            <span className="block text-sm font-bold theme-text">Talk to OrganicAI Compass</span>
            <span className="text-[11px]">Your voice is the most natural way to begin.</span>
          </span>
        </div>
        <span className="hidden text-sm text-[color:var(--teal)] sm:block">|||||..||||...</span>
      </button>
    </section>
  );
}
