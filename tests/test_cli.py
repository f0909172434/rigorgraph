from __future__ import annotations

import json

from typer.testing import CliRunner

from rigorgraph.audit import sha256_file
from rigorgraph.cli import app

runner = CliRunner()


def test_help_is_localized() -> None:
    expected = {
        "en": "Usage",
        "zh-TW": "用法",
        "zh-CN": "用法",
        "ja": "使い方",
    }
    for language, heading in expected.items():
        result = runner.invoke(app, ["--lang", language, "--help"])
        assert result.exit_code == 0, result.output
        assert heading in result.output


def test_version_is_stable_machine_readable_output() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.output.strip() == "rigorgraph 0.1.0b1"


def test_four_language_init_and_no_overwrite(tmp_path) -> None:
    expected = {
        "en": "Initialized",
        "zh-TW": "初始化",
        "zh-CN": "初始化",
        "ja": "初期化",
    }
    for language, text in expected.items():
        root = tmp_path / language
        first = runner.invoke(app, ["--lang", language, "init", str(root)])
        second = runner.invoke(app, ["--lang", language, "init", str(root)])
        assert first.exit_code == 0, first.output
        assert text in first.output
        assert second.exit_code == 0
        assert (root / ".rigorgraph" / "claims.jsonl").exists()


def test_full_cli_golden_path(tmp_path) -> None:
    root = tmp_path / "研究 project"
    assert runner.invoke(app, ["--lang", "zh-TW", "init", str(root)]).exit_code == 0
    artifact = root / "proof.md"
    artifact.write_text("A complete proof packet.\n", encoding="utf-8")
    evidence = {
        "id": "EV-001",
        "type": "proof",
        "title": "Proof packet",
        "producer": "Author",
        "path": "proof.md",
        "scope": "Claim CLM-001 only.",
        "sha256": sha256_file(artifact),
    }
    claim = {
        "id": "CLM-001",
        "statement": "A test formal claim.",
        "type": "formal",
        "status": "PROPOSED",
        "authors": ["Author"],
        "evidence_ids": ["EV-001"],
    }
    review = {
        "id": "VER-001",
        "verifier": "Independent reviewer",
        "outcome": "ACCEPT",
        "rationale": "Checked every step in the supplied test packet.",
        "checked_evidence_ids": ["EV-001"],
    }
    evidence_file = tmp_path / "evidence.json"
    claim_file = tmp_path / "claim.json"
    review_file = tmp_path / "review.json"
    evidence_file.write_text(json.dumps(evidence), encoding="utf-8")
    claim_file.write_text(json.dumps(claim), encoding="utf-8")
    review_file.write_text(json.dumps(review), encoding="utf-8")
    assert (
        runner.invoke(app, ["evidence", "add", str(evidence_file), "--path", str(root)]).exit_code
        == 0
    )
    assert runner.invoke(app, ["claim", "add", str(claim_file), "--path", str(root)]).exit_code == 0
    assert (
        runner.invoke(
            app, ["verify", "CLM-001", "--file", str(review_file), "--path", str(root)]
        ).exit_code
        == 0
    )
    audit = runner.invoke(app, ["audit", str(root), "--json"])
    assert audit.exit_code == 0, audit.output
    payload = json.loads(audit.output)
    assert payload["status"] == "PASS"
    report = root / "報告.html"
    generated = runner.invoke(app, ["--lang", "ja", "report", str(root), "-o", str(report)])
    assert generated.exit_code == 0, generated.output
    assert report.is_file()


def test_invalid_demo_returns_failing_audit(tmp_path) -> None:
    root = tmp_path / "invalid"
    assert runner.invoke(app, ["demo", str(root), "--scenario", "invalid"]).exit_code == 0
    result = runner.invoke(app, ["audit", str(root)])
    assert result.exit_code == 1
    assert "RG_EVIDENCE_TYPE_MISSING" in result.output


def test_demo_does_not_overwrite_unrelated_directory(tmp_path) -> None:
    target = tmp_path / "existing"
    target.mkdir()
    sentinel = target / "keep.txt"
    sentinel.write_text("keep", encoding="utf-8")
    result = runner.invoke(app, ["demo", str(target), "--scenario", "math"])
    assert result.exit_code == 1
    assert sentinel.read_text(encoding="utf-8") == "keep"
    assert not (target / "rigorgraph.yaml").exists()
