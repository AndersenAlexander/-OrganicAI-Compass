# Category Deletion Matrix

Technical draft - requires legal review before public deployment.

Category deletion uses preview-before-delete semantics.

| Category | Export | Deletion | Research | Provider impact |
| --- | --- | --- | --- | --- |
| Account profile | Included with secret exclusion | Tombstone during account deletion | Direct identifiers excluded | Not shared by default |
| Diagnostic profile | Included | Active delete or account deletion | Pseudonymous only when opted in | AI provider processing only when feature used |
| Conversation history | Included when persisted | Active delete for conversations and messages | Excluded when ephemeral | Provider review may be required |
| Voice interaction | Transcript included only if persisted | Active delete where locally stored | Ephemeral by default | ElevenLabs deletion adapter is opt-in |
| Career workspace | Included | Active delete or account deletion | Pseudonymous only when opted in | Provider review by feature |
| Research participation | Separate research scope | Withdraw future collection, manual review for historical linkage | Pseudonymous | No direct provider deletion by default |
| Security and operations | Limited export metadata | Retained for security windows | Excluded | Not shared except operational necessity |
