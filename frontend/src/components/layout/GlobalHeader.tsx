import { ChevronDown, LogOut, Menu, UserRound } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { Link, NavLink, useLocation, useNavigate } from "react-router-dom";
import { buildWorkspaceNavigation, globalNavigation } from "../../config/navigation";
import { useAuth } from "../../context/AuthContext";
import { useAppActions } from "../../hooks/useAppActions";
import { AppHeaderShell } from "./AppHeaderShell";
import { BrandLockup } from "./BrandLockup";
import { ThemeToggle } from "./ThemeToggle";

const workspaceRoutePatterns = [/^\/dashboard$/, /^\/my-journey$/, /^\/diagnostic$/, /^\/profile\//, /^\/coach\//, /^\/recommendations\//, /^\/roadmap\//, /^\/workspace\//, /^\/assessment\//, /^\/career-compatibility\//, /^\/career-compare\//, /^\/learning\//, /^\/knowledge-base$/, /^\/privacy$/, /^\/settings$/];

function isWorkspaceRoute(pathname: string) {
  return workspaceRoutePatterns.some((pattern) => pattern.test(pathname));
}

function isWorkspaceItemActive(label: string, pathname: string) {
  if (label === "Dashboard") return pathname === "/dashboard" || pathname === "/my-journey";
  if (label === "Diagnostic" || label === "Natural Discovery") return pathname === "/diagnostic";
  if (label === "Career Assessment" || label === "Capability Assessment") return pathname.includes("/assessment");
  if (label === "Career Compatibility" || label === "Career Hypotheses") return pathname.includes("/career-compatibility") || pathname.includes("/career-compare");
  if (label === "Career Experiments") return pathname.includes("/experiments") || pathname.includes("/career-resilience");
  if (label === "Evidence Passport") return pathname.includes("/evidence-passport");
  if (label === "Supported Paths") return pathname.includes("/supported-paths");
  if (label === "Market Radar") return pathname.includes("/market-radar");
  if (label === "Job Analyzer") return pathname.includes("/job-analyzer");
  if (label === "Applications") return pathname.includes("/applications") || pathname.includes("/application-studio");
  if (label === "Interview Journey" || label === "Panel Interview") return pathname.includes("/interviews");
  if (label === "STAR Stories") return pathname.includes("/star-stories");
  if (label === "Offer Review") return pathname.includes("/offer-review");
  if (label === "Career Encyclopedia") return pathname.includes("/career-encyclopedia");
  if (label === "Adaptive Experiments") return pathname.includes("/adaptive-experiments");
  if (label === "Transition Simulator") return pathname.includes("/transition-simulator");
  if (label === "Decision Journal") return pathname.includes("/decision-journal");
  if (label === "Recommendation Robustness") return pathname.includes("/recommendation-robustness");
  if (label === "Synthetic Fairness Lab") return pathname.includes("/synthetic-fairness-lab");
  if (label === "Advisor Collaboration") return pathname.includes("/advisor-collaboration");
  if (label === "Browser Extension") return pathname.includes("/integrations/browser-extension");
  if (label === "Research Evaluation") return pathname.includes("/research-evaluation");
  if (label === "Job Loss Support") return pathname.includes("/job-loss-support") || pathname.includes("/support-brief");
  if (label === "Learning Path") return pathname.includes("/learning");
  if (label === "Knowledge Base") return pathname === "/knowledge-base";
  if (label === "Privacy Center") return pathname === "/privacy";
  if (label === "Settings") return pathname === "/settings";
  if (label === "Human Potential Map") return pathname.startsWith("/profile/");
  if (label === "AI Coach") return pathname.startsWith("/coach/");
  if (label === "Recommendations") return pathname.startsWith("/recommendations/");
  if (label === "My Roadmap") return pathname.startsWith("/roadmap/");
  return false;
}

const desktopLinkClass = ({ isActive }: { isActive: boolean }) =>
  isActive
    ? "global-header__link global-header__link--active"
    : "global-header__link";

const mobileLinkClass = ({ isActive }: { isActive: boolean }) =>
  isActive
    ? "rounded-xl bg-white/12 px-3 py-3 text-sm font-semibold text-[#99f6e4] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#5eead4]"
    : "rounded-xl px-3 py-3 text-sm font-semibold text-white/82 hover:bg-white/10 hover:text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#5eead4]";

export function GlobalHeader() {
  const { user, isAuthenticated, isLoading, isDemo, logout } = useAuth();
  const { activeProfileId } = useAppActions();
  const location = useLocation();
  const navigate = useNavigate();
  const workspaceDropdownRef = useRef<HTMLDivElement>(null);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [workspaceOpen, setWorkspaceOpen] = useState(false);
  const workspaceNavigation = useMemo(() => buildWorkspaceNavigation(activeProfileId), [activeProfileId]);
  const workspaceActive = isWorkspaceRoute(location.pathname);

  useEffect(() => {
    setMobileOpen(false);
    setWorkspaceOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    if (!workspaceOpen) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setWorkspaceOpen(false);
    };
    const handlePointerDown = (event: PointerEvent) => {
      if (!workspaceDropdownRef.current?.contains(event.target as Node)) setWorkspaceOpen(false);
    };

    window.addEventListener("keydown", handleKeyDown);
    window.addEventListener("pointerdown", handlePointerDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      window.removeEventListener("pointerdown", handlePointerDown);
    };
  }, [workspaceOpen]);

  async function exitAccount() {
    await logout();
    if (isDemo) localStorage.removeItem("organicai_active_profile_id");
    navigate("/login");
  }

  const accountActions = isLoading ? (
    <div className="app-header__auth-skeleton" aria-hidden="true">
      <span />
      <span />
    </div>
  ) : isAuthenticated ? (
    <>
      {isDemo ? (
        <span className="global-header__demo-pill">Demo Mode</span>
      ) : (
        <Link to="/dashboard" className="global-header__user-link">
          <UserRound size={16} />
          {user?.name.split(" ")[0] ?? "Account"}
        </Link>
      )}
        <button type="button" onClick={() => void exitAccount()} className="global-header__account-button">
        <LogOut size={16} />
        <span className="hidden sm:inline">{isDemo ? "Exit Demo" : "Logout"}</span>
      </button>
    </>
  ) : (
    <>
      <Link to="/login" className="global-header__account-link">
        Log in
      </Link>
      <Link to="/diagnostic" className="global-header__primary-action">
        Get Started
      </Link>
    </>
  );

  const workspaceDropdown = (
    <div className="global-header__workspace" ref={workspaceDropdownRef}>
      <button
        type="button"
        className={workspaceActive ? "global-header__link global-header__link--active" : "global-header__link"}
        aria-expanded={workspaceOpen}
        aria-controls="global-workspace-dropdown"
        aria-haspopup="menu"
        onClick={() => setWorkspaceOpen((current) => !current)}
      >
        Workspace
        <ChevronDown size={15} aria-hidden="true" />
      </button>
      {workspaceOpen ? (
        <div id="global-workspace-dropdown" className="global-header__workspace-menu" role="menu">
          {workspaceNavigation.map((link) => {
            const active = isWorkspaceItemActive(link.label, location.pathname);
            return (
              <Link
                key={link.label}
                to={link.to}
                role="menuitem"
                aria-current={active ? "page" : undefined}
                className={active ? "global-header__workspace-item active" : "global-header__workspace-item"}
              >
                {link.label}
              </Link>
            );
          })}
        </div>
      ) : null}
    </div>
  );

  const mobileMenu = (
    <div className="global-header__mobile-menu">
      <section>
        <p>Explore</p>
        <nav aria-label="Global mobile navigation" className="grid gap-1">
          {globalNavigation.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.end ?? link.to === "/"}
              onClick={() => setMobileOpen(false)}
              className={mobileLinkClass}
            >
              {link.label}
            </NavLink>
          ))}
        </nav>
      </section>

      <section>
        <p>Workspace</p>
        <nav aria-label="Global mobile workspace navigation" className="grid gap-1">
          {workspaceNavigation.map((link) => (
            <Link
              key={link.label}
              to={link.to}
              aria-current={isWorkspaceItemActive(link.label, location.pathname) ? "page" : undefined}
              onClick={() => setMobileOpen(false)}
              className={
                isWorkspaceItemActive(link.label, location.pathname)
                  ? "rounded-xl bg-white/12 px-3 py-3 text-sm font-semibold text-[#99f6e4]"
                  : "rounded-xl px-3 py-3 text-sm font-semibold text-white/82 hover:bg-white/10 hover:text-white"
              }
            >
              {link.label}
            </Link>
          ))}
        </nav>
      </section>

      <section>
        <p>Account</p>
        <div className="global-header__mobile-account">
          {isLoading ? (
            <span className="px-3 py-2 text-sm font-semibold text-white/60">Loading account...</span>
          ) : isAuthenticated ? (
            <>
              {isDemo ? (
                <span className="global-header__mobile-status">Demo Mode</span>
              ) : (
                <Link to="/dashboard" onClick={() => setMobileOpen(false)} className="app-header__mobile-action-link">
                  {user?.name.split(" ")[0] ?? "Account"}
                </Link>
              )}
              <button
                type="button"
                onClick={() => {
                  setMobileOpen(false);
                  void exitAccount();
                }}
                className="app-header__mobile-action-link"
              >
                {isDemo ? "Exit Demo" : "Logout"}
              </button>
            </>
          ) : (
            <>
              <Link to="/login" onClick={() => setMobileOpen(false)} className="app-header__mobile-action-link">
                Log in
              </Link>
              <Link to="/diagnostic" onClick={() => setMobileOpen(false)} className="app-header__mobile-action-link primary">
                Get Started
              </Link>
            </>
          )}
        </div>
      </section>
    </div>
  );

  return (
    <AppHeaderShell mobileOpen={mobileOpen} mobileMenuId="global-mobile-navigation" mobileMenu={mobileMenu} onMobileClose={() => setMobileOpen(false)}>
      <BrandLockup className="app-header__brand" textClassName="app-header__brand-text" />

      <nav aria-label="Global navigation" className="app-header__nav global-desktop-navigation">
        {globalNavigation.map((link) => (
          <NavLink key={link.to} to={link.to} end={link.end ?? link.to === "/"} className={desktopLinkClass}>
            {link.label}
          </NavLink>
        ))}
        {workspaceDropdown}
      </nav>

      <div className="app-header__actions global-header__actions">
        <ThemeToggle />
        {accountActions}
        <button
          type="button"
          onClick={() => setMobileOpen((current) => !current)}
          className="app-header__mobile-toggle grid h-10 w-10 place-items-center rounded-full border border-white/20 text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[#5eead4]"
          aria-label={mobileOpen ? "Close navigation menu" : "Open navigation menu"}
          aria-controls="global-mobile-navigation"
          aria-expanded={mobileOpen}
        >
          <Menu size={18} />
        </button>
      </div>
    </AppHeaderShell>
  );
}
