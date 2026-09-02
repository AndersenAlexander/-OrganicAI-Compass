# Synthetic Fairness Audit

The fairness audit uses only synthetic fixtures. It does not run on identifiable real-user profiles and does not infer protected attributes.

Implemented fixture types:

- gender marker invariance
- age band invariance
- location as expected market context
- accessibility feasibility check
- employment-gap wording proxy check

Audit statuses:

- Passed
- Review required
- Possible unjustified dependency
- Data limitation
- Expected contextual difference
- Not applicable

The audit separates legitimate contextual effects from unsupported effects. Example: location may affect Market Fit, but it must not change Capability Fit. Accessibility constraints may affect experiment feasibility and support options, but must not lower demonstrated skill evidence.

The audit uses cautious technical language and does not declare discrimination.
