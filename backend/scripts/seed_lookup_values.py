"""Seed approved system lookup values and optional tenant-extensible defaults."""

from __future__ import annotations

import argparse

from app.db.session import SessionLocal
from app.modules.core.lookup_seed import seed_lookup_values


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tenant-id", help="Seed tenant-extensible lookup values for a specific tenant.")
    parser.add_argument("--actor-user-id", help="Optional actor UUID for audit columns.")
    args = parser.parse_args()

    with SessionLocal() as session:
        result = seed_lookup_values(
            session,
            tenant_id=args.tenant_id,
            actor_user_id=args.actor_user_id,
        )
        session.commit()

    scope = f"tenant {args.tenant_id}" if args.tenant_id else "system"
    print(f"seeded lookup values for {scope}: inserted={result['inserted']} updated={result['updated']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
