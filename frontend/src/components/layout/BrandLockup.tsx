import { Link } from "react-router-dom";
import { LivingCompassLogoMark } from "../landing/LivingCompass";

type BrandLockupProps = {
  className?: string;
  textClassName?: string;
};

export function BrandLockup({ className = "", textClassName = "" }: BrandLockupProps) {
  return (
    <Link to="/" className={`group flex w-[230px] shrink-0 items-center gap-3 ${className}`}>
      <span className="brand-compass-anchor" data-living-compass-anchor="header">
        <LivingCompassLogoMark />
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
