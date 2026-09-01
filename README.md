# AywGram Language Packs

AI-maintained desktop language packs for AywGram. English and Simplified
Chinese are sourced from the AywGram Desktop repository; all other locales are
best-effort translations that fall back to the compiled English contract per
key.

The `main` branch is both the review branch and the jsDelivr publication
source. Model calls are intentionally kept out of CI: an agent updates
`translations/` in a pull request, while CI only performs deterministic
validation and verifies generated files.

## Maintenance

From an AywGram Desktop checkout where this repository is mounted at
`Telegram/Resources/ayw_langpacks`:

```powershell
py -3 scripts/sync_sources.py --desktop ../../..
py -3 scripts/build.py
py -3 scripts/audit.py
```

The generated endpoint is:

```text
https://cdn.jsdelivr.net/gh/AywGram/LanguagePacks@main/dist/manifest.json
```

Language JSON is a data file, not executable code, but it can still change the
meaning of security-sensitive UI. Runtime packs therefore carry a fingerprint
of the English source for every translated key.

