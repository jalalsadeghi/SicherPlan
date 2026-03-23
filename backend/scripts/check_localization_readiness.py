"""Run lightweight localization/readiness checks for critical Sprint 12 surfaces."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CHECKS = (
    (
        ROOT / "mobile/lib/l10n/app_localizations.dart",
        ("Wachbuch folgt in US-23", "Watchbook arrives in US-23", "Placeholder for released watchbook"),
    ),
)


def main() -> int:
    failures: list[str] = []
    for path, banned_tokens in CHECKS:
        text = path.read_text(encoding="utf-8")
        for token in banned_tokens:
            if token in text:
                failures.append(f"{path}: contains banned token {token!r}")
    if failures:
        print("Localization readiness check failed")
        for failure in failures:
            print(failure)
        return 1
    print("Localization readiness check passed")
    for path, _tokens in CHECKS:
        print(path.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
