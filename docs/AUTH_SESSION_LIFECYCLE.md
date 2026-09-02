# Auth Session Lifecycle

Date: 2026-07-27

Login and registration create an `auth_sessions` row, store only the refresh-token hash, return a short-lived access token, and set an opaque refresh token in an HttpOnly cookie.

Refresh reads the cookie, hashes the presented token, finds the active session, revokes it as rotated, creates a replacement session in the same token family, and sets a new cookie. If a rotated or revoked token is presented again, the full token family is revoked.

Logout revokes the server-side session associated with the refresh cookie and clears the cookie. Repeated logout is safe.

Password change and reset increment `auth_version` and revoke other active sessions, invalidating old access tokens.

