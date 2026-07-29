from __future__ import annotations

import hashlib
from pathlib import Path

from pydantic import ValidationError

from rigorgraph.models import EvidenceBundle


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
