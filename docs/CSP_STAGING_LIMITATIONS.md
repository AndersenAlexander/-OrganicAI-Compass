# CSP Staging Limitations

Status: staging limitation documented. Production CSP readiness is not claimed.

The current backend security middleware sends CSP in report-only mode and keeps these staging exceptions:

- `script-src 'unsafe-inline'`
- `script-src 'unsafe-eval'`
- `style-src 'unsafe-inline'`

## Dependency Inventory

| Exception | Current dependency | Reason it remains in staging |
| --- | --- | --- |
| `script-src 'unsafe-inline'` | Vite development/runtime scripts and route-level frontend bootstrapping during local staging validation | Removing it before nonce/hash wiring can break local validation and frontend boot. |
| `script-src 'unsafe-eval'` | Three.js / React Three Fiber development paths and bundled tooling that may use eval-like transforms in non-production validation | Must be validated against 3D scenes and voice UI before removal. |
| `style-src 'unsafe-inline'` | Tailwind utility runtime output, component inline styles, React-driven dynamic layout styles, and third-party UI integrations | Needs nonce/hash or extraction plan before production enforcement. |

## Production Hardening Plan

1. Add request-scoped CSP nonces in backend middleware and pass them to the frontend document shell.
2. Replace inline scripts with nonce-bearing scripts or hashed static snippets.
3. Build a hash inventory for any unavoidable static inline bootstrap.
4. Validate Three.js, React Three Fiber, and ElevenLabs UI paths with `unsafe-eval` removed.
5. Move from report-only to enforced CSP only after desktop and mobile smoke tests pass.
6. Keep SMTP, OpenAI, and ElevenLabs provider validation separate from CSP hardening; CSP validation must not call live providers.

Production CSP readiness remains blocked until the exceptions are removed or justified by validated nonces, hashes, and external script allowlists.
