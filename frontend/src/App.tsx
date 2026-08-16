import { Outlet } from "react-router-dom";
import { ScrollToTop } from "./components/layout/ScrollToTop";
import { ActionFeedback } from "./components/shared/ActionFeedback";
import { AppActionsProvider } from "./context/AppActionsContext";
import { CoachProvider } from "./context/CoachContext";
import { LiveVoiceProvider } from "./context/LiveVoiceContext";

export function App() {
  return (
    <AppActionsProvider>
      <ScrollToTop />

      <LiveVoiceProvider>
        <CoachProvider>
          <Outlet />
          <ActionFeedback />
        </CoachProvider>
      </LiveVoiceProvider>
    </AppActionsProvider>
  );
}
