# Evidence Bundle v1

RigorGraph Evidence Bundle v1 is an additive, local-first JSON contract for preserving tool-produced evidence without turning that evidence into a truth claim.

## Core contract

Every bundle has `format: rigorgraph-evidence-bundle`, `schema_version: 1`, a profile, an existing RigorGraph evidence type, a title and scope, a SemVer producer identity, a creation time, one or more artifact digests, and a result object. Artifact paths are unique relative POSIX paths with no traversal. Future 1.x producers may add optional fields; consumers must preserve the original JSON and ignore unknown optional fields.

The canonical generated schema is [`schemas/evidence-bundle.schema.json`](../schemas/evidence-bundle.schema.json). Required fields cannot be removed or redefined within schema version 1. A breaking change requires schema version 2.

## HonestCI profile

`honest-ci/check-result-v1` requires `evidence_type: computation`, producer name `honest-ci`, and an HonestCI `CheckResult` v1 payload. The bundle may contain allowlisted GitHub repository, commit, ref, workflow, run, and event provenance. It records digests and summaries only: no JUnit XML, test names, logs, arbitrary environment variables, or secrets.

## Import

```console
rigorgraph evidence import honest-ci-evidence.json --claim CLM-CI --path research-project
```

The importer validates and copies the exact bundle to `.rigorgraph/artifacts/`, then creates a local evidence record. `--claim` is optional and is accepted only for `DRAFT` or `PROPOSED` claims. Import never changes claim status. Re-importing the same digest is idempotent; reusing an ID for different bytes is an error.

## Trust boundary

SHA-256 detects changes to the preserved bytes. Producer-supplied artifact hashes record what the producer observed, but RigorGraph cannot independently re-read artifacts that are not included. A bundle does not prove producer identity, runner authenticity, test quality, program correctness, mathematical truth, formal certification, peer review, or expert consensus.
