# End-to-end workflow

This guide takes one formal claim from a scoped record to an independently reviewed, audited report. It uses only the published RigorGraph 1.0.1 CLI and deliberately ends with a failure test.

RigorGraph verifies the integrity of this workflow. The reviewer is still responsible for the substance of the proof, and `VERIFIED` remains a recorded workflow status rather than a truth certificate.

## 1. Install and initialize

RigorGraph requires Python 3.11 or newer.

```console
python -m pip install "rigorgraph==1.0.1"
rigorgraph init research-project --name "Odd-number identity review"
```

On Windows, `py -3.11` or a newer installed Python may be used in place of `python`.

The initialized project contains a versioned YAML configuration and three empty JSONL record files. `init` creates missing files but does not overwrite existing records.

## 2. Write the evidence artifact

Create `research-project/evidence/proof.md` with the proof to be reviewed. Keep the claim's scope no broader than the artifact actually supports.

Compute its SHA-256 digest with the required Python runtime:

```console
python -c "from hashlib import sha256; from pathlib import Path; print(sha256(Path('research-project/evidence/proof.md').read_bytes()).hexdigest())"
```

The digest binds the evidence record to those exact local bytes. It does not establish who wrote them or whether the proof is correct.

## 3. Add the evidence record

Create `proof-evidence.json`, replacing the placeholder digest with the 64-character value from the previous step:

```json
{
  "id": "EV-PROOF-001",
  "type": "proof",
  "title": "Induction proof for the odd-number identity",
  "producer": "Alice Researcher",
  "path": "evidence/proof.md",
  "scope": "Only the identity 1 + 3 + ... + (2n - 1) = n^2 for positive integers n.",
  "sha256": "REPLACE_WITH_THE_64_CHARACTER_SHA256_DIGEST"
}
```

The `path` is resolved relative to the RigorGraph project, not relative to the JSON input file. A local record requires both `path` and `sha256`. A remote record instead requires one absolute `http`, `https`, or `doi:` URI plus an exact `locator`; it is not fetched during audit.

Add the record:

```console
rigorgraph evidence add proof-evidence.json --path research-project
```

## 4. Add a claim ready for review

Create `claim.json`:

```json
{
  "id": "CLM-ODD-001",
  "statement": "The sum of the first n odd positive integers is n squared.",
  "type": "formal",
  "status": "PROPOSED",
  "authors": ["Alice Researcher"],
  "dependencies": [],
  "evidence_ids": ["EV-PROOF-001"]
}
```

Then add and inspect it:

```console
rigorgraph claim add claim.json --path research-project
rigorgraph audit research-project --json
```

New claims accepted by `claim add` must be `DRAFT` or `PROPOSED`. `quickstart` always creates a `DRAFT` and is best used for initial capture; the current v1 CLI has no dedicated draft-to-proposed update command.

An audit can pass while a claim remains `DRAFT` or `PROPOSED`: PASS means the current records are internally consistent. It does not silently promote open work.

## 5. Record an independent decision

After a reviewer has inspected the exact claim and evidence, create `review.json`:

```json
{
  "id": "VER-ODD-001",
  "verifier": "Bob Reviewer",
  "outcome": "ACCEPT",
  "rationale": "The induction covers the base case and the n-to-n+1 step for the stated domain.",
  "checked_evidence_ids": ["EV-PROOF-001"]
}
```

Record the decision:

```console
rigorgraph verify CLM-ODD-001 --file review.json --path research-project
```

The command accepts claims in `PROPOSED` or `UNDER_REVIEW`, rejects a verifier name that exactly matches an author, checks that listed evidence is linked, and requires the claim type's evidence classes for `ACCEPT`. Outcomes map to statuses as follows:

| Review outcome | Resulting status |
| --- | --- |
| `ACCEPT` | `VERIFIED` |
| `REJECT` | `REJECTED` |
| `UNCERTAIN` | `UNCERTAIN` |

The command records the previous and resulting statuses plus a SHA-256 snapshot of the reviewed claim and linked evidence metadata. Names are recorded identifiers, not authenticated identities.

## 6. Audit and generate the report

```console
rigorgraph audit research-project --json
rigorgraph report research-project --output research-report.html --open
```

The report is read-only and self-contained. It includes the project records and audit findings, so inspect it for private information before sharing.

Useful audit modes:

```console
# Human-readable output; exit 1 on errors (the default)
rigorgraph audit research-project

# Stable machine-readable result
rigorgraph audit research-project --json

# Observe a failed audit without blocking the calling process
rigorgraph audit research-project --json --fail-on never
```

`--fail-on never` changes only the process exit behavior. It does not turn a JSON `FAIL` into `PASS`.

## 7. Prove the gate is live

Change one byte in `research-project/evidence/proof.md`, then rerun:

```console
rigorgraph audit research-project --json
```

The audit should return `FAIL`, emit `RG_HASH_MISMATCH`, and exit nonzero under the default threshold. Restore the reviewed bytes or intentionally create a new digest and review packet; do not merely suppress the gate.

Changing the claim or its linked evidence metadata after acceptance instead invalidates the recorded review snapshot with `RG_SNAPSHOT_MISMATCH`.

## 8. Put the same gate in GitHub Actions

Add a workflow step after checkout and Python setup:

```yaml
permissions:
  contents: read

steps:
  - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7
  - uses: actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7
    with:
      python-version: "3.12"
  - name: Audit research records
    id: rigorgraph
    uses: f0909172434/rigorgraph@v1.0.1
    with:
      path: research-project
      fail-on: error
      report: rigorgraph-report.html
```

The composite action installs the source pinned by the action reference, writes a Job Summary, exposes `status` and `report` outputs, and uploads the report even if the audit fails. It does not add PR comments or authenticate the research records.

## Record and version-control guidance

- Commit `rigorgraph.yaml`, `.rigorgraph/*.jsonl`, and the evidence needed for reproducibility when the material is safe to share.
- Do not commit `.rigorgraph/.lock`; it exists only while a mutating command holds the local project lock.
- Treat `.rigorgraph/artifacts/` and generated reports as potentially sensitive: imported bundles and reports preserve project data.
- A remote URI is a reference, not an archive. Preserve important source snapshots through a separately governed process when licensing and policy permit.
- Review diffs to claims, evidence scope, hashes, verification outcomes, and dependency status as substantive research changes.

For Evidence Bundle imports, see [Evidence Bundle v1](EVIDENCE_BUNDLES.md). For internal semantics and the full trust matrix, see [Technical architecture](ARCHITECTURE.md).
