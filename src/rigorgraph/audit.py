from __future__ import annotations

from collections import defaultdict

from pydantic import ValidationError

from rigorgraph.integrity import claim_snapshot_sha256, sha256_file
from rigorgraph.models import (
    AuditIssue,
    AuditResult,
    Claim,
    ClaimStatus,
    ClaimType,
    Evidence,
    EvidenceBundle,
    EvidenceType,
    ProjectData,
    Verification,
    VerificationOutcome,
)

REQUIRED_EVIDENCE: dict[ClaimType, list[set[EvidenceType]]] = {
    ClaimType.FORMAL: [{EvidenceType.PROOF}],
    ClaimType.LITERATURE: [{EvidenceType.SOURCE}],
    ClaimType.EMPIRICAL: [{EvidenceType.DATASET}, {EvidenceType.COMPUTATION}],
    ClaimType.BENCHMARK: [{EvidenceType.DATASET}, {EvidenceType.BENCHMARK_RUN}],
    ClaimType.SYNTHESIS: [],
}

OUTCOME_STATUS = {
    VerificationOutcome.ACCEPT: ClaimStatus.VERIFIED,
    VerificationOutcome.REJECT: ClaimStatus.REJECTED,
    VerificationOutcome.UNCERTAIN: ClaimStatus.UNCERTAIN,
}


def _issue(
    code: str,
    message_id: str,
    subject_id: str | None = None,
    severity: str = "error",
    **details: object,
) -> AuditIssue:
    return AuditIssue(
        code=code,
        severity=severity,
        message_id=message_id,
        subject_id=subject_id,
        details=details,
    )


def _duplicates(records: list[Claim | Evidence | Verification]) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for record in records:
        if record.id in seen:
            duplicates.add(record.id)
        seen.add(record.id)
    return duplicates


def _cycles(claims: dict[str, Claim]) -> list[list[str]]:
    cycles: list[list[str]] = []
    state: dict[str, int] = defaultdict(int)
    stack: list[str] = []

    def visit(claim_id: str) -> None:
        if state[claim_id] == 1:
            start = stack.index(claim_id)
            cycles.append(stack[start:] + [claim_id])
            return
        if state[claim_id] == 2:
            return
        state[claim_id] = 1
        stack.append(claim_id)
        for dependency in claims[claim_id].dependencies:
            if dependency in claims:
                visit(dependency)
        stack.pop()
        state[claim_id] = 2

    for claim_id in claims:
        if state[claim_id] == 0:
            visit(claim_id)
    return cycles


def _audit_claim_links(claims: dict[str, Claim], evidence: dict[str, Evidence]) -> list[AuditIssue]:
    issues: list[AuditIssue] = []
    for claim in claims.values():
        for dependency in claim.dependencies:
            if dependency not in claims:
                issues.append(
                    _issue(
                        "RG_DEPENDENCY_MISSING",
                        "issue.dependency_missing",
                        claim.id,
                        dependency=dependency,
                    )
                )
                continue
            dependency_status = claims[dependency].status
            if dependency_status in {ClaimStatus.REVOKED, ClaimStatus.REJECTED}:
                issues.append(
                    _issue(
                        "RG_DEPENDENCY_INVALID",
                        "issue.dependency_invalid",
                        claim.id,
                        dependency=dependency,
                        status=dependency_status.value,
                    )
                )
            elif claim.status == ClaimStatus.VERIFIED and dependency_status != ClaimStatus.VERIFIED:
                issues.append(
                    _issue(
                        "RG_DEPENDENCY_NOT_VERIFIED",
                        "issue.dependency_not_verified",
                        claim.id,
                        dependency=dependency,
                        status=dependency_status.value,
                    )
                )
        for evidence_id in claim.evidence_ids:
            if evidence_id not in evidence:
                issues.append(
                    _issue(
                        "RG_EVIDENCE_MISSING",
                        "issue.evidence_missing",
                        claim.id,
                        evidence=evidence_id,
                    )
                )
        if claim.status == ClaimStatus.SUPERSEDED:
            if not claim.supersedes:
                issues.append(_issue("RG_SUPERSEDES_MISSING", "issue.supersedes_missing", claim.id))
            elif claim.supersedes == claim.id or claim.supersedes not in claims:
                issues.append(
                    _issue(
                        "RG_SUPERSEDES_INVALID",
                        "issue.supersedes_invalid",
                        claim.id,
                        target=claim.supersedes,
                    )
                )
    for cycle in _cycles(claims):
        issues.append(
            _issue(
                "RG_DEPENDENCY_CYCLE",
                "issue.dependency_cycle",
                cycle[0],
                cycle=" -> ".join(cycle),
            )
        )
    return issues


