import type { ReactNode } from "react";
export function PublicCTASection({ title, description, children }:{title:string;description?:string;children:ReactNode}) { return <section className="public-cta"><h2>{title}</h2>{description && <p>{description}</p>}<div className="public-actions">{children}</div></section>; }
