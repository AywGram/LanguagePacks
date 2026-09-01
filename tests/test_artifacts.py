from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY / "scripts"))

from build import build_into  # noqa: E402
from common import LOCALES, source_fingerprint  # noqa: E402


class GeneratedArtifactsTest(unittest.TestCase):
    def test_manifest_and_per_key_fingerprints(self) -> None:
        source = json.loads((REPOSITORY / "source/en.json").read_text(encoding="utf-8"))
        manifest = json.loads((REPOSITORY / "dist/manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(set(manifest["locales"]), set(LOCALES))
        for locale, metadata in manifest["locales"].items():
            raw = (REPOSITORY / "dist" / metadata["path"]).read_bytes()
            self.assertEqual(len(raw), metadata["size"])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), metadata["sha256"])
            pack = json.loads(raw)
            self.assertEqual(pack["locale"], locale)
            for key, entry in pack["strings"].items():
                self.assertIn(key, source)
                self.assertEqual(entry["source"], source_fingerprint(source[key]))

    def test_missing_translation_is_a_valid_english_fallback(self) -> None:
        pack = json.loads((REPOSITORY / "dist/locales/ja.json").read_text(encoding="utf-8"))
        self.assertEqual(pack["strings"], {})

    def test_placeholder_mismatch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            checkout = Path(temporary) / "repository"
            checkout.mkdir()
            (checkout / "source").mkdir()
            (checkout / "translations").mkdir()
            source = {"Example": "Hello {item}"}
            (checkout / "source/en.json").write_text(json.dumps(source), encoding="utf-8")
            for locale in LOCALES:
                value = {"Example": "Hello {wrong}"} if locale == "ar" else {}
                (checkout / f"translations/{locale}.json").write_text(
                    json.dumps(value), encoding="utf-8"
                )
            with self.assertRaisesRegex(ValueError, "Placeholder mismatch"):
                build_into(checkout, Path(temporary) / "dist")

    def test_corrupt_translation_json_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            checkout = Path(temporary) / "repository"
            checkout.mkdir()
            (checkout / "source").mkdir()
            (checkout / "translations").mkdir()
            (checkout / "source/en.json").write_text("{}", encoding="utf-8")
            for locale in LOCALES:
                (checkout / f"translations/{locale}.json").write_text(
                    "{" if locale == "ar" else "{}", encoding="utf-8"
                )
            with self.assertRaises(json.JSONDecodeError):
                build_into(checkout, Path(temporary) / "dist")


if __name__ == "__main__":
    unittest.main()
