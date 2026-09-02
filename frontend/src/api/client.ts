import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";

export const LAST_REQUEST_ID_KEY = "organicai.last_request_id";

let accessToken: string | null = null;
let refreshPromise: Promise<string | null> | null = null;
let refreshPromiseGeneration: number | null = null;
let authStateGeneration = 0;
let authFailureHandler: (() => void) | null = null;

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "/api",
  withCredentials: true,
  headers: {
    "Content-Type": "application/json"
  }
});

export function setAccessToken(token: string | null) {
  accessToken = token;
  authStateGeneration += 1;
}

export function getAccessToken() {
  return accessToken;
}

export function setAuthFailureHandler(handler: (() => void) | null) {
  authFailureHandler = handler;
}

function shouldSkipRefresh(url = "") {
  return url.includes("/auth/login") || url.includes("/auth/register") || url.includes("/auth/refresh");
}

function getOrStartRefresh(): { generation: number; promise: Promise<string | null> } {
  if (!refreshPromise) {
    const generation = authStateGeneration;
    refreshPromiseGeneration = generation;
    refreshPromise = apiClient.post<{ access_token: string }>("/auth/refresh").then((response) => {
      if (authStateGeneration !== generation) return accessToken;
      setAccessToken(response.data.access_token);
      return response.data.access_token;
    }).finally(() => {
      refreshPromise = null;
      refreshPromiseGeneration = null;
    });
  }
  return {
    generation: refreshPromiseGeneration ?? authStateGeneration,
    promise: refreshPromise,
  };
}

apiClient.interceptors.request.use((config) => {
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => {
    const requestId = response.headers["x-request-id"];
    if (typeof requestId === "string" && requestId && typeof localStorage !== "undefined") localStorage.setItem(LAST_REQUEST_ID_KEY, requestId);
    return response;
  },
  async (error: AxiosError) => {
    const requestId = error?.response?.headers?.["x-request-id"] || (error?.response?.data as { error?: { requestId?: string } } | undefined)?.error?.requestId;
    if (typeof requestId === "string" && requestId && typeof localStorage !== "undefined") localStorage.setItem(LAST_REQUEST_ID_KEY, requestId);

    const config = error.config as (InternalAxiosRequestConfig & { _retry?: boolean }) | undefined;
    if (error.response?.status !== 401 || !config || config._retry || shouldSkipRefresh(config.url || "")) {
      return Promise.reject(error);
    }
    config._retry = true;
    const { generation, promise } = getOrStartRefresh();
    try {
      const token = await promise;
      if (!token) throw error;
      config.headers.Authorization = `Bearer ${token}`;
      return apiClient(config);
    } catch {
      if (authStateGeneration === generation) {
        setAccessToken(null);
        authFailureHandler?.();
      }
      return Promise.reject(error);
    }
  },
);

export async function refreshAccessToken() {
  const { generation, promise } = getOrStartRefresh();
  return promise.catch(() => {
    if (authStateGeneration === generation) {
      setAccessToken(null);
    }
    return null;
  });
}

export function getLastRequestId() {
  if (typeof localStorage === "undefined") return "";
  return localStorage.getItem(LAST_REQUEST_ID_KEY) || "";
}

export function extractApiError(error: unknown): { code: string; message: string; requestId: string } {
  const response = (error as { response?: { data?: unknown; headers?: Record<string, string> } }).response;
  const data = response?.data as { error?: { code?: string; message?: string; requestId?: string }; detail?: string } | undefined;
  return {
    code: data?.error?.code || "REQUEST_FAILED",
    message: data?.error?.message || data?.detail || "The request failed.",
    // An error must never be labelled with a previous request's identifier.
    // Historical request IDs remain available through getLastRequestId() for
    // explicit diagnostics, but user-visible failures use this response only.
    requestId: data?.error?.requestId || response?.headers?.["x-request-id"] || "",
  };
}
