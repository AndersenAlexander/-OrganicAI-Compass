# Career Transition Pareto Method

Status: implemented; deterministic technical test; pending empirical validation.

The Career Transition Pareto Simulator compares several possible paths without selecting an authoritative best career. A path is dominated only when another path is at least as favourable on all selected comparable criteria and strictly more favourable on at least one criterion.

Dominated paths remain visible. Hard-constraint violations are shown and excluded from feasible recommendations unless the user explicitly includes infeasible paths in a later workflow.

Recalculation creates a new `CareerTransitionSimulation` and preserves the historical result.

Roadmap actions and Decision Journal entries require explicit user action. A saved path does not replace Career Hypotheses or roadmap state.
