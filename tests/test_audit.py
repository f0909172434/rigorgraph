from __future__ import annotations

from rigorgraph.audit import audit_project
from rigorgraph.demo import create_demo
from rigorgraph.models import (
    Claim,
    ClaimStatus,
    ClaimType,
    Verification,
    VerificationOutcome,
)
from rigorgraph.storage import (
    CLAIMS_FILE,
    STATE_DIR,
    VERIFICATIONS_FILE,
    load_project,
    write_records,
)


def issue_codes(result) -> set[str]:
    return {issue.code for issue in result.issues}


def test_valid_math_and_benchmark_demos_pass(tmp_path) -> None:
    for scenario in ("math", "benchmark"):
        root = tmp_path / scenario
        create_demo(root, scenario, "en")
        result = audit_project(load_project(root))
        assert result.status == "PASS", result.model_dump()


def test_numeric_scan_cannot_be_promoted_to_formal_proof(tmp_path) -> None:
    create_demo(tmp_path, "invalid", "en")
    result = audit_project(load_project(tmp_path))
    assert result.status == "FAIL"
    assert "RG_EVIDENCE_TYPE_MISSING" in issue_codes(result)


def test_cycle_and_missing_dependency_fail(tmp_path) -> None:
    create_demo(tmp_path, "math", "en")
    project = load_project(tmp_path)
    first = project.claims[0].model_copy(update={"dependencies": ["CLM-TWO"]})
    second = Claim(
        id="CLM-TWO",
        statement="A dependent statement.",
        type=ClaimType.SYNTHESIS,
        status=ClaimStatus.PROPOSED,
        authors=["Other author"],
        dependencies=[first.id, "CLM-MISSING"],
    )
    write_records(tmp_path / STATE_DIR / CLAIMS_FILE, [first, second])
    result = audit_project(load_project(tmp_path))
    assert {"RG_DEPENDENCY_CYCLE", "RG_DEPENDENCY_MISSING"}.issubset(issue_codes(result))


def test_hash_mismatch_fails(tmp_path) -> None:
    create_demo(tmp_path, "math", "en")
    (tmp_path / "evidence" / "odd-sum-proof.md").write_text("changed", encoding="utf-8")
    result = audit_project(load_project(tmp_path))
    assert "RG_HASH_MISMATCH" in issue_codes(result)


def test_self_verification_fails(tmp_path) -> None:
    create_demo(tmp_path, "math", "en")
    project = load_project(tmp_path)
    verification = project.verifications[0].model_copy(update={"verifier": "Example author"})
    write_records(tmp_path / STATE_DIR / VERIFICATIONS_FILE, [verification])
    result = audit_project(load_project(tmp_path))
    assert "RG_SELF_VERIFICATION" in issue_codes(result)
    assert "RG_ACCEPT_MISSING" in issue_codes(result)


def test_changed_claim_invalidates_old_accept(tmp_path) -> None:
    create_demo(tmp_path, "math", "en")
    project = load_project(tmp_path)
    changed = project.claims[0].model_copy(update={"statement": "A materially changed claim."})
    write_records(tmp_path / STATE_DIR / CLAIMS_FILE, [changed])
    result = audit_project(load_project(tmp_path))
    assert "RG_SNAPSHOT_MISMATCH" in issue_codes(result)


def test_accept_must_check_required_evidence(tmp_path) -> None:
    create_demo(tmp_path, "math", "en")
    project = load_project(tmp_path)
    unchecked = project.verifications[0].model_copy(update={"checked_evidence_ids": []})
    write_records(tmp_path / STATE_DIR / VERIFICATIONS_FILE, [unchecked])
    result = audit_project(load_project(tmp_path))
    assert "RG_ACCEPT_EVIDENCE_UNCHECKED" in issue_codes(result)


def test_latest_verification_controls_current_status(tmp_path) -> None:
    create_demo(tmp_path, "math", "en")
    project = load_project(tmp_path)
    first = project.verifications[0]
    later = Verification(
        id="VER-ODD-002",
        claim_id=project.claims[0].id,
        verifier="Second independent reviewer",
        outcome=VerificationOutcome.REJECT,
        rationale="A later review rejects the packet.",
        checked_evidence_ids=project.claims[0].evidence_ids,
        previous_status=ClaimStatus.VERIFIED,
        resulting_status=ClaimStatus.REJECTED,
        snapshot_sha256=first.snapshot_sha256,
        created_at=first.created_at.replace(microsecond=first.created_at.microsecond + 1),
    )
    write_records(tmp_path / STATE_DIR / VERIFICATIONS_FILE, [first, later])
    result = audit_project(load_project(tmp_path))
    assert "RG_VERIFICATION_CURRENT_STATUS_MISMATCH" in issue_codes(result)
    assert "RG_ACCEPT_MISSING" in issue_codes(result)


def test_unreadable_evidence_is_a_deterministic_issue(tmp_path, monkeypatch) -> None:
    create_demo(tmp_path, "math", "en")

    def fail_read(_path):
        raise OSError("simulated read failure")

    monkeypatch.setattr("rigorgraph.audit.sha256_file", fail_read)
    result = audit_project(load_project(tmp_path))
    assert "RG_EVIDENCE_FILE_UNREADABLE" in issue_codes(result)
