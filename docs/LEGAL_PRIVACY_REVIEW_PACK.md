# Legal And Privacy Review Pack

Status: technical pack requiring professional legal/privacy review. This is not legal approval.

System data-flow inventory:

- account registration and authentication;
- diagnostic/profile inputs;
- recommendations and reports;
- chat and conversation data;
- RAG/provider interactions;
- voice provider sessions if enabled;
- email verification/reset/security notifications;
- privacy export/delete/retention workflows;
- telemetry and operational logs.

Personal data categories:

- identity: name, email, account status;
- authentication/security metadata;
- career/profile assessment inputs;
- generated recommendations;
- conversation/message content;
- provider session identifiers;
- email delivery metadata stored as hashes;
- privacy request records.

Review placeholders:

- lawful basis per processing purpose;
- retention period per category;
- subprocessors and provider data-processing terms;
- international transfer mechanism;
- data subject rights SLA;
- backup deletion limitations;
- AI transparency disclosure;
- voice recording/transcription disclosure;
- automated recommendation limitations;
- research consent and withdrawal process.

Technical controls summary:

- hashed refresh tokens and account tokens;
- memory-only frontend access token policy;
- privacy export/delete controls;
- provider diagnostics sanitization;
- route authorization audit;
- telemetry privacy audit;
- source archive secret exclusions.

Unresolved legal questions:

- final privacy notice wording;
- DPA/subprocessor list;
- transfer impact assessment;
- retention and deletion across backups;
- provider training/retention claims;
- research participant consent wording.

Legal approval remains `EXTERNAL MANUAL ACTION REQUIRED`.
