"""Seed the baseline IAM roles and permissions."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.config import settings
from app.modules.iam.seed_permissions import seed_iam_catalog


def main() -> None:
    engine = create_engine(settings.database_url)
    with Session(engine) as session:
        summary = seed_iam_catalog(session)
        session.commit()

    print(summary)


if __name__ == "__main__":
    main()
