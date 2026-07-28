# AI-assisted launch drafts

These drafts require final human approval before posting.

## Show HN

**Title:** Show HN: RigorGraph – auditable claim-evidence graphs for AI research agents

I built RigorGraph because research agents are good at producing plausible text but chat logs are a poor truth layer. RigorGraph records claims, scoped evidence, dependencies, independent verification, and revocation in local version-controlled files. A deterministic audit rejects common overclaims, such as promoting a finite numerical scan into a formal proof.

It ships as a Python CLI, four agent skills, a Codex plugin manifest, a GitHub Action, and a self-contained offline report. The interface supports English, Traditional Chinese, Simplified Chinese, and Japanese. There is no telemetry, hosted account, or built-in paid model API.

I would especially value feedback on the evidence model, false-positive audit gates, and the five-minute quick start.

## Research and agent-tool communities

RigorGraph is a local-first verification layer for AI-assisted research. It separates proof, literature support, empirical data, benchmark runs, and uncertainty; requires independent verification for workflow-verified claims; and generates an offline multilingual evidence graph. The repository includes a valid proof demo, a reproducible benchmark demo, and an intentionally invalid numerical-to-proof promotion that the audit rejects.

Feedback and small reproducible issue reports are welcome. Please do not upload private research data.
