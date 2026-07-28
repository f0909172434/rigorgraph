from __future__ import annotations

import json
import sys
import webbrowser
from pathlib import Path
from typing import Annotated, Any

import typer
from pydantic import ValidationError
from rich.console import Console
from rich.table import Table
from typer.core import TyperCommand, TyperGroup

from rigorgraph import __version__
from rigorgraph.audit import OUTCOME_STATUS, audit_project, should_fail
from rigorgraph.demo import create_demo
from rigorgraph.i18n import LanguageChoice, Translator, resolve_language
from rigorgraph.integrity import claim_snapshot_sha256
from rigorgraph.models import (
    Claim,
    ClaimStatus,
    ClaimType,
    Evidence,
    Verification,
    VerificationRequest,
)
from rigorgraph.report import ViewerMissingError, generate_report
from rigorgraph.storage import (
    CLAIMS_FILE,
    EVIDENCE_FILE,
    STATE_DIR,
    VERIFICATIONS_FILE,
    ProjectLoadError,
    ProjectLockError,
    append_record,
    find_duplicate_id,
    initialize_project,
    load_project,
    project_lock,
    write_records,
)

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")


def _help_text(ctx: typer.Context) -> str:
    root = ctx.find_root()
    explicit = (root.obj or {}).get("lang")
    if explicit is None and root.params:
        explicit = root.params.get("lang")
    choice = resolve_language(Path.cwd(), explicit)
    translator = Translator(choice.code)
    parts = ctx.command_path.split()[1:]
    key = ".".join(parts) if parts else "root"
    return translator.text(f"help.{key}")


class LocalizedGroup(TyperGroup):
    def get_help(self, ctx: typer.Context) -> str:
        return _help_text(ctx)


class LocalizedCommand(TyperCommand):
    def get_help(self, ctx: typer.Context) -> str:
        return _help_text(ctx)


def _capture_language(ctx: typer.Context, value: str | None) -> str | None:
    ctx.ensure_object(dict)
    ctx.obj["lang"] = value
    return value


def _show_version(value: bool) -> None:
    if value:
        typer.echo(f"rigorgraph {__version__}")
        raise typer.Exit()


app = typer.Typer(
    name="rigorgraph",
    help="Turn AI research into auditable claim-evidence graphs.",
    no_args_is_help=True,
    cls=LocalizedGroup,
)
claim_app = typer.Typer(
    help="Create and manage research claims.", no_args_is_help=True, cls=LocalizedGroup
)
evidence_app = typer.Typer(
    help="Create and manage evidence records.", no_args_is_help=True, cls=LocalizedGroup
)
app.add_typer(claim_app, name="claim")
app.add_typer(evidence_app, name="evidence")
console = Console()
error_console = Console(stderr=True)


@app.callback()
def main(
    ctx: typer.Context,
    lang: Annotated[
        str | None,
        typer.Option(
            "--lang",
            help="Display language: en, zh-TW, zh-CN, or ja.",
            callback=_capture_language,
            is_eager=True,
        ),
    ] = None,
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            help="Show the installed RigorGraph version.",
            callback=_show_version,
            is_eager=True,
        ),
    ] = False,
) -> None:
    """Use --lang before a subcommand to override the configured or system language."""
    ctx.ensure_object(dict)
    ctx.obj["lang"] = lang


def _explicit_language(ctx: typer.Context) -> str | None:
    root = ctx.find_root()
    return (root.obj or {}).get("lang")


def _language(ctx: typer.Context, path: Path) -> tuple[LanguageChoice, Translator]:
    choice = resolve_language(path, _explicit_language(ctx))
    translator = Translator(choice.code)
    if not choice.supported:
        error_console.print(
            translator.text("language.unsupported", requested=choice.requested or ""),
            style="yellow",
        )
    return choice, translator


def _load(path: Path, translator: Translator):
    try:
        return load_project(path)
    except ProjectLoadError as exc:
        error_console.print(
            translator.text(
                "project.load_error",
                code=exc.code,
                path=exc.path,
                detail=exc.detail,
            ),
            style="red",
        )
        raise typer.Exit(2) from exc


