# Five-minute beta demo

This reproducible demo is pinned to `v0.1.0-beta.1`. It was fresh-installed from tag commit `cce3a7242c6cef359b2724ad65a361f12406a0bd` on 2026-07-28 with Python 3.14 on Windows.

## Open the first real report

Requirements: Python 3.11 or newer. No account, API key, model provider, or network service is required after installation.

```bash
python -m pip install "git+https://github.com/f0909172434/rigorgraph.git@v0.1.0-beta.1"
rigorgraph demo --scenario math --open
```

Expected result: an offline report named `rigorgraph-report.html` opens with one formal claim, one proof evidence record, one independent verification, and a passing workflow audit.

## See the evidence boundary

```bash
rigorgraph demo benchmark-demo --scenario benchmark --open
rigorgraph demo invalid-demo --scenario invalid --open
rigorgraph audit invalid-demo
```

The benchmark demo passes with separate dataset and benchmark-run evidence. The invalid demo must fail with:

- `RG_EVIDENCE_TYPE_MISSING`
- `RG_ACCEPT_EVIDENCE_UNCHECKED`

That failure is the point: a finite numerical scan cannot be promoted into proof evidence.

## Interpret the result accurately

`VERIFIED` is a RigorGraph workflow status. It means the recorded workflow accepted the exact claim-and-evidence snapshot under the configured rules. It does not mean absolute truth, formal certification, peer review, or expert consensus.

The newer `rigorgraph quickstart` command is present on `main` after PR #4, but it is not in `v0.1.0-beta.1`. Use the commands above when reproducing the tagged beta.1 behavior.
