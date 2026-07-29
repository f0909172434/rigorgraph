from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXED_TIME = (2020, 1, 1, 0, 0, 0)


def _entry(archive: zipfile.ZipFile, name: str, content: bytes) -> None:
    info = zipfile.ZipInfo(name, FIXED_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    archive.writestr(info, content)


def build(output: Path | None = None) -> Path:
    manifest_path = ROOT / ".codex-plugin" / "plugin.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    version = manifest["version"]
    marketplace = {
        "name": "rigorgraph-release",
        "interface": {"displayName": "RigorGraph Releases"},
        "plugins": [
            {
                "name": "rigorgraph",
                "source": {"source": "local", "path": "./plugins/rigorgraph"},
                "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                "category": "Productivity",
            }
        ],
    }
    output = output or ROOT / "dist" / f"rigorgraph-codex-plugin-{version}.zip"
    output.parent.mkdir(parents=True, exist_ok=True)
    files: dict[str, bytes] = {
        ".agents/plugins/marketplace.json": (
            json.dumps(marketplace, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        ).encode(),
        "plugins/rigorgraph/.codex-plugin/plugin.json": manifest_path.read_bytes(),
        "plugins/rigorgraph/README.md": (ROOT / "README.md").read_bytes(),
        "plugins/rigorgraph/LICENSE": (ROOT / "LICENSE").read_bytes(),
        "plugins/rigorgraph/docs/CODEX_PLUGIN.md": (
            ROOT / "docs" / "CODEX_PLUGIN.md"
        ).read_bytes(),
    }
    for path in sorted((ROOT / "skills").rglob("*")):
        if path.is_file():
            relative = path.relative_to(ROOT).as_posix()
            files[f"plugins/rigorgraph/{relative}"] = path.read_bytes()
    with zipfile.ZipFile(output, "w") as archive:
        for name in sorted(files):
            _entry(archive, name, files[name])
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output = build(args.output)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
