# Security policy

## Supported versions

RigorGraph is a public-beta project. Security fixes are made against the latest 1.x release and `main`; older releases may require upgrading.

| Version | Security support |
| --- | --- |
| Latest 1.x | Supported |
| Older 1.x | Upgrade to the latest 1.x |
| Pre-1.0 | Not supported |

## Report a vulnerability

Use a [private GitHub Security Advisory](https://github.com/f0909172434/rigorgraph/security/advisories/new). Do not open a public issue for a suspected vulnerability.

Please include the affected version or commit, operating system, impact, a minimal sanitized reproduction, and any proposed mitigation. Remove credentials, private research records, unpublished findings, and unnecessary exploit payloads. The maintainer will confirm receipt and coordinate remediation and disclosure on a best-effort basis.

## Data and credential boundary

RigorGraph does not require an account, API key, telemetry endpoint, hosted database, or built-in paid model API. It treats project YAML, JSONL records, evidence bundles, local evidence files, and user-authored text as untrusted input.

- Do not store credentials or personal secrets in `rigorgraph.yaml`, `.rigorgraph/`, evidence bundles, or generated reports.
- A report embeds the project's claims, evidence metadata, verification records, and audit findings. Review it before sharing; self-contained does not mean safe to publish.
- Remote evidence URIs are recorded as references. RigorGraph does not authenticate their owner or fetch them during an audit.
- SHA-256 checks detect byte changes; they do not establish authorship, provenance, runner authenticity, or truth.
- The GitHub Action runs with the permissions and repository contents supplied by the caller. Use least-privilege workflow permissions and do not expose secrets to untrusted pull-request code.

## Security scope

The main security boundaries are project-root path containment, symlink handling, safe JSON/YAML parsing, HTML data embedding, evidence and bundle hashing, concurrent record writes, release provenance, and third-party dependencies. The maintained threat model and residual risks are documented in [docs/THREAT_MODEL.md](docs/THREAT_MODEL.md).

Workflow-integrity checks do not prove that a claim is correct. `VERIFIED` means accepted by the recorded workflow, not formal certification, peer review, expert consensus, or absolute truth.
