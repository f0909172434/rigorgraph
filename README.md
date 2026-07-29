# RigorGraph

[English](README.md) · [繁體中文](README.zh-TW.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md)

**Turn AI research into auditable claim-evidence graphs.**

RigorGraph is a local-first CLI, offline report, GitHub Action, and skill pack for recording what a research claim says, what evidence supports it, who independently checked it, and what remains open. It preserves the difference between proof, literature support, numerical evidence, benchmark evidence, and uncertainty.

> RigorGraph checks workflow integrity and traceability. `VERIFIED` means accepted by the recorded workflow; it does not mean absolute truth, formal certification, peer review, or expert consensus.

> **RigorGraph 1.0:** Public interfaces remain additive throughout 1.x. External use is evidence, not permission to weaken the deterministic quality gates. Do not include private research data in public feedback.

![RigorGraph claim-evidence flow](assets/rigorgraph-flow.svg)

## Quick start

RigorGraph requires Python 3.11 or newer and no API key. Install the stable release with:

```bash
python -m pip install "rigorgraph==1.0.0"
rigorgraph demo --scenario math --open
```

The demo creates a project, runs a deterministic audit, and opens a self-contained report. Try the intentionally invalid promotion:

```bash
rigorgraph demo invalid-demo --scenario invalid
rigorgraph audit invalid-demo
```

The audit rejects the attempt to treat a finite numerical scan as a formal proof.

### Start your own project

```bash
rigorgraph --lang en quickstart my-research --name "My research project" --author "Your name" --type formal --statement "Every bounded sequence has property P." --open
```

This creates one real `DRAFT` claim in the language you supplied and opens its offline report. The claim appears under Open gaps; RigorGraph does not invent evidence or promote it to `VERIFIED`. The project stores human-readable, version-controlled records:

```text
my-research/
├── rigorgraph.yaml
└── .rigorgraph/
    ├── claims.jsonl
    ├── evidence.jsonl
    └── verifications.jsonl
```

## Commands

| Command | Purpose |
| --- | --- |
| `rigorgraph quickstart` | Create a first `DRAFT` claim and readable offline report without fabricating evidence |
| `rigorgraph init` | Create a project without overwriting existing files |
| `rigorgraph claim add CLAIM.json` | Add a `DRAFT` or `PROPOSED` claim |
| `rigorgraph evidence add EVIDENCE.json` | Add scoped evidence; local files require a SHA-256 digest |
| `rigorgraph evidence import BUNDLE.json` | Validate and preserve a versioned evidence bundle; optionally link it to a draft claim |
| `rigorgraph verify CLAIM_ID --file REVIEW.json` | Record an independent `ACCEPT`, `REJECT`, or `UNCERTAIN` outcome |
| `rigorgraph audit` | Check schemas, graph integrity, evidence class, independence, and hashes |
| `rigorgraph report` | Generate a four-language offline HTML report |
| `rigorgraph demo` | Create a valid math, valid benchmark, or intentionally invalid demo |

Use `--lang en`, `--lang zh-TW`, `--lang zh-CN`, or `--lang ja` before a command. Without it, RigorGraph uses project configuration, then the operating-system locale, then English.

## What the audit enforces

- IDs are unique and links resolve.
- Claim dependencies are acyclic.
- Revoked or rejected claims cannot silently support downstream claims.
- A claim author cannot be its independent verifier.
- `VERIFIED` requires an independent `ACCEPT` record.
- Formal claims need proof evidence; literature claims need an exact source locator; empirical and benchmark claims need reproducibility artifacts.
- Local evidence paths cannot escape the project and their required SHA-256 digests must match.
- An ACCEPT record is bound to the exact claim-and-evidence snapshot it reviewed.
- A verified synthesis depends only on currently verified claims.

User-authored claims, formulas, quotations, and evidence remain in their original language. The interface translates labels only.

## Evidence bundles

RigorGraph 1.0 defines an additive, versioned evidence-bundle contract. An HonestCI run can emit a bundle containing result summaries, allowlisted GitHub provenance, and SHA-256 digests for the configuration and observed artifacts. Importing it copies the exact JSON into `.rigorgraph/artifacts/`; it never promotes or verifies a claim.

```bash
rigorgraph evidence import honest-ci-evidence.json --claim CLM-CI --path my-research
```

Only `DRAFT` and `PROPOSED` claims can be linked. See [Evidence bundles](docs/EVIDENCE_BUNDLES.md) for the schema, compatibility policy, privacy boundary, and HonestCI profile.

## Agent skills and Codex plugin

The repository includes four focused [Agent Skills](skills/):

- `research-intake`
- `capture-claim`
- `adversarial-verify`
- `release-audit`

It also ships a native `.codex-plugin/plugin.json`. The GitHub Release includes `rigorgraph-codex-plugin-1.0.0.zip`; extract it, then install its isolated marketplace:

```console
codex plugin marketplace add PATH_TO_EXTRACTED_BUNDLE
codex plugin add rigorgraph@rigorgraph-release
```

Start a new Codex task after installation so the four skills are discovered. See [Codex plugin installation](docs/CODEX_PLUGIN.md). The ZIP does not edit your personal marketplace file.

## GitHub Action

```yaml
steps:
  - uses: actions/checkout@v7
  - uses: actions/setup-python@v7
    with:
      python-version: "3.12"
  - uses: f0909172434/rigorgraph@v1.0.0
    with:
      path: .
      fail-on: error
```

The action writes a GitHub Job Summary and uploads the offline report. It does not post PR comments by default. Use immutable `@v1.0.0` for reproducibility; the moving `@v1` tag follows the latest compatible 1.x release.

## Develop from source

```bash
git clone https://github.com/f0909172434/rigorgraph.git
cd rigorgraph
python -m venv .venv
python -m pip install -e ".[dev]"
cd frontend
npm install
npm run build
cd ..
pytest
python scripts/release_check.py
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for translation and verification rules, and [Release policy](docs/RELEASE_POLICY.md) for the solo-maintainer release criteria.

## Privacy and boundaries

- Local by default; no account, telemetry, remote database, or built-in paid model API.
- The HTML report is self-contained and makes no runtime network requests.
- Deterministic gates can catch incomplete records and invalid promotion, but cannot guarantee that a human or AI proof is mathematically correct.
- Core results still need appropriate expert review.

MIT License.
