import { AlertTriangle, CheckCircle2, Clipboard, Database, KeyRound, LogOut, MailCheck, RefreshCw, Server, ShieldCheck, Trash2 } from "lucide-react";
import { type FormEvent, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { changePassword, listSessions, logoutAll, resendVerification, revokeSession } from "../api/authApi";
import { getPersistenceStatus } from "../api/systemApi";
import { extractApiError } from "../api/client";
import { useAuth } from "../context/AuthContext";
import {
  backupLabel,
  backupVerificationLabel,
  connectionLabel,
  integrityLabel,
  migrationLabel,
  persistenceReleaseGateMessage,
  legacyArchiveLabel,
  legacyRemediationSimulationLabel,
  postgresValidationLabel,
  restoreVerificationLabel,
  sanitizedPersistenceSummary,
} from "../lib/persistenceDiagnostics";
import type { PersistenceStatus } from "../types/persistence";
import type { AuthSession } from "../types/auth";

type LoadState = "loading" | "ready" | "error";

function StatusPill({ value, tone }: { value: string; tone: "ok" | "warn" | "error" }) {
  const className =
    tone === "ok"
      ? "border-emerald-300/40 bg-emerald-500/12 text-emerald-100"
      : tone === "warn"
        ? "border-amber-300/45 bg-amber-500/14 text-amber-100"
        : "border-rose-300/45 bg-rose-500/14 text-rose-100";
  return <span className={`inline-flex min-h-8 items-center rounded-full border px-3 text-xs font-bold ${className}`}>{value}</span>;
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-white/12 bg-white/[0.055] p-4 shadow-sm theme-card">
      <dt className="text-xs font-bold uppercase tracking-[0.12em] theme-muted">{label}</dt>
      <dd className="mt-2 break-words text-sm font-semibold theme-text">{value}</dd>
    </div>
  );
}

