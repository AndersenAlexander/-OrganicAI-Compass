# OrganicAI Compass Light Mode Audit

Date: 2026-07-15

Scope: public pages, authentication pages, primary workspace pages, floating chat UI, forms, dropdown/navigation surfaces, RAG feedback, source chips, confidence/ethical notes, empty/error states, mobile layout, and selected 3D/visualization overlays.

Automated audit source: `frontend/tests/e2e/light-mode-visibility.spec.ts`

Contrast thresholds used:

- Normal readable text: 4.5:1
- Large headings and selected large card text: 3:1
- UI/card boundaries: visible border or shadow
- Disabled controls: not strict WCAG-scored, but styled to remain understandable

Known audit limits:

- Canvas/WebGL internals cannot be fully sampled by DOM contrast checks; HTML overlays and accessible fallbacks were checked.
- Image/cinematic inverse surfaces are classified separately from ordinary Light Mode panels.
- Screenshots are evidence captures, not pixel-diff baselines.

## Route checklist

| Route | Status | Primary text | Secondary text | Cards | Buttons | Forms | Dropdowns / menus | Empty / error states | Mobile | Screenshot | Remaining issue |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| `/` | FIXED | PASS | PASS | PASS | PASS | N/A | PASS | N/A | PASS | `qa/qa-light-home-1448.png`, `qa/qa-light-home-1366.png`, `qa/qa-light-home-390.png` | None from audit |
| `/about` | FIXED | PASS | PASS | PASS | PASS | N/A | PASS | N/A | PASS | `qa/qa-light-about-1448.png` | None from audit |
| `/how-it-works` | FIXED | PASS | PASS | PASS | PASS | N/A | PASS | N/A | PASS | `qa/qa-light-how-it-works-1448.png` | None from audit |
| `/principles` | FIXED | PASS | PASS | PASS | PASS | N/A | PASS | N/A | PASS | `qa/qa-light-principles-1448.png` | None from audit |
| `/research` | FIXED | PASS | PASS | PASS | PASS | N/A | PASS | N/A | PASS | `qa/qa-light-research-1448.png` | Canvas/3D interior remains manual-review territory |
| `/project-roadmap` | FIXED | PASS | PASS | PASS | PASS | N/A | PASS | N/A | PASS | `qa/qa-light-project-roadmap-1448.png` | None from audit |
| `/blog` | FIXED | PASS | PASS | PASS | PASS | N/A | PASS | N/A | PASS | `qa/qa-light-blog-1448.png` | None from audit |
| `/blog/rag-source-visible-coaching` | PASS | PASS | PASS | PASS | PASS | N/A | PASS | N/A | PASS | Route smoke-tested; no dedicated screenshot | None from audit |
| `/login` | FIXED | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | `qa/qa-light-login-1448.png` | None from audit |
| `/register` | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | Route sweep-tested; no dedicated screenshot | None from audit |
| `/dashboard` | FIXED | PASS | PASS | PASS | PASS | N/A | PASS | PASS | PASS | `qa/qa-light-dashboard-1448.png`, `qa/qa-light-dashboard-1024.png`, `qa/qa-light-dashboard-390.png` | None from audit |
| `/diagnostic` | FIXED | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | `qa/qa-light-diagnostic-1448.png`, `qa/qa-light-diagnostic-390.png` | Disabled CTA understandable; excluded from strict active-button contrast |
| `/profile/demo-profile` | FIXED | PASS | PASS | PASS | PASS | N/A | PASS | N/A | PASS | `qa/qa-light-profile-1448.png` | WebGL scene internals require manual visual review |
| `/coach/demo-profile` | FIXED | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | `qa/qa-light-coach-1448.png`, `qa/qa-light-coach-390.png` | Dark sidebar is intentional inverse surface |
| `/recommendations/demo-profile` | FIXED | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | `qa/qa-light-recommendations-1448.png` | None from audit |
| `/roadmap/demo-profile` | FIXED | PASS | PASS | PASS | PASS | N/A | PASS | PASS | PASS | `qa/qa-light-roadmap-1448.png` | None from audit |
| `/knowledge-base` | FIXED | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | `qa/qa-light-knowledge-base-1448.png`, `qa/qa-light-knowledge-base-768.png`, `qa/qa-light-knowledge-base-390.png` | None from audit |
| `/demo` | PASS | PASS | PASS | PASS | PASS | N/A | PASS | N/A | PASS | Route smoke-tested; no dedicated screenshot | None from audit |
| `/learning-paths` | PASS | PASS | PASS | PASS | PASS | N/A | PASS | N/A | PASS | Route smoke-tested; no dedicated screenshot | None from audit |
| `/future-scenarios` | PASS | PASS | PASS | PASS | PASS | N/A | PASS | N/A | PASS | Route smoke-tested; no dedicated screenshot | None from audit |
| `/projects` | PASS | PASS | PASS | PASS | PASS | N/A | PASS | N/A | PASS | Route smoke-tested; no dedicated screenshot | None from audit |
| `/growth-timeline` | PASS | PASS | PASS | PASS | PASS | N/A | PASS | N/A | PASS | Route smoke-tested; no dedicated screenshot | None from audit |
| `/community` | PASS | PASS | PASS | PASS | PASS | N/A | PASS | N/A | PASS | Route smoke-tested; no dedicated screenshot | None from audit |
| `/co-creation-studio` | PASS | PASS | PASS | PASS | PASS | N/A | PASS | N/A | PASS | Route smoke-tested; no dedicated screenshot | None from audit |
| `/ai-constitution` | PASS | PASS | PASS | PASS | PASS | N/A | PASS | N/A | PASS | Route smoke-tested; no dedicated screenshot | None from audit |
| `/report/demo-profile` | PASS | PASS | PASS | PASS | PASS | N/A | PASS | N/A | PASS | Route smoke-tested; no dedicated screenshot | None from audit |
| `/fear-transformer/demo-profile` | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | Route smoke-tested; no dedicated screenshot | None from audit |
| `/my-journey` | PASS | PASS | PASS | PASS | PASS | N/A | PASS | PASS | PASS | Route smoke-tested; no dedicated screenshot | None from audit |
| `/settings` | NOT APPLICABLE | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | Not present in current router | Route not implemented |
| `/evaluation` | NOT APPLICABLE | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | Not present in current router | Route not implemented |
| `/admin` | NOT APPLICABLE | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | Not present in current router | Route not implemented |

