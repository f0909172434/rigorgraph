# RigorGraph agent guidance

## Product boundary

- Preserve the distinction between proof, literature support, numerical evidence, benchmark evidence, and open questions.
- `VERIFIED` is a workflow status, not absolute truth, formal certification, peer review, or expert consensus.
- Keep v1 local-first: no telemetry, hosted database, built-in paid model API, editable report, or MCP server.

## Source of truth

- Python source: `src/rigorgraph/`.
- Frontend source: `frontend/`; regenerate `src/rigorgraph/viewer/index.html` with `npm.cmd run build` on Windows or `npm run build` elsewhere. Do not hand-edit the generated HTML.
- Schemas: generate with `python scripts/export_schemas.py`; do not hand-edit generated schema JSON.
- Canonical skill content: `skills/`; plugin manifest: `.codex-plugin/plugin.json`.

## Internationalization

- Every core message ID must exist in `en`, `zh-TW`, `zh-CN`, and `ja`.
- Keep machine keys, enum values, error codes, IDs, paths, and hashes in English.
- Do not automatically translate user-authored claims, quotations, formulas, or evidence.
- Run `python scripts/validate_locales.py` after changing any user-facing string.

## Verification

Before reporting completion, run:

```text
python -m pytest
python -m ruff check .
python scripts/export_schemas.py --check
python scripts/release_check.py --full
```

Also build the frontend and validate the plugin and all four skills. Static checks alone do not establish that the CLI, report, wheel, or GitHub Action works.
