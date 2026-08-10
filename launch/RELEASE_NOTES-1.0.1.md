# RigorGraph 1.0.1

RigorGraph 1.0.1 is an additive public-beta security and reliability patch. It rejects linked or reparse-point project configuration, state, and report destinations; writes complete UTF-8 reports atomically; validates all imported Evidence Bundle record fields; rejects invalid Unicode scalar values; and constrains GitHub Action report outputs to literal HTML basenames.

The release also adds a stable cross-platform CI gate, CodeQL, grouped Dependabot updates, full-commit Action pins, an explicit threat model, safer release validation, and GitHub Linguist classification for the generated offline viewer.

Evidence Bundle v1, stable audit codes, CLI JSON fields, GitHub Action inputs and outputs, and the four Codex skills remain additively compatible. Imported computation evidence still cannot promote or verify a claim.
