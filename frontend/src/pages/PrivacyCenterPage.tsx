import {
  AlertTriangle,
  CheckCircle2,
  Database,
  Download,
  Eye,
  FileArchive,
  KeyRound,
  RefreshCw,
  ShieldCheck,
  Trash2,
  UserX,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import {
  cancelAccountDeletion,
  createPrivacyExport,
  deletePrivacyCategory,
  deletePrivacyExport,
  downloadPrivacyExport,
  getPrivacyConsents,
  getPrivacyExports,
  getPrivacyInventory,
  getPrivacyPreferences,
  getPrivacyProviders,
  getPrivacyRequests,
  getPrivacyResearch,
  getPrivacySummary,
  previewCategoryDeletion,
  reauthenticatePrivacy,
  requestAccountDeletion,
  updatePrivacyPreferences,
  withdrawResearchParticipation,
} from "../api/privacyApi";
import { extractApiError } from "../api/client";
import { publishPrivacyPreferences } from "../lib/privacyTranscriptStorage";
import type {
  CategoryDeletionPreview,
  PersonalDataCategory,
  PrivacyConsentEvent,
  PrivacyExportArtifact,
  PrivacyInventory,
  PrivacyPreferences,
  PrivacyProvider,
  PrivacyRequestRecord,
  PrivacyResearchSummary,
  PrivacySummary,
} from "../types/privacy";

type LoadState = "loading" | "ready" | "error";
type SensitiveAction = "export" | "download" | "delete-category" | "account-deletion" | "research-withdraw";

function Pill({ children, tone = "neutral" }: { children: string; tone?: "ok" | "warn" | "error" | "neutral" }) {
  const className =
    tone === "ok"
      ? "border-emerald-300/35 bg-emerald-500/10 text-emerald-100"
      : tone === "warn"
        ? "border-amber-300/40 bg-amber-500/12 text-amber-100"
        : tone === "error"
          ? "border-rose-300/40 bg-rose-500/12 text-rose-100"
          : "border-white/15 bg-white/[0.065] theme-text";
  return <span className={`inline-flex min-h-7 items-center rounded-full border px-2.5 text-xs font-bold ${className}`}>{children}</span>;
}

function Toggle({
  label,
  checked,
  onChange,
  disabled,
}: {
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled?: boolean;
}) {
  return (
    <label className="flex items-center justify-between gap-4 rounded-lg border border-white/10 bg-white/[0.045] p-3">
      <span className="text-sm font-semibold theme-text">{label}</span>
      <input
        type="checkbox"
        checked={checked}
        disabled={disabled}
        onChange={(event) => onChange(event.target.checked)}
        className="h-5 w-5 accent-teal-300"
      />
    </label>
  );
}

function SegmentedMode({
  value,
  onChange,
  disabled,
  label,
}: {
  value: "account-history" | "ephemeral";
  onChange: (value: "account-history" | "ephemeral") => void;
  disabled?: boolean;
  label: string;
}) {
  return (
    <div className="rounded-lg border border-white/10 bg-white/[0.045] p-3">
      <p className="mb-2 text-sm font-semibold theme-text">{label}</p>
      <div className="grid grid-cols-2 gap-2">
        {(["account-history", "ephemeral"] as const).map((mode) => (
          <button
            key={mode}
            type="button"
            disabled={disabled}
            onClick={() => onChange(mode)}
            className={
              value === mode
                ? "min-h-10 rounded-lg bg-teal-300 px-3 text-sm font-black text-slate-950"
                : "min-h-10 rounded-lg border border-white/15 px-3 text-sm font-bold theme-text hover:bg-white/10"
            }
          >
            {mode === "account-history" ? "Account history" : "Ephemeral"}
          </button>
        ))}
      </div>
    </div>
  );
}

function categoryTone(category: PersonalDataCategory) {
  if (category.sensitivity.includes("special") || category.sensitivity.includes("security")) return "warn";
  if (category.deletion_behavior.includes("delete")) return "ok";
  return "neutral";
}

export function PrivacyCenterPage() {
  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [summary, setSummary] = useState<PrivacySummary | null>(null);
  const [preferences, setPreferences] = useState<PrivacyPreferences | null>(null);
  const [inventory, setInventory] = useState<PrivacyInventory | null>(null);
  const [providers, setProviders] = useState<PrivacyProvider[]>([]);
  const [research, setResearch] = useState<PrivacyResearchSummary | null>(null);
  const [exports, setExports] = useState<PrivacyExportArtifact[]>([]);
  const [requests, setRequests] = useState<PrivacyRequestRecord[]>([]);
  const [consents, setConsents] = useState<PrivacyConsentEvent[]>([]);
  const [preview, setPreview] = useState<CategoryDeletionPreview | null>(null);
  const [selectedCategory, setSelectedCategory] = useState("conversation-history");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState("");
  const [reauthPassword, setReauthPassword] = useState("");
  const [pendingAction, setPendingAction] = useState<{ action: SensitiveAction; artifactId?: string } | null>(null);

  const accountDeletionRequest = useMemo(() => requests.find((request) => request.type === "account-deletion" && request.status === "queued"), [requests]);
  const categories = inventory?.categories ?? [];

  async function load() {
    setLoadState("loading");
    setError("");
    try {
      const [nextSummary, nextPreferences, nextInventory, nextProviders, nextResearch, nextExports, nextRequests, nextConsents] = await Promise.all([
        getPrivacySummary(),
        getPrivacyPreferences(),
        getPrivacyInventory(),
        getPrivacyProviders(),
        getPrivacyResearch(),
        getPrivacyExports(),
        getPrivacyRequests(),
        getPrivacyConsents(),
      ]);
      setSummary(nextSummary);
      setPreferences(nextPreferences);
      setInventory(nextInventory);
      setProviders(nextProviders);
      setResearch(nextResearch);
      setExports(nextExports);
      setRequests(nextRequests);
      setConsents(nextConsents);
      setLoadState("ready");
    } catch (loadError) {
      const apiError = extractApiError(loadError);
      setError(apiError.requestId ? `${apiError.message} Request ID: ${apiError.requestId}` : apiError.message);
      setLoadState("error");
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function savePreference(payload: Partial<PrivacyPreferences>) {
    if (!preferences) return;
    setBusy("preferences");
    setMessage("");
    setError("");
    const previous = preferences;
    setPreferences({ ...preferences, ...payload });
    try {
      const updated = await updatePrivacyPreferences(payload);
      setPreferences(updated);
      publishPrivacyPreferences(updated);
      setMessage("Privacy preferences saved.");
      await Promise.all([getPrivacyConsents().then(setConsents), getPrivacyResearch().then(setResearch)]);
    } catch (saveError) {
      setPreferences(previous);
      const apiError = extractApiError(saveError);
      setError(apiError.requestId ? `${apiError.message} Request ID: ${apiError.requestId}` : apiError.message);
    } finally {
      setBusy("");
    }
  }

  async function runSensitiveAction() {
    if (!pendingAction) return;
    setBusy(pendingAction.action);
    setMessage("");
    setError("");
    try {
      if (reauthPassword) await reauthenticatePrivacy(reauthPassword);
      if (pendingAction.action === "export") {
        const artifact = await createPrivacyExport();
        setMessage("Personal data export generated.");
        setExports((current) => [artifact, ...current]);
      }
      if (pendingAction.action === "download" && pendingAction.artifactId) {
        const blob = await downloadPrivacyExport(pendingAction.artifactId);
        const url = URL.createObjectURL(blob);
        const anchor = document.createElement("a");
        anchor.href = url;
        anchor.download = "organicai-personal-data.zip.enc";
        anchor.click();
        URL.revokeObjectURL(url);
        setMessage("Export download started.");
      }
      if (pendingAction.action === "delete-category") {
        const result = await deletePrivacyCategory(selectedCategory);
        setMessage(`Deleted category ${result.categoryKey}.`);
        setPreview(null);
      }
      if (pendingAction.action === "account-deletion") {
        const request = await requestAccountDeletion();
        setMessage(`Account deletion queued until ${new Date(request.graceUntil).toLocaleString()}.`);
      }
      if (pendingAction.action === "research-withdraw") {
        await withdrawResearchParticipation();
        setMessage("Research participation withdrawn.");
      }
      setPendingAction(null);
      setReauthPassword("");
      await load();
    } catch (actionError) {
      const apiError = extractApiError(actionError);
      if (apiError.message === "RECENT_AUTH_REQUIRED" || apiError.code === "RECENT_AUTH_REQUIRED") {
        setError("Recent authentication is required for this action.");
      } else {
        setError(apiError.requestId ? `${apiError.message} Request ID: ${apiError.requestId}` : apiError.message);
      }
    } finally {
      setBusy("");
    }
  }

  async function loadPreview(categoryKey = selectedCategory) {
    setBusy("preview");
    setError("");
    try {
      setSelectedCategory(categoryKey);
      setPreview(await previewCategoryDeletion(categoryKey));
    } catch (previewError) {
      const apiError = extractApiError(previewError);
      setError(apiError.requestId ? `${apiError.message} Request ID: ${apiError.requestId}` : apiError.message);
    } finally {
      setBusy("");
    }
  }

  async function removeExport(artifactId: string) {
    setBusy(`delete-export-${artifactId}`);
    setError("");
    try {
      await deletePrivacyExport(artifactId);
      setExports((current) => current.filter((artifact) => artifact.id !== artifactId));
      setMessage("Export artifact removed.");
    } catch (removeError) {
      const apiError = extractApiError(removeError);
      setError(apiError.requestId ? `${apiError.message} Request ID: ${apiError.requestId}` : apiError.message);
    } finally {
      setBusy("");
    }
  }

  async function cancelDeletion() {
    if (!accountDeletionRequest) return;
    setBusy("cancel-account-deletion");
    setError("");
    try {
      await cancelAccountDeletion(accountDeletionRequest.id);
      setMessage("Account deletion cancelled.");
      await getPrivacyRequests().then(setRequests);
    } catch (cancelError) {
      const apiError = extractApiError(cancelError);
      setError(apiError.requestId ? `${apiError.message} Request ID: ${apiError.requestId}` : apiError.message);
    } finally {
      setBusy("");
    }
  }

  return (
    <section className="mx-auto w-full max-w-7xl py-8">
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.18em] text-teal-200">Privacy Center</p>
          <h1 className="mt-2 font-display text-4xl font-semibold theme-text">Data controls</h1>
          <p className="mt-2 max-w-3xl text-sm leading-6 theme-muted">
            Technical draft - requires legal review before public deployment.
          </p>
        </div>
        <button type="button" onClick={() => void load()} className="inline-flex min-h-10 items-center gap-2 rounded-lg border border-white/15 px-3 text-sm font-bold theme-text hover:bg-white/10">
          <RefreshCw size={16} />
          Refresh
        </button>
      </div>

      {error ? (
        <div role="alert" className="mb-5 flex items-start gap-3 rounded-lg border border-rose-300/35 bg-rose-500/12 p-4 text-rose-100">
          <AlertTriangle className="mt-0.5 shrink-0" size={18} />
          <span>{error}</span>
        </div>
      ) : null}
      {message ? (
        <div role="status" className="mb-5 flex items-center gap-3 rounded-lg border border-emerald-300/30 bg-emerald-500/10 p-4 text-emerald-100">
          <CheckCircle2 size={18} />
          <span>{message}</span>
        </div>
      ) : null}

      {loadState === "loading" ? <p className="rounded-lg border border-white/12 bg-white/[0.055] p-4 theme-muted">Loading privacy controls.</p> : null}

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_380px]">
        <div className="space-y-5">
          <div className="rounded-lg border border-white/12 bg-slate-950/45 p-5 shadow-xl theme-card">
            <div className="mb-4 flex items-center gap-3">
              <ShieldCheck className="text-teal-200" size={22} />
              <h2 className="text-xl font-bold theme-text">Preferences</h2>
            </div>
            {preferences ? (
              <div className="grid gap-3 lg:grid-cols-2">
                <SegmentedMode value={preferences.conversationPersistenceMode} disabled={busy === "preferences"} label="Coach conversation transcript" onChange={(value) => void savePreference({ conversationPersistenceMode: value })} />
                <SegmentedMode value={preferences.voiceTranscriptPersistenceMode} disabled={busy === "preferences"} label="Live voice transcript" onChange={(value) => void savePreference({ voiceTranscriptPersistenceMode: value })} />
                <Toggle label="Product analytics" checked={preferences.productAnalyticsEnabled} disabled={busy === "preferences"} onChange={(checked) => void savePreference({ productAnalyticsEnabled: checked })} />
                <Toggle label="Research participation" checked={preferences.researchParticipationEnabled} disabled={busy === "preferences"} onChange={(checked) => void savePreference({ researchParticipationEnabled: checked })} />
                <Toggle label="Personalization" checked={preferences.personalizationEnabled} disabled={busy === "preferences"} onChange={(checked) => void savePreference({ personalizationEnabled: checked })} />
                <Toggle label="Service email" checked={preferences.serviceEmailEnabled} disabled={busy === "preferences"} onChange={(checked) => void savePreference({ serviceEmailEnabled: checked })} />
                <Toggle label="Marketing email" checked={preferences.marketingEmailEnabled} disabled={busy === "preferences"} onChange={(checked) => void savePreference({ marketingEmailEnabled: checked })} />
                <div className="rounded-lg border border-white/10 bg-white/[0.045] p-3">
                  <p className="text-sm font-semibold theme-text">Voice audio storage</p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    <Pill tone="ok">Disabled</Pill>
                    <Pill>Not offered</Pill>
                  </div>
                </div>
              </div>
            ) : null}
          </div>

          <div className="grid gap-5 lg:grid-cols-2">
            <div className="rounded-lg border border-white/12 bg-slate-950/45 p-5 shadow-xl theme-card">
              <div className="mb-4 flex items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <FileArchive className="text-cyan-200" size={22} />
                  <h2 className="text-xl font-bold theme-text">Export</h2>
                </div>
                <button type="button" onClick={() => setPendingAction({ action: "export" })} className="inline-flex min-h-10 items-center gap-2 rounded-lg bg-teal-300 px-3 text-sm font-black text-slate-950">
                  <FileArchive size={16} />
                  Create
                </button>
              </div>
              <div className="space-y-2">
                {exports.map((artifact) => (
                  <div key={artifact.id} className="rounded-lg border border-white/10 bg-white/[0.045] p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div>
                        <p className="text-sm font-bold theme-text">{artifact.format} export</p>
                        <p className="text-xs theme-muted">Expires {new Date(artifact.expiresAt).toLocaleString()}</p>
                      </div>
                      <Pill tone={artifact.status === "ready" ? "ok" : "warn"}>{artifact.status}</Pill>
                    </div>
                    <div className="mt-3 flex flex-wrap gap-2">
                      <button type="button" onClick={() => setPendingAction({ action: "download", artifactId: artifact.id })} className="inline-flex min-h-9 items-center gap-2 rounded-lg border border-white/15 px-3 text-xs font-bold theme-text hover:bg-white/10">
                        <Download size={14} />
                        Download
                      </button>
                      <button type="button" onClick={() => void removeExport(artifact.id)} className="inline-flex min-h-9 items-center gap-2 rounded-lg border border-rose-300/40 px-3 text-xs font-bold text-rose-100 hover:bg-rose-500/10">
                        <Trash2 size={14} />
                        Delete
                      </button>
                    </div>
                  </div>
                ))}
                {exports.length === 0 ? <p className="text-sm theme-muted">No active exports.</p> : null}
              </div>
            </div>

            <div className="rounded-lg border border-white/12 bg-slate-950/45 p-5 shadow-xl theme-card">
              <div className="mb-4 flex items-center gap-3">
                <Trash2 className="text-rose-200" size={22} />
                <h2 className="text-xl font-bold theme-text">Deletion</h2>
              </div>
              <select value={selectedCategory} onChange={(event) => void loadPreview(event.target.value)} className="mb-3 w-full rounded-lg border border-white/15 bg-white/90 p-3 text-sm font-semibold text-slate-950">
                {categories.map((category) => (
                  <option key={category.key} value={category.key}>{category.title}</option>
                ))}
              </select>
              <div className="flex flex-wrap gap-2">
                <button type="button" onClick={() => void loadPreview()} className="inline-flex min-h-10 items-center gap-2 rounded-lg border border-white/15 px-3 text-sm font-bold theme-text hover:bg-white/10">
                  <Eye size={16} />
                  Preview
                </button>
                <button type="button" disabled={!preview} onClick={() => setPendingAction({ action: "delete-category" })} className="inline-flex min-h-10 items-center gap-2 rounded-lg border border-rose-300/40 px-3 text-sm font-bold text-rose-100 disabled:cursor-not-allowed disabled:opacity-50 hover:bg-rose-500/10">
                  <Trash2 size={16} />
                  Delete category
                </button>
              </div>
              {preview ? (
                <div className="mt-4 rounded-lg border border-white/10 bg-white/[0.045] p-3">
                  <p className="text-sm font-bold theme-text">{preview.category.title}</p>
                  <p className="mt-1 text-xs leading-5 theme-muted">{preview.providerImpact}</p>
                  <div className="mt-3 grid gap-2">
                    {Object.entries(preview.rowCounts).map(([table, count]) => (
                      <div key={table} className="flex items-center justify-between gap-3 text-sm">
                        <span className="theme-muted">{table}</span>
                        <span className="font-bold theme-text">{count}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}
            </div>
          </div>

          <div className="rounded-lg border border-white/12 bg-slate-950/45 p-5 shadow-xl theme-card">
            <div className="mb-4 flex items-center gap-3">
              <Database className="text-teal-200" size={22} />
              <h2 className="text-xl font-bold theme-text">Data Inventory</h2>
            </div>
            <div className="grid gap-3 md:grid-cols-2">
              {categories.map((category) => (
                <article key={category.key} className="rounded-lg border border-white/10 bg-white/[0.045] p-4">
                  <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                    <h3 className="text-sm font-black theme-text">{category.title}</h3>
                    <Pill tone={categoryTone(category)}>{category.sensitivity}</Pill>
                  </div>
                  <p className="text-xs leading-5 theme-muted">{category.description}</p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    <Pill>{category.export_behavior}</Pill>
                    <Pill>{category.deletion_behavior}</Pill>
                  </div>
                </article>
              ))}
            </div>
          </div>
        </div>

        <aside className="space-y-5">
          <div className="rounded-lg border border-white/12 bg-white/[0.055] p-5 shadow-xl theme-card">
            <h2 className="text-lg font-bold theme-text">Overview</h2>
            <div className="mt-3 grid gap-2">
              <Pill tone={summary?.policy.legalReviewRequired ? "warn" : "ok"}>{summary?.policy.version ?? "Policy loading"}</Pill>
              <Pill>{`${summary?.categoryCount ?? 0} categories`}</Pill>
              <Pill>{`${summary?.providerCount ?? 0} providers`}</Pill>
              <Pill>{`${inventory?.tableCount ?? 0} inventoried tables`}</Pill>
            </div>
            <p className="mt-4 text-xs leading-5 theme-muted">{summary?.backupDisclosure}</p>
            <p className="mt-3 text-xs leading-5 theme-muted">{summary?.legacyOrphanArchive}</p>
          </div>

          <div className="rounded-lg border border-white/12 bg-white/[0.055] p-5 shadow-xl theme-card">
            <div className="mb-3 flex items-center justify-between gap-2">
              <h2 className="text-lg font-bold theme-text">Research</h2>
              <Pill tone={research?.participationEnabled ? "ok" : "neutral"}>{research?.participationEnabled ? "Enabled" : "Disabled"}</Pill>
            </div>
            <p className="text-xs leading-5 theme-muted">Ephemeral conversations are excluded from research collection. Direct identifiers are not included in the pseudonymous research subject ID.</p>
            <button type="button" disabled={!research?.withdrawalAvailable} onClick={() => setPendingAction({ action: "research-withdraw" })} className="mt-4 inline-flex min-h-10 items-center gap-2 rounded-lg border border-white/15 px-3 text-sm font-bold theme-text disabled:cursor-not-allowed disabled:opacity-50 hover:bg-white/10">
              <UserX size={16} />
              Withdraw
            </button>
          </div>

          <div className="rounded-lg border border-white/12 bg-white/[0.055] p-5 shadow-xl theme-card">
            <h2 className="text-lg font-bold theme-text">Providers</h2>
            <div className="mt-3 space-y-3">
              {providers.map((provider) => (
                <div key={provider.provider} className="rounded-lg border border-white/10 bg-black/15 p-3">
                  <p className="text-sm font-bold theme-text">{provider.provider}</p>
                  <p className="mt-1 text-xs leading-5 theme-muted">{provider.purpose}</p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {provider.connectivity ? <Pill>{provider.connectivity}</Pill> : null}
                    <Pill>{provider.retentionStatus}</Pill>
                    <Pill>{provider.deletionCapability}</Pill>
                    {provider.provider === "OpenAI" && provider.trainingOptInStatus ? <Pill>{`training: ${provider.trainingOptInStatus}`}</Pill> : null}
                    {provider.provider === "OpenAI" && provider.abuseMonitoringMode ? <Pill>{`abuse: ${provider.abuseMonitoringMode}`}</Pill> : null}
                    {provider.provider === "OpenAI" && provider.dataResidencyStatus ? <Pill>{`residency: ${provider.dataResidencyStatus}`}</Pill> : null}
                    {provider.provider === "OpenAI" ? <Pill tone={provider.dataControlsVerified ? "ok" : "warn"}>{provider.dataControlsVerified ? "data controls verified" : "data controls not verified"}</Pill> : null}
                    {provider.audioSavingStatus ? <Pill>{`audio: ${provider.audioSavingStatus}`}</Pill> : null}
                    {provider.zeroRetentionStatus ? <Pill>{`zero retention: ${provider.zeroRetentionStatus}`}</Pill> : null}
                    {provider.webhookSignatureStatus ? <Pill>{`webhook HMAC: ${provider.webhookSignatureStatus}`}</Pill> : null}
                    {provider.deliveryDriver ? <Pill>{`driver: ${provider.deliveryDriver}`}</Pill> : null}
                    {provider.deliveryTrackingStatus ? <Pill>{provider.deliveryTrackingStatus}</Pill> : null}
                    <Pill tone={provider.transferReviewStatus.includes("required") ? "warn" : "ok"}>{provider.transferReviewStatus}</Pill>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-lg border border-rose-300/25 bg-rose-500/10 p-5 shadow-xl">
            <h2 className="text-lg font-bold text-rose-50">Account Deletion</h2>
            {accountDeletionRequest ? (
              <div className="mt-3">
                <Pill tone="warn">Queued</Pill>
                <p className="mt-3 text-sm leading-6 text-rose-50">Request submitted {new Date(accountDeletionRequest.submittedAt).toLocaleString()}.</p>
                <button type="button" onClick={() => void cancelDeletion()} className="mt-3 inline-flex min-h-10 items-center gap-2 rounded-lg border border-white/20 px-3 text-sm font-bold text-white hover:bg-white/10">
                  Cancel deletion
                </button>
              </div>
            ) : (
              <button type="button" onClick={() => setPendingAction({ action: "account-deletion" })} className="mt-3 inline-flex min-h-10 items-center gap-2 rounded-lg border border-rose-200/60 px-3 text-sm font-bold text-rose-50 hover:bg-rose-500/20">
                <UserX size={16} />
                Request deletion
              </button>
            )}
          </div>

          <div className="rounded-lg border border-white/12 bg-white/[0.055] p-5 shadow-xl theme-card">
            <h2 className="text-lg font-bold theme-text">Activity</h2>
            <div className="mt-3 space-y-2">
              {consents.slice(0, 5).map((consent) => (
                <div key={consent.id} className="rounded-lg border border-white/10 bg-black/15 p-3 text-xs">
                  <p className="font-bold theme-text">{consent.purposeKey}: {consent.action}</p>
                  <p className="mt-1 theme-muted">{new Date(consent.occurredAt).toLocaleString()}</p>
                </div>
              ))}
              {consents.length === 0 ? <p className="text-sm theme-muted">No consent events yet.</p> : null}
            </div>
          </div>
        </aside>
      </div>

      {pendingAction ? (
        <div className="fixed inset-0 z-50 grid place-items-center bg-black/70 p-4">
          <form
            onSubmit={(event) => {
              event.preventDefault();
              void runSensitiveAction();
            }}
            className="w-full max-w-md rounded-lg border border-white/15 bg-slate-950 p-5 shadow-2xl"
          >
            <div className="mb-4 flex items-center gap-3">
              <KeyRound className="text-teal-200" size={22} />
              <h2 className="text-xl font-bold text-white">Confirm recent authentication</h2>
            </div>
            <input
              type="password"
              required
              value={reauthPassword}
              onChange={(event) => setReauthPassword(event.target.value)}
              placeholder="Password"
              className="w-full rounded-lg border border-white/15 bg-white p-3 text-sm text-slate-950 outline-none focus:ring-4 focus:ring-teal-300/40"
            />
            <div className="mt-4 flex flex-wrap justify-end gap-2">
              <button type="button" onClick={() => setPendingAction(null)} className="inline-flex min-h-10 items-center rounded-lg border border-white/15 px-3 text-sm font-bold text-white hover:bg-white/10">
                Cancel
              </button>
              <button type="submit" disabled={Boolean(busy)} className="inline-flex min-h-10 items-center gap-2 rounded-lg bg-teal-300 px-3 text-sm font-black text-slate-950 disabled:cursor-not-allowed disabled:opacity-50">
                <KeyRound size={16} />
                Continue
              </button>
            </div>
          </form>
        </div>
      ) : null}
    </section>
  );
}
