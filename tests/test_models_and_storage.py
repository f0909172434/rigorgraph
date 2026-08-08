from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from rigorgraph.models import Evidence, EvidenceBundle
from rigorgraph.storage import (
    ProjectLoadError,
    ProjectLockError,
    initialize_project,
    load_project,
    project_lock,
)


def test_evidence_requires_real_location_and_digest() -> None:
    base = {
        "id": "EV-001",
        "type": "proof",
        "title": "Proof",
        "producer": "Author",
        "scope": "One claim.",
    }
    with pytest.raises(ValidationError):
        Evidence.model_validate(base)
    with pytest.raises(ValidationError):
        Evidence.model_validate({**base, "path": "proof.md"})
    with pytest.raises(ValidationError):
        Evidence.model_validate({**base, "uri": "http://", "locator": "p. 1"})
    with pytest.raises(ValidationError):
        Evidence.model_validate({**base, "uri": "https://example.com/proof"})


def test_evidence_bundle_v1_validates_known_profile_and_allows_additive_fields() -> None:
    payload = {
        "format": "rigorgraph-evidence-bundle",
        "schema_version": 1,
        "profile": "honest-ci/check-result-v1",
        "evidence_type": "computation",
        "title": "HonestCI test execution evidence",
        "scope": "Observed JUnit execution only.",
        "created_at": "2026-07-29T00:00:00Z",
        "producer": {"name": "honest-ci", "version": "1.0.0-rc.1"},
        "artifacts": [
            {
                "role": "report",
                "path": "reports/junit.xml",
                "size": 12,
                "sha256": "a" * 64,
                "media_type": "application/xml",
            }
        ],
        "result": {
            "schemaVersion": 1,
            "status": "passed",
            "totals": {"tests": 1, "failures": 0, "errors": 0, "skipped": 0},
            "baselineTests": None,
            "dropPercent": None,
            "reports": [],
            "findings": [],
            "futureOptionalField": True,
        },
        "future_optional_field": True,
    }
    bundle = EvidenceBundle.model_validate(payload)
    assert bundle.profile == "honest-ci/check-result-v1"
    assert bundle.model_extra == {"future_optional_field": True}

    with pytest.raises(ValidationError):
        EvidenceBundle.model_validate(
            {
                **payload,
                "artifacts": [{**payload["artifacts"][0], "path": "../secret.xml"}],
            }
        )

    with pytest.raises(ValidationError):
        EvidenceBundle.model_validate(
            {**payload, "result": {**payload["result"], "status": "unknown"}}
        )

    with pytest.raises(ValidationError):
        EvidenceBundle.model_validate({**payload, "profile": "unknown/profile-v1"})


def test_config_requires_mapping_and_supported_version(tmp_path) -> None:
    state = tmp_path / ".rigorgraph"
    state.mkdir()
    for name in ("claims.jsonl", "evidence.jsonl", "verifications.jsonl"):
        (state / name).write_text("", encoding="utf-8")
    for invalid in ("[]\n", "false\n", "version: 999\nname: test\n"):
        (tmp_path / "rigorgraph.yaml").write_text(invalid, encoding="utf-8")
        with pytest.raises(ProjectLoadError):
            load_project(tmp_path)


def test_project_lock_rejects_second_writer(tmp_path) -> None:
    (tmp_path / ".rigorgraph").mkdir()
    with project_lock(tmp_path):
        with pytest.raises(ProjectLockError):
            with project_lock(tmp_path, timeout=0):
                pass


def test_load_rejects_symlinked_state_directory(tmp_path) -> None:
    project = tmp_path / "project"
    external = tmp_path / "external"
    initialize_project(external, "external", "en")
    project.mkdir()
    (project / "rigorgraph.yaml").write_text(
        "version: 1\nname: project\nlanguage: en\nfail_on: error\n",
        encoding="utf-8",
    )
    try:
        (project / ".rigorgraph").symlink_to(external / ".rigorgraph", target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"symbolic links are unavailable: {exc}")

    with pytest.raises(ProjectLoadError, match="symbolic link"):
        load_project(project)
    with pytest.raises(ProjectLockError, match="symbolic link"):
        with project_lock(project):
            pass


def test_load_rejects_symlinked_state_file(tmp_path) -> None:
    initialize_project(tmp_path, "project", "en")
    claims = tmp_path / ".rigorgraph" / "claims.jsonl"
    external = tmp_path / "external-claims.jsonl"
    external.write_text("", encoding="utf-8")
    claims.unlink()
    try:
        claims.symlink_to(external)
    except OSError as exc:
        pytest.skip(f"symbolic links are unavailable: {exc}")

    with pytest.raises(ProjectLoadError, match="symbolic link"):
        load_project(tmp_path)


def test_json_machine_fields_remain_english(tmp_path) -> None:
    payload = {
        "id": "EV-001",
        "type": "source",
        "title": "來源",
        "producer": "作者",
        "uri": "https://example.com/paper",
        "locator": "Theorem 1",
        "scope": "只支持命題 A。",
    }
    item = Evidence.model_validate(payload)
    encoded = json.loads(item.model_dump_json())
    assert encoded["type"] == "source"
    assert encoded["scope"] == "只支持命題 A。"
