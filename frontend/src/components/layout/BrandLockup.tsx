import { Compass, Leaf, Network } from "lucide-react";
import { Link } from "react-router-dom";

type BrandLockupProps = {
  className?: string;
  textClassName?: string;
};

export function BrandLockup({ className = "", textClassName = "" }: BrandLockupProps) {
  return (
    <Link to="/" className={`group flex w-[230px] shrink-0 items-center gap-3 ${className}`}>
      <span className="relative grid h-12 w-12 shrink-0 place-items-center rounded-full bg-white/8 text-[#99f6e4] shadow-[0_0_34px_rgba(45,212,191,0.36)] ring-1 ring-white/15">
        <Compass size={21} />
        <Leaf size={13} className="absolute -right-1 -top-1 rounded-full bg-white text-[#65a30d]" />
        <Network size={12} className="absolute -bottom-1 -left-1 rounded-full bg-white text-[#0f766e]" />
      </span>
      <span className={`font-serif text-2xl font-semibold leading-none tracking-tight text-white ${textClassName}`}>
        OrganicAI
        <span className="mt-1 block font-sans text-[0.68rem] font-bold tracking-[0.42em] text-[#99f6e4]">
          COMPASS
        </span>
      </span>
    </Link>
  );
}
