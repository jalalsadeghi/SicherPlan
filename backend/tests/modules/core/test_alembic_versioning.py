from __future__ import annotations

import unittest
from pathlib import Path

from app.db.alembic_versioning import (
    ALEMBIC_VERSION_NUM_LENGTH,
    build_version_table,
    max_revision_id_length,
)


class TestAlembicVersioning(unittest.TestCase):
    def test_version_table_uses_wide_enough_revision_column(self) -> None:
        table = build_version_table(
            version_table="alembic_version",
            version_table_schema=None,
            version_table_pk=True,
        )
        self.assertEqual(table.c.version_num.type.length, ALEMBIC_VERSION_NUM_LENGTH)

    def test_revision_column_is_longer_than_all_revision_ids(self) -> None:
        versions_dir = Path(__file__).resolve().parents[3] / "alembic" / "versions"
        self.assertLessEqual(max_revision_id_length(versions_dir), ALEMBIC_VERSION_NUM_LENGTH)
        self.assertGreater(max_revision_id_length(versions_dir), 32)


if __name__ == "__main__":
    unittest.main()
