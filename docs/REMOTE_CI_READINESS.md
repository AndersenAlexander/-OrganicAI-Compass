# Remote CI Readiness

Status: workflow definitions hardened locally; remote execution remains `EXTERNAL MANUAL ACTION REQUIRED`.

Workflow:

- `.github/workflows/ci.yml`

Coverage:

- backend compile and non-PostgreSQL tests;
- disposable PostgreSQL service, migration preflight and marker tests;
- frontend unit tests;
- TypeScript typecheck;
- production build;
- Playwright mock/local E2E suite;
- source archive generation and archive regression tests;
- security/privacy/secret audits;
- dependency reporting;
- container image builds.

CI safety rules:

- dummy test credentials only;
- no developer `.env` dependency;
- real-provider tests disabled by default;
- external provider acceptance not mandatory for pull requests;
- sanitized artifacts only;
- no secret echoing;
- dependency vulnerability reports are uploaded as review artifacts.

Local syntax/readiness validation:

```powershell
cd backend
.\.venv\Scripts\python.exe -m app.scripts.validate_ci_workflows
```

Remote production acceptance requires a private repository, repository owner approval, remote run URL and sanitized artifact review.
