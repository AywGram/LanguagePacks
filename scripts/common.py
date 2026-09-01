#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


LOCALES = (
    "ar", "be", "de", "el", "eo", "es", "fa", "fi", "fr", "he",
    "it", "ja", "lv", "os", "pl", "pt", "ro", "ru", "tr", "uk",
    "vi", "zh", "zh-hans", "zh-hant",
)
PLURAL_SUFFIXES = ("zero", "one", "two", "few", "many", "other")
STRING_PATTERN = re.compile(
    r'^"ayu_([^"\n]+)"\s*=\s*"((?:\\.|[^"\\])*)";$',
    re.MULTILINE,
)
PLACEHOLDER_PATTERN = re.compile(r"\{[a-zA-Z][a-zA-Z0-9_]*\}")


def read_json(path: Path) -> dict[str, object]:
    with path.open(encoding="utf-8") as stream:
        result = json.load(stream)
    if not isinstance(result, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return result


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def load_contract(path: Path) -> dict[str, str]:
    content = path.read_text(encoding="utf-8")
    return {
        key: json.loads(f'"{encoded}"')
        for key, encoded in STRING_PATTERN.findall(content)
    }


def desktop_key(raw_key: str) -> str | None:
    if raw_key.endswith("_Android"):
        return None
    key = raw_key
    for suffix in PLURAL_SUFFIXES:
        marker = f"_{suffix}"
        if key.endswith(marker):
            key = f"{key[:-len(marker)]}#{suffix}"
            break
    if key.endswith("_PC"):
        key = key[:-3]
    return key


def desktop_value(value: str) -> str:
    value = value.replace("&amp;", "&")
    if "%1$d" in value and "%2$d" not in value:
        return value.replace("%1$d", "{count}")
    if "%1$d" in value and "%2$d" in value:
        return value.replace("%1$d", "{count1}").replace("%2$d", "{count2}")
    if "%1$s" in value and "%2$s" not in value:
        return value.replace("%1$s", "{item}")
    if "%1$s" in value and "%2$s" in value:
        return value.replace("%1$s", "{item1}").replace("%2$s", "{item2}")
    return value


def load_shared(path: Path) -> dict[str, str]:
    raw = read_json(path)
    result: dict[str, str] = {}
    for raw_key, raw_value in raw.items():
        if not isinstance(raw_value, str):
            continue
        key = desktop_key(raw_key)
        if key is not None:
            result[key] = desktop_value(raw_value)
    return result


def placeholders(value: str) -> set[str]:
    return set(PLACEHOLDER_PATTERN.findall(value))


def source_fingerprint(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def file_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

