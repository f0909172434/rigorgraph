from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from rigorgraph.models import Evidence
from rigorgraph.storage import ProjectLoadError, ProjectLockError, load_project, project_lock


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
