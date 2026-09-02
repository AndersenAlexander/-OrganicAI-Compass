# Career Transition Pareto Simulator

Feature name: Career Transition Pareto Simulator.

Purpose: compare multiple career-transition paths without collapsing objectives into one opaque best-career score.

Objective version: `career-transition-objectives-v1`.

Implemented objectives:

- transition duration
- direct monetary cost
- weekly effort
- financial risk
- evidence gap
- capability gap
- Personal Fit
- Capability Fit
- Market Fit
- Support Fit
- local opportunity availability
- language barrier
- accessibility
- reversibility
- portfolio reuse
- transferable skill reuse
- dependence on uncertain assumptions
- expected stability under AI-related change

The simulator calculates non-dominated paths. A path is dominated when another path is equal or better on all selected objectives and strictly better on at least one objective.

Scenario presets:

- Fastest realistic transition
- Lowest financial risk
- Maximum use of existing evidence
- Strongest market alignment
- Highest support feasibility
- Balanced transition
- User-defined scenario

Presets only configure objective preferences. They do not contain hidden career preferences.

Roadmap proposals remain proposals until the user confirms them through a roadmap workflow.
