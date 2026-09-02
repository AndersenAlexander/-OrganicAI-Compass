# Container Registry Plan

Technical draft - requires registry approval before publishing.

- Registry: not selected.
- Images must remain private by default.
- Tags must be immutable for release candidates.
- Deployments should reference image digests where supported.
- Retention policy must be configured before publishing.
- Vulnerability scanning is required.
- SBOM attachment is required.
- Provenance is required for release candidates.
- Secrets must not exist in image layers.

Suggested tags:

```text
organicai-backend:<semantic-version>
organicai-backend:<commit-sha>
organicai-frontend:<semantic-version>
organicai-frontend:<commit-sha>
```

No images are published during Task 13B.0.
