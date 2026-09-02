# Defence Runbook

Use the isolated Demo only. Do not reset a database, run migrations, change scoring, or start normal PostgreSQL for the presentation.

## Before presentation

1. Confirm ports 5192 and 8022 are either free or owned by the intended Demo processes:

   ```powershell
   Get-NetTCPConnection -State Listen -LocalPort 5192,8022 -ErrorAction SilentlyContinue
   ```

2. In PowerShell window 1, start the backend from the intended worktree. The existing local `backend/.env` supplies configured provider credentials; do not print or copy them.

   ```powershell
   Set-Location 'C:\Users\alexa\Desktop\31.08\1. OrganicAI Compass\backend'
   $env:APP_ENV='development'
   $env:DATABASE_URL='sqlite:///./tmp/organicai-local-demo.db'
   $env:DATABASE_REQUIRE_POSTGRES_IN_PRODUCTION='false'
   $env:DB_AUTO_CREATE_SCHEMA='true'
   $env:DB_AUTO_MIGRATE='false'
   $env:DB_REQUIRE_MIGRATION_HEAD='false'
   $env:DEMO_ACCOUNT_ENABLED='true'
   $env:DEMO_RESET_ON_LOGIN='false'
   $env:DEMO_RESET_ON_STARTUP='false'
   $env:FRONTEND_URL='http://127.0.0.1:5192'
   $env:FRONTEND_PUBLIC_URL='http://127.0.0.1:5192'
   $env:ALLOWED_ORIGINS='http://127.0.0.1:5192,http://localhost:5192'
   .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8022 --log-config ..\.tmp\uvicorn_demo_logging.json
   ```

3. In PowerShell window 2, start the frontend:

   ```powershell
   Set-Location 'C:\Users\alexa\Desktop\31.08\1. OrganicAI Compass\frontend'
   $env:VITE_API_BASE_URL='http://127.0.0.1:8022/api'
   $env:VITE_PROXY_TARGET='http://127.0.0.1:8022'
   npm.cmd run dev -- --host 127.0.0.1 --port 5192
   ```

4. Verify both services:

   ```powershell
   (Invoke-WebRequest -UseBasicParsing 'http://127.0.0.1:8022/health').StatusCode
   (Invoke-WebRequest -UseBasicParsing 'http://127.0.0.1:5192').StatusCode
   ```

   Both must print `200`.

5. Open `http://127.0.0.1:5192/login`, click **Explore Demo**, and confirm the Human Potential Map opens.
6. Open AI Coach and send `What is OrganicAI Compass?` Confirm a visible answer.
7. Open Voice connection diagnostics. If internet/provider access is available, test ElevenLabs. If the safe unavailable message appears, continue with text chat.

## Presentation order

1. Home — explain the Living Compass and human-centred framing.
2. Explore Demo — show idempotent access to the completed Demo journey.
3. Human Potential Map — archetype, signals, career interests, AI collaboration style and interpretation controls.
4. Career Compatibility — separate Natural Fit, Capability Fit, Evidence Strength, Transition Feasibility and AI Opportunity.
5. Career Experiment — show the current in-progress experiment and deterministic review rubric; do not create another experiment.
6. Evidence Passport — contrast self-report/needs-verification with practically verified evidence and provenance.
7. My Roadmap — show 24% progress and the persisted current actions; do not apply recalibration during the defence.
8. AI Coach text — use the prepared questions in `docs/PRESENTATION_COACH_SCRIPT.md`.
9. ElevenLabs voice — use only if the token and WebRTC connection succeed; otherwise state the external dependency and continue.
10. Employment Journey / Decision Journal — show tracker identity, interview preparation/reflection, offer review, and the separated user/evidence/AI/system record.
11. Conclusions and limitations — emphasize deterministic scoring, RAG traceability, human authority, and prototype limitations.

## Emergency fallbacks

- **OpenAI or semantic retrieval fails:** continue with the deterministic/profile-grounded Coach and lexical RAG fallback. Do not claim that an LLM calculated scores.
- **ElevenLabs fails:** end/close voice and continue in AI Coach text chat. The verified safe state is `ElevenLabs is temporarily unavailable.`
- **Normal PostgreSQL is unavailable:** take no action. The defence Demo is intentionally isolated on `backend/tmp/organicai-local-demo.db`.
- **Demo session becomes stale:** click **Exit Demo**, return to `/login`, then click **Explore Demo**. This reuses the same Demo user and profile.
- **Frontend looks stale or strange:** use a hard refresh (`Ctrl+Shift+R`) first. If that does not recover, verify `/health`, then restart only the affected 5192 or 8022 Demo process from the commands above.
- **A port is occupied:** identify the exact owning PID and command line before stopping it. Never stop PostgreSQL or unrelated services.
- **A cosmetic console warning appears:** continue if the visible behavior works. Known benign examples are the auth bootstrap 401, React `fetchPriority`, Three/WebGL development warnings and dependency deprecations.

Do not push, reset data, add features, upgrade dependencies, modify migrations, or change provider architecture immediately before the defence.
