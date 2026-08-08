const PROFILE_KEY = "organicai_active_profile_id";

export function getActiveProfileId(
  pathname = window.location.pathname,
  options: { allowDemoFallback?: boolean } = {}
) {
  const match = pathname.match(/^\/(?:profile|roadmap|report|coach|fear-transformer|recommendations|assessment|career-compatibility|career-compare|learning)\/([^/]+)/)
    || pathname.match(/^\/workspace\/(?:profiles\/)?([^/]+)/);
  return match?.[1] || localStorage.getItem(PROFILE_KEY) || (options.allowDemoFallback === false ? "" : "demo-profile");
}
