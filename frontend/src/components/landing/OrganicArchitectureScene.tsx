import { motion } from "motion/react";

export function OrganicArchitectureScene() {
  return (
    <>
      <motion.div animate={{ y: [0, -6, 0] }} transition={{ duration: 10, repeat: Infinity, ease: "easeInOut" }} className="absolute left-[2%] top-[8%] h-[520px] w-[480px] rotate-[-12deg] rounded-[55%_45%_60%_40%] border-2 border-white/65" />
      <motion.div animate={{ y: [0, 7, 0] }} transition={{ duration: 12, repeat: Infinity, ease: "easeInOut" }} className="absolute right-[-4%] top-[5%] h-[560px] w-[520px] rotate-[10deg] rounded-full border-2 border-white/75" />
      <div className="absolute bottom-0 left-0 right-0 h-[180px] bg-[radial-gradient(circle_at_20%_20%,rgba(132,204,22,0.24),transparent_28%),radial-gradient(circle_at_80%_15%,rgba(94,234,212,0.18),transparent_26%),linear-gradient(180deg,rgba(255,255,255,0),rgba(236,253,245,0.88))]" />
      <div className="absolute bottom-16 left-[4%] h-28 w-56 rounded-[3rem] border border-white/50 bg-white/35 backdrop-blur-sm" />
      <div className="absolute bottom-20 left-[31%] h-24 w-64 rounded-[3rem] border border-white/50 bg-white/28 backdrop-blur-sm" />
      <div className="absolute bottom-12 right-[4%] h-36 w-64 rounded-[4rem] border border-white/50 bg-white/32 backdrop-blur-sm" />
      <svg className="absolute inset-0 h-full w-full opacity-40" viewBox="0 0 800 640" aria-hidden="true">
        <path d="M20 520 C122 462 212 460 298 500 C380 538 482 542 582 492 C650 458 724 454 788 474" fill="none" stroke="rgba(15,118,110,0.32)" strokeWidth="2" />
        <path d="M68 180 C174 118 280 100 382 126 C494 154 616 132 742 70" fill="none" stroke="rgba(255,255,255,0.8)" strokeWidth="2" />
      </svg>
      <div className="absolute bottom-20 left-[12%] h-20 w-12">
        <div className="absolute bottom-0 left-1/2 h-12 w-px -translate-x-1/2 bg-emerald-900/30" />
        <div className="absolute left-0 top-0 h-12 w-12 rounded-full bg-leaf/35 blur-[1px]" />
      </div>
      <div className="absolute bottom-24 right-[16%] h-24 w-16">
        <div className="absolute bottom-0 left-1/2 h-14 w-px -translate-x-1/2 bg-emerald-900/30" />
        <div className="absolute left-0 top-0 h-16 w-16 rounded-full bg-teal/20 blur-[1px]" />
      </div>
    </>
  );
}
