# Supply Chain Security

Technical draft - requires legal and operational review before public deployment.

Supply-chain checks cover Python dependency consistency, npm audit, container audit where a scanner is available, secret scanning, unsafe source artifacts and SBOM generation.

Temporary acceptances must be documented by package, version, reason, owner and review date. Findings are classified as blocking, high-priority, advisory, accepted-temporary or false-positive-reviewed.

Task 13A.2 local result:

- Python audit: passed.
- npm audit: advisory.
- Container audit: advisory because Trivy or Docker Scout was not available in the local validation path.
- Source secret scan: no blocking findings.
- Image/source artifact checks: no environment files, databases, dumps or logs included in the safe source archive.
- SBOM report paths emitted by the supply-chain script: `reports/supply-chain/backend-image-sbom.spdx.json`, `reports/supply-chain/frontend-image-sbom.spdx.json`, `reports/supply-chain/source-sbom.spdx.json`.
- Task 13A.2 expected SBOM aliases also exist at `reports/supply-chain/backend-image-sbom.json`, `reports/supply-chain/frontend-image-sbom.json` and `reports/supply-chain/source-sbom.json`.
- SBOM limitation: the local SPDX files parse and identify format/name/license, but they are minimal documents and do not contain a complete component inventory.
- Blocking findings: 0.

Accepted advisories must be reviewed before public production readiness is claimed.
