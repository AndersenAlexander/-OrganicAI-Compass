import { motion } from "motion/react";

export function HumanFigure() {
  return (
    <motion.div initial={{ opacity: 0, x: -18 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.8, delay: 0.2 }} className="absolute left-[27%] top-[24%] z-20 h-[350px] w-[190px]">
      <div className="absolute left-[34%] top-0 h-20 w-20 rounded-full bg-[#6f604f]" />
      <div className="absolute left-[48%] top-3 h-[86px] w-[72px] rounded-[46%_54%_52%_48%] bg-[linear-gradient(180deg,#f5ead8,#e8d8c5)] shadow-[0_24px_60px_rgba(101,163,13,0.2)]" />
      <div className="absolute left-[73%] top-11 h-4 w-4 rounded-full bg-[#ead7c2]" />
      <div className="absolute left-[56%] top-[78px] h-12 w-7 rounded-full bg-[#e5d0bb]" />
      <div className="absolute bottom-0 left-[36%] h-[250px] w-[108px] rounded-t-[5rem] rounded-b-[2rem] bg-[linear-gradient(180deg,rgba(113,143,99,0.92),rgba(66,93,71,0.96))] shadow-[0_30px_80px_rgba(101,163,13,0.26)]" />
      <div className="absolute left-[24%] top-[120px] h-[138px] w-[120px] rounded-[55%] bg-white/18 blur-[1px]" />
      <div className="absolute bottom-[-8px] left-[39%] rounded-full bg-white/80 px-4 py-2 text-sm font-bold text-navy">Human</div>
    </motion.div>
  );
}
