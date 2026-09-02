# Innovation Extension Architecture

The Innovation Extension Pack adds five connected modules to OrganicAI Compass:

- Browser Job Capture Extension
- Advisor Collaboration Mode
- Multi-Persona Panel Interview
- Enhanced Career Encyclopedia
- Career Decision Journal

The workflow is intentionally connected to existing platform concepts: saved external job data enters the existing Job Analyzer, confirmed requirements connect to Evidence Passport matching, adviser comments remain human review objects, interview panel questions reuse the Interview Journey, career roles connect to hypotheses and experiments, and decision outcomes remain journal records until the user confirms any roadmap change elsewhere.

## Repository Audit Findings

The implementation reuses the current FastAPI, SQLAlchemy, React, Vite, typed API-client, workspace navigation, demo reset, and Playwright conventions.

Backend anchors reused:

- `JobPosting`, `JobAnalysis`, `JobRequirement`, `JobApplication`, `ApplicationDocument`, and `DocumentClaim` from the market/application module.
- Evidence Passport, Career Hypotheses, Career Experiments, Supported Paths, and Job Loss support boundaries from the career-resilience module.
- `Interview`, `InterviewQuestion`, `MockInterviewSession`, `MockInterviewTurn`, voice-session conventions, and deterministic rubric patterns from Interview Journey.
- Existing research export separation and demo reset services.
- Additive Alembic migration `0009_collaboration_traceability_extensions` for capture confirmation provenance, share scope/version metadata, proposal versioning, and journal source separation.

Frontend anchors reused:

- React Router lazy-loaded workspace routes.
- Existing global and workspace navigation groups.
- Typed API module pattern under `frontend/src/api`.
- Mapping helper tests under `frontend/src/lib`.
- Existing light/dark design tokens and dense workspace panel styling.
- Existing Playwright frontend-only mock pattern.

No duplicate Job Analyzer, Evidence Passport, mock-interview engine, career experiment engine, roadmap engine, or research export system was created.

## Backend Data Model

New SQLAlchemy models live in `backend/app/models/innovation_extension.py`.

- `BrowserExtensionConnection`: short-lived extension pairing token hash, permissions, expiry, revocation, and last-use metadata.
- `BrowserJobCapture`: user-triggered captured job page data, sanitized/raw/confirmed text, canonical source type, content hash, review status, quality warnings, duplicate reference, and optional Job Analysis link.
- `AdvisorShare`: temporary selected-section share, secure token hash, optional PIN hash, canonical permission code, included/excluded scope snapshot, expiry, access attempt limits, version and revocation.
- `AdvisorComment`: human-adviser comment or versioned proposal with provenance, status, user response and explicit owner decision.
- `CareerRoleProfile`: curated role profile with schema-rich profile JSON, status, family, version, review date, and source metadata.
- `CareerRoleProfileVersion`: immutable role-profile version snapshots.
- `CareerDecisionJournalEntry`: versioned user decision, assumptions, uncertainty, source-separated inputs, evidence/adviser links, experiment/interview links, outcome, lessons, privacy scope, and roadmap mutation boundary.
- `CareerDecisionJournalVersion`: immutable journal snapshots.
- `InnovationAuditEvent`: token, share, comment, capture, role, and journal audit events.

## Browser Extension

The extension package is in `browser-extension/` and uses TypeScript plus Manifest V3.

Architecture:

- `manifest.json` defines a Chrome-compatible extension named `Save to OrganicAI Compass`.
- `popup.html` and `popup.css` render the editable capture UI.
- `src/popup.ts` reads the active tab only when the popup is opened by the user, then sends a corrected payload to the OrganicAI Compass backend.
- `src/types.ts` contains extension-local payload types.

Browser permissions:

- `activeTab`: allows current-tab access only after user interaction.
- `storage`: stores backend URL, profile ID, and the user-generated extension token.
- `scripting`: runs a one-time content extraction function from the popup.
- Host permissions are limited to local backend URLs for development.

Privacy boundaries:

- No automatic background scraping.
- No crawling.
- No browser history, cookies, passwords, form contents, private messages, or account data.
- No raw DOM snapshot or remote executable code.
- No backend secrets or database credentials in the extension.

