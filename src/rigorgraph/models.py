from __future__ import annotations

import re
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path, PurePosixPath
from typing import Any, Literal
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def utc_now() -> datetime:
    return datetime.now(UTC)


def _require_unicode_scalars(value: Any) -> None:
    if isinstance(value, str):
        if any("\ud800" <= character <= "\udfff" for character in value):
            raise ValueError("strings must contain valid Unicode scalar values")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            _require_unicode_scalars(key)
            _require_unicode_scalars(item)
        return
    if isinstance(value, (list, tuple, set, frozenset)):
        for item in value:
            _require_unicode_scalars(item)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @model_validator(mode="before")
    @classmethod
    def validate_unicode_scalars(cls, value: Any) -> Any:
        _require_unicode_scalars(value)
        return value


class AdditiveModel(BaseModel):
    """A stable v1 wire model that permits future optional fields."""

    model_config = ConfigDict(extra="allow", str_strip_whitespace=True, populate_by_name=True)

    @model_validator(mode="before")
    @classmethod
    def validate_unicode_scalars(cls, value: Any) -> Any:
        _require_unicode_scalars(value)
        return value


class ClaimType(StrEnum):
    FORMAL = "formal"
    LITERATURE = "literature"
    EMPIRICAL = "empirical"
    BENCHMARK = "benchmark"
    SYNTHESIS = "synthesis"


class EvidenceType(StrEnum):
    PROOF = "proof"
    SOURCE = "source"
    DATASET = "dataset"
    COMPUTATION = "computation"
    BENCHMARK_RUN = "benchmark_run"
    HUMAN_REVIEW = "human_review"


class EvidenceProducer(StrictModel):
    name: str = Field(min_length=1)
    version: str = Field(
        pattern=r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
    )


class EvidenceProvenance(StrictModel):
    repository: str | None = Field(default=None, min_length=1)
    commit: str | None = Field(default=None, pattern=r"^[a-fA-F0-9]{40,64}$")
    ref: str | None = Field(default=None, min_length=1)
    workflow_ref: str | None = Field(default=None, min_length=1)
    run_id: str | None = Field(default=None, min_length=1)
    run_attempt: int | None = Field(default=None, ge=1)
    event: str | None = Field(default=None, min_length=1)


