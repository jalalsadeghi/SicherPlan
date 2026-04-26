from __future__ import annotations

import asyncio
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import Request
from sqlalchemy.exc import OperationalError

from app.config import AppSettings, _parse_env_line, load_env_files
from app.errors import unhandled_exception_handler


class TestRuntimeConfig(unittest.TestCase):
    def test_ai_settings_defaults_are_safe(self) -> None:
        with patch.dict(os.environ, {}, clear=False):
            for key in (
                "SP_AI_ENABLED",
                "SP_AI_PROVIDER",
                "SP_AI_ALLOW_MOCK_PROVIDER",
                "SP_OPENAI_API_KEY",
                "SP_AI_RESPONSE_MODEL",
                "SP_AI_EMBEDDING_MODEL",
                "SP_AI_RETRIEVAL_MODE",
                "SP_AI_EMBEDDINGS_ENABLED",
                "SP_AI_RETRIEVAL_DEBUG",
                "SP_AI_STORE_RESPONSES",
                "SP_AI_MAX_TOOL_CALLS",
                "SP_AI_MAX_CONTEXT_CHUNKS",
                "SP_AI_MAX_INPUT_CHARS",
                "SP_AI_TIMEOUT_SECONDS",
                "SP_AI_RATE_LIMIT_PER_USER_PER_MINUTE",
                "SP_AI_RATE_LIMIT_PER_TENANT_PER_MINUTE",
                "SP_AI_REDACTION_ENABLED",
                "SP_AI_AUDIT_ENABLED",
            ):
                os.environ.pop(key, None)
            settings = AppSettings()

        self.assertFalse(settings.ai_enabled)
        self.assertEqual(settings.ai_provider, "mock")
        self.assertFalse(settings.ai_allow_mock_provider)
        self.assertFalse(settings.ai_mock_provider_allowed)
        self.assertFalse(settings.ai_openai_configured)
        self.assertEqual(settings.ai_response_model, "gpt-5.5-or-configured-model")
        self.assertEqual(settings.ai_embedding_model, "text-embedding-3-small")
        self.assertEqual(settings.ai_retrieval_mode, "lexical")
        self.assertEqual(settings.ai_effective_retrieval_mode, "lexical")
        self.assertFalse(settings.ai_embeddings_enabled)
        self.assertFalse(settings.ai_retrieval_debug)
        self.assertFalse(settings.ai_store_responses)
        self.assertEqual(settings.ai_max_tool_calls, 8)
        self.assertEqual(settings.ai_max_context_chunks, 8)
        self.assertEqual(settings.ai_max_input_chars, 12000)
        self.assertEqual(settings.ai_timeout_seconds, 45)
        self.assertEqual(settings.ai_rate_limit_per_user_per_minute, 10)
        self.assertEqual(settings.ai_rate_limit_per_tenant_per_minute, 100)
        self.assertTrue(settings.ai_redaction_enabled)
        self.assertTrue(settings.ai_audit_enabled)

    def test_ai_disabled_does_not_require_openai_key(self) -> None:
        with patch.dict(
            os.environ,
            {
                "SP_AI_ENABLED": "false",
                "SP_AI_PROVIDER": "openai",
                "SP_OPENAI_API_KEY": "",
            },
            clear=False,
        ):
            settings = AppSettings()

        self.assertFalse(settings.ai_enabled)
        self.assertEqual(settings.ai_provider, "openai")

    def test_ai_mock_provider_does_not_require_openai_key(self) -> None:
        with patch.dict(
            os.environ,
            {
                "SP_AI_ENABLED": "true",
                "SP_AI_PROVIDER": "mock",
                "SP_OPENAI_API_KEY": "",
            },
            clear=False,
        ):
            settings = AppSettings()

        self.assertTrue(settings.ai_enabled)
        self.assertEqual(settings.ai_provider, "mock")
        self.assertFalse(settings.ai_mock_provider_allowed)

    def test_ai_openai_provider_accepts_api_key_when_enabled(self) -> None:
        with patch.dict(
            os.environ,
            {
                "SP_AI_ENABLED": "true",
                "SP_AI_PROVIDER": "openai",
                "SP_OPENAI_API_KEY": "test-openai-key",
                "SP_AI_RESPONSE_MODEL": "gpt-5.5-mini",
            },
            clear=False,
        ):
            settings = AppSettings()

        self.assertTrue(settings.ai_enabled)
        self.assertEqual(settings.ai_provider, "openai")
        self.assertTrue(settings.ai_openai_configured)

    def test_ai_openai_provider_requires_key_when_enabled(self) -> None:
        with patch.dict(
            os.environ,
            {
                "SP_AI_ENABLED": "true",
                "SP_AI_PROVIDER": "openai",
                "SP_OPENAI_API_KEY": "",
            },
            clear=False,
        ):
            with self.assertRaisesRegex(
                ValueError,
                "SP_OPENAI_API_KEY is required when SP_AI_ENABLED=true and SP_AI_PROVIDER=openai.",
            ):
                AppSettings()

    def test_ai_invalid_provider_is_rejected(self) -> None:
        with patch.dict(
            os.environ,
            {
                "SP_AI_ENABLED": "true",
                "SP_AI_PROVIDER": "unknown",
            },
            clear=False,
        ):
            with self.assertRaisesRegex(
                ValueError,
                "Invalid SP_AI_PROVIDER value. Expected one of: mock, openai.",
            ):
                AppSettings()

    def test_ai_invalid_retrieval_mode_is_rejected(self) -> None:
        with patch.dict(
            os.environ,
            {
                "SP_AI_RETRIEVAL_MODE": "invalid",
            },
            clear=False,
        ):
            with self.assertRaisesRegex(
                ValueError,
                "Invalid SP_AI_RETRIEVAL_MODE value. Expected one of: lexical, semantic, hybrid.",
            ):
                AppSettings()

    def test_ai_effective_retrieval_mode_falls_back_to_lexical_without_embeddings(self) -> None:
        with patch.dict(
            os.environ,
            {
                "SP_AI_RETRIEVAL_MODE": "hybrid",
                "SP_AI_EMBEDDINGS_ENABLED": "false",
            },
            clear=False,
        ):
            settings = AppSettings()

        self.assertEqual(settings.ai_retrieval_mode, "hybrid")
        self.assertEqual(settings.ai_effective_retrieval_mode, "lexical")

    def test_ai_openai_provider_rejects_placeholder_model_when_enabled(self) -> None:
        with patch.dict(
            os.environ,
            {
                "SP_AI_ENABLED": "true",
                "SP_AI_PROVIDER": "openai",
                "SP_OPENAI_API_KEY": "test-openai-key",
                "SP_AI_RESPONSE_MODEL": "gpt-5.5-or-configured-model",
            },
            clear=False,
        ):
            with self.assertRaisesRegex(
                ValueError,
                "SP_AI_RESPONSE_MODEL must be set to a real model name when SP_AI_ENABLED=true and SP_AI_PROVIDER=openai.",
            ):
                AppSettings()

    def test_ai_mock_provider_allowed_in_ci_and_explicit_local_override(self) -> None:
        ci_settings = object.__new__(AppSettings)
        object.__setattr__(ci_settings, "env", "ci")
        object.__setattr__(ci_settings, "ai_allow_mock_provider", False)
        self.assertTrue(ci_settings.ai_mock_provider_allowed)

        local_settings = object.__new__(AppSettings)
        object.__setattr__(local_settings, "env", "development")
        object.__setattr__(local_settings, "ai_allow_mock_provider", True)
        self.assertTrue(local_settings.ai_mock_provider_allowed)

    def test_ai_openai_api_key_is_not_in_settings_repr(self) -> None:
        with patch.dict(
            os.environ,
            {
                "SP_AI_ENABLED": "true",
                "SP_AI_PROVIDER": "openai",
                "SP_OPENAI_API_KEY": "super-secret-key",
                "SP_AI_RESPONSE_MODEL": "gpt-5.5-mini",
            },
            clear=False,
        ):
            settings = AppSettings()

        self.assertNotIn("super-secret-key", repr(settings))

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
