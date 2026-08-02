from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path

import yaml
from export_schemas import expected_schemas
from validate_locales import validate as validate_locales

ROOT = Path(__file__).resolve().parents[1]
PROJECT_METADATA = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
PYTHON_VERSION = str(PROJECT_METADATA["project"]["version"])
PLUGIN_VERSION = PYTHON_VERSION
RELEASE_TAG = f"v{PYTHON_VERSION}"
PYPI_PUBLISH_ACTION = (
    "pypa/gh-action-pypi-publish@dc37677b2e1c63e2034f94d8a5b11f265b73ba33"
)
ATTEST_BUILD_PROVENANCE_ACTION = (
    "actions/attest-build-provenance@0f67c3f4856b2e3261c31976d6725780e5e4c373"
)
KNOWN_NON_COMMIT_ACTION_OBJECTS = {
    "78e6cbd37d0ac1a40113c04f2037dacf1ea3f12e": "annotated actions/attest-build-provenance v4 tag",
    "a892a5a61159132606e93a2fa6f4358831b04d26": "annotated pypa/gh-action-pypi-publish v1.14.2 tag",
    "bce182f857edf1feab116e9795a3393d21977282": "annotated github/codeql-action v4 tag",
}
REMOTE_ACTION = re.compile(r"^\s*-?\s*uses:\s*([^\s#]+)(?:\s+#\s*(\S+))?\s*$")


def check_manifest() -> list[str]:
    errors: list[str] = []
    path = ROOT / ".codex-plugin" / "plugin.json"
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"plugin manifest: {exc}"]
    required = ("name", "version", "description", "author", "skills", "interface")
    for key in required:
        if key not in manifest:
            errors.append(f"plugin manifest missing {key}")
    if manifest.get("name") != "rigorgraph":
        errors.append("plugin name must be rigorgraph")
    if not re.fullmatch(
        r"\d+\.\d+\.\d+(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?",
        str(manifest.get("version", "")),
    ):
        errors.append("plugin version must use strict semver")
    if manifest.get("version") != PLUGIN_VERSION:
        errors.append("plugin version must match the release")
    for forbidden in ("mcpServers", "apps", "hooks"):
        if forbidden in manifest:
            errors.append(f"plugin must not declare unused {forbidden}")
    return errors


def check_action_manifest() -> list[str]:
    path = ROOT / "action.yml"
    try:
        manifest = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        return [f"action manifest: {exc}"]
    if not isinstance(manifest, dict):
        return ["action manifest root must be a mapping"]
    errors: list[str] = []
    for key in ("name", "description", "inputs", "outputs", "runs"):
        if key not in manifest:
            errors.append(f"action manifest missing {key}")
    runs = manifest.get("runs")
    if not isinstance(runs, dict) or runs.get("using") != "composite":
        errors.append("action manifest must declare composite runs")
    elif not isinstance(runs.get("steps"), list) or not runs["steps"]:
        errors.append("action manifest must declare at least one step")
    return errors


def check_pinned_actions() -> list[str]:
    errors: list[str] = []
    paths = [ROOT / "action.yml", *(ROOT / ".github" / "workflows").glob("*.y*ml")]
    for path in sorted(paths):
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            match = REMOTE_ACTION.match(line)
            if not match:
                continue
            target, version_comment = match.groups()
            if target.startswith("./"):
                continue
            if "@" not in target:
                errors.append(f"{path.relative_to(ROOT)}:{line_number}: action has no ref")
                continue
            _, ref = target.rsplit("@", 1)
            if not re.fullmatch(r"[0-9a-f]{40}", ref):
                errors.append(
                    f"{path.relative_to(ROOT)}:{line_number}: action must use a full commit SHA"
                )
            elif ref in KNOWN_NON_COMMIT_ACTION_OBJECTS:
                errors.append(
                    f"{path.relative_to(ROOT)}:{line_number}: action ref is a known non-commit "
                    f"object ({KNOWN_NON_COMMIT_ACTION_OBJECTS[ref]})"
                )
            if not version_comment or not re.fullmatch(r"v\d+(?:\.\d+){0,2}", version_comment):
                errors.append(
                    f"{path.relative_to(ROOT)}:{line_number}: action needs a version comment"
                )
    return errors


def check_skills() -> list[str]:
    errors: list[str] = []
    expected = {"research-intake", "capture-claim", "adversarial-verify", "release-audit"}
    found = {path.parent.name for path in (ROOT / "skills").glob("*/SKILL.md")}
    if found != expected:
        errors.append(f"skill set {sorted(found)} != {sorted(expected)}")
    for name in sorted(found):
        skill_path = ROOT / "skills" / name / "SKILL.md"
        content = skill_path.read_text(encoding="utf-8")
        if "TODO" in content or "[TODO" in content:
            errors.append(f"{name}: TODO placeholder remains")
        match = re.match(r"---\n(.*?)\n---", content, re.DOTALL)
        if not match:
            errors.append(f"{name}: invalid frontmatter")
            continue
        metadata = yaml.safe_load(match.group(1))
        if set(metadata) != {"name", "description"} or metadata.get("name") != name:
            errors.append(f"{name}: frontmatter must contain matching name and description only")
        for language in ("Traditional Chinese", "Simplified Chinese", "Japanese"):
            if language not in content:
                errors.append(f"{name}: missing {language} output rule")
        agent_path = skill_path.parent / "agents" / "openai.yaml"
        try:
            agent = yaml.safe_load(agent_path.read_text(encoding="utf-8"))
            prompt = agent["interface"]["default_prompt"]
        except (OSError, KeyError, TypeError, yaml.YAMLError) as exc:
            errors.append(f"{name}: invalid agents/openai.yaml: {exc}")
            continue
        if f"${name}" not in prompt:
            errors.append(f"{name}: default_prompt must mention ${name}")
    return errors


