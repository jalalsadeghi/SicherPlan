"""Validate backup/restore state for key transactional and document tables."""

from __future__ import annotations

import argparse
import json

from sqlalchemy import create_engine, text

from app.config import settings


CHECKS = {
    "core_tenants": "SELECT count(*) FROM core.tenant",
    "user_accounts": "SELECT count(*) FROM iam.user_account",
    "documents": "SELECT count(*) FROM docs.document",
    "document_versions": "SELECT count(*) FROM docs.document_version",
    "watchbooks": "SELECT count(*) FROM field.watchbook",
    "time_events": "SELECT count(*) FROM field.time_event",
    "actual_records": "SELECT count(*) FROM finance.actual_record",
    "invoices": "SELECT count(*) FROM finance.customer_invoice",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate restored SicherPlan database state.")
    parser.add_argument("--database-url", default=settings.database_url)
    args = parser.parse_args()

    engine = create_engine(args.database_url, future=True)
    payload: dict[str, int] = {}
    with engine.connect() as connection:
        for key, statement in CHECKS.items():
            payload[key] = int(connection.execute(text(statement)).scalar_one())
        payload["document_links_without_document"] = int(
            connection.execute(
                text(
                    """
                    SELECT count(*)
                    FROM docs.document_link AS l
                    LEFT JOIN docs.document AS d
                      ON d.tenant_id = l.tenant_id
                     AND d.id = l.document_id
                    WHERE d.id IS NULL
                    """
                )
            ).scalar_one()
        )
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
