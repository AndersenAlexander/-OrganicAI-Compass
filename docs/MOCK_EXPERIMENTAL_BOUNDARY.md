# Mock And Experimental Boundary

Status: explicit boundary established for Task 13B.0.1.

These modules are classified as Experimental Concept Demo, not evaluated MVP functionality:

| Module | Strategy | Boundary |
| --- | --- | --- |
| Future Scenarios | Experimental Concept Demo | Synthetic frontend data, non-persistent, visible experimental notice. |
| Human Contribution Projects | Experimental Concept Demo | Synthetic frontend data, non-persistent, visible experimental notice. |
| Growth Timeline | Experimental Concept Demo | Synthetic frontend data, non-persistent, visible experimental notice. |
| Learning Paths prototype | Experimental Concept Demo | Synthetic frontend data, non-persistent, visible experimental notice. |
| Personal AI Constitution | Experimental Concept Demo | Synthetic frontend data, non-persistent, visible experimental notice. |
| `backend/app/routers/advanced.py` | Protected experimental API | Requires authenticated user, uses bounded Pydantic request schemas, rejects extra payload fields, and does not echo arbitrary user payloads. |

The prototype links were removed from `exploreNavigation` so they do not distract from the career-resilience MVP workspace.

Evaluated MVP claims must exclude these modules until each is connected to a real authenticated persistent workflow and covered by release-gate validation.
