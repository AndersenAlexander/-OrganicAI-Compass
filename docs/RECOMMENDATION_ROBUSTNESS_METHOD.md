# Recommendation Robustness Method

Status: implemented; deterministic technical test; pending empirical validation.

The robustness lab perturbs non-sensitive operational inputs:

- weekly learning time
- learning budget
- market-data window
- evidence recency
- support availability

Metrics include:

- top-1 stability
- top-k overlap
- label stability
- path-frontier overlap
- maximum rank movement
- average rank movement
- sensitivity count
- threshold-crossing count
- missing-data impact
- constraint-violation changes

Interpretations are qualitative: stable under tested scenarios, moderately sensitive, highly sensitive, data-limited or insufficient information. Robustness is not proof that a recommendation is correct.
