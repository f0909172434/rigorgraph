from __future__ import annotations

import hashlib
import json

from typer.testing import CliRunner

from rigorgraph.audit import sha256_file
from rigorgraph.cli import app

runner = CliRunner()


def honest_bundle(*, status: str = "passed", title: str = "HonestCI evidence") -> dict:
    findings = []
    if status == "failed":
        findings = [
            {
                "code": "HCI004_ZERO_TESTS",
                "severity": "error",
                "message": "The report contains zero tests.",
                "report": "unit",
            }
        ]
    return {
        "format": "rigorgraph-evidence-bundle",
        "schema_version": 1,
        "profile": "honest-ci/check-result-v1",
        "evidence_type": "computation",
        "title": title,
        "scope": "Observed test execution only.",
        "created_at": "2026-07-29T00:00:00Z",
        "producer": {"name": "honest-ci", "version": "1.0.0-rc.1"},
        "provenance": {
            "repository": "f0909172434/honest-ci",
            "commit": "a" * 40,
            "ref": "refs/heads/main",
        },
        "artifacts": [
            {
                "role": "report",
                "path": "reports/junit.xml",
                "size": 14,
                "sha256": "b" * 64,
            }
        ],
        "result": {
            "schemaVersion": 1,
            "status": status,
            "totals": {
                "tests": 0 if status == "failed" else 1,
                "failures": 0,
                "errors": 0,
                "skipped": 0,
            },
            "baselineTests": None,
            "dropPercent": None,
            "reports": [],
            "findings": findings,
        },
    }


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


def test_quickstart_help_is_localized() -> None:
    expected = {
        "en": "original language",
        "zh-TW": "原始語言",
        "zh-CN": "原始语言",
        "ja": "原文",
    }
    for language, phrase in expected.items():
        result = runner.invoke(app, ["--lang", language, "quickstart", "--help"])
        assert result.exit_code == 0, result.output
        assert phrase in result.output


def test_version_is_stable_machine_readable_output() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.output.strip() == "rigorgraph 1.0.0rc1"


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


def test_four_language_quickstart_creates_original_draft_and_report(tmp_path) -> None:
    expected = {
        "en": "DRAFT",
        "zh-TW": "DRAFT",
        "zh-CN": "DRAFT",
        "ja": "DRAFT",
    }
    statements = {
        "en": "Every bounded sequence has property P.",
        "zh-TW": "每個有界數列都具有性質 P。",
        "zh-CN": "每个有界数列都具有性质 P。",
        "ja": "すべての有界数列は性質 P を持つ。",
    }
    for language, marker in expected.items():
        root = tmp_path / language
        result = runner.invoke(
            app,
            [
                "--lang",
                language,
                "quickstart",
                str(root),
                "--statement",
                statements[language],
                "--author",
                "Researcher",
                "--type",
                "formal",
            ],
        )
        assert result.exit_code == 0, result.output
        assert marker in result.output
        project = json.loads((root / ".rigorgraph" / "claims.jsonl").read_text(encoding="utf-8"))
        assert project["statement"] == statements[language]
        assert project["status"] == "DRAFT"
        report = (root / "rigorgraph-report.html").read_text(encoding="utf-8")
        assert statements[language] in report


def test_quickstart_rejects_synthesis_and_never_overwrites(tmp_path) -> None:
    invalid = runner.invoke(
        app,
        [
            "quickstart",
            str(tmp_path / "invalid"),
            "--statement",
            "Unsupported synthesis shortcut.",
            "--author",
            "Researcher",
            "--type",
            "synthesis",
        ],
    )
    assert invalid.exit_code == 2
    assert not (tmp_path / "invalid" / "rigorgraph.yaml").exists()

    target = tmp_path / "existing"
    target.mkdir()
    sentinel = target / "keep.txt"
    sentinel.write_text("keep", encoding="utf-8")
    existing = runner.invoke(
        app,
        [
            "quickstart",
            str(target),
            "--statement",
            "A claim.",
            "--author",
            "Researcher",
        ],
    )
    assert existing.exit_code == 1
    assert sentinel.read_text(encoding="utf-8") == "keep"
    assert not (target / "rigorgraph.yaml").exists()


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


