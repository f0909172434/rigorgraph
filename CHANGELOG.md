# Changelog

## Unreleased

- Add CodeQL, grouped Dependabot updates, full-SHA Action pinning, and a stable `ci-gate`.
- Document the security, data, credential, and threat-model boundaries.
- Clarify that RigorGraph remains a public-beta product while published 1.x interfaces follow additive compatibility.
- Add an actual offline demo-report screenshot and clearer use, non-use, and interoperability guidance.
- Derive release-tag validation from the package version instead of a hard-coded tag.

## 1.0.0

- Promote the additive Evidence Bundle v1 and HonestCI profile after cross-project tests.
- Confirm fresh public-registry installs on Windows, Ubuntu, and macOS with Python 3.11 and 3.14.
- Ship reproducible Python distributions, checksums, attestations, a composite Action, and an isolated Codex marketplace ZIP.
- Preserve the boundary that imported computation evidence never promotes or verifies a claim.

## 1.0.0rc2

- Add the additive Evidence Bundle v1 schema and HonestCI result profile.
- Add idempotent, local-first bundle import with explicit draft-claim linking.
- Revalidate imported bundles during audits and expose their provenance boundary in reports.
- Add reproducible Codex marketplace packaging and OIDC release automation.
- Pin the PyPI Trusted Publisher action to the verified `v1.14.2` release.

## 1.0.0rc1 (unpublished)

- The tag reached the protected release workflow, but publishing stopped before contacting PyPI because the workflow referenced a nonexistent action tag.

## 0.1.0b1

- Initial public beta CLI, offline report, GitHub Action, skill pack, and deterministic audit gates.
