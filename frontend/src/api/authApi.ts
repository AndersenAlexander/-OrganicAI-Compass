import { apiClient, refreshAccessToken, setAccessToken } from "./client";
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
