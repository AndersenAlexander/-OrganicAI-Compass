# NAV Job Vacancy Feed Integration Notes

OrganicAI Compass uses a provider-adapter boundary for labour-market data. The NAV Job Vacancy Feed adapter is designed for backend-only use and does not expose credentials or direct feed calls to the frontend.

Official references checked on 2026-07-21:

- NAV Job Vacancy Feed documentation: https://navikt.github.io/pam-stilling-feed/
- Arbeidsplassen API terms: https://arbeidsplassen.nav.no/vilkar-api

Implementation constraints:

- The deprecated public feed is not used.
- The frontend never calls NAV directly.
- NAV credentials are stored only in backend settings.
- Missing credentials do not break the application; provider status degrades to demo mode.
- Provider sync stores a cursor, ETag, Last-Modified metadata, run status, error details, and content hashes.
- Provider and external job ID are unique together, making feed processing idempotent.
- Stopped, expired, inactive, or deleted ads are not displayed as active opportunities.
- Historical inactive records are retained only as local research/audit records when allowed by source rules.

NAV compliance assumptions:

- Consumers must keep local copies up to date with changes in the feed.
- Consumers must remove inactive or deleted advertisements from public active views.
- Application flows must link back to the official ad or employer application function when available.
- Personal data obligations remain with the data controller operating the system.

The current default deployment uses curated demo data. Enabling live NAV data requires backend environment configuration and operational review.

