import { useEffect } from "react";
import { useLocation } from "react-router-dom";
import { useReducedMotionPreference } from "../../hooks/useReducedMotionPreference";

export function ScrollToTop() {
  const { pathname } = useLocation();
  const reduced = useReducedMotionPreference();
  useEffect(() => { window.scrollTo({ top:0, behavior:reduced ? "auto" : "smooth" }); }, [pathname, reduced]);
  return null;
}
