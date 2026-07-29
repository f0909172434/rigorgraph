# RigorGraph 1.0.0

RigorGraph 1.0 turns AI-assisted research into an auditable, local-first claim-evidence graph. It records claims, scoped evidence, independent verification, dependencies, and unresolved gaps without treating numerical scans, model consensus, or CI results as proof.

The stable release defines the additive Evidence Bundle v1 contract and imports HonestCI computation results with allowlisted provenance and artifact hashes. Importing a bundle preserves the exact JSON and may link it only to a `DRAFT` or `PROPOSED` claim; it never changes claim status. Audits recheck the stored hash, schema, paths, profile, and evidence boundary.

Release artifacts include Python wheel and source distributions, the composite GitHub Action, checksums, GitHub attestations, and a reproducible `rigorgraph-release` Codex marketplace ZIP containing all four skills. Public PyPI fresh installs passed on Windows, Ubuntu, and macOS with Python 3.11 and 3.14.

RigorGraph verifies workflow integrity and traceability. Evidence bundles and `VERIFIED` status do not establish absolute truth, runner authenticity, formal certification, peer review, or expert consensus.
