export const PROFILE_KEY = "organicai_active_profile_id";

const PROFILE_ROUTE_PATTERN = /^\/(?:profile|roadmap|report|coach|fear-transformer|recommendations|assessment|career-compatibility|career-compare|learning)\/([^/]+)/;
const WORKSPACE_ROUTE_PATTERN = /^\/workspace\/(?:profiles\/)?([^/]+)/;

export type ProfileContextState =
  | "loading"
  | "anonymous-public"
  | "authenticated-no-profile"
  | "authenticated-owned-profile"
  | "explicit-demo"
  | "profile-error";

export function cleanProfileId(value?: string | null) {
  const id = String(value || "").trim();
  return id && !["undefined", "null"].includes(id) ? id : "";
}

export function profileIdFromPath(pathname = window.location.pathname) {
  return cleanProfileId(pathname.match(PROFILE_ROUTE_PATTERN)?.[1] || pathname.match(WORKSPACE_ROUTE_PATTERN)?.[1] || "");
}

export function selectOwnedProfileId({
  routeProfileId,
  storedProfileId,
  ownedProfileIds,
  isDemo,
}: {
  routeProfileId?: string | null;
  storedProfileId?: string | null;
  ownedProfileIds: string[];
  isDemo: boolean;
}) {
  const routeId = cleanProfileId(routeProfileId);
  const storedId = cleanProfileId(storedProfileId);
  if (isDemo) return routeId || storedId || "demo-profile";
  if (routeId && ownedProfileIds.includes(routeId)) return routeId;
  if (storedId && ownedProfileIds.includes(storedId)) return storedId;
  return ownedProfileIds[0] || "";
}

export function profileContextState({
  loading,
  authenticated,
  isDemo,
  profileId,
  error,
}: {
  loading: boolean;
  authenticated: boolean;
  isDemo: boolean;
  profileId: string;
  error?: string;
}): ProfileContextState {
  if (loading) return "loading";
  if (error) return "profile-error";
  if (!authenticated) return "anonymous-public";
  if (isDemo) return "explicit-demo";
  return profileId ? "authenticated-owned-profile" : "authenticated-no-profile";
}

export function getActiveProfileId(
  pathname = window.location.pathname,
  options: { allowDemoFallback?: boolean } = {}
) {
  const stored = typeof localStorage === "undefined" ? "" : cleanProfileId(localStorage.getItem(PROFILE_KEY));
  return profileIdFromPath(pathname) || stored || (options.allowDemoFallback ? "demo-profile" : "");
}
