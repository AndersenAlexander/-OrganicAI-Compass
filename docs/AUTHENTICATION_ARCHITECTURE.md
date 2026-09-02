# Authentication Architecture

Date: 2026-07-27

Task 12A replaces persistent browser JWT storage with server-managed sessions.

## Token Model

- Access token: short-lived JWT, default `15` minutes.
- Access token claims: `type=access`, `sub`, `sid`, `ver`, `jti`, `iat`, `exp`.
- Access token storage: frontend memory only.
- Refresh token: opaque random token stored only in an HttpOnly cookie.
- Refresh token database storage: HMAC-SHA256 hash only.
- Refresh behavior: rotate on every successful refresh.
- Reuse detection: presenting a rotated or revoked refresh token revokes the token family.

## Passwords

New passwords use Argon2id through `argon2-cffi`. Existing bcrypt hashes remain valid and are upgraded after successful login.

Password policy: minimum `12` characters, Unicode and spaces allowed, no mandatory composition rule, not equal to normalized email, and not equal to the configured demo password for normal users.

## Account Status

Users have `account_status`, `auth_version`, verification, lockout, and password-change metadata. Disabled and pending-deletion accounts are rejected. Unverified users may use core local features unless `AUTH_REQUIRE_VERIFIED_EMAIL=true` is enabled.
# Task 12B Privacy Sensitive Actions

Technical draft - requires legal review before public deployment.

Privacy export creation/download, category deletion, research withdrawal, and account deletion require recent authentication through `/api/privacy/reauthenticate`. The dependency checks the current `auth_sessions.last_used_at` timestamp and returns `RECENT_AUTH_REQUIRED` when the active session is stale.

