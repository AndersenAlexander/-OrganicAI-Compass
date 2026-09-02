# Secret Rotation After Archive Exposure

Date: 2026-07-27

The latest local source archive contained local environment files, database artifacts, logs, and configured provider/database credentials. Do not publish or reuse that archive.

Task 12A does not rotate external secrets automatically. Rotate these manually in the provider/admin consoles:

- OpenAI API key
- ElevenLabs API key
- PostgreSQL password
- JWT signing secret
- diagnostics token
- Custom LLM secret
- webhook secret
- demo password

After rotation, update ignored local `.env` files or deployment secret stores, restart services that read those values, invalidate old archives, and create a new sanitized source archive. Do not paste rotated values into documentation, issue trackers, test logs, or release reports.

