---
name: research-intake
description: Formalize a new technical or academic research question in a RigorGraph project while separating goals, assumptions, evidence, and open gaps. Use when starting research, clarifying an ambiguous question, or defining completion criteria before proof, experiments, or literature work.
---

# Research intake

1. Read `rigorgraph.yaml` and existing `.rigorgraph/` records when present.
2. Determine the user's language from the explicit request, project language, or system language. Reply in that language: English, Traditional Chinese, Simplified Chinese, or Japanese.
3. Clarify the domain, variables, quantifiers, assumptions, target claim type, allowed evidence, constraints, and completion test. Ask only for material missing information.
4. Separate established facts, user assumptions, proposed claims, and open gaps. Do not attempt a proof or literature conclusion during intake.
5. If a later CI or experiment run will produce a RigorGraph Evidence Bundle, record the expected scope and producer as a plan only. Do not fabricate the bundle, digest, provenance, or successful result during intake.
6. Preserve mathematical notation and quoted source text exactly; never translate user-authored claims unless asked.
7. Initialize the project with `rigorgraph init` if needed. Record candidate claims only as `DRAFT` or `PROPOSED` through `rigorgraph claim add`.
8. End with the formalized question, assumptions, completion criteria, open gaps, and the safest next step.

Use these localized headings:

| en | zh-TW | zh-CN | ja |
| --- | --- | --- | --- |
| Research question | 研究問題 | 研究问题 | 研究課題 |
| Assumptions | 假設 | 假设 | 仮定 |
| Completion criteria | 完成標準 | 完成标准 | 完了基準 |
| Open gaps | 未解缺口 | 未解缺口 | 未解決のギャップ |
| Next safe step | 下一個安全步驟 | 下一步安全操作 | 次の安全な手順 |

Never present model consensus, a finite scan, or an unverified citation as a verified result.
