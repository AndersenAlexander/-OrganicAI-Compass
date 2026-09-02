# Market-to-Application Workflow

The implemented workflow is:

`Career Hypothesis → Market Radar → Job Opportunity → Job Advertisement Analysis → User-confirmed requirements → Evidence Mapping → Application Readiness → Evidence-locked CV/Cover Letter → Application Tracker`

The workflow is decision support. It does not select a career for the user, predict hiring, estimate ATS success, submit applications, or change My Roadmap automatically.

## Provenance and source safety

Every market provider exposes its configured provider, availability state, last successful fetch, freshness timestamp, freshness label, error state, fallback state, and coverage notes. The supported states are `LIVE`, `CACHED`, `STALE`, `DEMO`, and `UNAVAILABLE`.

The API never silently substitutes fictional vacancies for an unavailable live provider. HTTP callers must send `demo_mode=true` to view the isolated deterministic fixture feed. Demo records are marked at provider, posting, analysis, document, and application level.

Vacancies preserve source URL, provider event metadata, source version, content hash, canonical job key, and source provenance. Different provider records with the same canonical identity are deduplicated in user-facing results while their source records remain available for traceability.

Market signals store observation and comparison windows, sample counts, coverage sufficiency, source metadata, and cautious observed-sample language. Insufficient samples are labelled as insufficient coverage; they are not presented as forecasts or hiring probabilities.

## Job Advertisement Analysis

The analyser accepts a saved market posting, supported allowlisted URL, pasted text, or confirmed browser capture. Imported content is sanitised and bounded. URL fetching is backend-only, allowlisted, size-limited, and protected by a private-IP guard.

Deterministic extraction stores the original excerpt, source location, extraction method, extraction timestamp, confidence, extracted category/type, normalised skill where available, and analysis version. The extracted interpretation is not authoritative until the user accepts, edits, reclassifies, or rejects each active requirement.

The user-confirmation endpoint creates a versioned confirmation record. Evidence mapping reports `NOT ASSESSED` for unconfirmed requirements. Rejected requirements are excluded from readiness counts; they remain preserved in analysis history.

## Evidence Mapping and readiness

Confirmed requirements are matched only against the profile's Evidence Passport and dated evidence metadata. Mapping can report `CONFIRMED EVIDENCE`, `PARTIAL EVIDENCE`, `SELF-REPORT ONLY`, `MISSING`, `OUTDATED`, or `CONFLICTING`, plus deterministic reasons and recommended next actions.

Readiness is a transparent evidence summary with supported, partial, missing, outdated, and unknown counts. It can say `Apply now`, `Apply with positioning`, `Prepare first`, `Low current feasibility`, or `Insufficient information`. It never emits recruiter, ATS, interview, employability, or hiring probabilities.

## Evidence Lock and documents

CV and cover-letter claims carry a support state: `SUPPORTED`, `PARTIALLY_SUPPORTED`, `SELF_REPORT_ONLY`, `UNSUPPORTED`, `NEEDS_REVIEW`, or `MOTIVATIONAL`. Motivational language is intentionally kept separate from factual evidence claims. Unsupported high-risk claims are blocked by deterministic rules and safer alternatives are offered.

Document versions snapshot the profile version, confirmed job-analysis version, Evidence Passport version, evidence-lock state, warnings, and whether the user edited the version. Export is local HTML plus structured JSON; blocked or unreviewed claims require explicit warning acknowledgement. The platform never auto-applies and makes no ATS guarantee.

## Tracker and Journey integration

Application records store the confirmed analysis version and readiness/evidence snapshots. Tracker stages, contacts, outcomes, and recalibration suggestions are user-recorded observations. Recalibration suggestions require explicit confirmation and do not mutate My Roadmap.

My Journey exposes the market/application counts and links back into the same workflow. Interview Journey remains a separate existing module; this workflow does not create a second interview engine or alter its ownership boundaries.

## Limitations

Live NAV availability depends on backend credentials and operational review. Demo data is fictional and not current Norwegian market coverage. Local signal windows are sample-bounded, ESCO may remain a local fallback, PDF generation is not enabled, and research exports remain consent-based and pseudonymous.
