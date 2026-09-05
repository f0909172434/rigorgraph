# Open a report, then make an audit fail

These three self-contained reports were generated from the repository's built-in
demo fixtures on September 5, 2026:

- [Valid math demo](https://f0909172434.github.io/examples/rigorgraph/math.html)
  — audit `PASS`, process exit 0.
- [Invalid promotion demo](https://f0909172434.github.io/examples/rigorgraph/invalid.html)
  — audit `FAIL`, process exit 1, with `RG_EVIDENCE_TYPE_MISSING` and
  `RG_ACCEPT_EVIDENCE_UNCHECKED`.
- [Evidence changed after review](https://f0909172434.github.io/examples/rigorgraph/tampered.html)
  — a copy of the valid demo with one sentence appended to its evidence file;
  audit `FAIL`, process exit 1, with `RG_HASH_MISMATCH`.

They contain synthetic demo claims and review records, not a new independent
review of a real research result. The report itself includes its data and viewer;
it can be saved and opened offline. Hosted copies are convenience previews.

## Five-minute inspection

1. Open the valid report and select a claim. Follow its evidence and review record.
2. Switch the interface language. User-authored research text stays in its
   original language; the controls support English, Traditional Chinese,
   Simplified Chinese and Japanese.
3. Open the invalid report, select **Open gaps**, and read both audit codes.
4. Explain why a numerical scan cannot satisfy a formal-proof evidence
   requirement. A workflow `PASS` also does not establish scientific truth.
5. Open the changed-evidence report and select **Open gaps**. The stored evidence
   hash no longer matches the file bytes even though the old review record remains.

## Reproduce locally

```sh
rigorgraph demo report-math --scenario math
rigorgraph audit report-math --json
rigorgraph demo report-invalid --scenario invalid
rigorgraph audit report-invalid --json
```

The last command intentionally exits nonzero. Each demo directory contains
`rigorgraph-report.html`; do not edit its embedded JSON by hand to change a result.
Use the [end-to-end workflow](WORKFLOW.md) for a record-by-record example and a
deliberate file-tampering check.

To reproduce the third case in a disposable copy of `report-math`, append a
sentence to `evidence/odd-sum-proof.md`, then audit it. Generate a new report with
`rigorgraph report PATH --output PATH/rigorgraph-report.html`; the default output
is relative to the current working directory, not automatically the project path.

## Snapshot identity

The hosted files were copied from the generated reports without editing them:

| Report | SHA-256 |
|---|---|
| math.html | `192f730f65d35cff9b9acde272deda398ea26664beaf9ff41fc031f5ed9b9800` |
| invalid.html | `558b056b63cc739046f9bf27eef798ae7c01db6762a679aa3514149c6313c154` |
| tampered.html | `c45bcf68f5f2819c440930b28cc8abe0ffe0182ea603b0300a6a8b048e8ce6ca` |

Demo timestamps and other record metadata can change on a fresh run. These hashes
identify the published snapshots; they are not expected hashes for every rerun.
