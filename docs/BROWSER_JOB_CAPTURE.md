# Browser Job Capture

Capture is user-triggered only. The Manifest V3 extension uses `activeTab`, `storage` and `scripting`; it does not request history, cookies, passwords, unrelated form fields, clipboard access or background monitoring.

The extension reads the visible page title, URL, selected text and visible text after the user opens the popup. It sends a short-lived profile-scoped token through `X-OrganicAI-Extension-Token`; only a hash is stored server-side. Tokens expire and can be revoked.

The backend stores `source_type=BROWSER_CAPTURE`, source URL, capture time, method, raw/sanitised text and user-confirmed text separately. Captures remain editable and removable in the review queue. A Job Analysis is created only after explicit confirmation, retaining the capture ID and source provenance. The backend never fetches an arbitrary user-provided URL for this flow.