def _mutation_error(exc: ProjectLockError, translator: Translator) -> None:
    error_console.print(translator.text("error.project_locked", detail=exc), style="red")


def _parse_file(path: Path, model: type[Any], translator: Translator):
    try:
        return model.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValidationError, json.JSONDecodeError) as exc:
        error_console.print(translator.text("error.input_invalid", detail=exc), style="red")
        raise typer.Exit(2) from exc


@app.command("init", cls=LocalizedCommand)
def init_command(
    ctx: typer.Context,
    path: Annotated[Path, typer.Argument(help="Project directory.")] = Path("."),
    name: Annotated[
        str, typer.Option("--name", help="Project name.")
    ] = "RigorGraph research project",
) -> None:
    choice, translator = _language(ctx, path)
    created = initialize_project(path.resolve(), name, choice.code)
    if created:
        console.print(translator.text("init.created", path=path.resolve()), style="green")
    else:
        console.print(translator.text("init.existing"), style="yellow")


@app.command("quickstart", cls=LocalizedCommand)
def quickstart_command(
    ctx: typer.Context,
    statement: Annotated[
        str,
        typer.Option("--statement", help="Initial research claim in the user's original language."),
    ],
    author: Annotated[
        str,
        typer.Option("--author", help="Author of the initial research claim."),
    ],
    path: Annotated[Path, typer.Argument(help="Directory for the new project.")] = Path(
        "rigorgraph-project"
    ),
    claim_type: Annotated[
        str,
        typer.Option("--type", help="Claim type: formal, literature, empirical, or benchmark."),
    ] = "formal",
    claim_id: Annotated[
        str,
        typer.Option("--claim-id", help="Stable English identifier for the initial claim."),
    ] = "CLM-001",
    name: Annotated[
        str,
        typer.Option("--name", help="Project name."),
    ] = "RigorGraph research project",
    open_report: Annotated[
        bool,
        typer.Option("--open", help="Open the generated report in a browser."),
    ] = False,
) -> None:
    choice, translator = _language(ctx, path)
    target = path.resolve()
    if target.exists() and (not target.is_dir() or any(target.iterdir())):
        error_console.print(translator.text("error.file_exists", path=target), style="red")
        raise typer.Exit(1)
    try:
        selected_type = ClaimType(claim_type)
        if selected_type == ClaimType.SYNTHESIS:
            raise ValueError("quickstart requires a primary claim type, not synthesis")
        claim = Claim(
            id=claim_id,
            statement=statement,
            type=selected_type,
            status=ClaimStatus.DRAFT,
            authors=[author],
        )
    except (ValidationError, ValueError) as exc:
        error_console.print(translator.text("error.input_invalid", detail=exc), style="red")
        raise typer.Exit(2) from exc

    initialize_project(target, name, choice.code)
    append_record(target / STATE_DIR / CLAIMS_FILE, claim)
    project = _load(target, translator)
    result = audit_project(project)
    report_path = target / "rigorgraph-report.html"
    try:
        generate_report(project, result, report_path, choice)
    except ViewerMissingError as exc:
        error_console.print(translator.text("error.viewer_missing"), style="red")
        raise typer.Exit(2) from exc
    console.print(
        translator.text(
            "quickstart.created",
            id=claim.id,
            path=report_path,
        ),
        style="green",
    )
    console.print(translator.text("quickstart.boundary"), style="yellow")
    if open_report:
        webbrowser.open(report_path.as_uri())


@claim_app.command("add", cls=LocalizedCommand)
def claim_add(
    ctx: typer.Context,
    record_file: Annotated[Path, typer.Argument(help="JSON file containing one claim.")],
    path: Annotated[Path, typer.Option("--path", help="RigorGraph project directory.")] = Path("."),
) -> None:
    _, translator = _language(ctx, path)
    claim = _parse_file(record_file, Claim, translator)
    if claim.status not in {ClaimStatus.DRAFT, ClaimStatus.PROPOSED}:
        error_console.print(
            translator.text("error.input_invalid", detail="new claims must be DRAFT or PROPOSED"),
            style="red",
        )
        raise typer.Exit(2)
    try:
        with project_lock(path):
            project = _load(path, translator)
            if find_duplicate_id(project.claims, claim.id):
                error_console.print(translator.text("record.duplicate", id=claim.id), style="red")
                raise typer.Exit(1)
            append_record(project.root / STATE_DIR / CLAIMS_FILE, claim)
    except ProjectLockError as exc:
        _mutation_error(exc, translator)
        raise typer.Exit(2) from exc
    console.print(translator.text("record.added", kind="claim", id=claim.id), style="green")


