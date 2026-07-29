from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from rigorgraph.models import (
    Claim,
    Evidence,
    EvidenceBundle,
    ProjectConfig,
    Verification,
    VerificationRequest,
)

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas"
MODELS = {
    "project-config": ProjectConfig,
    "claim": Claim,
    "evidence": Evidence,
    "evidence-bundle": EvidenceBundle,
    "verification": Verification,
    "verification-request": VerificationRequest,
}


def expected_schemas() -> dict[str, str]:
    output: dict[str, str] = {}
    for name, model in MODELS.items():
        schema = model.model_json_schema(mode="validation")
        schema["$id"] = f"https://github.com/f0909172434/rigorgraph/schemas/{name}.schema.json"
        output[f"{name}.schema.json"] = (
            json.dumps(schema, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        )
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = expected_schemas()
    if args.check:
        mismatches = [
            name
            for name, content in expected.items()
            if not (SCHEMA_DIR / name).is_file()
            or (SCHEMA_DIR / name).read_text(encoding="utf-8") != content
        ]
        if mismatches:
            print("SCHEMA_MISMATCH", ", ".join(mismatches))
            return 1
        print(f"SCHEMAS_OK count={len(expected)}")
        return 0
    SCHEMA_DIR.mkdir(parents=True, exist_ok=True)
    for name, content in expected.items():
        (SCHEMA_DIR / name).write_text(content, encoding="utf-8", newline="\n")
    print(f"SCHEMAS_WRITTEN count={len(expected)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
