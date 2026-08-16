import { describe, expect, it } from "vitest";
import { sanitizedPersistenceSummary } from "./persistenceDiagnostics";
import type { PersistenceStatus } from "../types/persistence";

const status: PersistenceStatus = {
  driver: "postgresql",
  reachable: true,
  schemaVersion: "0001_initial_schema",
  headVersion: "0001_initial_schema",
  migrationState: "current",
  productionPostgresRequired: true,
  pool: { enabled: true, sizeConfigured: 5, prePing: true },
  backup: { directoryConfigured: true, latestBackupAvailable: true, retentionDays: 30 },
  integrity: { lastCheckStatus: "not_run" },
  releaseGate: {
    preActivationBackupVerified: true,
    rollbackFallbackAvailable: true,
    legacyOriginalPreserved: true,
    legacyOrphanArchiveVerified: true,
    legacyDataLoss: 0,
    originalDatabaseRole: "immutable evidence",
  },
  requestId: "request-1",
};

describe("persistence diagnostics", () => {
  it("builds a sanitized diagnostic summary", () => {
    const summary = sanitizedPersistenceSummary(status);
    expect(summary).toContain("Database driver: postgresql");
    expect(summary).toContain("Schema revision: 0001_initial_schema");
    expect(summary).toContain("Legacy remediation simulation: passed");
    expect(summary).toContain("Legacy orphan archive: verified");
    expect(summary).toContain("Legacy original database: preserved");
    expect(summary).toContain("Archived orphan messages: 156");
    expect(summary).toContain("Legacy data loss: 0");
    expect(summary).toContain("Active persistence: PostgreSQL");
    expect(summary).not.toContain("DATABASE_URL");
    expect(summary).not.toContain("password");
    expect(summary).not.toContain("postgresql://");
    expect(summary).not.toContain("organicai-orphan-messages");
  });
});
