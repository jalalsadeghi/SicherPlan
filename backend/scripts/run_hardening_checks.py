"""Sprint 11 hardening check manifest for local and CI-friendly execution."""

from __future__ import annotations

import json

from app.hardening_manifest import CHECKS


def main() -> None:
    print(json.dumps(CHECKS, indent=2))


if __name__ == "__main__":
    main()
