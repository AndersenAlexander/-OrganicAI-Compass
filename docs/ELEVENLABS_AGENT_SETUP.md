# ElevenLabs Agent Setup for OrganicAI Coach

## Backend Configuration

Add these settings to `backend/.env`:

```env
ELEVENLABS_API_KEY=
ELEVENLABS_AGENT_ID=
ELEVENLABS_LIVE_VOICE_ENABLED=true
ELEVENLABS_API_BASE_URL=https://api.elevenlabs.io
ELEVENLABS_RESIDENCY_MODE=standard
# Deprecated. Do not use this to infer isolated residency.
ELEVENLABS_SERVER_LOCATION=
ELEVENLABS_ENVIRONMENT=production
ELEVENLABS_REQUEST_TIMEOUT_SECONDS=15
ELEVENLABS_CUSTOM_LLM_ENABLED=false
ELEVENLABS_CUSTOM_LLM_SECRET=
ELEVENLABS_LEGACY_VOICE_FALLBACK_ENABLED=true
```

Do not expose these values in frontend environment variables.

`standard` is the default ElevenLabs environment. Use `isolated-eu`, `isolated-in`, or `isolated-sg` only if your ElevenLabs account and Agent are configured for that isolated environment, and set `ELEVENLABS_API_BASE_URL` explicitly. OrganicAI does not invent isolated API URLs.

`ELEVENLABS_CUSTOM_LLM_ENABLED=false` is the verified local live-voice mode. It keeps the Agent's native ElevenLabs LLM while OrganicAI owns authenticated token minting, consent, the WebRTC UI, transcript rendering, and fallback. Enabling Custom LLM is a separate deployment choice and is not required for live voice.

## Optional Custom LLM Public URL

This section applies only when `ELEVENLABS_CUSTOM_LLM_ENABLED=true`. ElevenLabs must then be able to reach the OrganicAI backend over HTTPS. For local development use a tunnel such as Cloudflare Tunnel, ngrok, or a staging deployment.

The Custom LLM URL is:

```text
https://<public-backend-host>/api/elevenlabs/v1/chat/completions
```

Use this authorization header in the ElevenLabs Custom LLM settings:

```http
Authorization: Bearer <ELEVENLABS_CUSTOM_LLM_SECRET>
```

Run the safe configuration validator before requesting any real token:

```powershell
.\.venv\Scripts\python.exe -m app.scripts.validate_elevenlabs
```

Requesting a real token is opt-in and requires `REAL_PROVIDER_TESTS_ENABLED=true`:

```powershell
.\.venv\Scripts\python.exe -m app.scripts.validate_elevenlabs --request-token
```

## Agent Settings

Create or update an ElevenLabs Conversational AI Agent:

1. Enable WebRTC live conversation.
2. Configure the desired voice and speech model.
3. Enable interruption or barge-in if available for the agent.
4. For the verified native mode, keep the Agent's configured ElevenLabs LLM and attach the canonical OrganicAI knowledge sources listed below.
5. Only for a deliberate Custom LLM deployment, set the LLM provider to Custom LLM, use the OrganicAI HTTPS URL, add the bearer secret, and retain OpenAI-compatible streaming chat completions.

Do not switch a working native Agent to Custom LLM merely to share local per-turn metadata. Custom LLM needs a reachable HTTPS backend and its own release validation.

## Canonical Knowledge Sources

The presentation knowledge sources are:

- `backend/knowledge_base/organicai_compass_master_knowledge.md` — 41 canonical platform sections;
- `backend/knowledge_base/organicai_compass_defence_qa.md` — 110 concise defence and demo answers.

The text Coach indexes both files through OrganicAI RAG automatically. Native ElevenLabs mode cannot read the repository index at runtime; its Agent knowledge must be synchronized from these same files in the ElevenLabs dashboard or approved Agent-configuration workflow. Synchronize only static platform knowledge: never upload user profiles, Evidence Passport records, applications, transcripts, secrets, or conversation tokens.

After a native Agent knowledge update, verify several canonical questions in a real voice session and record the source revision. If the native Agent lacks persisted OrganicAI user context, it must say that the personal information is unavailable rather than invent it.

## Prompt Guidance

Use the policy shape that matches the selected mode. In native mode, the Agent relies on the synchronized canonical files. In Custom LLM mode, OrganicAI supplies per-turn RAG and authenticated profile context.

```text
You are OrganicAI Coach's live voice interface.
Speak naturally and concisely.
Use the attached canonical OrganicAI knowledge for platform facts.
Scores are deterministic application results; never claim that the LLM calculates or changes them.
Treat career directions as provisional hypotheses, not predictions or employment-suitability verdicts.
Distinguish persisted facts from suggestions and keep final career decisions with the user.
Do not invent OrganicAI profile facts, roadmap data, or citations.
If authenticated user context is not supplied in this mode, say it is unavailable.
If the user asks to navigate or update app state, call the provided client tool.
Do not read technical metadata aloud unless the user asks for it.
```

For Custom LLM mode, add: `Use the Custom LLM response as the source of truth.`

## Dynamic Context

The browser sends:

- `organicai_profile_id`
- `organicai_route`
- `organicai_language`

When Custom LLM mode is enabled, its extra body sends richer context:

- OrganicAI user ID
- active profile ID
- app conversation ID
- ElevenLabs conversation ID
- current route
- selected profile node
- selected recommendation
- language
- personality and conversation mode
- theme

## Client Tool Registration

Register these tool names in the ElevenLabs Agent if you want voice-controlled app actions:

- `navigate_to`
- `switch_theme`
- `confirm_selected_node`
- `add_note_to_selected_node`
- `open_selected_learning_path`
- `regenerate_roadmap`
- `hide_selected_recommendation`
- `open_profile`
- `open_roadmap`
- `open_recommendations`
- `open_diagnostic`

All tool results are compact JSON strings.

## Fallback Mode

Keep `ELEVENLABS_LEGACY_VOICE_FALLBACK_ENABLED=true` while rolling out live voice. Users can switch to **Voice message** when WebRTC, microphone permission, or ElevenLabs live service is unavailable.
