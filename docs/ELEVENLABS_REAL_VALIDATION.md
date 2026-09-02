# ElevenLabs Real Validation

Automated tests remain mock-only and do not consume provider credits.

## Configuration-Only Validation

Run from `backend`:

```powershell
.\.venv\Scripts\python.exe -m app.scripts.validate_elevenlabs
```

This checks runtime configuration, residency mode, token endpoint construction, Agent ID format, public backend URL shape, and blocking issues. It does not request a real token by default.

## Real Token Validation

Real token validation is opt-in:

```powershell
.\.venv\Scripts\python.exe -m app.scripts.validate_elevenlabs --request-token
```

It also requires:

```env
REAL_PROVIDER_TESTS_ENABLED=true
ELEVENLABS_API_KEY=
ELEVENLABS_AGENT_ID=
ELEVENLABS_LIVE_VOICE_ENABLED=true
```

The script never prints the token or API key. It prints only a truncated conversation ID after success.

## Custom LLM Public URL

When `ELEVENLABS_CUSTOM_LLM_ENABLED=true`, configure:

```env
PUBLIC_BACKEND_URL=https://<public-backend-host>
ELEVENLABS_CUSTOM_LLM_SECRET=
```

The final Custom LLM endpoint is:

```text
{PUBLIC_BACKEND_URL}/api/elevenlabs/v1/chat/completions
```

Production must not use localhost, `127.0.0.1`, private IPs, relative URLs, or HTTP for the Custom LLM public URL.

## Public Endpoint Validation

Run:

```powershell
.\.venv\Scripts\python.exe -m app.scripts.validate_public_endpoint
```

This checks:

- `GET {PUBLIC_BACKEND_URL}/health/live`
- `GET {PUBLIC_BACKEND_URL}/health/ready`

It does not send the Custom LLM secret to health endpoints.

## Real WebRTC

Real WebRTC validation is not part of standard CI. Use `npm.cmd run test:e2e:live-real` only with `REAL_PROVIDER_TESTS_ENABLED=true` and real provider configuration. Manual validation must confirm speech, agent audio, interruption, mute/unmute, navigation, shared floating widget, text in the same session, end cleanup, transcript display, and latest-turn metadata.

