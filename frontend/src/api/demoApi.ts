import { apiClient, extractApiError, setAccessToken } from "./client";
import type { AuthUser } from "../types/auth";

export type DemoLoginResponse = { access_token: string; token_type: "bearer"; expires_in?: number; active_profile_id: string; demo_mode: true; user: AuthUser & { is_demo: true } };
export type DemoResetResponse = { ok: true; status: "reset"; profile_id: string; active_profile_id: string; reset_sections: string[]; message: string };

export async function loginDemo() {
  const { data } = await apiClient.post<DemoLoginResponse>("/auth/demo-login");
  setAccessToken(data.access_token);
  localStorage.setItem("organicai_active_profile_id", data.active_profile_id);
  return data;
}

export function demoLoginFailureMessage(error: unknown) {
  const response = (error as { response?: { status?: number } } | undefined)?.response;
  const { code, message, requestId } = extractApiError(error);
  const requestReference = requestId ? ` Request ID: ${requestId}.` : "";

  if (!response) {
    return "The Demo service could not be reached. Check the frontend API target and that the isolated Demo backend is running.";
  }
  if (code === "DATABASE_UNAVAILABLE" || response.status === 503) {
    return `The Demo backend cannot prepare its data store. ${message}${requestReference}`;
  }
  if (response.status === 404) {
    return `Demo Mode is disabled or unavailable on the configured backend. ${message}${requestReference}`;
  }
  return `The Demo account could not be prepared. ${message}${requestReference}`;
}

export async function resetDemoData() {
  return (await apiClient.post<DemoResetResponse>("/demo/reset")).data;
}
