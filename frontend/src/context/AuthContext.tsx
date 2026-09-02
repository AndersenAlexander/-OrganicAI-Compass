import { createContext, ReactNode, useContext, useEffect, useMemo, useRef, useState } from "react";
import {
  bootRefresh,
  getCurrentUser,
  loginUser,
  logoutUser,
  registerUser,
} from "../api/authApi";
import { setAccessToken, setAuthFailureHandler } from "../api/client";
import { loginDemo } from "../api/demoApi";
import { clearAllTranscriptStorage } from "../lib/privacyTranscriptStorage";
import type { AuthUser, LoginPayload, RegisterPayload } from "../types/auth";

type AuthContextValue = {
  user: AuthUser | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isDemo: boolean;
  sessionExpired: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  loginDemo: () => Promise<string>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);
const LOGOUT_CHANNEL = "organicai-auth";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [sessionExpired, setSessionExpired] = useState(false);
  const channelRef = useRef<BroadcastChannel | null>(null);
  const demoLoginPromiseRef = useRef<Promise<string> | null>(null);

  function clearAuth(expired = false) {
    setAccessToken(null);
    setUser(null);
    setToken(null);
    setSessionExpired(expired);
    clearAllTranscriptStorage();
    window.dispatchEvent(new CustomEvent("organicai:auth-cleared", { detail: { expired } }));
  }

  async function refreshUser() {
    try {
      const currentUser = await getCurrentUser();
      setUser(currentUser);
    } catch {
      clearAuth(true);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    setAuthFailureHandler(() => clearAuth(true));
    if ("BroadcastChannel" in window) {
      channelRef.current = new BroadcastChannel(LOGOUT_CHANNEL);
      channelRef.current.onmessage = (event) => {
        if (event.data?.type === "logout") clearAuth(false);
      };
    }
    void bootRefresh().then((currentUser) => {
      if (currentUser) {
        setUser(currentUser);
        setToken("memory");
      } else {
        clearAuth(false);
      }
      setIsLoading(false);
    });
    return () => {
      setAuthFailureHandler(null);
      channelRef.current?.close();
    };
  }, []);

  async function login(payload: LoginPayload) {
    localStorage.removeItem("organicai_active_profile_id");
    const response = await loginUser(payload);
    setUser(response.user);
    setToken("memory");
    setSessionExpired(false);
  }

  async function register(payload: RegisterPayload) {
    localStorage.removeItem("organicai_active_profile_id");
    const response = await registerUser(payload);
    setUser(response.user);
    setToken("memory");
    setSessionExpired(false);
  }

  async function loginAsDemo() {
    if (demoLoginPromiseRef.current) return demoLoginPromiseRef.current;

    const pendingLogin = (async () => {
      const response = await loginDemo();
      setUser(response.user);
      setToken("memory");
      setSessionExpired(false);
      return response.active_profile_id;
    })();
    demoLoginPromiseRef.current = pendingLogin;
    try {
      return await pendingLogin;
    } finally {
      if (demoLoginPromiseRef.current === pendingLogin) demoLoginPromiseRef.current = null;
    }
  }

  async function logout() {
    try {
      await logoutUser();
    } finally {
      clearAuth(false);
      localStorage.removeItem("organicai_active_profile_id");
      channelRef.current?.postMessage({ type: "logout", at: Date.now() });
    }
  }

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      token,
      isAuthenticated: Boolean(user && token),
      isLoading,
      isDemo: Boolean(user?.is_demo),
      sessionExpired,
      login,
      register,
      loginDemo: loginAsDemo,
      logout,
      refreshUser,
    }),
    [user, token, isLoading, sessionExpired]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider.");
  }
  return context;
}
