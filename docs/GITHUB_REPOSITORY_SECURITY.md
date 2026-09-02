# GitHub Repository Security

Status: manual-action-required until verified in GitHub.

Recommended baseline:

- Private initial visibility.
- Two-factor authentication for maintainers.
- Branch protection for `main`.
- Required pull requests.
- Required CI status checks.
- No force pushes to `main`.
- No branch deletion for `main`.
- Secret scanning where available.
- Dependency alerts and Dependabot alerts.
- Workflow permissions read-only by default.
- Protected environments for staging and production.
- No long-lived cloud credentials.
- OIDC for future cloud deployment identity.
- Required review for workflow, migration, deploy and secret-management changes.