@evidence_app.command("add", cls=LocalizedCommand)
def evidence_add(
    ctx: typer.Context,
    record_file: Annotated[Path, typer.Argument(help="JSON file containing one evidence record.")],
    path: Annotated[Path, typer.Option("--path", help="RigorGraph project directory.")] = Path("."),
) -> None:
    _, translator = _language(ctx, path)
    evidence = _parse_file(record_file, Evidence, translator)
    try:
        with project_lock(path):
            project = _load(path, translator)
            if find_duplicate_id(project.evidence, evidence.id):
                error_console.print(
                    translator.text("record.duplicate", id=evidence.id), style="red"
                )
                raise typer.Exit(1)
            append_record(project.root / STATE_DIR / EVIDENCE_FILE, evidence)
    except ProjectLockError as exc:
        _mutation_error(exc, translator)
        raise typer.Exit(2) from exc
    console.print(translator.text("record.added", kind="evidence", id=evidence.id), style="green")


@app.command("verify", cls=LocalizedCommand)
def verify_command(
    ctx: typer.Context,
    claim_id: Annotated[str, typer.Argument(help="Claim ID to verify.")],
    record_file: Annotated[Path, typer.Option("--file", help="JSON verification request.")],
    path: Annotated[Path, typer.Option("--path", help="RigorGraph project directory.")] = Path("."),
) -> None:
    _, translator = _language(ctx, path)
    request = _parse_file(record_file, VerificationRequest, translator)
    try:
        with project_lock(path):
            project = _load(path, translator)
            claim = next((item for item in project.claims if item.id == claim_id), None)
            if claim is None:
                error_console.print(
                    translator.text("error.claim_not_found", id=claim_id), style="red"
                )
                raise typer.Exit(1)
            if claim.status not in {ClaimStatus.PROPOSED, ClaimStatus.UNDER_REVIEW}:
                error_console.print(
                    translator.text("error.claim_status", id=claim.id, status=claim.status.value),
                    style="red",
                )
                raise typer.Exit(1)
            if request.verifier in claim.authors:
                error_console.print(translator.text("issue.self_verification"), style="red")
                raise typer.Exit(1)
            if find_duplicate_id(project.verifications, request.id):
                error_console.print(translator.text("record.duplicate", id=request.id), style="red")
                raise typer.Exit(1)
            unlinked = set(request.checked_evidence_ids) - set(claim.evidence_ids)
            if unlinked:
                detail = translator.text(
                    "issue.unlinked_checked_evidence", evidence=sorted(unlinked)[0]
                )
                error_console.print(
                    translator.text("error.input_invalid", detail=detail), style="red"
                )
                raise typer.Exit(2)
            evidence_map = {item.id: item for item in project.evidence}
            checked_types = {
                evidence_map[item_id].type
                for item_id in request.checked_evidence_ids
                if item_id in evidence_map
            }
            if request.outcome.value == "ACCEPT":
                from rigorgraph.audit import REQUIRED_EVIDENCE

                for required_group in REQUIRED_EVIDENCE[claim.type]:
                    if not checked_types.intersection(required_group):
                        detail = translator.text(
                            "issue.accept_evidence_unchecked",
                            required=" or ".join(sorted(item.value for item in required_group)),
                        )
                        error_console.print(
                            translator.text("error.input_invalid", detail=detail), style="red"
                        )
                        raise typer.Exit(2)
            new_status = OUTCOME_STATUS[request.outcome]
            verification = Verification(
                **request.model_dump(),
                claim_id=claim.id,
                previous_status=claim.status,
                resulting_status=new_status,
                snapshot_sha256=claim_snapshot_sha256(claim, evidence_map),
            )
            updated_claims = [
                item.model_copy(
                    update={"status": new_status, "updated_at": verification.created_at}
                )
                if item.id == claim.id
                else item
                for item in project.claims
            ]
            append_record(project.root / STATE_DIR / VERIFICATIONS_FILE, verification)
            write_records(project.root / STATE_DIR / CLAIMS_FILE, updated_claims)
    except ProjectLockError as exc:
        _mutation_error(exc, translator)
        raise typer.Exit(2) from exc
    console.print(
        translator.text(
            "verify.updated",
            outcome=request.outcome.value,
            claim=claim.id,
            status=new_status.value,
        ),
        style="green",
    )


