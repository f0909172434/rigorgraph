# Contributing to RigorGraph

Thank you for helping make research records more auditable.

## Development checks

```bash
python -m pip install -e ".[dev]"
cd frontend && npm install && npm run build && cd ..
pytest
ruff check .
python scripts/validate_locales.py
python scripts/release_check.py
```

## Evidence integrity

- Do not describe model consensus, finite search, or a benchmark as proof.
- Preserve the exact supported scope of every source or artifact.
- Tests may use synthetic examples, but documentation must label them as such.
- Never weaken an audit gate merely to make a fixture pass.

## Translation integrity

Core message IDs must exist in `en`, `zh-TW`, `zh-CN`, and `ja`. Do not create Simplified Chinese by character conversion alone. Preserve these distinctions:

- `VERIFIED`: accepted by the recorded workflow, not absolute truth.
- proof: deductive support for a formal claim.
- numerical evidence: finite computational evidence, not proof.
- open gap: unresolved information or reasoning.

Run `python scripts/validate_locales.py` before submitting a change.

## Pull requests

Keep changes scoped, include tests, and explain which evidence or validation invariant changes. All CI checks must pass before merge.
