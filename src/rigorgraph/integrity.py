from __future__ import annotations

import hashlib
import json
from pathlib import Path

from rigorgraph.models import Claim, Evidence


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def claim_snapshot_sha256(claim: Claim, evidence: dict[str, Evidence]) -> str:
    claim_payload = claim.model_dump(
        mode="json",
        exclude={"status", "created_at", "updated_at"},
        exclude_none=True,
    )
    evidence_payload = [
        evidence[evidence_id].model_dump(mode="json", exclude={"created_at"}, exclude_none=True)
        for evidence_id in sorted(claim.evidence_ids)
        if evidence_id in evidence
    ]
    payload = {"claim": claim_payload, "evidence": evidence_payload}
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