def _audit_evidence_files(project: ProjectData) -> list[AuditIssue]:
    issues: list[AuditIssue] = []
    for item in project.evidence:
        if item.type == EvidenceType.SOURCE and (not item.locator or not item.uri):
            issues.append(_issue("RG_SOURCE_UNSCOPED", "issue.source_unscoped", item.id))
        if not item.path:
            continue
        try:
            evidence_path = (project.root / item.path).resolve()
            evidence_path.relative_to(project.root)
            if not evidence_path.is_file():
                issues.append(
                    _issue(
                        "RG_EVIDENCE_FILE_MISSING",
                        "issue.evidence_file_missing",
                        item.id,
                        path=item.path,
                    )
                )
            elif sha256_file(evidence_path).lower() != item.sha256.lower():
                issues.append(
                    _issue("RG_HASH_MISMATCH", "issue.hash_mismatch", item.id, path=item.path)
                )
            elif (
                isinstance(item.metadata.get("bundle"), dict)
                and item.metadata["bundle"].get("format") == "rigorgraph-evidence-bundle"
            ):
                try:
                    EvidenceBundle.model_validate_json(evidence_path.read_bytes())
                except (OSError, ValidationError, ValueError) as exc:
                    issues.append(
                        _issue(
                            "RG_BUNDLE_INVALID",
                            "issue.bundle_invalid",
                            item.id,
                            detail=str(exc),
                        )
                    )
        except ValueError:
            issues.append(_issue("RG_PATH_ESCAPE", "issue.path_escape", item.id, path=item.path))
        except (OSError, RuntimeError) as exc:
            issues.append(
                _issue(
                    "RG_EVIDENCE_FILE_UNREADABLE",
                    "issue.evidence_file_unreadable",
                    item.id,
                    path=item.path,
                    detail=str(exc),
                )
            )
    return issues


