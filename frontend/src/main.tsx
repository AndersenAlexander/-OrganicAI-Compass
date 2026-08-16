import React from "react";
import ReactDOM from "react-dom/client";
import { RouterProvider } from "react-router-dom";
import { router } from "./routes/router";
import { AuthProvider } from "./context/AuthContext";
import { ThemeProvider } from "./context/ThemeContext";
import "@fontsource/cormorant-garamond/latin-500.css";
import "@fontsource/cormorant-garamond/latin-600.css";
import "./styles/globals.css";
import "./styles/organicai-tokens.css";
import "./styles/about.css";
import "./styles/home.css";
import "./styles/rag-feedback.css";
import "./styles/how-it-works.css";
import "./styles/market-application.css";
import "./styles/interview-journey.css";
import "./styles/innovation-extension.css";
import "./styles/originality-research.css";
import "./styles/live-voice.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ThemeProvider>
      <AuthProvider>
        <RouterProvider router={router} />
      </AuthProvider>
    </ThemeProvider>
  </React.StrictMode>
);
