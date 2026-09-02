# Task 15C - Profile, Demo Mode and Browser Extension Integration

## Normal Profile Resolution

Normal authenticated profile resolution now uses one frontend source of truth:

1. `AuthContext` establishes authenticated, demo, loading, or anonymous state.
2. `AppActionsContext` reads route profile IDs with `profileIdFromPath`.
3. For non-demo users, `AppActionsContext` calls `GET /profiles` through `listProfiles`.
4. `selectOwnedProfileId` chooses the route ID only when it is owned, otherwise the stored ID only when it is owned, otherwise the first owned profile, otherwise no profile.
5. Consumers read `activeProfileId` from `useAppActions`.

The frontend profile ID remains UX state only. Backend routes still enforce ownership with `require_owned_profile` / `require_profile` before profile-specific reads and writes.

## Explicit Profile Context States

The frontend profile resolver exposes these states:

- `loading`
- `anonymous-public`
- `authenticated-no-profile`
- `authenticated-owned-profile`
- `explicit-demo`
- `profile-error`

Normal users without an owned profile remain in `authenticated-no-profile` and workspace routes render a profile-required state or route back to Natural Discovery. They no longer receive `demo-profile` as a silent fallback.

## Explicit Demo Mode

Demo Mode remains entered deliberately through the login page demo action. Demo users are marked by auth state (`is_demo`) and only that explicit context may resolve to `demo-profile` when no route or stored demo profile is present.

The global header shows a visible `Demo Mode` pill and changes logout text to `Exit Demo`. This keeps synthetic data distinguishable without changing the broader UI.

## Demo Isolation and Reset

Demo records continue to use the existing demo seed model and `DEMO_PROFILE_ID`. Demo reset remains deterministic and scoped to demo data. Task 15C did not add migrations or broaden reset behavior.

## No-Profile Handling

Profile-required workspace surfaces no longer invent a demo profile. They either:

- stop loading profile-specific data until a profile ID exists; or
- show `ProfileRequiredState` with a Natural Discovery link; or
- navigate profile-aware commands to `/diagnostic` when no profile is active.

Navigation now generates workspace links from the resolved profile ID. When no profile exists, it keeps only safe destinations such as Dashboard, Natural Discovery, Knowledge Base, Privacy Center, and Settings.

Public pages with profile-aware calls to action now also read `activeProfileId` from `AppActionsContext` instead of direct localStorage helpers. If no resolved profile exists, those calls to action lead to Natural Discovery.

## Session Switch Handling

`AuthContext` removes `organicai_active_profile_id` before normal login and registration. Logout dispatches the existing `organicai:auth-cleared` event. `AppActionsContext` listens for that event and cross-tab storage changes, clears the active profile, and revalidates stored profile IDs after auth changes by querying `/profiles`.

This prevents stale demo IDs or another user's profile ID from becoming trusted frontend context after account switches.

## Browser Extension Authentication Model

The browser extension uses a short-lived server-issued connection token. The token is:

- stored as a hash server-side;
- bound to one user;
- bound to one profile;
- scoped to browser job capture;
- naturally expiring;
- revocable through the existing connection status;
- validated before capture writes.

The extension popup still requires the user to provide the OrganicAI backend URL, connection token, and owned profile ID. It no longer defaults a missing profile ID to `demo-profile`.

## Token Validation Order

For `POST /profiles/{profile_id}/job-captures`:

1. If `X-OrganicAI-Extension-Token` is present, validate the token hash first.
2. Verify the token profile matches the route profile.
3. If a bearer session is also present, verify the token owner matches the current user.
4. Verify connection status is active.
5. Expire and reject expired connections.
6. Load the bound profile.
7. Verify token owner matches profile owner.
8. Write the capture only to the bound profile.

Without an extension token, the route falls back to ordinary authenticated profile ownership checks.

## Extension Ownership Enforcement

The backend rejects:

- no token and no authenticated session;
- invalid token;
- expired token;
- token used with a different route profile;
- token used with `demo-profile` unless the token is actually bound to that profile;
- token used by a different authenticated user.

The popup maps rejection categories to user-safe messages and does not display raw backend internals.

## Remaining Limitations

- The browser extension still requires manual entry of the profile ID and token; there is no automatic in-app pairing workflow in this task.
- There is no browser-extension Playwright harness. The token contract is covered by backend tests and the extension popup TypeScript build.
- Git metadata is still unavailable in this working copy and was not repaired because that belongs to Task 15D.
