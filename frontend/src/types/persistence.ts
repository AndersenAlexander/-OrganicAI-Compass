export type PersistenceStatus = {
  driver: string;
  reachable: boolean;
  schemaVersion: string | null;
  headVersion: string | null;
  migrationState: "current" | "behind" | "missing" | "multiple_heads" | "unreachable" | "unknown" | "not_required" | string;
  productionPostgresRequired: boolean;
  pool: {
    enabled: boolean;
    sizeConfigured: number | null;
    prePing: boolean;
  };
  backup: {
    directoryConfigured: boolean;
    latestBackupAvailable: boolean;
    retentionDays: number;
  };
  integrity: {
    lastCheckStatus: "not_run" | "passed" | "failed" | string;
  };
  releaseGate?: {
    preActivationBackupVerified: boolean;
    rollbackFallbackAvailable: boolean;
    legacyOriginalPreserved: boolean;
    legacyOrphanArchiveVerified: boolean;
    legacyDataLoss: number | null;
    originalDatabaseRole: string;
  };
  requestId: string;
};
