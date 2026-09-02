import type { ReactNode } from "react";
export function PublicGlassCard({ children, className="" }:{children:ReactNode;className?:string}) { return <article className={`public-glass-card ${className}`}>{children}</article>; }