def test_import_bundle_copies_links_and_is_idempotent(tmp_path) -> None:
    root = tmp_path / "project"
    assert runner.invoke(app, ["init", str(root)]).exit_code == 0
    claim_file = tmp_path / "claim.json"
    claim_file.write_text(
        json.dumps(
            {
                "id": "CLM-CI",
                "statement": "Expected tests ran.",
                "type": "empirical",
                "status": "DRAFT",
                "authors": ["Maintainer"],
            }
        ),
        encoding="utf-8",
    )
    assert runner.invoke(app, ["claim", "add", str(claim_file), "--path", str(root)]).exit_code == 0
    bundle_file = tmp_path / "bundle.json"
    raw = json.dumps(honest_bundle(), separators=(",", ":")).encode()
    bundle_file.write_bytes(raw)
    expected_id = f"EV-{hashlib.sha256(raw).hexdigest()[:16]}"

    first = runner.invoke(
        app,
        ["evidence", "import", str(bundle_file), "--claim", "CLM-CI", "--path", str(root)],
    )
    assert first.exit_code == 0, first.output
    claims = [
        json.loads(line)
        for line in (root / ".rigorgraph" / "claims.jsonl").read_text().splitlines()
    ]
    evidence = [
        json.loads(line)
        for line in (root / ".rigorgraph" / "evidence.jsonl").read_text().splitlines()
    ]
    assert claims[0]["status"] == "DRAFT"
    assert claims[0]["evidence_ids"] == [expected_id]
    assert evidence[0]["id"] == expected_id
    assert evidence[0]["metadata"]["bundle"]["result_status"] == "passed"
    stored = root / ".rigorgraph" / "artifacts" / f"{expected_id}.json"
    assert stored.read_bytes() == raw

    again = runner.invoke(
        app,
        ["evidence", "import", str(bundle_file), "--claim", "CLM-CI", "--path", str(root)],
    )
    assert again.exit_code == 0, again.output
    assert len((root / ".rigorgraph" / "evidence.jsonl").read_text().splitlines()) == 1


def test_import_bundle_rejects_conflict_and_non_draft_claim_without_partial_write(
    tmp_path,
) -> None:
    root = tmp_path / "project"
    assert runner.invoke(app, ["demo", str(root), "--scenario", "math"]).exit_code == 0
    bundle_file = tmp_path / "bundle.json"
    bundle_file.write_text(json.dumps(honest_bundle()), encoding="utf-8")
    before_evidence = (root / ".rigorgraph" / "evidence.jsonl").read_bytes()

    rejected = runner.invoke(
        app,
        [
            "evidence",
            "import",
            str(bundle_file),
            "--id",
            "EV-CI",
            "--claim",
            "CLM-ODD-SUM",
            "--path",
            str(root),
        ],
    )
    assert rejected.exit_code == 1
    assert (root / ".rigorgraph" / "evidence.jsonl").read_bytes() == before_evidence
    assert not (root / ".rigorgraph" / "artifacts" / "EV-CI.json").exists()

    draft_root = tmp_path / "draft"
    assert runner.invoke(app, ["init", str(draft_root)]).exit_code == 0
    first = runner.invoke(
        app,
        ["evidence", "import", str(bundle_file), "--id", "EV-CI", "--path", str(draft_root)],
    )
    assert first.exit_code == 0
    changed = tmp_path / "changed.json"
    changed.write_text(json.dumps(honest_bundle(title="Different bundle")), encoding="utf-8")
    conflict = runner.invoke(
        app,
        ["evidence", "import", str(changed), "--id", "EV-CI", "--path", str(draft_root)],
    )
    assert conflict.exit_code == 1


def test_import_bundle_rejects_invalid_input_and_tampering_fails_audit(tmp_path) -> None:
    root = tmp_path / "project"
    assert runner.invoke(app, ["init", str(root)]).exit_code == 0
    invalid = tmp_path / "invalid.json"
    invalid.write_text('{"format":"rigorgraph-evidence-bundle"}', encoding="utf-8")
    result = runner.invoke(app, ["evidence", "import", str(invalid), "--path", str(root)])
    assert result.exit_code == 2
    assert not (root / ".rigorgraph" / "artifacts").exists()

    bundle_file = tmp_path / "bundle.json"
    raw = json.dumps(honest_bundle()).encode()
    bundle_file.write_bytes(raw)
    imported = runner.invoke(app, ["evidence", "import", str(bundle_file), "--path", str(root)])
    assert imported.exit_code == 0
    evidence_id = f"EV-{hashlib.sha256(raw).hexdigest()[:16]}"
    stored = root / ".rigorgraph" / "artifacts" / f"{evidence_id}.json"
    stored.write_text("{}", encoding="utf-8")
    audit = runner.invoke(app, ["audit", str(root), "--json"])
    assert audit.exit_code == 1
    assert "RG_HASH_MISMATCH" in audit.output


def test_demo_does_not_overwrite_unrelated_directory(tmp_path) -> None:
    target = tmp_path / "existing"
    target.mkdir()
    sentinel = target / "keep.txt"
    sentinel.write_text("keep", encoding="utf-8")
    result = runner.invoke(app, ["demo", str(target), "--scenario", "math"])
    assert result.exit_code == 1
    assert sentinel.read_text(encoding="utf-8") == "keep"
    assert not (target / "rigorgraph.yaml").exists()
