#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path

from common import LOCALES, load_contract, load_shared, placeholders, read_json, write_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--desktop", type=Path, required=True)
    parser.add_argument("--legacy-l10n", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repository = Path(__file__).resolve().parents[1]
    desktop = args.desktop.resolve()
    contract = load_contract(desktop / "Telegram/Resources/langs/lang.strings")
    zh_hans = read_json(
        desktop / "Telegram/Resources/langs/zh-hans.lproj/zh-hans.json"
    )
    if set(zh_hans) != set(contract):
        missing = sorted(set(contract) - set(zh_hans))
        extra = sorted(set(zh_hans) - set(contract))
        raise ValueError(f"zh-hans contract mismatch: missing={missing} extra={extra}")
    if not all(isinstance(value, str) for value in zh_hans.values()):
        raise ValueError("Every zh-hans value must be a string")

    write_json(repository / "source/en.json", contract)
    write_json(repository / "translations/zh-hans.json", zh_hans)

    if args.legacy_l10n is None:
        print(f"Synced {len(contract)} English and Simplified Chinese keys.")
        return 0

    legacy_root = args.legacy_l10n.resolve() / "values/langs"
    legacy_english = load_shared(legacy_root / "en/Shared.json")
    imported_total = 0
    for locale in LOCALES:
        if locale == "zh-hans":
            continue
        path = legacy_root / locale / "Shared.json"
        imported: dict[str, str] = {}
        if path.exists():
            translated = load_shared(path)
            for key, source_value in contract.items():
                value = translated.get(key)
                if (
                    value
                    and legacy_english.get(key) == source_value
                    and value != source_value
                    and "AyuGram" not in value
                    and placeholders(value) == placeholders(source_value)
                ):
                    imported[key] = value.replace("Ayugram", "AywGram")
        write_json(repository / f"translations/{locale}.json", imported)
        imported_total += len(imported)
        print(f"{locale}: imported {len(imported)} safe legacy translations")

    print(f"Imported {imported_total} safe legacy translations in total.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