The extension README contains the installation and privacy guide.

## Extension Authentication

OrganicAI Compass creates a user-generated extension connection token. The backend stores only a SHA-256 token hash, returns the plaintext token once, tracks expiry and last use, and supports revocation.

Capture endpoints accept the token through `X-OrganicAI-Extension-Token`. Demo/manual captures inside the authenticated app can be created without the extension token, but external extension capture requires a valid profile-scoped connection.

## Job Capture Workflow

Endpoint:

- `POST /api/v1/profiles/{profile_id}/job-captures`

Backend responsibilities:

- Validates the target profile through existing request context.
- Rejects localhost, private-network, reserved, and local/intranet-style URLs.
- Sanitizes captured text and enforces size limits.
- Preserves raw captured text separately from user-confirmed fields.
- Deduplicates by profile, normalized source URL, and content hash.
- Records source domain, capture method, requested action, timestamp, and extension version.
- Produces quality warnings when title or description evidence is weak.
- Remains editable/reviewable and can create or link a `JobAnalysis` only after explicit user confirmation; the capture ID and canonical source type remain in provenance metadata.

Statuses:

- `Captured`
- `Needs review`
- `Confirmed`
- `Analysed`
- `Duplicate`
- `Rejected`
- `Archived`

Captured content is not treated as verified until the user confirms it.

## Advisor Collaboration

Adviser sharing is limited, temporary, and selected-section based.

Routes:

- `/workspace/:profileId/advisor-collaboration`
- `/workspace/:profileId/advisor-collaboration/shares`
- `/workspace/:profileId/advisor-collaboration/shares/:shareId`
- `/advisor-review/:shareToken`

Supported adviser roles include career adviser, academic supervisor, mentor, NAV counsellor, recruiter or HR specialist, teacher or trainer, and other. Role labels are display labels, not identity verification.

Default exclusions:

- Entire profile access
- Sensitive Job Loss fields
- Benefit-screening inputs
- Private transcripts
- Unrelated applications

Adviser comments can be accepted or rejected by the user. Acceptance stores the user response and provenance, but does not directly edit profile facts, Evidence Passport levels, application status, benefit screening, documents, or roadmap actions.

## Adviser Permission Model

Permission levels:

- View only
- Comment
- Suggest changes
- Validate selected evidence
- Recommend an experiment
- Recommend a roadmap action

Allowed actions are stored explicitly on each share. The external adviser page is read-only except for comment submission unless export is explicitly allowed by the user. Share tokens expire, can be revoked, have maximum access attempts, support optional PIN validation, and are audited without logging plaintext tokens.

## Multi-Persona Panel Interview

Panel simulation extends the existing Interview Journey. It reuses `MockInterviewSession`, `MockInterviewTurn`, interview questions, deterministic rubrics, and voice-mode boundaries instead of creating a second interview engine.

Route:

- `/workspace/:profileId/interviews/:interviewId/panel-simulation`

Implemented personas:

- Recruiter
- Hiring Manager
- Technical Lead
- Product Manager
- Design Lead
- Client Stakeholder
- Academic or Research Reviewer
- Custom panel member

Each persona defines purpose, question categories, expected depth, follow-up style, terminology level, allowed evidence focus, maximum question count, and optional voice configuration.

Question methodology:

- Questions are generated from confirmed job requirements when available.
- Existing interview and application context is reused.
- Company facts and requirements absent from Job Analysis are not invented.
- Each turn stores persona, question, category, source, related requirement, answer, follow-up, rubric data, and prohibited inference labels.

Feedback methodology:

- Feedback is separated by persona.
- Shared strengths, repeated gaps, unsupported claims, and next practice are displayed separately.
- There is no single opaque panel score.
- The system does not infer honesty, personality, emotion, mental state, employability, or accent quality.

Voice limitation:

- Text mode is implemented.
- Multi-voice persona routing is treated as optional future work unless the existing voice provider layer is validated for stable multi-voice panel playback.

## Career Encyclopedia

The enhanced Career Encyclopedia is a curated role catalogue, not a shallow bulk role database.

Routes:

- `/careers`
- `/careers/:careerSlug`
- `/workspace/:profileId/career-encyclopedia`
- `/workspace/:profileId/career-encyclopedia/:careerSlug`