def check_viewer() -> list[str]:
    path = ROOT / "src" / "rigorgraph" / "viewer" / "index.html"
    if not path.is_file():
        return ["viewer/index.html is missing"]
    raw = path.read_bytes()
    content = raw.decode("utf-8")
    errors: list[str] = []
    if b"\r\n" in raw or b"\r" in raw:
        errors.append("viewer must use reproducible LF line endings")
    if content.count("__RIGORGRAPH_DATA__") != 1:
        errors.append("viewer must contain exactly one report data marker")
    if re.search(r"<(script|link)[^>]+(src|href)=[\"']https?://", content, re.IGNORECASE):
        errors.append("viewer contains a runtime network dependency")
    if len(content) < 100_000:
        errors.append("viewer does not appear to contain the bundled application")
    return errors


def check_readmes() -> list[str]:
    errors: list[str] = []
    readmes = ("README.md", "README.zh-TW.md", "README.zh-CN.md", "README.ja.md")
    for name in readmes:
        content = (ROOT / name).read_text(encoding="utf-8")
        for link in readmes:
            if link not in content:
                errors.append(f"{name}: missing language link {link}")
        if (
            "Quick start" not in content
            and "快速開始" not in content
            and "快速开始" not in content
            and "クイックスタート" not in content
        ):
            errors.append(f"{name}: missing localized quick start")
    return errors


def check_release_surfaces() -> list[str]:
    errors: list[str] = []
    readmes = ("README.md", "README.zh-TW.md", "README.zh-CN.md", "README.ja.md")
    fixed_tester_phrases = ("first five external", "前 5 位外部", "外部ユーザー 5 名")
    for name in readmes:
        content = (ROOT / name).read_text(encoding="utf-8")
        if PYTHON_VERSION not in content:
            errors.append(f"{name}: missing release version")
        if "docs/EVIDENCE_BUNDLES.md" not in content:
            errors.append(f"{name}: missing evidence bundle documentation")
        if any(phrase in content for phrase in fixed_tester_phrases):
            errors.append(f"{name}: fixed external tester quota must not block beta releases")

    policy_path = ROOT / "docs" / "RELEASE_POLICY.md"
    try:
        policy = policy_path.read_text(encoding="utf-8")
    except OSError as exc:
        errors.append(f"release policy: {exc}")
    else:
        if "External use is evidence, not permission" not in policy:
            errors.append("release policy must separate external evidence from permission")

    if PROJECT_METADATA.get("project", {}).get("version") != PYTHON_VERSION:
        errors.append("Python package version must match the release")
    classifiers = PROJECT_METADATA.get("project", {}).get("classifiers", [])
    if "Development Status :: 4 - Beta" not in classifiers:
        errors.append("Python package metadata must identify the public-beta status")
    module = (ROOT / "src" / "rigorgraph" / "__init__.py").read_text(encoding="utf-8")
    if f'__version__ = "{PYTHON_VERSION}"' not in module:
        errors.append("runtime version must match the release")
    for required in (
        ROOT / "CHANGELOG.md",
        ROOT / "docs" / "EVIDENCE_BUNDLES.md",
        ROOT / "launch" / f"RELEASE_NOTES-{PLUGIN_VERSION}.md",
        ROOT / "schemas" / "evidence-bundle.schema.json",
    ):
        if not required.is_file():
            errors.append(f"release surface missing: {required.relative_to(ROOT)}")
    if RELEASE_TAG not in (ROOT / "README.md").read_text(encoding="utf-8"):
        errors.append("English README must pin the release Action tag")
    workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
    if "pyproject.toml" not in workflow or 'expected_tag="v${package_version}"' not in workflow:
        errors.append("release workflow must derive the expected tag from pyproject.toml")
    if PYPI_PUBLISH_ACTION not in workflow:
        errors.append("release workflow must pin the verified PyPI publisher action")
    if ATTEST_BUILD_PROVENANCE_ACTION not in workflow:
        errors.append("release workflow must pin the peeled provenance attestation commit")
    for required in (
        ROOT / "assets" / "rigorgraph-report.png",
        ROOT / "SECURITY.md",
        ROOT / "docs" / "THREAT_MODEL.md",
    ):
        if not required.is_file():
            errors.append(f"adoption surface missing: {required.relative_to(ROOT)}")
    return errors


def check_schemas() -> list[str]:
    errors: list[str] = []
    schema_dir = ROOT / "schemas"
    for name, expected in expected_schemas().items():
        path = schema_dir / name
        if not path.is_file() or path.read_text(encoding="utf-8") != expected:
            errors.append(f"generated schema is stale: {name}")
    return errors


def run(command: list[str], cwd: Path = ROOT) -> int:
    print("RUN", " ".join(command))
    return subprocess.run(command, cwd=cwd, check=False).returncode


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true")
    args = parser.parse_args()
    errors = (
        validate_locales()
        + check_manifest()
        + check_action_manifest()
        + check_pinned_actions()
        + check_skills()
        + check_viewer()
        + check_readmes()
        + check_release_surfaces()
        + check_schemas()
    )
    if errors:
        for error in errors:
            print("RELEASE_ERROR", error)
        return 1
    if args.full:
        commands = [
            [sys.executable, "-m", "pytest"],
            [sys.executable, "-m", "ruff", "check", "."],
            [sys.executable, "-m", "build"],
            [sys.executable, "scripts/build_plugin_bundle.py"],
        ]
        for command in commands:
            if run(command):
                return 1
    print("RELEASE_CHECK_PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
