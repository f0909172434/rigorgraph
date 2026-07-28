---
name: release-audit
description: Audit a RigorGraph project before release and produce a local read-only claim-evidence report. Use when preparing a tag, paper, dataset, benchmark, public repository, handoff, or other research release.
---

# Release audit

1. Read the project config and all `.rigorgraph/` records. Reply in the explicit or configured language: English, Traditional Chinese, Simplified Chinese, or Japanese.
2. Run `rigorgraph audit --json` and preserve its stable English codes and enums in machine output.
3. Treat every error as release-blocking. Do not waive missing evidence, self-verification, invalid dependency status, hash mismatch, or cycle failures.
4. Review open `DRAFT`, `PROPOSED`, `UNDER_REVIEW`, and `UNCERTAIN` claims. Ensure release copy does not present them as verified results.
5. Run `rigorgraph report --output rigorgraph-report.html` and confirm the offline report opens without network access.
6. Report the audit status, blocking issues, limitations, report path, and release recommendation. Do not publish, tag, push, or post without explicit authorization.

Use localized headings:

| en | zh-TW | zh-CN | ja |
| --- | --- | --- | --- |
| Audit status | 稽核狀態 | 审计状态 | 監査状態 |
| Blocking issues | 阻擋問題 | 阻塞问题 | ブロッキング問題 |
| Evidence limitations | 證據限制 | 证据限制 | 証拠の限界 |
| Release recommendation | 發布建議 | 发布建议 | リリース推奨 |

Passing deterministic checks does not establish that every research claim is true.