def _audit_verifications(
    claims: dict[str, Claim],
    evidence: dict[str, Evidence],
    verifications: list[Verification],
) -> list[AuditIssue]:
    issues: list[AuditIssue] = []
    by_claim: dict[str, list[Verification]] = defaultdict(list)
    for verification in verifications:
        if verification.claim_id not in claims:
            issues.append(
                _issue(
                    "RG_VERIFICATION_CLAIM_MISSING",
                    "issue.verification_claim_missing",
                    verification.id,
                )
            )
            continue
        claim = claims[verification.claim_id]
        by_claim[claim.id].append(verification)
        if verification.verifier in claim.authors:
            issues.append(
                _issue("RG_SELF_VERIFICATION", "issue.self_verification", verification.id)
            )
        expected = OUTCOME_STATUS[verification.outcome]
        if verification.resulting_status != expected:
            issues.append(
                _issue(
                    "RG_OUTCOME_STATUS_MISMATCH",
                    "issue.outcome_status_mismatch",
                    verification.id,
                    expected=expected.value,
                )
            )
        for evidence_id in verification.checked_evidence_ids:
            if evidence_id not in claim.evidence_ids:
                issues.append(
                    _issue(
                        "RG_UNLINKED_CHECKED_EVIDENCE",
                        "issue.unlinked_checked_evidence",
                        verification.id,
                        evidence=evidence_id,
                    )
                )

    for claim in claims.values():
        history = sorted(by_claim.get(claim.id, []), key=lambda item: (item.created_at, item.id))
        previous_result: ClaimStatus | None = None
        for index, verification in enumerate(history):
            if index == 0 and verification.previous_status not in {
                ClaimStatus.PROPOSED,
                ClaimStatus.UNDER_REVIEW,
            }:
                issues.append(
                    _issue(
                        "RG_VERIFICATION_HISTORY_MISMATCH",
                        "issue.verification_history_mismatch",
                        verification.id,
                    )
                )
            if previous_result is not None and verification.previous_status != previous_result:
                issues.append(
                    _issue(
                        "RG_VERIFICATION_HISTORY_MISMATCH",
                        "issue.verification_history_mismatch",
                        verification.id,
                    )
                )
            previous_result = verification.resulting_status

        if history and claim.status not in {ClaimStatus.REVOKED, ClaimStatus.SUPERSEDED}:
            if history[-1].resulting_status != claim.status:
                issues.append(
                    _issue(
                        "RG_VERIFICATION_CURRENT_STATUS_MISMATCH",
                        "issue.verification_current_status_mismatch",
                        claim.id,
                        expected=history[-1].resulting_status.value,
                    )
                )

        if claim.status != ClaimStatus.VERIFIED:
            continue
        if not history:
            issues.append(_issue("RG_ACCEPT_MISSING", "issue.accept_missing", claim.id))
            continue
        accepted = history[-1]
        if accepted.outcome != VerificationOutcome.ACCEPT or accepted.verifier in claim.authors:
            issues.append(_issue("RG_ACCEPT_MISSING", "issue.accept_missing", claim.id))
            continue
        expected_snapshot = claim_snapshot_sha256(claim, evidence)
        if accepted.snapshot_sha256.lower() != expected_snapshot:
            issues.append(_issue("RG_SNAPSHOT_MISMATCH", "issue.snapshot_mismatch", claim.id))

        linked_types = {
            evidence[evidence_id].type
            for evidence_id in claim.evidence_ids
            if evidence_id in evidence
        }
        checked_types = {
            evidence[evidence_id].type
            for evidence_id in accepted.checked_evidence_ids
            if evidence_id in evidence
        }
        for required_group in REQUIRED_EVIDENCE[claim.type]:
            required = " or ".join(sorted(item.value for item in required_group))
            if not linked_types.intersection(required_group):
                issues.append(
                    _issue(
                        "RG_EVIDENCE_TYPE_MISSING",
                        "issue.evidence_type_missing",
                        claim.id,
                        required=required,
                    )
                )
            if not checked_types.intersection(required_group):
                issues.append(
                    _issue(
                        "RG_ACCEPT_EVIDENCE_UNCHECKED",
                        "issue.accept_evidence_unchecked",
                        claim.id,
                        required=required,
                    )
                )
        if claim.type == ClaimType.SYNTHESIS and not claim.dependencies:
            issues.append(
                _issue(
                    "RG_SYNTHESIS_DEPENDENCIES_INVALID",
                    "issue.synthesis_dependencies_invalid",
                    claim.id,
                )
            )
    return issues


def audit_project(project: ProjectData) -> AuditResult:
    issues: list[AuditIssue] = []
    for group, records in (
        ("claim", project.claims),
        ("evidence", project.evidence),
        ("verification", project.verifications),
    ):
        for record_id in _duplicates(records):
            issues.append(_issue("RG_DUPLICATE_ID", "issue.duplicate_id", record_id, group=group))

    claims = {claim.id: claim for claim in project.claims}
    evidence = {item.id: item for item in project.evidence}
    verification_map = {item.id: item for item in project.verifications}
    issues.extend(_audit_claim_links(claims, evidence))
    issues.extend(_audit_evidence_files(project))
    issues.extend(_audit_verifications(claims, evidence, project.verifications))

    errors = sum(issue.severity == "error" for issue in issues)
    warnings = sum(issue.severity == "warning" for issue in issues)
    return AuditResult(
        status="PASS" if errors == 0 else "FAIL",
        errors=errors,
        warnings=warnings,
        claims=len(project.claims),
        evidence=len(project.evidence),
        verifications=len(verification_map),
        issues=issues,
    )


def should_fail(result: AuditResult, fail_on: str) -> bool:
    if fail_on == "never":
        return False
    if fail_on == "warning":
        return result.errors > 0 or result.warnings > 0
    return result.errors > 0
