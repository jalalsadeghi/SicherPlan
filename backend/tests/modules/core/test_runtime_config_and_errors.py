from __future__ import annotations

import asyncio
import os
import tempfile
import unittest
from pathlib import Path

from fastapi import Request
from sqlalchemy.exc import OperationalError

from app.config import AppSettings, _parse_env_line, load_env_files
from app.errors import unhandled_exception_handler


class TestRuntimeConfig(unittest.TestCase):
    def test_parse_env_line_ignores_comments_and_strips_quotes(self) -> None:
        self.assertIsNone(_parse_env_line(""))
        self.assertIsNone(_parse_env_line("# comment"))
        self.assertEqual(_parse_env_line("SP_DB_PASSWORD='change-me'"), ("SP_DB_PASSWORD", "change-me"))
        self.assertEqual(_parse_env_line('export SP_ENV="development"'), ("SP_ENV", "development"))

    def test_load_env_files_sets_defaults_without_overwriting_existing_env(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"
            env_path.write_text(
                "SP_TEST_FILE_ONLY=from-file\nSP_TEST_KEEP_EXISTING=from-file\n",
                encoding="utf-8",
            )
            old_file_only = os.environ.get("SP_TEST_FILE_ONLY")
            old_keep_existing = os.environ.get("SP_TEST_KEEP_EXISTING")
            os.environ["SP_TEST_KEEP_EXISTING"] = "from-env"
            try:
                load_env_files([env_path], override=False)
                self.assertEqual(os.environ["SP_TEST_KEEP_EXISTING"], "from-env")
                self.assertEqual(os.environ["SP_TEST_FILE_ONLY"], "from-file")
            finally:
                if old_file_only is None:
                    os.environ.pop("SP_TEST_FILE_ONLY", None)
                else:
                    os.environ["SP_TEST_FILE_ONLY"] = old_file_only
                if old_keep_existing is None:
                    os.environ.pop("SP_TEST_KEEP_EXISTING", None)
                else:
                    os.environ["SP_TEST_KEEP_EXISTING"] = old_keep_existing

    def test_app_settings_default_database_url_matches_local_compose_defaults(self) -> None:
        self.assertEqual(
            AppSettings().database_url,
            "postgresql+psycopg://sicherplan:change-me@localhost:5432/sicherplan",
        )


class TestRuntimeErrors(unittest.TestCase):
    def test_operational_error_maps_to_service_unavailable(self) -> None:
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/api/auth/login",
            "headers": [],
        }
        request = Request(scope)
        error = OperationalError("SELECT 1", {}, Exception("no password supplied"))
        response = asyncio.run(unhandled_exception_handler(request, error))
        self.assertEqual(response.status_code, 503)
        self.assertIn("errors.platform.database_unavailable", response.body.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
