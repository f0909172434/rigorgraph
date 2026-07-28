from __future__ import annotations

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).parents[1]


def test_readmes_link_all_languages_and_quickstart() -> None:
    names = ("README.md", "README.zh-TW.md", "README.zh-CN.md", "README.ja.md")
    for name in names:
        content = (ROOT / name).read_text(encoding="utf-8")
        assert all(link in content for link in names)
        assert "rigorgraph" in content.lower()
        assert "v0.1.0-beta.1" in content
        assert "beta-feedback.yml" in content


def test_plugin_manifest_is_skills_only() -> None:
    manifest = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
    assert manifest["name"] == "rigorgraph"
    assert manifest["skills"] == "./skills/"
    assert not {"mcpServers", "apps", "hooks"}.intersection(manifest)


def test_action_manifest_is_valid_composite_yaml() -> None:
    manifest = yaml.safe_load((ROOT / "action.yml").read_text(encoding="utf-8"))
    assert isinstance(manifest, dict)
    assert manifest["runs"]["using"] == "composite"
    assert manifest["runs"]["steps"]


def test_beta_feedback_form_and_release_notes() -> None:
    issue_form = yaml.safe_load(
        (ROOT / ".github" / "ISSUE_TEMPLATE" / "beta-feedback.yml").read_text(encoding="utf-8")
    )
    assert issue_form["labels"] == ["beta-feedback"]
    assert len(issue_form["body"]) >= 5
    for locale in ("en", "zh-TW", "zh-CN", "ja"):
        content = (ROOT / "launch" / f"BETA_RELEASE_NOTES.{locale}.md").read_text(encoding="utf-8")
        assert "v0.1.0-beta.1" in content


def test_beta_policy_does_not_require_a_fixed_external_tester_panel() -> None:
    policy = (ROOT / "docs" / "BETA_POLICY.md").read_text(encoding="utf-8")
    assert "External use is evidence, not permission" in policy

    fixed_tester_phrases = ("first five external", "前 5 位外部", "外部ユーザー 5 名")
    surfaces = [
        ROOT / "README.md",
        ROOT / "README.zh-TW.md",
        ROOT / "README.zh-CN.md",
        ROOT / "README.ja.md",
        *(ROOT / "launch").glob("BETA_RELEASE_NOTES.*.md"),
    ]
    for path in surfaces:
        content = path.read_text(encoding="utf-8")
        assert not any(phrase in content for phrase in fixed_tester_phrases), path


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
