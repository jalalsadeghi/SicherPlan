"""Seed go-live lookup, document-type, and tenant-setting baselines."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from sqlalchemy import select

from app.db.session import SessionLocal
from app.modules.core.config_seed import seed_default_tenant_settings
from app.modules.core.models import Tenant
from app.modules.core.lookup_seed import seed_lookup_values
from app.modules.employees.catalog_seed import seed_baseline_employee_catalogs
from app.modules.platform_services.document_type_seed import seed_document_types

ALL_TENANTS_CONFIRMATION = "RUN_ALL_TENANTS"


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tenant-id", help="Optional tenant UUID for tenant-scoped settings and HR catalog backfill.")
    parser.add_argument(
        "--all-tenants",
        action="store_true",
        help="Apply tenant-scoped baseline seeding to all active tenants. Requires --confirm-all-tenants.",
    )
    parser.add_argument(
        "--confirm-all-tenants",
        help=f"Required with --all-tenants. Must equal {ALL_TENANTS_CONFIRMATION!r}.",
    )
    parser.add_argument("--actor-user-id", help="Optional actor UUID for audit columns.")
    args = parser.parse_args(argv)
    _validate_args(args, parser)
    return args


def _validate_args(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    if args.tenant_id and args.all_tenants:
        parser.error("--tenant-id and --all-tenants cannot be used together.")
    if args.all_tenants and args.confirm_all_tenants != ALL_TENANTS_CONFIRMATION:
        parser.error(
            f"--all-tenants requires --confirm-all-tenants {ALL_TENANTS_CONFIRMATION!r}."
        )
    if args.confirm_all_tenants and not args.all_tenants:
        parser.error("--confirm-all-tenants can only be used together with --all-tenants.")


def _list_target_tenant_ids(session, args: argparse.Namespace) -> list[str]:  # noqa: ANN001
    if args.tenant_id:
        return [args.tenant_id]
    if not args.all_tenants:
        return []
    return list(
        session.scalars(
            select(Tenant.id).where(
                Tenant.archived_at.is_(None),
                Tenant.status == "active",
            )
        )
    )


def main() -> int:
    args = _parse_args()

    with SessionLocal() as session:
        lookup_result = seed_lookup_values(session, tenant_id=None, actor_user_id=args.actor_user_id)
        document_result = seed_document_types(session, actor_user_id=args.actor_user_id)
        tenant_results: dict[str, dict[str, object]] = {}
        for tenant_id in _list_target_tenant_ids(session, args):
            seed_lookup_values(session, tenant_id=tenant_id, actor_user_id=args.actor_user_id)
            tenant_setting_result = seed_default_tenant_settings(
                session,
                tenant_id=tenant_id,
                actor_user_id=args.actor_user_id,
            )
            hr_catalog_result = seed_baseline_employee_catalogs(
                session,
                tenant_id=tenant_id,
                actor_user_id=args.actor_user_id,
            )
            tenant_results[tenant_id] = {
                "tenant_settings": tenant_setting_result,
                "employee_catalogs": hr_catalog_result,
            }
        session.commit()

    print(
        "go-live seed applied:",
        {
            "system_lookup": lookup_result,
            "document_types": document_result,
            "tenant_scope": {
                "mode": "all-tenants" if args.all_tenants else ("single-tenant" if args.tenant_id else "system-only"),
                "tenant_count": len(tenant_results),
                "tenant_ids": list(tenant_results.keys()),
            },
            "tenants": tenant_results,
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
