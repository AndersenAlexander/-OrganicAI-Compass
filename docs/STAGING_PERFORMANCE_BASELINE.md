# Staging Performance Baseline

Technical draft - requires legal and operational review before public deployment.

Task 13A.2 local staging performance baseline - not a production capacity test.

Synthetic operations: frontend root, health, readiness, staging demo login, profile read, assessment read and Privacy Center summary. External AI providers were not called.

| Phase | Duration | Concurrency | Requests | Success | Failed | RPS | p50 | p95 | p99 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 60s | 5 | 133 | 133 | 0 | 2.167 | 2316.66 ms | 2499.51 ms | 2743.3 ms |
| 2 | 60s | 10 | 120 | 120 | 0 | 1.898 | 5257.1 ms | 5572.54 ms | 5624.03 ms |

Resource sample:

- backend CPU: 0.22%
- backend memory: 211.1MiB / 11.45GiB
- PostgreSQL connections: 6
- proxy CPU: 0.00%
- proxy memory: 3.066MiB / 11.45GiB

Interpretation: the stack completed all synthetic requests without errors. The latency values reflect local Windows/Docker Desktop staging constraints and do not represent cloud or production capacity.
