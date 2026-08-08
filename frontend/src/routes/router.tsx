import { createBrowserRouter } from "react-router-dom";
import { lazy, Suspense } from "react";
import { App } from "../App";
import { AuthLayout } from "../components/layout/AuthLayout";
import { PublicLayout } from "../components/layout/PublicLayout";
import { WorkspaceLayout } from "../components/layout/WorkspaceLayout";
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
import { RecommendationsPage } from "../pages/RecommendationsPage";
import { AboutPage } from "../pages/AboutPage";
import { HowItWorksPage } from "../pages/HowItWorksPage";
import { PrinciplesPage } from "../pages/PrinciplesPage";
import { DemoPage } from "../pages/DemoPage";
import { ResearchPage } from "../pages/ResearchPage";
import { PublicRoadmapPage } from "../pages/PublicRoadmapPage";
import { AssessmentPage } from "../pages/AssessmentPage";
import { AssessmentResultsPage } from "../pages/AssessmentResultsPage";
import { CareerCompatibilityPage } from "../pages/CareerCompatibilityPage";
import { CareerComparePage } from "../pages/CareerComparePage";

const BlogPage = lazy(() => import("../pages/BlogPage").then((module) => ({ default: module.BlogPage })));
const BlogArticlePage = lazy(() => import("../pages/BlogArticlePage").then((module) => ({ default: module.BlogArticlePage })));
const LearningPage = lazy(() => import("../pages/LearningPage").then((module) => ({ default: module.LearningPage })));
const LearningRecommendationsPage = lazy(() => import("../pages/LearningRecommendationsPage").then((module) => ({ default: module.LearningRecommendationsPage })));
const LearningComparePage = lazy(() => import("../pages/LearningComparePage").then((module) => ({ default: module.LearningComparePage })));
const LearningPreferencesPage = lazy(() => import("../pages/LearningPreferencesPage").then((module) => ({ default: module.LearningPreferencesPage })));
const LearningProgressPage = lazy(() => import("../pages/LearningProgressPage").then((module) => ({ default: module.LearningProgressPage })));

export const router = createBrowserRouter([
  {
    element: <App />,
    children: [
      {
        element: <PublicLayout />,
        children: [
          { path: "/", element: <LandingPage /> },
          { path: "/about", element: <AboutPage /> },
          { path: "/how-it-works", element: <HowItWorksPage /> },
          { path: "/principles", element: <PrinciplesPage /> },
          { path: "/research", element: <ResearchPage /> },
          { path: "/project-roadmap", element: <PublicRoadmapPage /> },
          { path: "/blog", element: <Suspense fallback={null}><BlogPage /></Suspense> },
          { path: "/blog/:slug", element: <Suspense fallback={null}><BlogArticlePage /></Suspense> },
          { path: "/demo", element: <DemoPage /> },
        ],
      },
      {
        element: <AuthLayout />,
        children: [
          { path: "/login", element: <LoginPage /> },
          { path: "/register", element: <RegisterPage /> },
        ],
      },
      {
        element: <WorkspaceLayout />,
        children: [
          { path: "/diagnostic", element: <DiagnosticPage /> },
          { path: "/profile/:id", element: <ProfilePage /> },
          { path: "/fear-transformer/:profileId", element: <FearTransformerPage /> },
          { path: "/coach/:profileId", element: <CoachPage /> },
          { path: "/roadmap/:profileId", element: <RoadmapPage /> },
          { path: "/report/:profileId", element: <ReportPage /> },
          { path: "/recommendations/:profileId", element: <RecommendationsPage /> },
          { path: "/workspace/:profileId/assessment", element: <AssessmentPage /> },
          { path: "/workspace/:profileId/assessment/quick", element: <AssessmentPage /> },
          { path: "/workspace/:profileId/assessment/complete", element: <AssessmentPage /> },
          { path: "/workspace/:profileId/assessment/evidence", element: <AssessmentPage /> },
          { path: "/workspace/:profileId/assessment/results", element: <AssessmentResultsPage /> },
          { path: "/workspace/:profileId/career-compatibility", element: <CareerCompatibilityPage /> },
          { path: "/workspace/profiles/:profileId/career-compatibility", element: <CareerCompatibilityPage /> },
          { path: "/workspace/:profileId/career-compare", element: <CareerComparePage /> },
          { path: "/workspace/:profileId/learning", element: <Suspense fallback={null}><LearningPage /></Suspense> },
          { path: "/workspace/:profileId/learning/recommendations", element: <Suspense fallback={null}><LearningRecommendationsPage /></Suspense> },
          { path: "/workspace/:profileId/learning/compare", element: <Suspense fallback={null}><LearningComparePage /></Suspense> },
          { path: "/workspace/:profileId/learning/preferences", element: <Suspense fallback={null}><LearningPreferencesPage /></Suspense> },
          { path: "/workspace/:profileId/learning/progress", element: <Suspense fallback={null}><LearningProgressPage /></Suspense> },
          { path: "/assessment/:profileId", element: <AssessmentPage /> },
          { path: "/career-compatibility/:profileId", element: <CareerCompatibilityPage /> },
          { path: "/career-compare/:profileId", element: <CareerComparePage /> },
          { path: "/learning/:profileId", element: <Suspense fallback={null}><LearningPage /></Suspense> },
          { path: "/knowledge-base", element: <KnowledgeBasePage /> },
          { path: "/future-scenarios", element: <FutureScenarioPage /> },
          { path: "/projects", element: <ProjectsPage /> },
          { path: "/growth-timeline", element: <GrowthTimelinePage /> },
          { path: "/community", element: <CommunityPage /> },
          { path: "/learning-paths", element: <LearningPathPage /> },
          { path: "/co-creation-studio", element: <CoCreationStudioPage /> },
          { path: "/ai-constitution", element: <AIConstitutionPage /> },
          {
            element: <ProtectedRoute />,
            children: [
              { path: "/dashboard", element: <MyJourneyPage /> },
              { path: "/my-journey", element: <MyJourneyPage /> },
            ],
          },
        ],
      },
      {
        element: <PublicLayout />,
        children: [{ path: "*", element: <NotFoundPage /> }],
      },
    ],
  },
]);
