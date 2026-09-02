import { Link } from "react-router-dom";
export function PageBreadcrumb({ current }:{current:string}) { return <nav aria-label="Breadcrumb" className="public-breadcrumb"><Link to="/">Home</Link><span aria-hidden="true">/</span><span>{current}</span></nav>; }
