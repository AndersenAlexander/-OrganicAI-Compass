import { Outlet } from "react-router-dom";
import { FloatingVoiceChat } from "../coach/FloatingVoiceChat";
import { Footer } from "./Footer";
import { GlobalHeader } from "./GlobalHeader";
import { SharedOrganicBackground } from "./SharedOrganicBackground";
import { DemoModeBanner } from "./DemoModeBanner";

export function WorkspaceLayout() {
  return (
    <div className="organic-gradient-bg relative min-h-screen overflow-x-clip">
      <SharedOrganicBackground />
      <GlobalHeader />
      <main id="main-content" className="app-layout-main relative mx-auto max-w-[1460px] px-4 pb-8 sm:px-6 lg:px-8">
        <DemoModeBanner />
        <Outlet />
      </main>
      <Footer />
      <FloatingVoiceChat />
    </div>
  );
}
