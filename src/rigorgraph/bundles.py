from __future__ import annotations

import hashlib
from pathlib import Path

from pydantic import ValidationError

from rigorgraph.models import Evidence, EvidenceBundle


class BundleLoadError(ValueError):
    pass


def load_bundle(path: Path) -> tuple[EvidenceBundle, bytes, str]:
    try:
        raw = path.read_bytes()
        bundle = EvidenceBundle.model_validate_json(raw)
    except (OSError, UnicodeError, ValidationError, ValueError) as exc:
        raise BundleLoadError(str(exc)) from exc
    return bundle, raw, hashlib.sha256(raw).hexdigest()


def bundle_metadata(bundle: EvidenceBundle) -> dict[str, object]:
    return {
        "bundle": {
            "format": bundle.format,
            "schema_version": bundle.schema_version,
            "profile": bundle.profile,
            "producer": bundle.producer.model_dump(mode="json"),
            "provenance": (
                bundle.provenance.model_dump(mode="json", exclude_none=True)
                if bundle.provenance
                else None
            ),
            "result_status": bundle.result.status,
            "artifacts": [
                artifact.model_dump(mode="json", exclude_none=True)
                for artifact in bundle.artifacts
            ],
        }
    }


def evidence_from_bundle(
    bundle: EvidenceBundle,
    *,
    record_id: str,
    relative_path: str,
    digest: str,
) -> Evidence:
    return Evidence(
        id=record_id,
        type=bundle.evidence_type,
        title=bundle.title,
        producer=f"{bundle.producer.name}@{bundle.producer.version}",
        path=relative_path,
        scope=bundle.scope,
        sha256=digest,
        created_at=bundle.created_at,
        metadata=bundle_metadata(bundle),
    )
