# Real Provider Acceptance

Status: harness prepared; real provider execution remains opt-in and manual.

Command:

```powershell
cd backend
.\.venv\Scripts\python.exe -m app.scripts.provider_acceptance
```

Default behavior is `NOT EXECUTED`. Real checks require:

- `--execute`;
- provider-specific credentials;
- `REAL_PROVIDER_TESTS_ENABLED=true`;
- `LIVE_PROVIDER_VALIDATION_ENABLED=true`;
- provider-specific approval flags.

Providers:

| Provider | Default | Execution boundary | Acceptance |
| --- | --- | --- | --- |
| OpenAI | Not executed | Read-only model listing or explicit low-token canary with `store=false` | Synthetic check passes, timeout bounded, no personal data. |
| ElevenLabs | Skipped by default | Existing opt-in Playwright live voice real-provider test | Synthetic live session passes and cleanup/privacy evidence exists. |
| Email | Not executed | One approved synthetic recipient only | Provider accepts message and inbox delivery is verified. |

No automatic retries should create uncontrolled charges. Evidence must exclude prompts containing personal data, response content, credentials and complete provider secrets.
