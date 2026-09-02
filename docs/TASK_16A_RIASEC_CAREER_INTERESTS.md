# Task 16A RIASEC-Inspired Career Interests

Date: 2026-08-09
Scope: post-acceptance extension from final dissertation baseline `7215f9a92671e8050f99d38d39fc699634631e18`.

## Why This Was Added

The audit found that Natural Discovery already collected broad interests, preferred activities, values, learning style, cognitive style, and optional capability prefill signals. It did not directly and evenly ask about all six RIASEC vocational-interest dimensions. Artistic, Investigative, and Social signals were reasonably represented through existing topic and orientation choices, while Realistic, Enterprising, and Conventional were weak or mostly indirect.

Task 16A therefore adds a compact RIASEC-inspired Career Interests subsection to Natural Discovery. It is used as one transparent vocational-interest signal inside Natural Fit, not as a replacement for the four-layer Human Discovery architecture.

## Current Natural Discovery Audit

The pre-Task 16A Natural Discovery question inventory is recorded in `evidence/task16a/question-inventory.json`. It covers 20 question groups:

- topics that attract attention;
- activities that create flow;
- problems naturally noticed;
- preferred orientation;
- AI concerns and uncertainty;
- values and desired future;
- contribution if barriers were removed;
- optional human needs;
- optional capability prefill;
- learning style;
- cognitive style;
- AI experience, tools, confidence, goals, and interaction preference.

Existing scoring before Task 16A:

- Natural Discovery stored a JSON diagnostic payload and generated a profile snapshot.
- Some answers prefilled the deeper Capability Assessment for later user confirmation.
- Skills and AI exposure were explicitly excluded from Natural Fit and treated only as capability prefill.
- Career-role Natural Fit was calculated later by the assessment engine from career interests, values, and work-style preferences.

## Coverage Before Task 16A

| Dimension | Existing coverage | Classification | Reason |
| --- | --- | --- | --- |
| Realistic | Nature, Technology, Hands-on practice, Practical cognitive style | Weak | Mostly indirect; no direct hands-on vocational-interest item. |
| Investigative | Science, Technology, Ideas, Systems, Learning, analysis/research skills | Adequate | Several direct or near-direct options, but some skill options mix capability. |
| Artistic | Design, Storytelling, Visual creation, Creativity | Adequate | Strong topic and value coverage, but not evenly scored as a vocational-interest dimension. |
| Social | Education, Well-being, Community, People, Care, Teaching | Adequate | Multiple clear preference signals. |
| Enterprising | Leadership skill, Plan projects goal, some autonomy/initiative text | Weak | Mostly capability or goal-adjacent; no direct interest item. |
| Conventional | Structured/practical cognitive style, responsibility, planning/process text | Weak | Indirect and sparse; no direct structured-process interest item. |

Audit decision: PARTIAL COVERAGE.

## Questions Added

One compact subsection was added to Natural Discovery:

Prompt: "How appealing would you find work that involves these activities?"

It contains six direct preference items:

- Realistic: practical hands-on activity with tools, physical systems, or technical operations.
- Investigative: research, analysis, data, science, or solving complex questions.
- Artistic: design, writing, visual expression, originality, or creating new concepts.
- Social: helping, teaching, mentoring, supporting, or developing people.
- Enterprising: initiating projects, persuading, negotiating, leading decisions, or building opportunities.
- Conventional: organising information, documenting details, planning procedures, or maintaining accurate systems.

Answer scale:

- Not appealing
- Slightly
- Moderately
- Very
- Extremely

No existing question was removed.

## Definitions

The implementation uses RIASEC-inspired Career Interests:

- R, Realistic: practical, hands-on, tools, physical systems, building, repair, technical operations.
- I, Investigative: analysis, research, data, science, complex questions, how systems work.
- A, Artistic: design, writing, visual expression, originality, aesthetics, imagination.
- S, Social: helping, teaching, mentoring, supporting, communication, human development.
- E, Enterprising: initiating, persuading, negotiation, entrepreneurship, leadership decisions.
- C, Conventional: organisation, documentation, accuracy, planning, procedures, predictable systems.

## Scoring Method

Rule-set version: `riasec-career-interests-v1`.

Direct Natural Discovery responses are converted from 1-5 appeal values to 0-100 platform-relative scores. Legacy answers can provide lower-confidence derived signals for older profiles, but only enough information produces a result. Missing or insufficient information produces `insufficient_information`.

Qualitative bands:

- High: 75-100
- Moderate-High: 60-74
- Moderate: 45-59
- Lower: 25-44
- Limited: 0-24

The top pattern, for example `A-I-S`, is labelled as the current career-interest pattern, not a personality type. Close scores are explicitly described as closely balanced.

## Source Of Truth Architecture

Natural Discovery remains the source for initial vocational-interest preferences. The deeper assessment may prefill matching career-interest items from Natural Discovery, but the user must confirm or edit them before assessment scoring persists.

No schema migration was added. Data is stored in the existing diagnostic/profile JSON structures.

## Relationship To Natural Fit

RIASEC-inspired Career Interests contribute to Natural Fit through career-interest signals. Natural Fit remains broader and also includes values and work-style preferences. Capability Fit, Evidence Strength, Transition Feasibility, Market Fit, and Support Fit remain separate.

## Distinctions

Capability Fit uses current self-reported skills, AI readiness, and professional exposure. RIASEC-inspired interests do not use years of experience, job title, education, certificates, portfolio, salary, or market demand.

Evidence Strength uses evidence status and practical/project/certification signals. A high interest with weak evidence remains worth testing, not proof of qualification.

Transition Feasibility uses constraints such as time, budget, readiness, and skill gaps. Constraint changes do not rewrite career interests.

## Ethical Wording And Limitations

The UI says "RIASEC-inspired Career Interests" and describes current preferences. It does not claim a clinical personality test, psychological diagnosis, population-norm percentile, fixed talent, ideal career, perfect career, destiny, guaranteed success, or employment probability.

Legacy profiles remain usable. If enough legacy Natural Discovery signals exist, the profile can show a lower-confidence derived result. Otherwise the UI asks the user to complete Natural Discovery.
