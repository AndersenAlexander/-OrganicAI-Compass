# OpenAI Data Controls Attestation

Technical draft — requires legal and operational review before public deployment.

Configuration keys:

- `OPENAI_TRAINING_OPT_IN_STATUS`
- `OPENAI_ABUSE_MONITORING_MODE`
- `OPENAI_DATA_RESIDENCY_REGION`
- `OPENAI_PROJECT_DATA_CONTROLS_VERIFIED`
- `OPENAI_DATA_CONTROLS_VERIFIED_AT`
- `OPENAI_DATA_CONTROLS_VERIFIED_BY`

The UI and provider registry must not show data controls as verified unless `OPENAI_PROJECT_DATA_CONTROLS_VERIFIED=true` and a verification date is present. ZDR must not be inferred from `store=false`.
