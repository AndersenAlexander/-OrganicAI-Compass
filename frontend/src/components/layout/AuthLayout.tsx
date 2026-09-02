import { Outlet } from "react-router-dom";
import { GlobalHeader } from "./GlobalHeader";
import { SharedOrganicBackground } from "./SharedOrganicBackground";

export function AuthLayout() {
  return (
    <div className="organic-gradient-bg relative min-h-screen overflow-x-clip">
      <SharedOrganicBackground />
      <GlobalHeader />
      <main id="main-content" className="app-layout-main relative mx-auto max-w-[960px] px-4 pb-8 sm:px-6 lg:px-8">
        <Outlet />
      </main>
      <footer className="relative mx-auto max-w-[960px] px-4 pb-8 text-center text-xs font-semibold text-slate-500 dark:text-slate-400 sm:px-6 lg:px-8">
        OrganicAI Compass · Master's Dissertation Research Prototype
      </footer>
    </div>
  );
}
