# Cloud Staging Architecture Options

Technical draft - requires provider and budget approval before provisioning.

## Option A - Single Virtual Machine with Docker Compose

Components: cloud VM, Docker Compose, managed PostgreSQL or isolated database container, Nginx, backend, frontend, worker and observability.

Advantages:

- Closest to validated local staging.
- Lowest architectural change.
- Simple thesis demonstration.
- Full control.
- Straightforward migration from the current Compose stack.

Limitations:

- More operating-system responsibility.
- Manual patching.
- Manual scaling.
- Monitoring and backup require explicit configuration.

## Option B - Managed Container Platform

Components: managed container applications, managed PostgreSQL, managed ingress, managed secrets, container registry and managed logs/metrics.

Advantages:

- Better managed operations.
- Cleaner secret handling.
- Easier health checks and rolling deployments.
- Better path to OIDC and protected environments.

Limitations:

- More provider-specific configuration.
- Higher learning curve.
- May require adapting Compose assumptions.
- Cost depends on provider defaults and idle resources.

## Option C - Kubernetes or Managed Kubernetes

Components: cluster, ingress controller, managed PostgreSQL, secrets, deployments, jobs, services and observability stack.

Advantages:

- Strong deployment primitives.
- Good separation of services.
- Scales to larger operational requirements.
- Rich ecosystem for observability and policy.

Limitations:

- Operationally heavy for a thesis staging environment.
- More expensive and complex.
- Requires Kubernetes-specific manifests and cluster security expertise.

## Provisional Recommendation

A small European-region cloud virtual machine or managed container host, combined with managed PostgreSQL where practical.

This is provisional and prioritizes compatibility with the existing Docker Compose staging environment, minimal architecture changes, private PostgreSQL, HTTPS, simple rollback, reasonable thesis-project cost, reproducibility and future migration to a more managed platform.
