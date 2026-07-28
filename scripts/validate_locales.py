from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCALES = ROOT / "src" / "rigorgraph" / "locales"
CODES = ("en", "zh-TW", "zh-CN", "ja")
PLACEHOLDER = re.compile(r"\{([A-Za-z0-9_]+)\}")

VERIFIED_LABELS = {
    "en": "Workflow verified",
    "zh-TW": "已通過工作流驗證",
    "zh-CN": "已通过工作流验证",
    "ja": "ワークフロー検証済み",
}


def validate() -> list[str]:
    errors: list[str] = []
    catalogs: dict[str, dict[str, str]] = {}
    for code in CODES:
        path = LOCALES / f"{code}.json"
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{code}: cannot load catalog: {exc}")
            continue
        if not isinstance(payload, dict) or not all(
            isinstance(key, str) and isinstance(value, str) for key, value in payload.items()
        ):
            errors.append(f"{code}: catalog must be a string-to-string object")
            continue
        catalogs[code] = payload

    if set(catalogs) != set(CODES):
        return errors
    canonical = set(catalogs["en"])
    for code, catalog in catalogs.items():
        missing = sorted(canonical - set(catalog))
        extra = sorted(set(catalog) - canonical)
        if missing:
            errors.append(f"{code}: missing keys: {', '.join(missing)}")
        if extra:
            errors.append(f"{code}: extra keys: {', '.join(extra)}")
        for key in canonical.intersection(catalog):
            if not catalog[key].strip():
                errors.append(f"{code}:{key}: empty translation")
            if "�" in catalog[key]:
                errors.append(f"{code}:{key}: replacement character found")
            expected = set(PLACEHOLDER.findall(catalogs["en"][key]))
            actual = set(PLACEHOLDER.findall(catalog[key]))
            if actual != expected:
                errors.append(f"{code}:{key}: placeholders {sorted(actual)} != {sorted(expected)}")
        if catalog.get("status.VERIFIED") != VERIFIED_LABELS[code]:
            errors.append(f"{code}: status.VERIFIED must use the approved workflow label")

    banned = {
        "zh-TW": ("絕對正確", "已證明為真"),
        "zh-CN": ("绝对正确", "已证明为真"),
        "ja": ("絶対に正しい", "真であることが証明済み"),
    }
    for code, phrases in banned.items():
        for key, value in catalogs[code].items():
            if any(phrase in value for phrase in phrases):
                errors.append(f"{code}:{key}: translation overstates epistemic status")
    return errors


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(f"LOCALE_ERROR {error}")
        return 1
    english = json.loads((LOCALES / "en.json").read_text(encoding="utf-8"))
    print(f"LOCALES_OK languages={len(CODES)} keys={len(english)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
