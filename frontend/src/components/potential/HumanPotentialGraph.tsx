import { useMemo, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { X } from "lucide-react";
import { mockPotentialGraph } from "../../data/mockPotentialGraph";
import { fadeUp } from "../../lib/animations";
import { PotentialConnection } from "./PotentialConnection";
import { PotentialNode } from "./PotentialNode";

export function HumanPotentialGraph() {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const selectedNode = mockPotentialGraph.find((node) => node.id === selectedId);
  const positions = useMemo(
    () =>
      mockPotentialGraph.map((node, index) => {
        const angle = (Math.PI * 2 * index) / mockPotentialGraph.length - Math.PI / 2;
        return { ...node, x: Math.cos(angle) * 185, y: Math.sin(angle) * 185 };
      }),
    []
  );

  return (
    <motion.section variants={fadeUp} initial="hidden" animate="visible" className="space-y-5">
      <div>
        <h2 className="font-display text-2xl font-bold text-navy">Your Human Potential Map</h2>
        <p className="mt-3 max-w-3xl text-slate-600">
          Your Human Potential Graph is a living map of what you notice, value, fear, create, and contribute.
        </p>
      </div>

      <div className="relative overflow-hidden rounded-[2rem] border border-white/70 bg-white/55 p-4 shadow-organic">
        <div className="relative mx-auto h-[520px] max-w-[620px]">
          <svg className="absolute inset-0 h-full w-full" viewBox="0 0 500 500" aria-hidden="true">
            {positions.map((node) => (
              <PotentialConnection key={node.id} x={node.x} y={node.y} />
            ))}
          </svg>
          <div className="absolute left-1/2 top-1/2 grid h-28 w-28 -translate-x-1/2 -translate-y-1/2 place-items-center rounded-full bg-deepNavy text-center text-sm font-black text-white shadow-glow">
            You
          </div>
          {positions.map((node) => (
            <PotentialNode key={node.id} {...node} onSelect={() => setSelectedId(node.id)} />
          ))}
        </div>
      </div>

      <AnimatePresence>
        {selectedNode ? (
          <motion.aside
            initial={{ opacity: 0, x: 18 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 18 }}
            className="rounded-2xl border border-white/80 bg-white/85 p-5 shadow-sm"
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-sm font-semibold uppercase tracking-[0.18em] text-teal">Selected node</p>
                <h3 className="mt-2 font-display text-xl font-bold text-navy">{selectedNode.label}</h3>
                <p className="mt-3 leading-7 text-slate-600">{selectedNode.detail}</p>
              </div>
              <button type="button" onClick={() => setSelectedId(null)} className="grid h-9 w-9 place-items-center rounded-full bg-white text-slate-500 ring-1 ring-slate-200">
                <X size={17} />
              </button>
            </div>
          </motion.aside>
        ) : null}
      </AnimatePresence>
    </motion.section>
  );
}
