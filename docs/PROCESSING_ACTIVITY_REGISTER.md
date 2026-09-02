# Processing Activity Register

Technical draft - requires legal review before public deployment.

| Activity | Purpose | Data categories | Default basis label | System |
| --- | --- | --- | --- | --- |
| Account service | Login, sessions, account settings | Account profile, security operations | essential-service | PostgreSQL |
| AI coaching | User-requested assistant responses | Conversation history, diagnostic profile | user-requested-feature | PostgreSQL, OpenAI when configured |
| Live voice | Voice conversation UX | Voice interaction, conversation history | user-requested-feature | ElevenLabs when configured |
| Personalization | Tailored roadmap and recommendations | Diagnostic profile, career workspace | optional-personalization | PostgreSQL |
| Research | Evaluation and robustness studies | Pseudonymous research participation | optional-research | PostgreSQL |
| Product analytics | Product improvement metrics | Operational metadata | optional-analytics | PostgreSQL |
| Security retention | Abuse prevention and audit | Security and operations | legal-or-security-retention | PostgreSQL |
