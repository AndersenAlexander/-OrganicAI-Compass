import { AUTH_TOKEN_KEY, apiClient } from "./client";
import type { AuthResponse, AuthUser, LoginPayload, RegisterPayload } from "../types/auth";

export function getStoredToken() {
  return localStorage.getItem(AUTH_TOKEN_KEY);
}

export function setStoredToken(token: string) {
  localStorage.setItem(AUTH_TOKEN_KEY, token);
}

export function clearStoredToken() {
  localStorage.removeItem(AUTH_TOKEN_KEY);
}

export async function registerUser(payload: RegisterPayload) {
  const { data } = await apiClient.post<AuthResponse>("/auth/register", payload);
  setStoredToken(data.access_token);
  return data;
}

export async function loginUser(payload: LoginPayload) {
  const { data } = await apiClient.post<AuthResponse>("/auth/login", payload);
  setStoredToken(data.access_token);
  return data;
}

export async function getCurrentUser() {
  const { data } = await apiClient.get<AuthUser>("/auth/me");
  return data;
}

export function logoutUser() {
  clearStoredToken();
}
