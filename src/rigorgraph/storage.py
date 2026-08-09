from __future__ import annotations

import json
import os
import stat
import tempfile
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import TypeVar

import yaml
from pydantic import BaseModel, ValidationError

from rigorgraph.models import Claim, Evidence, ProjectConfig, ProjectData, Verification

T = TypeVar("T", bound=BaseModel)

STATE_DIR = ".rigorgraph"
CLAIMS_FILE = "claims.jsonl"
EVIDENCE_FILE = "evidence.jsonl"
VERIFICATIONS_FILE = "verifications.jsonl"


class ProjectLoadError(Exception):
    def __init__(self, code: str, path: Path, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.path = path
        self.detail = detail


class ProjectLockError(RuntimeError):
    pass


def _unsafe_state_path(path: Path, detail: str) -> ProjectLoadError:
    return ProjectLoadError("RG_PATH_UNSAFE", path, detail)


def is_link_or_reparse(path: Path) -> bool:
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return False
    return stat.S_ISLNK(metadata.st_mode) or bool(
        getattr(metadata, "st_file_attributes", 0)
        & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    )


def project_config_path(root: Path) -> Path:
    root = root.resolve()
    candidate = root / "rigorgraph.yaml"
    if is_link_or_reparse(candidate):
        raise _unsafe_state_path(
            candidate, "project config must not be a symbolic link or reparse point"
        )
    resolved = candidate.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise _unsafe_state_path(candidate, "project config escapes the project") from exc
    return candidate


def _state_directory(root: Path, *, create: bool = False) -> Path:
    root = root.resolve()
    state = root / STATE_DIR
    if is_link_or_reparse(state):
        raise _unsafe_state_path(
            state, "state directory must not be a symbolic link or reparse point"
        )
    if create:
        state.mkdir(parents=True, exist_ok=True)
    if state.exists() and not state.is_dir():
        raise _unsafe_state_path(state, "state path must be a directory")
    resolved = state.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise _unsafe_state_path(state, "state directory escapes the project") from exc
    return resolved


def _safe_state_file(path: Path) -> Path:
    if path.parent.name != STATE_DIR:
        return path
    root = path.parent.parent.resolve()
    state = _state_directory(root)
    candidate = state / path.name
    if is_link_or_reparse(candidate):
        raise _unsafe_state_path(
            candidate, "state file must not be a symbolic link or reparse point"
        )
    resolved = candidate.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise _unsafe_state_path(candidate, "state file escapes the project") from exc
    return candidate


def _load_jsonl(path: Path, model: type[T]) -> list[T]:
    path = _safe_state_file(path)
    if not path.exists():
        raise ProjectLoadError("RG_FILE_MISSING", path, "required state file is missing")
    records: list[T] = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            payload = json.loads(raw)
            records.append(model.model_validate(payload))
        except (json.JSONDecodeError, ValidationError) as exc:
            raise ProjectLoadError("RG_RECORD_INVALID", path, f"line {line_number}: {exc}") from exc
    return records


def load_project(root: Path) -> ProjectData:
    root = root.resolve()
    config_path = project_config_path(root)
    if not config_path.exists():
        raise ProjectLoadError("RG_CONFIG_MISSING", config_path, "rigorgraph.yaml is missing")
    try:
        config_payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        if not isinstance(config_payload, dict):
            raise ValueError("rigorgraph.yaml must contain a mapping")
        config = ProjectConfig.model_validate(config_payload)
    except (OSError, yaml.YAMLError, ValidationError, ValueError) as exc:
        raise ProjectLoadError("RG_CONFIG_INVALID", config_path, str(exc)) from exc
    state = _state_directory(root)
    return ProjectData(
        root=root,
        config=config,
        claims=_load_jsonl(state / CLAIMS_FILE, Claim),
        evidence=_load_jsonl(state / EVIDENCE_FILE, Evidence),
        verifications=_load_jsonl(state / VERIFICATIONS_FILE, Verification),
    )


def initialize_project(root: Path, name: str, language: str) -> list[Path]:
    root.mkdir(parents=True, exist_ok=True)
    root = root.resolve()
    state = _state_directory(root, create=True)
    files = {
        root / "rigorgraph.yaml": yaml.safe_dump(
            {"version": 1, "name": name, "language": language, "fail_on": "error"},
            allow_unicode=True,
            sort_keys=False,
        ),
        state / CLAIMS_FILE: "",
        state / EVIDENCE_FILE: "",
        state / VERIFICATIONS_FILE: "",
    }
    created: list[Path] = []
    for path, content in files.items():
        if not path.exists():
            path.write_text(content, encoding="utf-8", newline="\n")
            created.append(path)
    return created


def append_record(path: Path, record: BaseModel) -> None:
    path = _safe_state_file(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    content = existing + record.model_dump_json(exclude_none=True) + "\n"
    _atomic_write(path, content)


def write_records(path: Path, records: list[BaseModel]) -> None:
    path = _safe_state_file(path)
    content = "".join(record.model_dump_json(exclude_none=True) + "\n" for record in records)
    _atomic_write(path, content)


def _atomic_write(path: Path, content: str) -> None:
    path = _safe_state_file(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary_path = Path(temporary)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)


def atomic_write_bytes(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary_path = Path(temporary)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)


@contextmanager
def project_lock(root: Path, timeout: float = 5.0) -> Iterator[None]:
    try:
        state = _state_directory(root, create=True)
    except ProjectLoadError as exc:
        raise ProjectLockError(exc.detail) from exc
    lock_path = state / ".lock"
    if is_link_or_reparse(lock_path):
        raise ProjectLockError(
            f"lock file must not be a symbolic link or reparse point: {lock_path}"
        )
    deadline = time.monotonic() + timeout
    descriptor: int | None = None
    while descriptor is None:
        try:
            descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as exc:
            if time.monotonic() >= deadline:
                raise ProjectLockError(f"project is locked: {lock_path}") from exc
            time.sleep(0.05)
    try:
        os.write(descriptor, str(os.getpid()).encode("ascii"))
        os.close(descriptor)
        descriptor = None
        yield
    finally:
        if descriptor is not None:
            os.close(descriptor)
        lock_path.unlink(missing_ok=True)


def find_duplicate_id(records: list[BaseModel], record_id: str) -> bool:
    return any(getattr(record, "id", None) == record_id for record in records)
