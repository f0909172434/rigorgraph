from __future__ import annotations

import json
import re

from rigorgraph.audit import audit_project
from rigorgraph.demo import create_demo
from rigorgraph.i18n import LanguageChoice
from rigorgraph.report import generate_report
from rigorgraph.storage import load_project


def test_report_is_self_contained_and_includes_four_locales(tmp_path) -> None:
    project_root = tmp_path / "project"
    create_demo(project_root, "benchmark", "zh-TW")
    project = load_project(project_root)
    output = tmp_path / "report.html"
    generate_report(
        project, audit_project(project), output, LanguageChoice("zh-TW", "config", True)
    )
    html = output.read_text(encoding="utf-8")
    assert "__RIGORGRAPH_DATA__" not in html
    assert '"zh-TW"' in html and '"zh-CN"' in html and '"ja"' in html
    assert "已通過工作流驗證" in html
    assert "ワークフロー検証済み" in html
    assert '<script type="module" src=' not in html
    assert "https://fonts" not in html
    assert len(html) > 600_000


def test_script_terminator_in_user_content_is_escaped(tmp_path) -> None:
    project_root = tmp_path / "project"
    create_demo(project_root, "math", "en")
    project = load_project(project_root)
    original = "<!-- marker --></script><script>alert(1)</script>"
    project.claims[0].statement = original
    output = tmp_path / "report.html"
    generate_report(project, audit_project(project), output, LanguageChoice("en", "cli", True))
    html = output.read_text(encoding="utf-8")
    assert original not in html
    assert "\\u003c" in html
    match = re.search(
        r'<script id="rigorgraph-data" type="application/json">(.*?)</script>',
        html,
        re.DOTALL,
    )
    assert match
    payload = json.loads(match.group(1))
    assert payload["claims"][0]["statement"] == original


def test_report_handles_missing_dependency_without_external_edge(tmp_path) -> None:
    project_root = tmp_path / "project"
    create_demo(project_root, "math", "en")
    project = load_project(project_root)
    project.claims[0].dependencies = ["CLM-MISSING"]
    output = tmp_path / "missing-dependency.html"
    generate_report(project, audit_project(project), output, LanguageChoice("en", "cli", True))
    html = output.read_text(encoding="utf-8")
    assert "RG_DEPENDENCY_MISSING" in html
