#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from common import (
    LOCALES,
    file_sha256,
    placeholders,
    read_json,
    source_fingerprint,
    write_json,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def build_into(repository: Path, output: Path) -> None:
    source_raw = read_json(repository / "source/en.json")
    if not all(isinstance(value, str) for value in source_raw.values()):
        raise ValueError("Every English source value must be a string")
    source = {key: value for key, value in source_raw.items() if isinstance(value, str)}
    source_bytes = json.dumps(
        source, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    source_sha256 = file_sha256(source_bytes)
    manifest: dict[str, object] = {
        "schema": 1,
        "revision": source_sha256[:16],
        "source_sha256": source_sha256,
        "locales": {},
    }

    for locale in LOCALES:
        translated_raw = read_json(repository / f"translations/{locale}.json")
        strings: dict[str, dict[str, str]] = {}
        for key, raw_value in translated_raw.items():
            if key not in source:
                raise ValueError(f"Unknown key {locale}:{key}")
            if not isinstance(raw_value, str) or not raw_value.strip():
                raise ValueError(f"Empty or non-string value {locale}:{key}")
            if placeholders(raw_value) != placeholders(source[key]):
                raise ValueError(f"Placeholder mismatch {locale}:{key}")
            strings[key] = {
                "source": source_fingerprint(source[key]),
                "value": raw_value,
            }
        pack = {
            "schema": 1,
            "locale": locale,
            "source_sha256": source_sha256,
            "strings": strings,
        }
        pack_path = output / f"locales/{locale}.json"
        write_json(pack_path, pack)
        pack_bytes = pack_path.read_bytes()
        locales = manifest["locales"]
        assert isinstance(locales, dict)
        locales[locale] = {
            "path": f"locales/{locale}.json",
            "sha256": file_sha256(pack_bytes),
            "size": len(pack_bytes),
        }

    write_json(output / "manifest.json", manifest)
    qrc_lines = ["<RCC>", '  <qresource prefix="/gui/ayw_langpacks">']
    qrc_lines.append('    <file alias="manifest.json">manifest.json</file>')
    for locale in LOCALES:
        qrc_lines.append(
            f'    <file alias="locales/{locale}.json">locales/{locale}.json</file>'
        )
    qrc_lines.extend(["  </qresource>", "</RCC>", ""])
    (output / "ayw_langpacks.qrc").write_text(
        "\n".join(qrc_lines), encoding="utf-8", newline="\n"
    )


def same_tree(left: Path, right: Path) -> bool:
    left_files = sorted(path.relative_to(left) for path in left.rglob("*") if path.is_file())
    right_files = sorted(path.relative_to(right) for path in right.rglob("*") if path.is_file())
    return left_files == right_files and all(
        (left / path).read_bytes() == (right / path).read_bytes()
        for path in left_files
    )


def main() -> int:
    args = parse_args()
    repository = Path(__file__).resolve().parents[1]
    dist = repository / "dist"
    if args.check:
        with tempfile.TemporaryDirectory() as temporary:
            generated = Path(temporary)
            build_into(repository, generated)
            if not dist.exists() or not same_tree(dist, generated):
                print("Generated language artifacts are stale. Run scripts/build.py.")
                return 1
        print("Generated language artifacts are current.")
        return 0
    build_into(repository, dist)
    print(f"Generated {len(LOCALES)} language packs in {dist}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

