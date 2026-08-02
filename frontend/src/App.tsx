import { Outlet } from "react-router-dom";
import { AppShell } from "./components/layout/AppShell";
import { AppActionsProvider } from "./context/AppActionsContext";
import { CoachProvider } from "./context/CoachContext";
import { ScrollToTop } from "./components/layout/ScrollToTop";

export function App() {
  return (
    <AppActionsProvider>
      <ScrollToTop /><CoachProvider><AppShell>
          <Outlet />
        </AppShell></CoachProvider>
    </AppActionsProvider>
  );
}