Initial role count: 16.

Families:

- AI and software
- Design and product
- Consulting and strategy
- Learning and communication

Role-profile schema includes role ID, slug, title, aliases, family, summary, responsibilities, daily tasks, work environment, entry routes, experience expectations, technical skills, transferable skills, human-critical skills, AI-augmented tasks, automatable tasks, tasks requiring human accountability, education pathways, certifications, portfolio evidence, recommended experiments, learning objectives, ESCO concepts, labour-market job titles, linked local opportunities, language considerations, interview categories, adjacent roles, progression routes, known uncertainties, source metadata, review date, and version.

Profile comparison reuses Personal Fit, Capability Fit, Market Fit, Support Fit, Evidence Passport links, career experiment history, and local market/application links.

The catalogue does not include salary figures and does not label roles as future-proof.

## Decision Journal

The Career Decision Journal stores decisions, assumptions, linked evidence, adviser comments, review dates, outcomes, and immutable versions.

Route:

- `/workspace/:profileId/decision-journal`

Workflow:

1. Create a decision with options, assumptions, selected evidence, and optional linked career/job/application context.
2. Store version 1 immediately.
3. Update creates a new version snapshot.
4. Record outcome separately from the original decision.
5. Compare expectation and outcome without rewriting the original version.
6. Keep roadmap mutation blocked unless another existing roadmap workflow receives explicit user confirmation.

Research export returns a pseudonymous preview and excludes raw journal text, private notes, and adviser free text by default.

## API Documentation

New API endpoints are under `/api/v1`.

Browser extension:

- `POST /profiles/{profile_id}/browser-extension/connection`
- `GET /profiles/{profile_id}/browser-extension/connection`
- `DELETE /profiles/{profile_id}/browser-extension/connection/{connection_id}`
- `GET /profiles/{profile_id}/browser-extension/settings`
- `POST /profiles/{profile_id}/job-captures`
- `GET /profiles/{profile_id}/job-captures`
- `POST /profiles/{profile_id}/job-captures/{capture_id}/confirm`

Advisor collaboration:

- `POST /profiles/{profile_id}/advisor-shares`
- `GET /profiles/{profile_id}/advisor-shares`
- `GET /profiles/{profile_id}/advisor-shares/{share_id}`
- `DELETE /profiles/{profile_id}/advisor-shares/{share_id}`
- `PATCH /profiles/{profile_id}/advisor-comments/{comment_id}`
- `GET /advisor-review/{share_token}`
- `POST /advisor-review/{share_token}/comments`

Panel interview:

- `GET /interviews/panel-personas`
- `POST /interviews/{interview_id}/panel-simulation`
- `GET /mock-sessions/{session_id}/panel`
- `POST /mock-sessions/{session_id}/panel-turns`
- `POST /mock-sessions/{session_id}/panel-complete`

Career Encyclopedia:

- `GET /careers`
- `GET /careers/{career_slug}`
- `POST /admin/career-encyclopedia/sync`
- `POST /admin/career-encyclopedia/roles`
- `PUT /admin/career-encyclopedia/roles/{career_slug}`
- `DELETE /admin/career-encyclopedia/roles/{career_slug}`
- `GET /profiles/{profile_id}/career-encyclopedia`
- `GET /profiles/{profile_id}/career-encyclopedia/{career_slug}`
- `GET /profiles/{profile_id}/career-encyclopedia/{career_slug}/compare`
- `POST /profiles/{profile_id}/career-encyclopedia/{career_slug}/hypothesis`
- `POST /profiles/{profile_id}/career-encyclopedia/{career_slug}/experiment`

Decision Journal:

- `GET /profiles/{profile_id}/decision-journal`
- `POST /profiles/{profile_id}/decision-journal`
- `GET /profiles/{profile_id}/decision-journal/research-export`
- `GET /profiles/{profile_id}/decision-journal/{entry_id}`
- `PUT /profiles/{profile_id}/decision-journal/{entry_id}`
- `POST /profiles/{profile_id}/decision-journal/{entry_id}/outcome`

## Frontend Routes

