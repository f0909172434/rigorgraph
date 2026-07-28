---
name: adversarial-verify
description: Independently challenge and verify a PROPOSED RigorGraph claim, recording ACCEPT, REJECT, or UNCERTAIN without strengthening the evidence. Use for proof checking, counterexample search, citation entailment, empirical reproduction, benchmark review, or cold-start verification.
---

# Adversarial verification

1. Read the UTF-8 target claim, its complete dependencies, linked evidence, and project policy from disk. Do not rely on a prior conversational summary. On Windows, use an explicitly UTF-8-safe reader.
2. Confirm the verifier is not listed as an author. Stop if independence cannot be established.
3. Reply in the explicit or configured language: English, Traditional Chinese, Simplified Chinese, or Japanese. Preserve the original claim and evidence text.
4. Attack the claim before accepting it:
   - formal: check hypotheses, implication direction, boundary cases, asymptotics, and every proof step;
   - literature: open the source and verify the exact locator and support scope;
   - empirical: reproduce or inspect the dataset, computation, uncertainty, and limitations;
   - benchmark: check data, environment, metric definition, baseline, and reproducibility;
   - synthesis: verify every dependency is currently `VERIFIED`.
5. Choose exactly one outcome: `ACCEPT`, `REJECT`, or `UNCERTAIN`. Absence of a found counterexample is not proof.
6. For a `PROPOSED` or `UNDER_REVIEW` claim, write a verification request with rationale and checked evidence IDs, then run `rigorgraph verify CLAIM_ID --file REQUEST.json`.
7. For an already `VERIFIED` claim whose support fails, do not overwrite history or try to verify it again. Report a release-blocking revocation recommendation and the decisive issue codes.
8. Run `rigorgraph audit` and report the outcome plus any remaining audit issues. If `rigorgraph` is not on `PATH`, use `python -m rigorgraph` or the project virtual-environment executable.

Use localized headings:

| en | zh-TW | zh-CN | ja |
| --- | --- | --- | --- |
| Verification outcome | 驗證結果 | 验证结果 | 検証結果 |
| Decisive checks | 決定性檢查 | 决定性检查 | 決定的な確認 |
| Evidence limitations | 證據限制 | 证据限制 | 証拠の限界 |
| Remaining uncertainty | 剩餘不確定性 | 剩余不确定性 | 残る不確実性 |

`VERIFIED` means accepted by this recorded workflow; it does not mean absolute truth, formal certification, or peer review.
