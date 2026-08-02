import { createContext, type ReactNode, useCallback, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useTheme } from "../hooks/useTheme";

const PROFILE_KEY = "organicai_active_profile_id";

export type VoiceCommandResult = { recognized: boolean; label?: string; message?: string; suggestion?: string };

type AppActionsValue = {
  activeProfileId: string;
  setActiveProfileId: (id: string) => void;
  isCoachOpen: boolean;
  coachPrompt: string | null;
  clearCoachPrompt: () => void;
  openCoach: (prompt?: string) => void;
  closeCoach: () => void;
  navigateToDiagnostic: () => void;
  navigateToProfile: (profileId?: string) => void;
  navigateToRoadmap: (profileId?: string) => void;
  navigateToFearTransformer: (profileId?: string) => void;
  navigateToKnowledgeBase: () => void;
  navigateToReport: (profileId?: string) => void;
  scrollToSection: (sectionId: string) => void;
  executeVoiceCommand: (command: string) => VoiceCommandResult;
};

export const AppActionsContext = createContext<AppActionsValue | undefined>(undefined);

function normalizeCommand(command: string) {
  return command.toLowerCase().trim().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-z0-9\s]/g, "").replace(/\s+/g, " ");
}

export function AppActionsProvider({ children }: { children: ReactNode }) {
  const navigate = useNavigate();
  const location = useLocation();
  const { setTheme } = useTheme();
  const routeProfileId = location.pathname.match(/^\/(?:profile|roadmap|report|coach|fear-transformer)\/([^/]+)/)?.[1];
  const [storedProfileId, setStoredProfileId] = useState(() => localStorage.getItem(PROFILE_KEY) || "demo-profile");
  const [isCoachOpen, setCoachOpen] = useState(false);
  const [coachPrompt, setCoachPrompt] = useState<string | null>(null);
  const activeProfileId = routeProfileId || storedProfileId || "demo-profile";

  const setActiveProfileId = useCallback((id: string) => {
    localStorage.setItem(PROFILE_KEY, id);
    setStoredProfileId(id);
  }, []);

  const openCoach = useCallback((prompt?: string) => {
    if (prompt) setCoachPrompt(prompt);
    setCoachOpen(true);
  }, []);

  const closeCoach = useCallback(() => setCoachOpen(false), []);
  const profilePath = useCallback((base: string, id?: string) => navigate(`/${base}/${id || activeProfileId}`), [activeProfileId, navigate]);

  const scrollToSection = useCallback((sectionId: string) => {
    const cleanId = sectionId.replace(/^#/, "");
    if (location.pathname === "/") {
      if (cleanId === "top") window.scrollTo({ top: 0, behavior: "smooth" });
      else document.getElementById(cleanId)?.scrollIntoView({ behavior: "smooth", block: "start" });
    } else {
      navigate(cleanId === "top" ? "/" : `/?section=${encodeURIComponent(cleanId)}`);
    }
  }, [location.pathname, navigate]);

  const executeVoiceCommand = useCallback((rawCommand: string): VoiceCommandResult => {
    const command = normalizeCommand(rawCommand);
    const recognized = (label: string, action: () => void, message: string) => {
      action();
      return { recognized: true, label, message };
    };
    if (["open home", "go home", "deschide acasa"].includes(command)) return recognized("Open Home", () => navigate("/"), "Opening home.");
    if (["open diagnostic", "start diagnostic", "deschide diagnosticul", "porneste diagnosticul"].includes(command)) return recognized("Open Diagnostic", () => navigate("/diagnostic"), "Opening the diagnostic.");
    if (["show roadmap", "open roadmap", "arata mi roadmap ul", "deschide roadmap ul"].includes(command)) return recognized("Show Roadmap", () => profilePath("roadmap"), "Opening your roadmap.");
    if (["open human potential map", "show human potential map", "open profile", "deschide harta potentialului", "arata harta potentialului"].includes(command)) return recognized("Open Human Potential Map", () => profilePath("profile"), "Opening your Human Potential Map.");
    if (["open fear transformer", "transform a fear", "transforma o frica"].includes(command)) return recognized("Open Fear Transformer", () => profilePath("fear-transformer"), "Opening Fear-to-Creativity.");
    if (["open knowledge base", "show knowledge base", "deschide baza de cunostinte"].includes(command)) return recognized("Open Knowledge Base", () => navigate("/knowledge-base"), "Opening the Knowledge Base.");
    if (["open learning paths", "deschide traseele de invatare"].includes(command)) return recognized("Open Learning Paths", () => navigate("/learning-paths"), "Opening learning paths.");
    if (["generate report", "open report", "show report", "deschide raportul"].includes(command)) return recognized("Generate Report", () => profilePath("report"), "Opening your report.");
    if (["switch to dark mode", "dark mode", "schimba in modul intunecat"].includes(command)) return recognized("Switch to Dark Mode", () => setTheme("dark"), "Dark mode enabled.");
    if (["switch to light mode", "light mode", "schimba in modul luminos"].includes(command)) return recognized("Switch to Light Mode", () => setTheme("light"), "Light mode enabled.");
    if (["open ai coach", "open coach"].includes(command)) return recognized("Open AI Coach", () => openCoach(), "Opening OrganicAI Coach.");
    if (command.includes("roadmap")) return { recognized: false, suggestion: "Did you mean Open Roadmap?" };
    return { recognized: false };
  }, [navigate, openCoach, profilePath, setTheme]);

  const value = useMemo<AppActionsValue>(() => ({
    activeProfileId, setActiveProfileId, isCoachOpen, coachPrompt, clearCoachPrompt: () => setCoachPrompt(null), openCoach, closeCoach,
    navigateToDiagnostic: () => navigate("/diagnostic"),
    navigateToProfile: (id) => profilePath("profile", id),
    navigateToRoadmap: (id) => profilePath("roadmap", id),
    navigateToFearTransformer: (id) => profilePath("fear-transformer", id),
    navigateToKnowledgeBase: () => navigate("/knowledge-base"),
    navigateToReport: (id) => profilePath("report", id),
    scrollToSection, executeVoiceCommand
  }), [activeProfileId, coachPrompt, closeCoach, executeVoiceCommand, isCoachOpen, navigate, openCoach, profilePath, scrollToSection, setActiveProfileId]);

  return <AppActionsContext.Provider value={value}>{children}</AppActionsContext.Provider>;
}
