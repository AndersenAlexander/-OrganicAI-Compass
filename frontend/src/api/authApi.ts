import { apiClient, extractApiError, refreshAccessToken, setAccessToken } from "./client";
import type { AuthResponse, AuthSession, AuthUser, ChangePasswordPayload, LoginPayload, RegisterPayload } from "../types/auth";

export async function registerUser(payload: RegisterPayload) {
  const { data } = await apiClient.post<AuthResponse>("/auth/register", payload);
  setAccessToken(data.access_token);
  return data;
}

export async function loginUser(payload: LoginPayload) {
  const { data } = await apiClient.post<AuthResponse>("/auth/login", payload);
  setAccessToken(data.access_token);
  return data;
}

/**
 * Keeps the normal credential response deliberately non-enumerating while
 * giving local developers enough context to tell an infrastructure failure
 * from an invalid sign-in attempt.
 */
export function loginFailureMessage(error: unknown): string {
  const response = (error as { response?: { status?: number } } | undefined)?.response;
  const status = response?.status;
  const { code } = extractApiError(error);

  if (!response) {
    return "The login service is unavailable. Check that the backend is running and try again.";
  }

  if (code === "ACCOUNT_LOCKED") {
    return "This account is temporarily locked. Please wait before trying again.";
  }

  if (status === 400 || status === 422) {
    return "Check the email address and password format, then try again.";
  }

  if (status === 404) {
    return import.meta.env.DEV
      ? "The login endpoint is unavailable. Check the local API route and base URL."
      : "The login service is temporarily unavailable. Please try again later.";
  }

  if (status === 503 || code === "DATABASE_UNAVAILABLE") {
    return "The login service cannot reach its data store. Please try again shortly.";
  }

  if (status && status >= 500) {
    return "The login service is temporarily unavailable. Please try again shortly.";
  }

  // The backend intentionally returns the same response for an unknown
  // address, a wrong password, a disabled account, or a locked account.
  return "Login failed. Check your email and password.";
}

export async function bootRefresh() {
  const token = await refreshAccessToken();
  if (!token) return null;
  return getCurrentUser();
}

export async function getCurrentUser() {
  const { data } = await apiClient.get<AuthUser>("/auth/me");
  return data;
}

export async function listSessions() {
  const { data } = await apiClient.get<AuthSession[]>("/auth/sessions");
  return data;
}

export async function revokeSession(sessionId: string) {
  await apiClient.delete(`/auth/sessions/${sessionId}`);
}

export async function changePassword(payload: ChangePasswordPayload) {
  await apiClient.post("/auth/change-password", payload);
}

export async function forgotPassword(email: string) {
  await apiClient.post("/auth/forgot-password", { email });
}

export async function resetPassword(token: string, newPassword: string) {
  await apiClient.post("/auth/reset-password", { token, new_password: newPassword });
}

export async function verifyEmail(token: string) {
  const { data } = await apiClient.post<AuthUser>("/auth/verify-email", { token });
  return data;
}

export async function resendVerification() {
  await apiClient.post("/auth/resend-verification");
}

export async function logoutUser() {
  try {
    await apiClient.post("/auth/logout");
  } finally {
    setAccessToken(null);
  }
}

export async function logoutAll() {
  try {
    await apiClient.post("/auth/logout-all");
  } finally {
    setAccessToken(null);
  }
}
