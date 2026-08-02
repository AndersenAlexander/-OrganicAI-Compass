import { createContext, ReactNode, useContext, useEffect, useMemo, useState } from "react";
import {
  clearStoredToken,
  getCurrentUser,
  getStoredToken,
  loginUser,
  logoutUser,
  registerUser,
} from "../api/authApi";
import { loginDemo } from "../api/demoApi";
import type { AuthUser, LoginPayload, RegisterPayload } from "../types/auth";

type AuthContextValue = {
  user: AuthUser | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isDemo: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  loginDemo: () => Promise<string>;
  logout: () => void;
  refreshUser: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(() => getStoredToken());
  const [isLoading, setIsLoading] = useState(true);

  async function refreshUser() {
    const storedToken = getStoredToken();
    if (!storedToken) {
      setUser(null);
      setToken(null);
      setIsLoading(false);
      return;
    }

    try {
      const currentUser = await getCurrentUser();
      setUser(currentUser);
      setToken(storedToken);
    } catch {
      clearStoredToken();
      setUser(null);
      setToken(null);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void refreshUser();
  }, []);

  async function login(payload: LoginPayload) {
    const response = await loginUser(payload);
    setUser(response.user);
    setToken(response.access_token);
  }

  async function register(payload: RegisterPayload) {
    const response = await registerUser(payload);
    setUser(response.user);
    setToken(response.access_token);
  }

  async function loginAsDemo() {
    const response = await loginDemo();
    setUser(response.user); setToken(response.access_token);
    return response.active_profile_id;
  }

  function logout() {
    logoutUser();
    setUser(null);
    setToken(null);
  }

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      token,
      isAuthenticated: Boolean(user && token),
      isLoading,
      isDemo: Boolean(user?.is_demo),
      login,
      register,
      loginDemo: loginAsDemo,
      logout,
      refreshUser,
    }),
    [user, token, isLoading]
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
