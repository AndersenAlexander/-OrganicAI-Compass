# Privacy Center User Flow

Technical draft - requires legal review before public deployment.

The Privacy Center is available at `/privacy` for authenticated users.

User flows:

1. Review policy status, inventory counts, backup disclosure, and legacy orphan archive boundary.
2. Change account conversation persistence between account history and ephemeral.
3. Keep live voice transcript history ephemeral by default.
4. Enable or disable optional analytics, research, personalization, service email, and marketing email.
5. Generate, download, and delete encrypted-at-rest data export artifacts.
6. Preview category deletion row counts before deletion.
7. Queue or cancel account deletion.
8. Withdraw research participation.
9. Review recent consent events and provider privacy status.

Sensitive actions open a recent-authentication dialog and call `/api/privacy/reauthenticate` before continuing.
