# Data Subject Rights Runbook

Technical draft - requires legal review before public deployment.

Supported technical workflows:

- Access: create export through `/api/privacy/exports`.
- Deletion: preview category deletion or queue account deletion.
- Withdrawal: update preferences or call research withdrawal.
- Portability: export artifact contains JSON files in an encrypted-at-rest ZIP artifact.
- Objection/restriction: disable optional analytics, research, personalization, and marketing email.

Operational steps:

1. Verify identity with authenticated session and recent authentication for sensitive actions.
2. Execute the relevant Privacy Center workflow.
3. Review `data_subject_requests` and `data_lifecycle_events`.
4. For restored databases, apply the deletion suppression ledger before access.
5. For providers, perform manual follow-up unless an enabled adapter confirms deletion.
