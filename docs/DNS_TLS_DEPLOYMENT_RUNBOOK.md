# DNS/TLS Deployment Runbook

Status: deployment-neutral runbook. Final domains are not selected.

Placeholders:

- frontend: `app.example.com`
- API: `api.example.com`
- optional provider callback: `api.example.com/api/webhooks/...`

Steps:

1. Approve final hostnames, owner and rollback TTL.
2. Create DNS records for frontend and API endpoints.
3. Issue trusted TLS certificates for every public hostname.
4. Verify HTTPS `/health` and `/health/ready`.
5. Configure HTTP to HTTPS redirect.
6. Set production `FRONTEND_PUBLIC_URL`, `PUBLIC_BACKEND_URL`, `ALLOWED_ORIGINS`, `ALLOWED_HOSTS`.
7. Enable secure cookies.
8. Move CSP from report-only to enforcement after report review.
9. Verify WebSocket/SSE/proxy behavior for live voice paths if enabled.
10. Verify ElevenLabs callback/webhook public reachability if enabled.
11. Enable HSTS only after TLS and rollback window are accepted.

Rollback:

- keep DNS TTL low before cutover;
- restore previous DNS target;
- restore previous certificate route;
- disable HSTS if it was not yet preloaded/permanent;
- disable live provider callbacks if callback routing fails.

Local staging must not permanently enable HSTS.
