# RigorGraph 1.0.0rc2

RigorGraph 1.0 adds an additive Evidence Bundle v1 contract and local-first importer. HonestCI is the first supported producer profile.

The importer validates and copies the exact JSON into `.rigorgraph/artifacts`, creates computation evidence, and optionally links it to a `DRAFT` or `PROPOSED` claim. It never changes claim status. Audits recheck the saved hash and schema; the offline report shows producer, profile, result, source commit, and the trust boundary.

This release candidate includes Python wheel/source distributions, the composite GitHub Action, and an installable `rigorgraph-release` Codex marketplace ZIP containing all four skills. RC2 also corrects the PyPI Trusted Publisher action reference after RC1 stopped before any package upload. Stable 1.0 requires cross-platform fresh installs and an end-to-end HonestCI bundle import.

RigorGraph verifies workflow integrity and traceability. Evidence bundles and `VERIFIED` status do not establish absolute truth, runner authenticity, formal certification, peer review, or expert consensus.
