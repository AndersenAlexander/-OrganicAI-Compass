# Live Voice Testing

## Automated Backend Tests

Run from `backend`:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_live_voice_conversation.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_release_gate_runtime_security.py -q
```

Coverage includes:

- live voice status without secret leakage
- authenticated token endpoint
- disabled and unconfigured token states
- ElevenLabs provider error mapping
- token rate limiting
- Custom LLM bearer secret enforcement
- Custom LLM SSE streaming shape
- profile/conversation ownership rejection
- latest-turn metadata lookup
- `/api/chat` regression coverage after service refactor

## Automated Frontend Tests

Run from `frontend`:

```powershell
npm.cmd run typecheck
npm.cmd run test
npm.cmd run test:e2e -- tests/e2e/live-voice.spec.ts
```

The Playwright spec uses a dev-only local adapter and mocked `/api/voice/*` endpoints. It verifies:

- start live conversation
- live transcript display
- OrganicAI metadata display after an agent response
- live mode does not show voice-message transcript review
- microphone mute/unmute controls
- one shared live session across Coach page and floating widget during SPA navigation
- ending the session from the widget
- request IDs and safe diagnostics
- provider-token error fallback
- no rendered token, secret, or full Agent ID

Real provider validation is separate and opt-in:

```powershell
.\.venv\Scripts\python.exe -m app.scripts.validate_elevenlabs
.\.venv\Scripts\python.exe -m app.scripts.validate_elevenlabs --request-token
```

The real token command requires `REAL_PROVIDER_TESTS_ENABLED=true` and never prints the token.

## Manual Endpoint Checks

With the backend running:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Check public status:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/voice/status
```

Expected safe output includes booleans such as `liveVoiceEnabled`, `liveVoiceConfigured`, and `agentIdConfigured`, but no API key and no raw Agent ID.

Authenticated checks require a valid OrganicAI access token:

```powershell
$headers = @{ Authorization = "Bearer <organicai-access-token>" }
Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/voice/conversation-token -Headers $headers -ContentType "application/json" -Body '{"route":"/coach/demo-profile","language":"en"}'
```

Custom LLM smoke test requires the ElevenLabs secret and an existing OrganicAI user/profile in the database:

```powershell
$headers = @{ Authorization = "Bearer <ELEVENLABS_CUSTOM_LLM_SECRET>" }
$body = @{
  model = "organicai-coach"
  stream = $true
  messages = @(@{ role = "user"; content = "How should I use AI responsibly?" })
  elevenlabs_extra_body = @{
    organicai_user_id = "<organicai-user-uuid>"
    profile_id = "<profile-id>"
    elevenlabs_conversation_id = "manual-live-test"
    language = "en"
    voice_personality = "Calm Guide"
    conversation_mode = "Explain simply"
  }
} | ConvertTo-Json -Depth 8
Invoke-WebRequest -Method Post http://127.0.0.1:8000/api/elevenlabs/v1/chat/completions -Headers $headers -ContentType "application/json" -Body $body
```

## Real ElevenLabs End-to-End Checks

These require a configured ElevenLabs Agent, valid `ELEVENLABS_API_KEY`, valid `ELEVENLABS_AGENT_ID`, enabled Custom LLM, and a public HTTPS backend.

1. Start the backend and frontend.
2. Log in to OrganicAI.
3. Open `/coach/<profile-id>`.
4. Start **Live conversation**.
5. Confirm the browser microphone permission prompt.
6. Speak a short question.
7. Verify the user transcript appears as captions.
8. Verify the spoken assistant answer is concise and profile-aware.
9. Interrupt while the agent speaks to test barge-in.
10. Mute, unmute, navigate to another page, open the floating widget, and confirm the same live session remains active.
11. End the session manually.
12. Switch to **Voice message** and verify transcript review still appears only there.
