import type { ReactNode } from "react";
import { OrganicAtmosphere } from "../visual/OrganicAtmosphere";

export function PublicPageShell({ children }:{children:ReactNode}) { return <div className="public-page"><OrganicAtmosphere />{children}</div>; }
