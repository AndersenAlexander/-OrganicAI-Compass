# ADR-001: Cloud Staging Provider

Status: Not selected.

## Context

Task 13B.0 prepares cloud staging but does not provision resources. The project has validated local Docker Compose staging with PostgreSQL, reverse proxy, backend, frontend, worker and observability.

## Decision

No provider is selected in Task 13B.0.

## Options

- Single VM with Docker Compose.
- Managed container platform with managed PostgreSQL.
- Kubernetes or managed Kubernetes.

## Provisional Recommendation

Use a small European-region cloud virtual machine or managed container host with managed PostgreSQL where practical. This remains provisional until the user approves provider, region, budget, staging hostname and architecture.

## Consequences

- Task 13B.1 remains blocked.
- No cloud resources are created.
- Provider-specific infrastructure files are deferred.
