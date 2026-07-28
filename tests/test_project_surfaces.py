from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_readmes_link_all_languages_and_quickstart() -> None:
    names = ("README.md", "README.zh-TW.md", "README.zh-CN.md", "README.ja.md")
    for name in names:
        content = (ROOT / name).read_text(encoding="utf-8")
        assert all(link in content for link in names)
        assert "rigorgraph" in content.lower()


def test_plugin_manifest_is_skills_only() -> None:
    manifest = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
    assert manifest["name"] == "rigorgraph"
    assert manifest["skills"] == "./skills/"
    assert not {"mcpServers", "apps", "hooks"}.intersection(manifest)


def test_skills_are_concise_localized_and_have_no_placeholders() -> None:
    for path in (ROOT / "skills").glob("*/SKILL.md"):
        content = path.read_text(encoding="utf-8")
        assert len(content.splitlines()) < 120
        assert "TODO" not in content
        assert "Traditional Chinese" in content
        assert "Simplified Chinese" in content
        assert "Japanese" in content
        lowered = content.lower()
        assert any(boundary in lowered for boundary in ("never", "do not", "does not"))
