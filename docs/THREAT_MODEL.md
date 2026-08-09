# Threat model

This document describes RigorGraph's maintained security boundary. It is a design and review aid, not a claim that the software is vulnerability-free.

## Protected assets

- the integrity and availability of claim, evidence, verification, and project configuration records;
- local evidence and imported bundle bytes referenced by those records;
- the confidentiality of research content before a user intentionally shares it;
- the integrity of generated reports, Python distributions, GitHub Action behavior, and Codex plugin bundles;
- CI and release credentials supplied by GitHub, PyPI, or a user's environment.

## Trust boundaries and data flow

1. A user or CI checkout supplies YAML, JSONL, evidence bundles, evidence files, paths, and report destinations.
2. The Python CLI parses and validates records, resolves local paths against the project root, hashes local bytes, and writes local state.
3. The report generator embeds validated project data into a self-contained HTML viewer. The viewer does not need a runtime network connection, but anyone who receives the file can read the embedded data.
4. The composite GitHub Action installs the checked-out RigorGraph source, audits the caller-selected path, writes a job summary, and uploads the generated report.
5. The release workflow builds distributions and a plugin bundle, writes checksums, creates GitHub provenance attestations, and publishes through GitHub-provided tokens only after the configured environment gate.

The project directory is trusted as the intended read/write scope, but its contents are not trusted to be well formed or truthful. The local operating system, Python runtime, browser, GitHub runner, package registries, and their administrators are outside RigorGraph's control.

## Threats and current controls

| Threat | Current controls | Residual risk / user action |
| --- | --- | --- |
| A local evidence path escapes the project | Paths are resolved against the project root; escapes and symlinked imported bundle targets are rejected; local evidence requires a SHA-256 digest. | A compromised OS or filesystem can race or replace files. Run sensitive audits on a trusted machine and review warnings. |
| Malformed or hostile JSON/YAML changes program state | Pydantic schemas, strict identifiers and enums, `json` parsing, and `yaml.safe_load` reject invalid records. | Resource-exhaustion inputs are not a hardened sandbox. Limit untrusted file size and isolate hostile repositories. |
| User text breaks out of the offline report | Embedded JSON escapes HTML-significant characters and the viewer bundles its runtime assets without remote script or stylesheet URLs. | The report contains the underlying research data. Treat the whole HTML file as sensitive and open it in an updated browser. |
| A bundle or evidence file changes after review | Imported bundle bytes are preserved and hashed; local evidence and accepted claim/evidence snapshots are rechecked during audit. | SHA-256 proves byte equality only. It does not authenticate the producer or establish correctness. |
| Concurrent commands corrupt append-only records | Project writes use a local lock and atomic record update paths. | Network filesystems and abrupt process or machine failure may have weaker guarantees; keep version-control backups. |
| CI input accesses secrets or gains excessive authority | Workflows declare explicit permissions, release publication uses OIDC, and external actions are pinned to full commit SHAs. | A caller can grant broader permissions. Do not make secrets available to workflows that execute untrusted repository code. |
| A dependency or release artifact is compromised | Dependabot covers Python, frontend npm, and Actions; CodeQL analyzes Python and JavaScript/TypeScript; release artifacts receive checksums and provenance attestations. | These controls reduce risk but do not eliminate supply-chain compromise. Verify the expected tag, digest, and attestation before high-trust use. |
| An audit result is mistaken for truth | Evidence classes, verifier independence, snapshot binding, and promotion rules are deterministic; reports repeat the truth-status disclaimer. | Human or AI reasoning can still be wrong. Use appropriate expert or formal review for important claims. |

## Explicit non-goals

RigorGraph is not a malware sandbox, secret scanner, cryptographic identity system, remote evidence retriever, formal proof checker, peer-review service, or hosted access-control system. It does not defend against an administrator or attacker who already controls the local machine, Python environment, browser, runner image, or package registry.

## Review triggers

Update this model when a change adds a network request, new parser or file format, executable plugin hook, credential, remote service, write-capable report, new release authority, or a broader project-root file operation. Security-sensitive changes should include tests for both the accepted path and the relevant failure boundary.
