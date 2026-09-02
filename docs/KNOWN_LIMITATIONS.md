# Known Limitations

This release candidate has technical implementation evidence, not empirical effectiveness evidence.

- **Empirical evaluation:** no participant study, career-outcome study, psychometric validation, hiring-validity study, or real-world fairness study is recorded.
- **Runtime PostgreSQL:** during the 2026-08-24 audit, `127.0.0.1:55432` was Docker Desktop proxy PID 15464. Docker Desktop repeatedly reported no route to its VM endpoint `192.168.65.7:2376`, and PostgreSQL container health checks plus a read-only SQLAlchemy connection timed out. Consequently live migration state, existing-account login, data integrity, and live provider status could not be revalidated. Restore Docker Desktop/WSL networking without resetting volumes or recreating `organicai_app` before controlled UAT.
- **Providers:** NAV/market, voice/ElevenLabs, OpenAI-related, browser-extension, and other optional integrations depend on explicit configuration, credentials, source availability, and network state. A provider being unavailable must not be represented as live data; text flows should remain usable where designed.
- **Market content:** catalogues, cached values, and demo vacancies can be partial, date-bound, or synthetic. They are not exhaustive live market intelligence or a suitability guarantee.
- **Synthetic Fairness Lab:** this is synthetic fixture engineering validation only; it is not proof of fairness, absence of bias, legal compliance, or certification.
- **Robustness Lab:** deterministic scenario offsets are not a causal model, statistical confidence interval, calibration proof, or validation of upstream scores.
- **Browser Job Capture:** it requires an explicit extension connection and user review/confirmation; it is not background job collection.
- **Applications and interviews:** outputs depend on user-entered material and source availability. They do not predict a hiring decision, employment outcome, personality, honesty, intelligence, anxiety, cultural fit, or employability.
- **Build performance:** the production build passes but reports chunks over the configured 500 kB warning threshold; this requires a later measured performance pass, not a late release-candidate refactor.
- **Test environment:** the repository virtual-environment Python launcher is currently not portable in this workstation context; isolated checks used the installed Python interpreter and explicit disposable databases. This is a reproducibility/environment issue to repair before CI or controlled UAT.