def _localized_issue(issue: Any, translator: Translator) -> str:
    return translator.text(issue.message_id, **issue.details)


@app.command("audit", cls=LocalizedCommand)
def audit_command(
    ctx: typer.Context,
    path: Annotated[Path, typer.Argument(help="RigorGraph project directory.")] = Path("."),
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON output.")] = False,
    fail_on: Annotated[
        str | None,
        typer.Option("--fail-on", help="Failure threshold: error, warning, or never."),
    ] = None,
) -> None:
    _, translator = _language(ctx, path)
    project = _load(path, translator)
    result = audit_project(project)
    threshold = fail_on or project.config.fail_on
    if json_output:
        console.print_json(result.model_dump_json())
    else:
        message_id = "audit.pass" if result.status == "PASS" else "audit.fail"
        console.print(
            translator.text(message_id, errors=result.errors, warnings=result.warnings),
            style="green" if result.status == "PASS" else "red",
        )
        console.print(
            translator.text(
                "audit.counts",
                claims=result.claims,
                evidence=result.evidence,
                verifications=result.verifications,
            )
        )
        if result.issues:
            table = Table(show_header=False, box=None)
            for issue in result.issues:
                table.add_row(
                    issue.severity.upper(),
                    issue.code,
                    issue.subject_id or "-",
                    _localized_issue(issue, translator),
                )
            console.print(table)
    if should_fail(result, threshold):
        raise typer.Exit(1)


@app.command("report", cls=LocalizedCommand)
def report_command(
    ctx: typer.Context,
    path: Annotated[Path, typer.Argument(help="RigorGraph project directory.")] = Path("."),
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output HTML file."),
    ] = Path("rigorgraph-report.html"),
    open_report: Annotated[
        bool, typer.Option("--open", help="Open the report in a browser.")
    ] = False,
) -> None:
    choice, translator = _language(ctx, path)
    project = _load(path, translator)
    result = audit_project(project)
    try:
        written = generate_report(project, result, output, choice)
    except ViewerMissingError as exc:
        error_console.print(translator.text("error.viewer_missing"), style="red")
        raise typer.Exit(2) from exc
    console.print(translator.text("report.written", path=written), style="green")
    if open_report:
        webbrowser.open(written.as_uri())


@app.command("demo", cls=LocalizedCommand)
def demo_command(
    ctx: typer.Context,
    path: Annotated[Path, typer.Argument(help="Directory for the demo.")] = Path("rigorgraph-demo"),
    scenario: Annotated[
        str,
        typer.Option("--scenario", help="Demo scenario: math, benchmark, or invalid."),
    ] = "math",
    open_report: Annotated[bool, typer.Option("--open", help="Open the generated report.")] = False,
) -> None:
    if scenario not in {"math", "benchmark", "invalid"}:
        raise typer.BadParameter("scenario must be math, benchmark, or invalid")
    choice, translator = _language(ctx, path)
    if path.exists() and any(path.iterdir()):
        error_console.print(translator.text("error.file_exists", path=path), style="red")
        raise typer.Exit(1)
    create_demo(path.resolve(), scenario, choice.code)
    project = _load(path, translator)
    result = audit_project(project)
    report_path = path.resolve() / "rigorgraph-report.html"
    generate_report(project, result, report_path, choice)
    console.print(
        translator.text("demo.created", scenario=scenario, path=path.resolve()),
        style="green",
    )
    if open_report:
        webbrowser.open(report_path.as_uri())


if __name__ == "__main__":
    app()
