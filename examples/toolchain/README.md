# Three evidence handoffs, one inspectable record

This runnable example connects independent tools without combining their verification kernels. It uses RigorGraph's existing HonestCI bundle importer and ordinary scoped evidence records for other tools.

| Input | What this run checks | What remains outside the check |
| --- | --- | --- |
| HonestCI 1.0.4 | Actual CLI execution with synthetic one-test and zero-test JUnit reports; exact bundle preservation, idempotent import | Application correctness, runner identity, test quality |
| Finite Witness | Independent Python replay of the C4 certificate and declared finite search prefix | General graph theorems, producer identity |
| ProofWeave simple-ring | SHA-256 of five publicly frozen artifacts | A new Lean run; semantic alignment remains UNCONFIRMED |
| RigorGraph | Consistent records, four DRAFT claims, HTML report; changed bundle bytes fail RG_HASH_MISMATCH | Scientific approval or automatic promotion |

The zero-test failure is retained as failed computation evidence. A project audit can pass while it contains that negative result and open DRAFT claims: PASS describes record consistency.

## Run

Use Python 3.11+ and Node 24. From this RigorGraph checkout:

```bash
python -m pip install -e .
git clone https://github.com/f0909172434/honest-ci.git ../honest-ci
git -C ../honest-ci checkout 175a3149315ac7efeb3add714481990945c5294b
git clone https://github.com/f0909172434/finite-witness-webmcp.git ../finite-witness-webmcp
git -C ../finite-witness-webmcp checkout 55ed2deb7fbe1087d462fdbaec5a7878f901ca57
git clone https://github.com/f0909172434/proofweave-math-lab.git ../proofweave-math-lab
git -C ../proofweave-math-lab checkout a144bef4d5bf04035a2174e24963b864b74d2215
python examples/toolchain/run.py --honest-cli ../honest-ci/dist/cli/index.js --finite-root ../finite-witness-webmcp --proofweave-root ../proofweave-math-lab --output toolchain-output
```

The output path must not already exist. Open `toolchain-output/report.html` and inspect `receipt.json`, the preserved bundles, and the deliberately damaged copy in `tampered-project/`. The script makes no network requests or model calls; cloning/installing prerequisites needs network access.

[`sample-receipt.json`](sample-receipt.json) is a recorded successful local run. Bundle digests vary between runs because HonestCI records creation time; expected outcomes and source artifact hashes remain stable. CI repeats the handoffs with the exact pinned source revisions above. Historical ProofWeave toolchain/commit identities remain in its copied `run-summary.json`; this example does not replace them.