class EvidenceArtifact(AdditiveModel):
    role: str = Field(min_length=1)
    path: str = Field(min_length=1)
    size: int = Field(ge=0)
    sha256: str = Field(pattern=r"^[a-fA-F0-9]{64}$")

    @field_validator("path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        candidate = PurePosixPath(value)
        if (
            "\\" in value
            or candidate.is_absolute()
            or value in {"", "."}
            or ".." in candidate.parts
        ):
            raise ValueError("artifact path must be a relative POSIX path without traversal")
        return value


class HonestCITotals(AdditiveModel):
    tests: int = Field(ge=0)
    failures: int = Field(ge=0)
    errors: int = Field(ge=0)
    skipped: int = Field(ge=0)


class HonestCIReport(HonestCITotals):
    name: str = Field(min_length=1)
    files: list[str]
    baseline_tests: int | None = Field(default=None, alias="baselineTests", ge=0)
    drop_percent: float | None = Field(default=None, alias="dropPercent", ge=0)


class HonestCIFinding(AdditiveModel):
    code: str = Field(pattern=r"^HCI\d{3}_[A-Z0-9_]+$")
    severity: Literal["error", "warning"]
    message: str = Field(min_length=1)
    file: str | None = None
    line: int | None = Field(default=None, ge=1)
    report: str | None = None


class HonestCIResult(AdditiveModel):
    schema_version: Literal[1] = Field(alias="schemaVersion")
    status: Literal["passed", "failed"]
    totals: HonestCITotals
    baseline_tests: int | None = Field(default=None, alias="baselineTests", ge=0)
    drop_percent: float | None = Field(default=None, alias="dropPercent", ge=0)
    reports: list[HonestCIReport]
    findings: list[HonestCIFinding]


class EvidenceBundle(AdditiveModel):
    format: Literal["rigorgraph-evidence-bundle"]
    schema_version: Literal[1]
    profile: Literal["honest-ci/check-result-v1"]
    evidence_type: EvidenceType
    title: str = Field(min_length=1)
    scope: str = Field(min_length=1)
    created_at: datetime
    producer: EvidenceProducer
    provenance: EvidenceProvenance | None = None
    artifacts: list[EvidenceArtifact] = Field(min_length=1)
    result: HonestCIResult

    @model_validator(mode="after")
    def validate_profile(self) -> EvidenceBundle:
        paths = [artifact.path for artifact in self.artifacts]
        if len(paths) != len(set(paths)):
            raise ValueError("artifact paths must be unique")
        if self.evidence_type != EvidenceType.COMPUTATION:
            raise ValueError("HonestCI bundles must use computation evidence")
        if self.producer.name != "honest-ci":
            raise ValueError("HonestCI bundle producer must be honest-ci")
        return self


class ClaimStatus(StrEnum):
    DRAFT = "DRAFT"
    PROPOSED = "PROPOSED"
    UNDER_REVIEW = "UNDER_REVIEW"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    UNCERTAIN = "UNCERTAIN"
    REVOKED = "REVOKED"
    SUPERSEDED = "SUPERSEDED"


class VerificationOutcome(StrEnum):
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"
    UNCERTAIN = "UNCERTAIN"


class ProjectConfig(StrictModel):
    version: Literal[1]
    name: str = Field(min_length=1)
    language: str | None = None
    fail_on: str = "error"

    @field_validator("fail_on")
    @classmethod
    def validate_fail_on(cls, value: str) -> str:
        if value not in {"error", "warning", "never"}:
            raise ValueError("fail_on must be error, warning, or never")
        return value


class Claim(StrictModel):
    id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{1,127}$")
    statement: str = Field(min_length=1)
    type: ClaimType
    status: ClaimStatus = ClaimStatus.DRAFT
    authors: list[str] = Field(min_length=1)
    dependencies: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    supersedes: str | None = None

    @field_validator("authors", "dependencies", "evidence_ids")
    @classmethod
    def unique_values(cls, values: list[str]) -> list[str]:
        if len(values) != len(set(values)):
            raise ValueError("values must be unique")
        return values


class Evidence(StrictModel):
    id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{1,127}$")
    type: EvidenceType
    title: str = Field(min_length=1)
    producer: str = Field(min_length=1)
    path: str | None = None
    uri: str | None = None
    locator: str | None = None
    scope: str = Field(min_length=1)
    sha256: str | None = Field(default=None, pattern=r"^[a-fA-F0-9]{64}$")
    created_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_location(self) -> Evidence:
        if bool(self.path) == bool(self.uri):
            raise ValueError("exactly one of path or uri is required")
        if self.path and not self.sha256:
            raise ValueError("local evidence requires sha256")
        if self.uri and not self.locator:
            raise ValueError("remote evidence requires an exact locator")
        return self

    @field_validator("uri")
    @classmethod
    def validate_uri(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if value.startswith("doi:"):
            if not re.fullmatch(r"doi:10\.\d{4,9}/\S+", value, re.IGNORECASE):
                raise ValueError("doi URI must contain a valid DOI")
            return value
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("uri must be an absolute http, https, or doi URI")
        return value


class Verification(StrictModel):
    id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{1,127}$")
    claim_id: str
    verifier: str = Field(min_length=1)
    outcome: VerificationOutcome
    rationale: str = Field(min_length=1)
    checked_evidence_ids: list[str] = Field(default_factory=list)
    previous_status: ClaimStatus
    resulting_status: ClaimStatus
    snapshot_sha256: str = Field(pattern=r"^[a-fA-F0-9]{64}$")
    created_at: datetime = Field(default_factory=utc_now)


class VerificationRequest(StrictModel):
    id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{1,127}$")
    verifier: str = Field(min_length=1)
    outcome: VerificationOutcome
    rationale: str = Field(min_length=1)
    checked_evidence_ids: list[str] = Field(default_factory=list)


class AuditIssue(StrictModel):
    code: str
    severity: str
    message_id: str
    subject_id: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class AuditResult(StrictModel):
    status: str
    errors: int
    warnings: int
    claims: int
    evidence: int
    verifications: int
    issues: list[AuditIssue]


class ProjectData(StrictModel):
    root: Path
    config: ProjectConfig
    claims: list[Claim]
    evidence: list[Evidence]
    verifications: list[Verification]

    model_config = ConfigDict(arbitrary_types_allowed=True)
