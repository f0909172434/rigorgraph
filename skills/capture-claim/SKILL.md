---
name: capture-claim
description: Capture a research claim and its scoped supporting evidence in a RigorGraph project. Use when recording a theorem target, literature result, empirical observation, benchmark result, synthesis, source, dataset, computation, proof packet, or human review.
---

# Capture a claim

1. Read `rigorgraph.yaml`, current claims, evidence, and verifications.
2. Reply in the explicit or configured language: English, Traditional Chinese, Simplified Chinese, or Japanese. Keep claim statements, quotations, formulas, identifiers, and source titles in their original language.
3. Classify the claim as `formal`, `literature`, `empirical`, `benchmark`, or `synthesis`.
4. State the exact scope. For a source, record its URI and precise locator. For a local artifact, record a project-relative path and SHA-256 digest.
5. Classify each evidence record as `proof`, `source`, `dataset`, `computation`, `benchmark_run`, or `human_review`. Never relabel numerical evidence as proof.
6. Create evidence JSON first and run `rigorgraph evidence add`. Then create a `DRAFT` or `PROPOSED` claim JSON and run `rigorgraph claim add`.
7. When the input is a versioned RigorGraph evidence bundle, preserve it with `rigorgraph evidence import BUNDLE.json --claim CLAIM_ID` instead of rewriting producer metadata. Bundle hashes record observed bytes; they do not prove producer identity, runner authenticity, or correctness.
8. Run `rigorgraph audit`. If it fails, report the exact issue codes and leave the epistemic status unchanged.

Use localized result headings:

| en | zh-TW | zh-CN | ja |
| --- | --- | --- | --- |
| Claim recorded | 已記錄命題 | 已记录命题 | 主張を記録しました |
| Evidence class | 證據類別 | 证据类别 | 証拠区分 |
| Supported scope | 支持範圍 | 支持范围 | 支持される範囲 |
| Remaining gap | 剩餘缺口 | 剩余缺口 | 残るギャップ |

Do not invent a locator, digest, author, verifier, experimental condition, or dependency.
