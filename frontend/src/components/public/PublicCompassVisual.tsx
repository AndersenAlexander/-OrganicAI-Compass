import { lazy, Suspense } from "react";
import { useReducedMotionPreference } from "../../hooks/useReducedMotionPreference";
const Orb = lazy(() => import("../three/HumanAIOrb3D").then(module => ({ default:module.HumanAIOrb3D })));

export function PublicCompassVisual({ labels=[] }:{labels?:string[]}) {
  const reduced=useReducedMotionPreference();
  return <div className="public-compass-visual" aria-label="A calm compass visual showing human, AI, and purposeful collaboration">{!reduced && <Suspense fallback={<div className="public-orb-fallback" /> }><Orb /></Suspense>}{reduced && <div className="public-orb-fallback" />}{labels.map((label,index)=><span key={label} className={`public-orb-label label-${index}`}>{label}</span>)}</div>;
}
