from __future__ import annotations

import argparse
import os
import sys
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


def main() -> int:
    args = parse_args()
    root = Path(args.path).resolve()
    report_path = Path(args.report)
    if not report_path.is_absolute():
        report_path = root / report_path
    try:
        project = load_project(root)
    except ProjectLoadError as exc:
        print(f"::error title={exc.code}::{exc.path}: {exc.detail}")
        return 2
    result = audit_project(project)
    generate_report(project, result, report_path, resolve_language(root))

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
            handle.write(f"report={report_path}\n")
            handle.write(f"status={result.status}\n")
    print(result.model_dump_json())
    return 1 if should_fail(result, args.fail_on) else 0


if __name__ == "__main__":
    sys.exit(main())
