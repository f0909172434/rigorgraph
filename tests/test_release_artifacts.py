from __future__ import annotations

import json
import subprocess
import sys
import tomllib
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
    package_text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    package = tomllib.loads(package_text)
    version = package["project"]["version"]
    module = (ROOT / "src" / "rigorgraph" / "__init__.py").read_text(encoding="utf-8")
    manifest = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
    workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
    assert 'Development Status :: 4 - Beta' in package["project"]["classifiers"]
    assert f'__version__ = "{version}"' in module
    assert manifest["version"] == version
    assert '      - "v*.*.*"' in workflow
    assert "pyproject.toml" in workflow
    assert 'expected_tag="v${package_version}"' in workflow
    assert f'test "${{GITHUB_REF_NAME}}" = "v{version}"' not in workflow
    assert (
        "pypa/gh-action-pypi-publish@dc37677b2e1c63e2034f94d8a5b11f265b73ba33"
        in workflow
    )
    assert (
        "actions/attest-build-provenance@0f67c3f4856b2e3261c31976d6725780e5e4c373"
        in workflow
    )
    assert "78e6cbd37d0ac1a40113c04f2037dacf1ea3f12e" not in workflow
    assert "a892a5a61159132606e93a2fa6f4358831b04d26" not in workflow


def test_registry_smoke_covers_supported_release_endpoints() -> None:
    workflow = (ROOT / ".github" / "workflows" / "registry-smoke.yml").read_text(
        encoding="utf-8"
    )
    assert "workflow_dispatch:" in workflow
    assert "--index-url https://pypi.org/simple" in workflow
    assert '"rigorgraph==${{ env.RIGORGRAPH_VERSION }}"' in workflow
    assert "os: [ubuntu-latest, macos-latest, windows-latest]" in workflow
    assert 'python: ["3.11", "3.14"]' in workflow
    assert "rigorgraph audit registry-smoke --json" in workflow
