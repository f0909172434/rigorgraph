from __future__ import annotations

import argparse
import os
import re
import sys
import uuid
from pathlib import Path

from rigorgraph.audit import audit_project, should_fail
from rigorgraph.i18n import resolve_language
from rigorgraph.report import generate_report
from rigorgraph.storage import ProjectLoadError, load_project


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", default=".")
    parser.add_argument("--fail-on", choices=("error", "warning", "never"), default="error")
    parser.add_argument("--report", default="rigorgraph-report.html")
    return parser.parse_args()


def _resolve_report_path(root: Path, value: str) -> Path:
    if not value or any(character in value for character in ("\0", "\r", "\n")):
        raise ValueError("report must be a non-empty single-line relative path")
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("report must remain inside the project directory")
    if relative.parent != Path(".") or not re.fullmatch(
        r"[A-Za-z0-9][A-Za-z0-9._-]*\.html", value, re.IGNORECASE
    ):
        raise ValueError("report must be a literal HTML filename without directories or patterns")

    root = root.resolve()
    destination = root / relative
    if destination.is_symlink():
        raise ValueError("report destination must not be a symbolic link")
    resolved_parent = destination.parent.resolve()
    try:
        resolved_parent.relative_to(root)
    except ValueError as exc:
        raise ValueError("report destination must remain inside the project directory") from exc
    return resolved_parent / destination.name


def _write_github_output(handle, name: str, value: str) -> None:
    delimiter = f"rigorgraph_{uuid.uuid4().hex}"
    handle.write(f"{name}<<{delimiter}\n{value}\n{delimiter}\n")


def main() -> int:
    args = parse_args()
    root = Path(args.path).resolve()
    try:
        report_path = _resolve_report_path(root, args.report)
    except ValueError as exc:
        print(f"::error title=RG_REPORT_PATH_INVALID::{exc}")
        return 2
    try:
        project = load_project(root)
    except ProjectLoadError as exc:
        print(f"::error title={exc.code}::{exc.path}: {exc.detail}")
        return 2
    result = audit_project(project)
    report_path = generate_report(project, result, report_path, resolve_language(root))

    summary = os.getenv("GITHUB_STEP_SUMMARY")
    if summary:
        with Path(summary).open("a", encoding="utf-8") as handle:
            handle.write("# RigorGraph audit\n\n")
            handle.write(
                f"**{result.status}** · {result.errors} errors · {result.warnings} warnings\n\n"
            )
            handle.write(
                f"{result.claims} claims · {result.evidence} evidence records · "
                f"{result.verifications} verifications\n\n"
            )
            if result.issues:
                handle.write("| Severity | Code | Subject |\n| --- | --- | --- |\n")
                for issue in result.issues:
                    handle.write(
                        f"| {issue.severity} | `{issue.code}` | `{issue.subject_id or '-'}` |\n"
                    )
            handle.write("\nRigorGraph validates workflow integrity, not absolute truth.\n")

    output = os.getenv("GITHUB_OUTPUT")
    if output:
        with Path(output).open("a", encoding="utf-8") as handle:
            _write_github_output(handle, "report", str(report_path))
            _write_github_output(handle, "status", result.status)
    print(result.model_dump_json())
    return 1 if should_fail(result, args.fail_on) else 0


if __name__ == "__main__":
    sys.exit(main())
