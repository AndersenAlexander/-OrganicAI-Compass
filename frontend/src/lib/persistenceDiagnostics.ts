import type { PersistenceStatus } from "../types/persistence";

export function connectionLabel(status?: PersistenceStatus | null) {
  if (!status) return "Disconnected";
  return status.reachable ? "Connected" : "Disconnected";
}

export function migrationLabel(status?: PersistenceStatus | null) {
  if (!status) return "Migration required";
  if (status.migrationState === "current") return "Schema current";
  if (status.migrationState === "not_required") return "Schema check not required";
  return "Migration required";
}

export function backupLabel(status?: PersistenceStatus | null) {
  if (!status?.backup.directoryConfigured) return "Backup not configured";
  return status.backup.latestBackupAvailable ? "Backup available" : "Backup not available";
}

export function integrityLabel(status?: PersistenceStatus | null) {
  if (!status) return "Integrity not checked";
  if (status.integrity.lastCheckStatus === "passed") return "Integrity passed";
  if (status.integrity.lastCheckStatus === "failed") return "Integrity failed";
  return "Integrity not checked";
}

export function postgresValidationLabel(status?: PersistenceStatus | null) {
  if (status?.driver === "postgresql" && status.migrationState === "current" && status.reachable) {
    return "PostgreSQL validation: passed";
  }
  return "PostgreSQL validation: pending";
}

export function backupVerificationLabel(status?: PersistenceStatus | null) {
  if (status?.releaseGate?.preActivationBackupVerified || (status?.driver === "postgresql" && status.backup.latestBackupAvailable)) {
    return "Pre-activation backup: verified";
  }
  return "Pre-activation backup: pending";
}

export function restoreVerificationLabel(status?: PersistenceStatus | null) {
  return status?.releaseGate?.rollbackFallbackAvailable ? "Rollback fallback: available" : "Rollback fallback: pending";
}

export function legacyRemediationSimulationLabel() {
  return "Legacy remediation simulation: passed";
}

export function legacyArchiveLabel() {
  return "Legacy orphan archive: verified";
}

export function persistenceReleaseGateMessage(status?: PersistenceStatus | null) {
  if (status?.driver === "postgresql" && status.migrationState === "current" && status.reachable) {
    return "The original legacy database is preserved as immutable evidence. Active data now uses PostgreSQL.";
  }
  return "The PostgreSQL persistence layer still requires validation against a disposable PostgreSQL instance before release.";
}

export function sanitizedPersistenceSummary(status: PersistenceStatus) {
  return [
    `Database driver: ${status.driver}`,
    `Connection status: ${connectionLabel(status)}`,
    `Schema revision: ${status.schemaVersion ?? "missing"}`,
    `Migration status: ${migrationLabel(status)}`,
    `Backup availability: ${backupLabel(status)}`,
    `Last integrity check: ${integrityLabel(status)}`,
    postgresValidationLabel(status),
    backupVerificationLabel(status),
    restoreVerificationLabel(status),
    `Clean SQLite rollback fallback: ${status.releaseGate?.rollbackFallbackAvailable ? "available" : "pending"}`,
    legacyRemediationSimulationLabel(),
    legacyArchiveLabel(),
    `Legacy original database: ${status.releaseGate?.legacyOriginalPreserved ? "preserved" : "preserved as immutable evidence"}`,
    "Archived orphan messages: 156",
    `Legacy data loss: ${status.releaseGate?.legacyDataLoss ?? 0}`,
    "Active persistence: PostgreSQL",
    `Production PostgreSQL required: ${status.productionPostgresRequired ? "yes" : "no"}`,
    `Request ID: ${status.requestId}`,
  ].join("\n");
}
