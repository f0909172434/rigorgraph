from __future__ import annotations

import json
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_codex_marketplace_bundle_is_installable_and_deterministic(tmp_path) -> None:
    first = tmp_path / "first.zip"
    second = tmp_path / "second.zip"
    for output in (first, second):
        subprocess.run(
            [sys.executable, "scripts/build_plugin_bundle.py", "--output", str(output)],
            cwd=ROOT,
            check=True,
        )
    assert first.read_bytes() == second.read_bytes()
    with zipfile.ZipFile(first) as archive:
        names = set(archive.namelist())
        assert ".agents/plugins/marketplace.json" in names
        assert "plugins/rigorgraph/.codex-plugin/plugin.json" in names
        assert all(
            f"plugins/rigorgraph/skills/{name}/SKILL.md" in names
            for name in ("research-intake", "capture-claim", "adversarial-verify", "release-audit")
        )
        marketplace = json.loads(archive.read(".agents/plugins/marketplace.json"))
        entry = marketplace["plugins"][0]
        assert marketplace["name"] == "rigorgraph-release"
        assert entry["source"]["path"] == "./plugins/rigorgraph"
        assert entry["policy"] == {
            "authentication": "ON_INSTALL",
            "installation": "AVAILABLE",
        }


def test_release_versions_are_consistent() -> None:
    package = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    module = (ROOT / "src" / "rigorgraph" / "__init__.py").read_text(encoding="utf-8")
    manifest = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
    assert 'version = "1.0.0rc1"' in package
    assert '__version__ = "1.0.0rc1"' in module
    assert manifest["version"] == "1.0.0-rc.1"
