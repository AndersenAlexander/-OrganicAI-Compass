import { useContext } from "react";
import { AppActionsContext } from "../context/AppActionsContext";

export function useAppActions() {
  const context = useContext(AppActionsContext);
  if (!context) throw new Error("useAppActions must be used within AppActionsProvider");
  return context;
}
