from __future__ import annotations

import json

from rigorgraph.i18n import normalize_language, resolve_language


def test_language_aliases() -> None:
    assert normalize_language("zh_Hant") == ("zh-TW", True)
    assert normalize_language("zh-Hans-CN") == ("zh-CN", True)
    assert normalize_language("zh-Hant-HK") == ("zh-TW", True)
    assert normalize_language("zh-CN") == ("zh-CN", True)
    assert normalize_language("ja_JP") == ("ja", True)
    assert normalize_language("en-US") == ("en", True)
    assert normalize_language("xx-YY") == ("en", False)


def test_language_precedence(tmp_path, monkeypatch) -> None:
    (tmp_path / "rigorgraph.yaml").write_text("language: ja\n", encoding="utf-8")
    monkeypatch.setenv("LANG", "zh_TW.UTF-8")
    configured = resolve_language(tmp_path)
    explicit = resolve_language(tmp_path, "zh-CN")
    assert configured.code == "ja" and configured.source == "config"
    assert explicit.code == "zh-CN" and explicit.source == "cli"


def test_catalogs_have_identical_keys() -> None:
    root = __import__("pathlib").Path(__file__).parents[1] / "src" / "rigorgraph" / "locales"
    catalogs = {
        code: json.loads((root / f"{code}.json").read_text(encoding="utf-8"))
        for code in ("en", "zh-TW", "zh-CN", "ja")
    }
    assert all(set(catalog) == set(catalogs["en"]) for catalog in catalogs.values())
    assert catalogs["zh-TW"]["status.VERIFIED"] == "已通過工作流驗證"
    assert catalogs["zh-CN"]["status.VERIFIED"] == "已通过工作流验证"
    assert catalogs["ja"]["status.VERIFIED"] == "ワークフロー検証済み"
