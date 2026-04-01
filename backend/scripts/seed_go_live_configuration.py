"""Seed go-live lookup, document-type, and tenant-setting baselines."""

from __future__ import annotations

import argparse

from app.db.session import SessionLocal
from app.modules.core.config_seed import seed_default_tenant_settings
from app.modules.core.lookup_seed import seed_lookup_values
from app.modules.employees.catalog_seed import seed_baseline_employee_catalogs
from app.modules.platform_services.document_type_seed import seed_document_types


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tenant-id", help="Optional tenant UUID for tenant-scoped settings and tenant-extensible lookups.")
    parser.add_argument("--actor-user-id", help="Optional actor UUID for audit columns.")
    args = parser.parse_args()

    with SessionLocal() as session:
        lookup_result = seed_lookup_values(session, tenant_id=None, actor_user_id=args.actor_user_id)
        document_result = seed_document_types(session, actor_user_id=args.actor_user_id)
        tenant_result = {"inserted": 0, "updated": 0}
        hr_catalog_result = {
            "function_types_inserted": 0,
            "function_types_updated": 0,
            "qualification_types_inserted": 0,
            "qualification_types_updated": 0,
        }
        if args.tenant_id:
            seed_lookup_values(session, tenant_id=args.tenant_id, actor_user_id=args.actor_user_id)
            tenant_result = seed_default_tenant_settings(
                session,
                tenant_id=args.tenant_id,
                actor_user_id=args.actor_user_id,
            )
            hr_catalog_result = seed_baseline_employee_catalogs(
                session,
                tenant_id=args.tenant_id,
                actor_user_id=args.actor_user_id,
            )
        session.commit()

    print(
        "go-live seed applied:",
        {
            "system_lookup": lookup_result,
            "document_types": document_result,
            "tenant_settings": tenant_result,
            "employee_catalogs": hr_catalog_result,
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
