from __future__ import annotations

import json
import locale
import os
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Any

import yaml

from rigorgraph.storage import ProjectLoadError, project_config_path

SUPPORTED_LANGUAGES = ("en", "zh-TW", "zh-CN", "ja")

ALIASES = {
    "en": "en",
    "en-us": "en",
    "en-gb": "en",
    "english": "en",
    "zh": "zh-TW",
    "zh-tw": "zh-TW",
    "zh-hant": "zh-TW",
    "zh-hk": "zh-TW",
    "zh_cn": "zh-CN",
    "zh-cn": "zh-CN",
    "zh-hans": "zh-CN",
    "zh-hans-cn": "zh-CN",
    "zh-hans-sg": "zh-CN",
    "zh-hant-tw": "zh-TW",
    "zh-hant-hk": "zh-TW",
    "zh-sg": "zh-CN",
    "ja": "ja",
    "ja-jp": "ja",
    "japanese": "ja",
}


def normalize_language(value: str | None) -> tuple[str, bool]:
    if not value:
        return "en", True
    key = value.strip().replace("_", "-").lower()
    if key in ALIASES:
        return ALIASES[key], True
    parts = key.split("-")
    if parts[0] == "zh":
        if "hans" in parts or any(region in parts for region in ("cn", "sg")):
            return "zh-CN", True
        if "hant" in parts or any(region in parts for region in ("tw", "hk", "mo")):
            return "zh-TW", True
        return "zh-TW", True
    prefix = key.split("-", 1)[0]
    if prefix in ALIASES:
        return ALIASES[prefix], True
    return "en", False


def system_language() -> str | None:
    candidates = [os.getenv("LC_ALL"), os.getenv("LC_MESSAGES"), os.getenv("LANG")]
    try:
        candidates.append(locale.getlocale()[0])
    except (ValueError, TypeError):
        pass
    for candidate in candidates:
        if candidate:
            return candidate.split(".", 1)[0]
    return None


def read_config_language(root: Path) -> str | None:
    try:
        path = project_config_path(root)
    except ProjectLoadError:
        return None
    if not path.exists():
        return None
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return None
    if not isinstance(payload, dict):
        return None
    value = payload.get("language")
    return str(value) if value else None


@dataclass(frozen=True)
class LanguageChoice:
    code: str
    source: str
    supported: bool
    requested: str | None = None


def resolve_language(root: Path, explicit: str | None = None) -> LanguageChoice:
    if explicit:
        code, supported = normalize_language(explicit)
        return LanguageChoice(code, "cli", supported, explicit)
    configured = read_config_language(root)
    if configured:
        code, supported = normalize_language(configured)
        return LanguageChoice(code, "config", supported, configured)
    detected = system_language()
    code, supported = normalize_language(detected)
    return LanguageChoice(code, "system", supported, detected)


def load_catalog(language: str) -> dict[str, str]:
    code, _ = normalize_language(language)
    resource = files("rigorgraph").joinpath("locales", f"{code}.json")
    return json.loads(resource.read_text(encoding="utf-8"))


def load_all_catalogs() -> dict[str, dict[str, str]]:
    return {code: load_catalog(code) for code in SUPPORTED_LANGUAGES}


class Translator:
    def __init__(self, language: str) -> None:
        self.language, _ = normalize_language(language)
        self.catalog = load_catalog(self.language)
        self.english = load_catalog("en") if self.language != "en" else self.catalog

    def text(self, message_id: str, **values: Any) -> str:
        template = self.catalog.get(message_id, self.english.get(message_id, message_id))
        try:
            return template.format(**values)
        except (KeyError, ValueError):
            return template
