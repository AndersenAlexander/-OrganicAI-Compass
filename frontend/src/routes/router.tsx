import { createBrowserRouter } from "react-router-dom";
import { App } from "../App";
import { LandingPage } from "../pages/LandingPage";
import { DiagnosticPage } from "../pages/DiagnosticPage";
import { ProfilePage } from "../pages/ProfilePage";
import { FearTransformerPage } from "../pages/FearTransformerPage";
import { CoachPage } from "../pages/CoachPage";
import { RoadmapPage } from "../pages/RoadmapPage";
import { ReportPage } from "../pages/ReportPage";
import { LoginPage } from "../pages/LoginPage";
import { RegisterPage } from "../pages/RegisterPage";
import { MyJourneyPage } from "../pages/MyJourneyPage";
import { ProtectedRoute } from "./ProtectedRoute";
import { FutureScenarioPage } from "../pages/FutureScenarioPage";
import { ProjectsPage } from "../pages/ProjectsPage";
import { GrowthTimelinePage } from "../pages/GrowthTimelinePage";
import { CommunityPage } from "../pages/CommunityPage";
import { LearningPathPage } from "../pages/LearningPathPage";
import { CoCreationStudioPage } from "../pages/CoCreationStudioPage";
import { AIConstitutionPage } from "../pages/AIConstitutionPage";
import { KnowledgeBasePage } from "../pages/KnowledgeBasePage";
import { NotFoundPage } from "../pages/NotFoundPage";
import { BlogPage } from "../pages/BlogPage";
import { RecommendationsPage } from "../pages/RecommendationsPage";
import { AboutPage } from "../pages/AboutPage";
import { HowItWorksPage } from "../pages/HowItWorksPage";
import { PrinciplesPage } from "../pages/PrinciplesPage";
import { DemoPage } from "../pages/DemoPage";

export const router = createBrowserRouter([
  {
    element: <App />,
    children: [
      { path: "/", element: <LandingPage /> },
      { path: "/about", element: <AboutPage /> },
      { path: "/how-it-works", element: <HowItWorksPage /> },
      { path: "/principles", element: <PrinciplesPage /> },
      { path: "/demo", element: <DemoPage /> },
      { path: "/diagnostic", element: <DiagnosticPage /> },
      { path: "/profile/:id", element: <ProfilePage /> },
      { path: "/fear-transformer/:profileId", element: <FearTransformerPage /> },
      { path: "/coach/:profileId", element: <CoachPage /> },
      { path: "/roadmap/:profileId", element: <RoadmapPage /> },
      { path: "/report/:profileId", element: <ReportPage /> },
      { path: "/login", element: <LoginPage /> },
      { path: "/register", element: <RegisterPage /> },
      { path: "/future-scenarios", element: <FutureScenarioPage /> },
      { path: "/projects", element: <ProjectsPage /> },
      { path: "/growth-timeline", element: <GrowthTimelinePage /> },
      { path: "/community", element: <CommunityPage /> },
      { path: "/learning-paths", element: <LearningPathPage /> },
      { path: "/co-creation-studio", element: <CoCreationStudioPage /> },
      { path: "/ai-constitution", element: <AIConstitutionPage /> },
      { path: "/knowledge-base", element: <KnowledgeBasePage /> },
      { path: "/blog", element: <BlogPage /> },
      { path: "/recommendations/:profileId", element: <RecommendationsPage /> },
      {
        element: <ProtectedRoute />,
        children: [{ path: "/my-journey", element: <MyJourneyPage /> }]
      },
      { path: "*", element: <NotFoundPage /> }
    ]
  }
]);
