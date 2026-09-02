import { Brain, Compass, HandHeart, HeartHandshake, Leaf, ShieldCheck } from "lucide-react";
import { motion } from "motion/react";
import { fadeUp, staggerContainer } from "../../lib/animations";

const principles = [
  {
    title: "Native Talent Discovery",
    description: "Help people identify natural strengths, interests, and creative tendencies.",
    icon: Brain
  },
  {
    title: "Clarity and Repositioning",
    description: "Support users in understanding their place in an AI-driven world.",
    icon: Compass
  },
  {
    title: "Positive AI Perspectives",
    description: "Transform fear into realistic, constructive understanding.",
    icon: ShieldCheck
  },
  {
    title: "Organic Human-Machine Collaboration",
    description: "Frame AI as a co-creative partner, not a replacement.",
    icon: HeartHandshake
  },
  {
    title: "Projects for Humanity",
    description: "Encourage ideas that support education, community, nature, health, and society.",
    icon: HandHeart
  },
  {
    title: "Purpose and Interdependence",
    description: "Show how individual talents connect to larger human and planetary systems.",
    icon: Leaf
  }
];

export function OrganicPrinciples() {
  return (
    <section id="principles" className="space-y-8 scroll-mt-28">
      <div className="max-w-4xl">
        <span className="organic-badge">Six principles</span>
        <h2 className="mt-4 font-display text-3xl font-black text-deepNavy sm:text-4xl">
          The six principles of Organic Human-AI Interaction
        </h2>
      </div>

      <motion.div variants={staggerContainer} initial="hidden" whileInView="visible" viewport={{ once: true, amount: 0.15 }} className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
        {principles.map((principle, index) => {
          const Icon = principle.icon;
          return (
            <motion.article key={principle.title} variants={fadeUp} className="organic-card min-h-[16rem]">
              <div className="absolute -right-10 -top-12 h-32 w-32 rounded-full bg-softTeal/20 blur-2xl" />
              <div className="relative">
                <div className="flex items-start justify-between gap-4">
                  <div className="grid h-14 w-14 place-items-center rounded-2xl bg-teal text-white shadow-glow">
                    <Icon size={24} />
                  </div>
                  <span className="text-3xl font-black text-teal/20">0{index + 1}</span>
                </div>
                <h3 className="mt-6 font-display text-xl font-black text-deepNavy">{principle.title}</h3>
                <p className="mt-3 text-sm leading-6 text-slate-600">{principle.description}</p>
              </div>
            </motion.article>
          );
        })}
      </motion.div>
    </section>
  );
}
