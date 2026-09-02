# Synthetic Fairness Test Protocol

Status: implemented as synthetic evaluation; pending empirical validation and legal review.

The Synthetic Fairness Lab uses synthetic fixtures only. It does not store protected personal attributes for normal users, infer sensitive attributes, or claim legal compliance.

Implemented test types:

- invariance tests;
- monotonicity tests;
- missing-data behavior tests;
- counterfactual consistency tests;
- rank-stability tests;
- dominance-consistency tests;
- evidence-category separation tests.

Expected contextual effects may occur when non-sensitive operational context changes, such as location affecting Market Fit. Those effects must not alter Capability Fit or verified evidence categories.

Current limitations:

- synthetic tests cannot prove real-world fairness;
- protected attributes are not inferred for real users;
- no fairness certification claim is made.
