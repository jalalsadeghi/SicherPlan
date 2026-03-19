"""Alembic version-table helpers for longer revision identifiers."""

from __future__ import annotations

from pathlib import Path
import re

from alembic.ddl.impl import DefaultImpl
from sqlalchemy import Column, MetaData, PrimaryKeyConstraint, String, Table


ALEMBIC_VERSION_NUM_LENGTH = 255
_PATCH_FLAG = "_sicherplan_version_table_patched"


def build_version_table(
    *,
    version_table: str,
    version_table_schema: str | None,
    version_table_pk: bool,
) -> Table:
    table = Table(
        version_table,
        MetaData(),
        Column("version_num", String(ALEMBIC_VERSION_NUM_LENGTH), nullable=False),
        schema=version_table_schema,
    )
    if version_table_pk:
        table.append_constraint(
            PrimaryKeyConstraint("version_num", name=f"{version_table}_pkc")
        )
    return table


def configure_alembic_version_table_impl() -> None:
    if getattr(DefaultImpl, _PATCH_FLAG, False):
        return

    def _version_table_impl(
        self,
        *,
        version_table: str,
        version_table_schema: str | None,
        version_table_pk: bool,
        **_: object,
    ) -> Table:
        return build_version_table(
            version_table=version_table,
            version_table_schema=version_table_schema,
            version_table_pk=version_table_pk,
        )

    DefaultImpl.version_table_impl = _version_table_impl  # type: ignore[assignment]
    setattr(DefaultImpl, _PATCH_FLAG, True)


def max_revision_id_length(versions_dir: Path) -> int:
    pattern = re.compile(r'^revision\s*=\s*["\']([^"\']+)["\']', re.MULTILINE)
    max_length = 0
    for path in versions_dir.glob("*.py"):
        match = pattern.search(path.read_text(encoding="utf-8"))
        if match is None:
            continue
        max_length = max(max_length, len(match.group(1)))
    return max_length
