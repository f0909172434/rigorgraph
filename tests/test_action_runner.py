from __future__ import annotations

from io import StringIO
from pathlib import Path

import pytest

from scripts.action_runner import _resolve_report_path, _write_github_output


@pytest.mark.parametrize(
    "value",
    ["", "../outside.html", "/tmp/outside.html", "report.html\nsecond=value", "bad\rname"],
)
def test_report_path_rejects_unsafe_values(tmp_path: Path, value: str) -> None:
    with pytest.raises(ValueError):
        _resolve_report_path(tmp_path, value)


def test_report_path_rejects_symlink_destination(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside-report.html"
    outside.write_text("sentinel", encoding="utf-8")
    destination = tmp_path / "report.html"
    try:
        destination.symlink_to(outside)
    except OSError as exc:
        pytest.skip(f"symbolic links are unavailable: {exc}")

    with pytest.raises(ValueError, match="symbolic link"):
        _resolve_report_path(tmp_path, "report.html")
    assert outside.read_text(encoding="utf-8") == "sentinel"


def test_github_output_uses_multiline_protocol() -> None:
    output = StringIO()
    _write_github_output(output, "report", "safe/report.html")
    lines = output.getvalue().splitlines()
    delimiter = lines[0].removeprefix("report<<")
    assert lines == [f"report<<{delimiter}", "safe/report.html", delimiter]


def test_action_does_not_interpolate_inputs_in_shell_source() -> None:
    action = Path("action.yml").read_text(encoding="utf-8")
    run_block = action.split("run: >-", maxsplit=1)[1].split("- name:", maxsplit=1)[0]
    assert "${{ inputs." not in run_block