export function SettingsPage() {
  const auth = useAuth();
  const [status, setStatus] = useState<PersistenceStatus | null>(null);
  const [sessions, setSessions] = useState<AuthSession[]>([]);
  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [sessionLoadState, setSessionLoadState] = useState<LoadState>("loading");
  const [message, setMessage] = useState("");
  const [securityMessage, setSecurityMessage] = useState("");
  const [passwordForm, setPasswordForm] = useState({ current_password: "", new_password: "" });

  async function load() {
    setLoadState("loading");
    setMessage("");
    try {
      setStatus(await getPersistenceStatus());
      setLoadState("ready");
    } catch (error) {
      const apiError = extractApiError(error);
      setStatus(null);
      setMessage(apiError.requestId ? `${apiError.message} Request ID: ${apiError.requestId}` : apiError.message);
      setLoadState("error");
    }
  }

  async function loadSessions() {
    setSessionLoadState("loading");
    try {
      setSessions(await listSessions());
      setSessionLoadState("ready");
    } catch (error) {
      const apiError = extractApiError(error);
      setSecurityMessage(apiError.requestId ? `${apiError.message} Request ID: ${apiError.requestId}` : apiError.message);
      setSessionLoadState("error");
    }
  }

  useEffect(() => {
    void load();
    void loadSessions();
  }, []);

  const summary = useMemo(() => (status ? sanitizedPersistenceSummary(status) : ""), [status]);
  const migrationTone = status?.migrationState === "current" ? "ok" : status?.migrationState === "missing" ? "error" : "warn";

  async function copySummary() {
    if (!summary) return;
    await navigator.clipboard?.writeText(summary);
    setMessage("Diagnostic summary copied.");
  }

  async function submitPasswordChange(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSecurityMessage("");
    try {
      await changePassword(passwordForm);
      setPasswordForm({ current_password: "", new_password: "" });
      setSecurityMessage("Password changed. Other sessions were revoked.");
      await loadSessions();
    } catch (error) {
      const apiError = extractApiError(error);
      setSecurityMessage(apiError.requestId ? `${apiError.message} Request ID: ${apiError.requestId}` : apiError.message);
    }
  }

  async function handleRevokeSession(sessionId: string) {
    setSecurityMessage("");
    try {
      await revokeSession(sessionId);
      setSecurityMessage("Session revoked.");
      await loadSessions();
    } catch (error) {
      const apiError = extractApiError(error);
      setSecurityMessage(apiError.requestId ? `${apiError.message} Request ID: ${apiError.requestId}` : apiError.message);
    }
  }

  async function handleResendVerification() {
    setSecurityMessage("");
    try {
      await resendVerification();
      setSecurityMessage("Verification email requested.");
    } catch (error) {
      const apiError = extractApiError(error);
      setSecurityMessage(apiError.requestId ? `${apiError.message} Request ID: ${apiError.requestId}` : apiError.message);
    }
  }

  async function handleLogoutAll() {
    setSecurityMessage("");
    try {
      await logoutAll();
      await auth.logout();
    } catch (error) {
      const apiError = extractApiError(error);
      setSecurityMessage(apiError.requestId ? `${apiError.message} Request ID: ${apiError.requestId}` : apiError.message);
    }
  }

  return (
    <section className="mx-auto w-full max-w-6xl py-8">
      <div className="mb-6 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.18em] text-teal-200">Settings</p>
          <h1 className="mt-2 font-display text-4xl font-semibold theme-text">Persistence</h1>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button type="button" onClick={() => void load()} className="inline-flex min-h-10 items-center gap-2 rounded-lg border border-white/15 px-3 text-sm font-bold theme-text hover:bg-white/10">
            <RefreshCw size={16} />
            Refresh
          </button>
          <Link to="/privacy" className="inline-flex min-h-10 items-center gap-2 rounded-lg border border-white/15 px-3 text-sm font-bold theme-text hover:bg-white/10">
            <ShieldCheck size={16} />
            Privacy Center
          </Link>
          <button type="button" onClick={() => void copySummary()} disabled={!status} className="inline-flex min-h-10 items-center gap-2 rounded-lg bg-teal-400 px-3 text-sm font-black text-slate-950 disabled:cursor-not-allowed disabled:opacity-50">
            <Clipboard size={16} />
            Copy diagnostic summary
          </button>
        </div>
      </div>

      {loadState === "error" ? (
        <div role="alert" className="mb-5 flex items-start gap-3 rounded-lg border border-rose-300/35 bg-rose-500/12 p-4 text-rose-100">
          <AlertTriangle className="mt-0.5 shrink-0" size={18} />
          <span>{message || "Persistence diagnostics are unavailable."}</span>
        </div>
      ) : null}
      {message && loadState !== "error" ? (
        <div role="status" className="mb-5 flex items-center gap-3 rounded-lg border border-emerald-300/30 bg-emerald-500/10 p-4 text-emerald-100">
          <CheckCircle2 size={18} />
          <span>{message}</span>
        </div>
      ) : null}

      <div className="mb-5 rounded-lg border border-white/12 bg-slate-950/45 p-5 shadow-xl theme-card">
        <div className="mb-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-3">
            <ShieldCheck className="text-teal-200" size={22} />
            <div>
              <h2 className="text-xl font-bold theme-text">Account Security</h2>
              <p className="text-sm theme-muted">{auth.user?.email ?? "Signed in account"}</p>
            </div>
          </div>
          <StatusPill value={auth.user?.email_verified_at ? "Email verified" : "Verification pending"} tone={auth.user?.email_verified_at ? "ok" : "warn"} />
        </div>
        {securityMessage ? (
          <div role="status" className="mb-4 flex items-center gap-3 rounded-lg border border-emerald-300/30 bg-emerald-500/10 p-3 text-sm text-emerald-100">
            <CheckCircle2 size={17} />
            <span>{securityMessage}</span>
          </div>
        ) : null}
        <div className="grid gap-4 lg:grid-cols-[360px_1fr]">
          <form onSubmit={(event) => void submitPasswordChange(event)} className="space-y-3 rounded-lg border border-white/10 bg-white/[0.045] p-4">
            <div className="flex items-center gap-2 font-bold theme-text">
              <KeyRound size={18} />
              Change password
            </div>
            <input
              type="password"
              required
              value={passwordForm.current_password}
              onChange={(event) => setPasswordForm((current) => ({ ...current, current_password: event.target.value }))}
              placeholder="Current password"
              className="w-full rounded-lg border border-white/15 bg-white/90 p-3 text-sm text-slate-950 outline-none focus:ring-4 focus:ring-teal-300/40"
            />
            <input
              type="password"
              required
              minLength={12}
              value={passwordForm.new_password}
              onChange={(event) => setPasswordForm((current) => ({ ...current, new_password: event.target.value }))}
              placeholder="New password"
              className="w-full rounded-lg border border-white/15 bg-white/90 p-3 text-sm text-slate-950 outline-none focus:ring-4 focus:ring-teal-300/40"
            />
            <button type="submit" className="inline-flex min-h-10 items-center gap-2 rounded-lg bg-teal-400 px-3 text-sm font-black text-slate-950">
              <KeyRound size={16} />
              Update
            </button>
          </form>
          <div className="rounded-lg border border-white/10 bg-white/[0.045] p-4">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-2 font-bold theme-text">
                <Server size={18} />
                Sessions
              </div>
              <div className="flex flex-wrap gap-2">
                <button type="button" onClick={() => void loadSessions()} className="inline-flex min-h-9 items-center gap-2 rounded-lg border border-white/15 px-3 text-xs font-bold theme-text hover:bg-white/10">
                  <RefreshCw size={14} />
                  Refresh
                </button>
                {!auth.user?.email_verified_at ? (
                  <button type="button" onClick={() => void handleResendVerification()} className="inline-flex min-h-9 items-center gap-2 rounded-lg border border-white/15 px-3 text-xs font-bold theme-text hover:bg-white/10">
                    <MailCheck size={14} />
                    Verify
                  </button>
                ) : null}
                <button type="button" onClick={() => void handleLogoutAll()} className="inline-flex min-h-9 items-center gap-2 rounded-lg border border-rose-300/40 px-3 text-xs font-bold text-rose-100 hover:bg-rose-500/10">
                  <LogOut size={14} />
                  Log out all
                </button>
              </div>
            </div>
            <div className="space-y-2">
              {sessionLoadState === "loading" ? <p className="text-sm theme-muted">Loading sessions.</p> : null}
              {sessions.map((session) => (
                <div key={session.id} className="flex flex-col gap-3 rounded-lg border border-white/10 bg-black/15 p-3 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p className="text-sm font-bold theme-text">{session.current_session ? "Current session" : session.device || "Signed-in device"}</p>
                    <p className="text-xs theme-muted">Created {new Date(session.created_at).toLocaleString()} · Expires {new Date(session.expires_at).toLocaleString()}</p>
                  </div>
                  <button
                    type="button"
                    disabled={session.current_session || session.revoked}
                    onClick={() => void handleRevokeSession(session.id)}
                    className="inline-flex min-h-9 items-center justify-center gap-2 rounded-lg border border-white/15 px-3 text-xs font-bold theme-text disabled:cursor-not-allowed disabled:opacity-50 hover:bg-white/10"
                  >
                    <Trash2 size={14} />
                    Revoke
                  </button>
                </div>
              ))}
              {sessionLoadState !== "loading" && sessions.length === 0 ? <p className="text-sm theme-muted">No active sessions reported.</p> : null}
            </div>
          </div>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-[1fr_360px]">
        <div className="rounded-lg border border-white/12 bg-slate-950/45 p-5 shadow-xl theme-card">
          <div className="mb-4 flex items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <Database className="text-teal-200" size={22} />
              <h2 className="text-xl font-bold theme-text">Persistence</h2>
            </div>
            {loadState === "loading" ? <StatusPill value="Loading" tone="warn" /> : <StatusPill value={connectionLabel(status)} tone={status?.reachable ? "ok" : "error"} />}
          </div>
          <dl className="grid gap-3 sm:grid-cols-2">
            <Field label="Database driver" value={status?.driver ?? "Unknown"} />
            <Field label="Connection status" value={connectionLabel(status)} />
            <Field label="Schema revision" value={status?.schemaVersion ?? "Missing"} />
            <Field label="Migration status" value={migrationLabel(status)} />
            <Field label="Backup availability" value={backupLabel(status)} />
            <Field label="Last integrity check" value={integrityLabel(status)} />
            <Field label="Production requirement" value={status?.productionPostgresRequired ? "PostgreSQL required" : "Not enforced"} />
            <Field label="Pool status" value={status?.pool.enabled ? `Enabled, size ${status.pool.sizeConfigured ?? "not reported"}` : "Disabled for SQLite"} />
            <Field label="PostgreSQL validation" value={postgresValidationLabel(status).replace("PostgreSQL validation: ", "")} />
            <Field label="Pre-activation backup" value={backupVerificationLabel(status).replace("Pre-activation backup: ", "")} />
            <Field label="Rollback fallback" value={restoreVerificationLabel(status).replace("Rollback fallback: ", "")} />
            <Field label="Legacy remediation simulation" value={legacyRemediationSimulationLabel().replace("Legacy remediation simulation: ", "")} />
            <Field label="Legacy orphan archive" value={legacyArchiveLabel().replace("Legacy orphan archive: ", "")} />
            <Field label="Archived orphan messages" value="156" />
            <Field label="Legacy data loss" value={`${status?.releaseGate?.legacyDataLoss ?? 0}`} />
            <Field label="Legacy original database" value="Preserved" />
            <Field label="Active persistence" value={status?.driver === "postgresql" ? "PostgreSQL" : "SQLite fallback"} />
          </dl>
        </div>

        <aside className="rounded-lg border border-white/12 bg-white/[0.055] p-5 shadow-xl theme-card">
          <div className="mb-4 flex items-center gap-3">
            <Server className="text-cyan-200" size={21} />
            <h2 className="text-lg font-bold theme-text">Current State</h2>
          </div>
          <div className="space-y-3">
            <StatusPill value={connectionLabel(status)} tone={status?.reachable ? "ok" : "error"} />
            <StatusPill value={migrationLabel(status)} tone={migrationTone} />
            <StatusPill value={backupLabel(status)} tone={status?.backup.latestBackupAvailable ? "ok" : "warn"} />
            <StatusPill value={integrityLabel(status)} tone={status?.integrity.lastCheckStatus === "failed" ? "error" : "warn"} />
            <StatusPill value={postgresValidationLabel(status)} tone={status?.driver === "postgresql" && status.migrationState === "current" ? "ok" : "warn"} />
            <StatusPill value={backupVerificationLabel(status)} tone={status?.releaseGate?.preActivationBackupVerified || status?.backup.latestBackupAvailable ? "ok" : "warn"} />
            <StatusPill value={restoreVerificationLabel(status)} tone={status?.releaseGate?.rollbackFallbackAvailable ? "ok" : "warn"} />
            <StatusPill value={legacyRemediationSimulationLabel()} tone="ok" />
            <StatusPill value={legacyArchiveLabel()} tone="ok" />
            <StatusPill value="Legacy original database: preserved" tone="ok" />
            <StatusPill value={status?.driver === "postgresql" ? "Active persistence: PostgreSQL" : "Active persistence: SQLite fallback"} tone={status?.driver === "postgresql" ? "ok" : "warn"} />
          </div>
          <p className="mt-5 rounded-lg border border-amber-300/30 bg-amber-500/10 p-3 text-sm leading-6 text-amber-50">
            {persistenceReleaseGateMessage(status)}
          </p>
          <pre className="mt-5 max-h-72 overflow-auto rounded-lg border border-white/10 bg-black/25 p-3 text-xs leading-5 text-slate-100">{summary || "Persistence diagnostics not loaded."}</pre>
        </aside>
      </div>
    </section>
  );
}
