# Branch and Release Policy

Technical draft - requires operational review before remote enforcement.

Branches:

- `main`
- `feature/<short-description>`
- `fix/<short-description>`
- `docs/<short-description>`
- `release/<version>`

Rules:

- `main` must remain deployable.
- Pull requests must pass CI before merge.
- No direct cloud deployment from unreviewed feature branches.
- No provider secrets, database URLs, exported archives or runtime artifacts may be committed to any branch.
- Pull-request CI must not call live OpenAI, ElevenLabs or email providers.
- Alembic migrations require review before merge.
- Release tags are immutable.
- Deployment must reference an exact commit and, where supported, immutable container image digests.
