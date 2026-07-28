from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path

from rigorgraph.i18n import LanguageChoice, load_all_catalogs
from rigorgraph.models import AuditResult, ProjectData


class ViewerMissingError(RuntimeError):
    pass


def _escape_script_json(payload: object) -> str:
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return (
        raw.replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


def generate_report(
    project: ProjectData,
    audit: AuditResult,
    output: Path,
    language: LanguageChoice,
) -> Path:
    template_resource = files("rigorgraph").joinpath("viewer", "index.html")
    if not template_resource.is_file():
        raise ViewerMissingError("viewer/index.html is not bundled")
    template = template_resource.read_text(encoding="utf-8")
    marker = "__RIGORGRAPH_DATA__"
    if marker not in template:
        raise ViewerMissingError("viewer data marker is missing")
    payload = {
        "project": {
            "name": project.config.name,
            "root": project.root.name,
        },
        "claims": [item.model_dump(mode="json", exclude_none=True) for item in project.claims],
        "evidence": [item.model_dump(mode="json", exclude_none=True) for item in project.evidence],
        "verifications": [
            item.model_dump(mode="json", exclude_none=True) for item in project.verifications
        ],
        "audit": audit.model_dump(mode="json"),
        "locales": load_all_catalogs(),
        "language": {
            "default": language.code,
            "source": language.source,
            "supported": language.supported,
        },
    }
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    html = template.replace(marker, _escape_script_json(payload), 1)
    output.write_text(html, encoding="utf-8", newline="\n")
    return output
