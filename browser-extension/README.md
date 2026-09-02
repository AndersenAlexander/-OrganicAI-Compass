# Save to OrganicAI Compass

Manifest V3 browser extension for user-triggered job advertisement capture.

## Installation Guide

```powershell
npm install
npm run build
```

Load `browser-extension/` as an unpacked extension in Chrome or Edge developer mode after building.

1. Open OrganicAI Compass and go to `/workspace/:profileId/integrations/browser-extension`.
2. Select `Connect extension` and copy the one-time connection token.
3. Open the extension popup and set the backend URL, profile ID, and token.
4. Open a job advertisement, select relevant text if useful, then open the extension popup.
5. Review the detected title, employer, URL, source domain, capture method, and description preview.
6. Choose `Save` or `Save for review`. OrganicAI Compass always requires a review/confirmation before creating a Job Analysis.

The popup supports manual correction before sending. Low-quality captures should be reviewed in OrganicAI Compass before confirmation.

## Permissions

- `activeTab`: reads the current tab only after the user opens the extension.
- `storage`: stores backend URL, profile ID, and the short-lived connection token locally.
- `scripting`: injects a one-time function from the popup to read selected text and visible text.
- Host permissions are limited to `http://localhost:8000/*` and `http://127.0.0.1:8000/*`.

The extension does not request browser history, cookie, password, form-content, or broad all-site permissions.

## Privacy Guide

Capture is not automatic. The popup reads the current page only after explicit user action and sends only the URL, title, selected text, visible text preview, source domain, capture method, requested action, and extension version to the OrganicAI Compass backend.

No backend secrets or database credentials are stored in the extension. Use the connection token generated inside OrganicAI Compass and revoke it from the browser-extension settings page when needed.

The extension does not crawl websites, run background scraping, capture cookies, capture passwords, capture form contents, store raw page HTML, or send a complete DOM snapshot.
