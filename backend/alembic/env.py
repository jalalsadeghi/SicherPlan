from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.config import settings
from app.db import Base
from app.db.alembic_versioning import configure_alembic_version_table_impl
from app.modules.core import models as core_models  # noqa: F401
from app.modules.customers import models as customer_models  # noqa: F401
from app.modules.employees import models as employee_models  # noqa: F401
from app.modules.iam import models as iam_models  # noqa: F401
from app.modules.iam import audit_models as audit_models  # noqa: F401
from app.modules.platform_services import comm_models as comm_models  # noqa: F401
from app.modules.platform_services import docs_models as docs_models  # noqa: F401
from app.modules.platform_services import info_models as info_models  # noqa: F401
from app.modules.platform_services import integration_models as integration_models  # noqa: F401
from app.modules.recruiting import models as recruiting_models  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", settings.alembic_database_url or settings.database_url)

configure_alembic_version_table_impl()

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
