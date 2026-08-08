import { Outlet } from "react-router-dom";
import { ScrollToTop } from "./components/layout/ScrollToTop";
import { ActionFeedback } from "./components/shared/ActionFeedback";
import { AppActionsProvider } from "./context/AppActionsContext";
import { CoachProvider } from "./context/CoachContext";

export function App() {
  return (
    <AppActionsProvider>
      <ScrollToTop />

      <CoachProvider>
        <Outlet />
        <ActionFeedback />
      </CoachProvider>
    </AppActionsProvider>
  );
}
