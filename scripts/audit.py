#!/usr/bin/env python3

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from common import LOCALES, placeholders, read_json


def main() -> int:
    repository = Path(__file__).resolve().parents[1]
    source = read_json(repository / "source/en.json")
    errors: list[str] = []
    for locale in LOCALES:
        translated = read_json(repository / f"translations/{locale}.json")
        exact_english = 0
        for key, raw_value in translated.items():
            if key not in source:
                errors.append(f"unknown key {locale}:{key}")
                continue
            if not isinstance(raw_value, str) or not raw_value.strip():
                errors.append(f"empty value {locale}:{key}")
                continue
            source_value = source[key]
            if not isinstance(source_value, str):
                errors.append(f"non-string source {key}")
                continue
            if placeholders(raw_value) != placeholders(source_value):
                errors.append(f"placeholder mismatch {locale}:{key}")
            if raw_value == source_value:
                exact_english += 1
            if "AyuGram" in raw_value or "Ayugram" in raw_value:
                errors.append(f"stale brand {locale}:{key}")
        print(
            f"{locale}: translated={len(translated)} "
            f"missing={len(source) - len(translated)} "
            f"exact-english={exact_english}"
        )

    result = subprocess.run(
        [sys.executable, str(repository / "scripts/build.py"), "--check"],
        check=False,
    )
    if result.returncode:
        errors.append("generated dist tree is stale")
    if errors:
        print("Errors:")
        for error in errors:
            print(f"  {error}")
        return 1
    print(f"Validated {len(source)} source keys across {len(LOCALES)} locales.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

