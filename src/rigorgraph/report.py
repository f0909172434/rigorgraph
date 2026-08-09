from __future__ import annotations

import json
import os
import tempfile
from importlib.resources import files
from pathlib import Path

from rigorgraph.i18n import LanguageChoice, load_all_catalogs
from rigorgraph.models import AuditResult, ProjectData
from rigorgraph.storage import is_link_or_reparse


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


def _safe_report_path(output: Path) -> Path:
    lexical_parent = Path(os.path.abspath(output.parent))
    resolved_parent = output.parent.resolve()
    if os.path.normcase(str(lexical_parent)) != os.path.normcase(str(resolved_parent)):
        raise ValueError("report parent must not contain a symbolic link or reparse point")
    destination = lexical_parent / output.name
    if is_link_or_reparse(destination):
        raise ValueError("report destination must not be a symbolic link or reparse point")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if is_link_or_reparse(destination):
        raise ValueError("report destination must not be a symbolic link or reparse point")
    return destination


def _atomic_write_report(path: Path, html: str) -> None:
    content = html.encode("utf-8")
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary_path = Path(temporary)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        if is_link_or_reparse(path):
            raise ValueError("report destination must not be a symbolic link or reparse point")
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)


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
    output = _safe_report_path(output)
    html = template.replace(marker, _escape_script_json(payload), 1)
    _atomic_write_report(output, html)
    return output