- `/workspace/:profileId/integrations/browser-extension`
- `/workspace/:profileId/advisor-collaboration`
- `/workspace/:profileId/advisor-collaboration/shares`
- `/workspace/:profileId/advisor-collaboration/shares/:shareId`
- `/advisor-review/:shareToken`
- `/workspace/:profileId/interviews/:interviewId/panel-simulation`
- `/careers`
- `/careers/:careerSlug`
- `/workspace/:profileId/career-encyclopedia`
- `/workspace/:profileId/career-encyclopedia/:careerSlug`
- `/workspace/:profileId/decision-journal`

## Demo Mode

Demo seeding creates complete innovation examples:

- An extension connection and captured job.
- An adviser share with adviser comments.
- A panel interview session linked to the existing interview journey.
- Sixteen curated career roles.
- Career role hypotheses and experiments.
- At least six journal entries including active, outcome-recorded, reconsidered, adviser-related, and weekly-reflection examples.

Reset Demo deletes innovation module rows for the demo profile and reseeds them with fictional people and employers.

## Security And Privacy

Implemented controls:

- Profile-scoped extension connections and adviser shares.
- Secure random tokens stored only as hashes.
- Expiry, revocation, access-attempt limits, and optional adviser PIN.
- URL validation and SSRF-style private-network rejection.
- Captured-text sanitization and size limits.
- Audit events for token, share, comment, capture, role, and journal actions.
- No full-profile sharing by default.
- No raw journal export by default.
- No automatic adviser-to-profile mutation.
- No automatic Decision Journal-to-roadmap mutation.
- No extension secrets.
- No automatic scraping.

## Accessibility

Frontend controls use semantic buttons, links, labels, textareas, status text, and non-color status text. The Playwright coverage includes desktop and mobile route rendering. Voice interaction remains optional; panel text labels remain visible.

## Testing Guide

Backend:

- Run `backend/.venv/Scripts/python.exe -m py_compile ...` for changed backend modules.
- Run `backend/.venv/Scripts/python.exe -m pytest tests/test_innovation_extension_engine.py -q`.
- Run `backend/.venv/Scripts/python.exe -m pytest -q`.

Frontend:

- Run `npm.cmd run typecheck` in `frontend`.
- Run `npm.cmd run test` in `frontend`.
- Run `PLAYWRIGHT_FRONTEND_ONLY=true npm.cmd run test:e2e -- tests/e2e/innovation-extension.spec.ts` in `frontend`.
- Run `npm.cmd run build` in `frontend`.

Browser extension:

- Run `npm.cmd install` in `browser-extension` when dependencies are not installed.
- Run `npm.cmd run build` in `browser-extension`.

## Limitations

- Collaboration traceability has an additive Alembic migration at `0009_collaboration_traceability_extensions`; development bootstrap still supports SQLAlchemy `create_all` for isolated test databases.
- Multi-voice panel playback is not enabled until the existing voice integration is validated for multiple persona voices.
- Career-role content is curated and schema-rich, but not official labour-market or salary data.
- Admin role management endpoints are present, but no dedicated admin UI was added.
- Browser extension host permissions are local-development focused and must be reviewed before store publication.
- Adviser links are token based; adviser role labels are not identity verification.
- The implementation is an MVP and should not be described as production-ready without operational security, migration, browser-store, and empirical evaluation work.

## Academic Framing

Contribution statement:

"The innovation extension of OrganicAI Compass introduces user-triggered job capture, controlled human-adviser collaboration, evidence-aware multi-persona interview simulation, deeply structured career-role profiles, and a versioned career decision journal. These components extend the platform from automated career guidance toward a transparent human-AI-adviser collaboration system in which professional decisions, evidence, assumptions, and outcomes remain traceable and under user control."

Potential research sub-questions:

1. Does adviser collaboration improve perceived trust and decision clarity?
2. Does evidence-aware panel-interview simulation improve answer specificity?
3. Does a structured Career Encyclopedia improve understanding of professional tasks and capability requirements?
4. Does a Decision Journal help users identify incorrect assumptions and revise career strategies?
5. Does user-triggered job capture reduce friction between job discovery and evidence-based application preparation?

These questions are framed as future evaluation questions. The implementation does not claim empirical answers.
