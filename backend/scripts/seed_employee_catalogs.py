"""Seed sample HR function and qualification catalogs for a tenant in development/test."""

from __future__ import annotations

import argparse

from app.config import settings
from app.db.session import SessionLocal
from app.modules.employees.catalog_seed import seed_sample_employee_catalogs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tenant-id", required=True, help="Tenant UUID that should receive sample HR catalog rows.")
    parser.add_argument("--actor-user-id", help="Optional actor UUID for audit columns.")
    args = parser.parse_args()

    if settings.env not in {"development", "test"}:
        raise SystemExit(
            "Sample HR catalog seeding is restricted to development/test environments. "
            f"Current SP_ENV={settings.env!r}."
        )

    with SessionLocal() as session:
        result = seed_sample_employee_catalogs(
            session,
            tenant_id=args.tenant_id,
            actor_user_id=args.actor_user_id,
        )
        session.commit()

    print("employee catalog seed applied:", result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
