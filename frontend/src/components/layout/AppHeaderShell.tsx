import { ReactNode, useEffect } from "react";

type AppHeaderShellProps = {
  children: ReactNode;
  mobileMenu?: ReactNode;
  mobileMenuId?: string;
  mobileOpen?: boolean;
  onMobileClose?: () => void;
  variant?: "global" | "public" | "workspace" | "auth";
};

export function AppHeaderShell({
  children,
  mobileMenu,
  mobileMenuId,
  mobileOpen = false,
  onMobileClose,
  variant = "global",
}: AppHeaderShellProps) {
  useEffect(() => {
    if (!mobileOpen || !onMobileClose) return;

    const previousOverflow = document.body.style.overflow;
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onMobileClose();
    };

    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", handleKeyDown);

    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [mobileOpen, onMobileClose]);

  return (
    <header
      className={`no-print app-header app-header--${variant}`}
      data-application-header="true"
      data-testid={variant === "global" ? "global-header" : undefined}
      data-header-variant={variant}
    >
      <div className="organic-header app-header__shell" data-app-header-shell="true">
        {children}
      </div>

      {mobileOpen && mobileMenu ? (
        <>
          <button
            type="button"
            aria-hidden="true"
            tabIndex={-1}
            className="app-header__mobile-backdrop"
            onClick={onMobileClose}
          />
          <div id={mobileMenuId} className="app-header__mobile-panel">
            {mobileMenu}
          </div>
        </>
      ) : null}
    </header>
  );
}
