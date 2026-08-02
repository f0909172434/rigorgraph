# RigorGraph release policy

RigorGraph remains a public-beta product while its 1.x public interfaces are additive. Required Evidence Bundle v1 fields, stable audit codes, CLI JSON fields, and GitHub Action inputs and outputs are not removed or redefined in a 1.x release. Breaking changes require a new major or bundle schema version.

## Hard gates

A release candidate or stable release requires tests, lint, generated schemas, locale parity, a reproducible frontend, plugin validation, clean wheel and source installs, GitHub Action coverage, and the full release check. Security defects, data-loss risk, invalid state transitions, broken packages, or misleading evidence promotion block release.

Stable 1.0 additionally requires the RC wheel, Action, HonestCI bundle integration, and Codex marketplace ZIP to pass fresh-install tests on the supported platform and runtime matrix.

## External evidence

External use is evidence, not permission. No fixed tester count blocks development or release. RigorGraph has no telemetry; public feedback must not contain private research data.

## Human approval

Publishing to PyPI, GitHub Releases, or a plugin marketplace requires an explicit maintainer approval after the automated gates pass.
