import { motion } from "motion/react";

export function AIFigure() {
  return (
    <motion.div initial={{ opacity: 0, x: 18 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.8, delay: 0.28 }} className="absolute right-[16%] top-[21%] z-20 h-[370px] w-[200px]">
      <div className="absolute left-[45%] top-0 h-24 w-20 -translate-x-1/2 rounded-[2.75rem] bg-[linear-gradient(180deg,rgba(255,255,255,0.95),rgba(186,230,253,0.82))] shadow-[0_24px_80px_rgba(56,189,248,0.35)]" />
      <div className="absolute left-[45%] top-6 h-12 w-9 -translate-x-1/2 rounded-[2rem] border border-white/80 bg-white/65" />
      <div className="absolute left-[44%] top-[48px] h-3 w-3 rounded-full bg-cyan-500 shadow-glow" />
      <div className="absolute right-[46px] top-9 h-12 w-12 rounded-full border-4 border-sky-100 bg-cyan-300/80 shadow-glow" />
      <div className="absolute left-[45%] top-[84px] h-12 w-8 -translate-x-1/2 rounded-full bg-sky-100" />
      <div className="absolute bottom-0 left-[45%] h-[268px] w-[120px] -translate-x-1/2 rounded-t-[5rem] rounded-b-[2rem] border border-white/80 bg-[linear-gradient(180deg,rgba(255,255,255,0.92),rgba(186,230,253,0.72))] shadow-[0_30px_80px_rgba(56,189,248,0.3)]" />
      <div className="absolute left-[44%] top-[146px] h-28 w-px bg-cyan-300" />
      <div className="absolute left-[30%] top-[160px] h-20 w-px bg-cyan-200" />
      <div className="absolute left-[58%] top-[160px] h-20 w-px bg-cyan-200" />
      <div className="absolute left-[44%] top-[180px] h-3 w-3 rounded-full bg-cyan-400" />
      <div className="absolute bottom-[-8px] left-[35%] rounded-full bg-white/80 px-4 py-2 text-sm font-bold text-navy">AI</div>
    </motion.div>
  );
}
