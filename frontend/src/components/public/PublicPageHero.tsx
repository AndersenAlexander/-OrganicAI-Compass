import { motion } from "motion/react";
import type { ReactNode } from "react";

export function PublicPageHero({ badge, title, description, actions, visual }:{badge:string;title:ReactNode;description:string;actions:ReactNode;visual:ReactNode}) {
  return <section className="public-hero"><motion.div initial={{opacity:0,y:18}} animate={{opacity:1,y:0}} transition={{duration:.45}} className="public-hero-copy"><span className="public-badge">{badge}</span><h1>{title}</h1><p>{description}</p><div className="public-actions">{actions}</div></motion.div><motion.div initial={{opacity:0,scale:.96}} animate={{opacity:1,scale:1}} transition={{duration:.55}} className="public-hero-visual">{visual}</motion.div></section>;
}