## Screenshot inventory

Desktop and public/auth:

- `qa/qa-light-home-1448.png`
- `qa/qa-light-about-1448.png`
- `qa/qa-light-how-it-works-1448.png`
- `qa/qa-light-principles-1448.png`
- `qa/qa-light-research-1448.png`
- `qa/qa-light-project-roadmap-1448.png`
- `qa/qa-light-blog-1448.png`
- `qa/qa-light-login-1448.png`
- `qa/qa-light-home-1366.png`

Workspace:

- `qa/qa-light-dashboard-1448.png`
- `qa/qa-light-diagnostic-1448.png`
- `qa/qa-light-profile-1448.png`
- `qa/qa-light-coach-1448.png`
- `qa/qa-light-recommendations-1448.png`
- `qa/qa-light-roadmap-1448.png`
- `qa/qa-light-knowledge-base-1448.png`
- `qa/qa-light-dashboard-1024.png`
- `qa/qa-light-knowledge-base-768.png`

Mobile:

- `qa/qa-light-home-390.png`
- `qa/qa-light-dashboard-390.png`
- `qa/qa-light-diagnostic-390.png`
- `qa/qa-light-coach-390.png`
- `qa/qa-light-knowledge-base-390.png`

Dark regression captures:

- `qa/qa-dark-home-regression.png`
- `qa/qa-dark-dashboard-regression.png`
- `qa/qa-dark-knowledge-base-regression.png`

## Fix summary

- Added/normalized semantic Light/Dark theme tokens in `organicai-tokens.css`.
- Replaced brittle Light Mode inheritance for cards, buttons, inputs, placeholders, chips, RAG feedback, source chips, confidence notes, ethical notes, footer text, and selected Tailwind compatibility classes.
- Fixed floating chat launcher and expanded chat panel Light Mode text/background/focus contrast.
- Fixed public page primary button gradients that used insufficient white-text contrast.
- Removed conflicting Principles floating-chat overrides.
- Fixed AI Coach chat message metadata/source-chip Light Mode colors.
- Fixed Human Potential Globe HTML labels and center text for Light Mode.
- Fixed Research scene core label for Light Mode.
- Classified the Coach page sidebar as an intentional inverse surface.
- Added Playwright contrast utility and broad Light Mode route audit.
