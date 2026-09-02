# API Authorization Matrix

Date: 2026-08-09

| Area | Classification | Authentication | Authorization Rule | Tests |
| --- | --- | --- | --- | --- |
| `/api/auth/register`, `/api/auth/login`, `/api/auth/forgot-password`, `/api/auth/reset-password`, `/api/auth/verify-email` | public auth ceremony | none or cookie depending on operation | origin check for cookie-sensitive operations; generic recovery responses | `test_task12a_auth_sessions.py` |
| `/api/auth/refresh`, `/api/auth/logout`, `/api/auth/logout-all`, `/api/auth/sessions` | session management | refresh cookie and/or access token | server-side session validation; refresh-family reuse detection; user owns session | `test_task12a_auth_sessions.py` |
| `/api/auth/me`, `/api/users/me` | authenticated personal | access token | active user, active session, matching auth version | `test_task12a_auth_sessions.py` |
| diagnostics, profiles, conversations, chat, roadmaps, recommendations, assessments, learning, career resilience, market applications, interviews, innovation extension, originality research, RAG feedback | authenticated personal | access token through `get_current_user` or hardened `get_optional_user` | anonymous requests rejected by centralized dependency except explicit public allowlist; owner checks continue to return 404/403 | route audit |
| `/api/voice/transcribe`, `/api/voice/speak`, `/api/voice/conversation-token` | authenticated personal/provider-mediated | access token | current user required before file/body provider work; provider-disabled configuration returns controlled non-2xx after auth | `test_task15a_security_authorization.py`, `test_live_voice_conversation.py` |
| `/api/voice/status` | public status | none | reports configuration state without secret values | `test_live_voice_conversation.py` |
| `/api/elevenlabs/v1/chat/completions` | internal provider callback | Custom LLM bearer secret | explicit provider-secret capability | route audit allowlist |
| `/api/admin/research/*` | admin | access token | centralized admin email guard in router | existing research tests |
| `/api/rag/search` | public read | none | public knowledge-base search allowlisted in `get_optional_user` policy | `test_task15a_security_authorization.py` |
| `/api/rag/ask`, `/api/rag/runs/*/feedback` | authenticated personal | access token through `get_optional_user` | anonymous requests rejected; run feedback remains scoped to owning user where a run has `user_id` | route audit, existing RAG tests |
| `/api/rag/reindex` | admin mutation | access token | `require_admin_user`; anonymous rejected with 401, non-admin rejected with 403 | `test_task15a_security_authorization.py` |
| `/api/v1/admin/career-encyclopedia/sync`, `/api/v1/admin/career-encyclopedia/roles*` | admin mutation | access token | `require_admin_user`; invalid admin resources still return 404 | `test_task15a_security_authorization.py` |
| `/api/v1/market/providers/status` | public read | none | read-only provider status; no demo sync, provider row, cursor row, or sync-run side effect | `test_task15a_security_authorization.py`, `test_market_application_engine.py` |
| `/api/v1/market/providers/demo/sync`, `/api/v1/market/esco/normalise` | admin/provider mutation | access token | `require_admin_user`; no live NAV or ESCO provider access in local tests | `test_task15a_security_authorization.py` |
| `/api/v1/research/studies/ensure`, `/api/v1/research/studies/{study_id}/exports`, `/api/v1/research/exports/{export_id}` | admin research operation | access token | `require_admin_user`; export creation and export retrieval are not exposed to ordinary users | `test_task15a_security_authorization.py` |
| `/api/v1/research/fairness-audits` `POST`, `/api/v1/research/fairness-audits/reset` | admin research mutation | access token | `require_admin_user`; public/read endpoints for synthetic fairness materials remain read-only | `test_task15a_security_authorization.py` |
| `/api/v1/research/originality-sessions/{session_id}/baseline`, `/experimental`, `/feedback`, `/results` | owned research session | access token through `get_optional_user` | session profile owner or same `user_id`; admins may remediate orphan/user sessions; cross-user rejected | `test_task15a_security_authorization.py` |
| advisor share routes | capability-token | share token | scoped advisor share capability | existing advisor tests |

Known follow-up:

- Browser-extension capture still evaluates the user/profile dependency before the extension token path. That is not an anonymous security bypass; it can reject legitimate extension-token capture and remains deferred to the extension/auth flow work instead of being redesigned in Task 15A.

Automated audit:

```powershell
.\.venv\Scripts\python.exe -m app.scripts.audit_route_authorization
```

Task 15A audit result: `0` blocking findings, with advisory optional-user review items retained for explicit route-by-route documentation.
