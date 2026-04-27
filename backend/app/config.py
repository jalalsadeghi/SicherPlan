"""Environment-backed backend settings for development and staging."""

from __future__ import annotations

from dataclasses import dataclass, field
from os import environ, getenv
from pathlib import Path


def _backend_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _parse_env_line(line: str) -> tuple[str, str] | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None
    if stripped.startswith("export "):
        stripped = stripped[7:].strip()
    if "=" not in stripped:
        return None
    key, raw_value = stripped.split("=", 1)
    key = key.strip()
    if not key:
        return None
    return key, _strip_quotes(raw_value.strip())


def _candidate_env_files() -> list[Path]:
    override = getenv("SP_ENV_FILE")
    if override:
        env_path = Path(override)
        if not env_path.is_absolute():
            env_path = _backend_root() / env_path
        return [env_path]
    root = _backend_root()
    return [root / ".env", root / ".env.local"]


def load_env_files(
    paths: list[Path] | tuple[Path, ...] | None = None,
    *,
    override: bool = False,
) -> tuple[Path, ...]:
    loaded: list[Path] = []
    for path in paths or _candidate_env_files():
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            parsed = _parse_env_line(line)
            if parsed is None:
                continue
            key, value = parsed
            if override:
                environ[key] = value
            else:
                environ.setdefault(key, value)
        loaded.append(path)
    return tuple(loaded)


LOADED_ENV_FILES = load_env_files()


def _get_bool(name: str, default: bool) -> bool:
    value = getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_int(name: str, default: int) -> int:
    value = getenv(name)
    if value is None or value.strip() == "":
        return default
    return int(value)


def _get_str(name: str, default: str = "") -> str:
    return getenv(name, default)


@dataclass(frozen=True)
class AppSettings:
    env: str = _get_str("SP_ENV", "development")
    app_name: str = _get_str("SP_APP_NAME", "SicherPlan API")
    app_version: str = _get_str("SP_APP_VERSION", "0.1.0")
    api_host: str = _get_str("SP_API_HOST", "0.0.0.0")
    api_port: int = _get_int("SP_API_PORT", 8000)
    api_base_url: str = _get_str("SP_API_BASE_URL", "http://localhost:8000")
    allowed_origins: str = _get_str("SP_ALLOWED_ORIGINS", "http://localhost:5173")
    log_level: str = _get_str("SP_LOG_LEVEL", "INFO")

    db_host: str = _get_str("SP_DB_HOST", "localhost")
    db_port: int = _get_int("SP_DB_PORT", 5432)
    db_name: str = _get_str("SP_DB_NAME", "sicherplan")
    db_user: str = _get_str("SP_DB_USER", "sicherplan")
    db_password: str = _get_str("SP_DB_PASSWORD", "change-me")
    db_echo: bool = _get_bool("SP_DB_ECHO", False)
    db_connect_timeout_seconds: int = _get_int("SP_DB_CONNECT_TIMEOUT_SECONDS", 5)
    database_url_override: str = _get_str("SP_DATABASE_URL")
    alembic_database_url: str = _get_str("SP_ALEMBIC_DATABASE_URL")
    db_rls_enabled: bool = _get_bool("SP_DB_RLS_ENABLED", False)
    db_rls_default_mode: str = _get_str("SP_DB_RLS_DEFAULT_MODE", "off")

    object_storage_endpoint: str = _get_str("SP_OBJECT_STORAGE_ENDPOINT")
    object_storage_backend: str = _get_str("SP_OBJECT_STORAGE_BACKEND", "filesystem")
    object_storage_region: str = _get_str("SP_OBJECT_STORAGE_REGION", "eu-central-1")
    object_storage_bucket: str = _get_str("SP_OBJECT_STORAGE_BUCKET", "sicherplan-dev")
    object_storage_access_key: str = _get_str("SP_OBJECT_STORAGE_ACCESS_KEY")
    object_storage_secret_key: str = _get_str("SP_OBJECT_STORAGE_SECRET_KEY")
    object_storage_use_ssl: bool = _get_bool("SP_OBJECT_STORAGE_USE_SSL", False)
    object_storage_filesystem_root: str = _get_str(
        "SP_OBJECT_STORAGE_FILESYSTEM_ROOT",
        "/tmp/sicherplan-object-storage",
    )

    auth_session_secret: str = _get_str("SP_AUTH_SESSION_SECRET", "change-me")
    auth_access_token_ttl_minutes: int = _get_int("SP_AUTH_ACCESS_TOKEN_TTL_MINUTES", 15)
    auth_refresh_token_ttl_minutes: int = _get_int("SP_AUTH_REFRESH_TOKEN_TTL_MINUTES", 10080)
    auth_remember_me_refresh_token_ttl_minutes: int = _get_int(
        "SP_AUTH_REMEMBER_ME_REFRESH_TOKEN_TTL_MINUTES",
        20160,
    )
    auth_password_reset_token_ttl_minutes: int = _get_int(
        "SP_AUTH_PASSWORD_RESET_TOKEN_TTL_MINUTES",
        30,
    )
    auth_login_max_attempts: int = _get_int("SP_AUTH_LOGIN_MAX_ATTEMPTS", 5)
    auth_lockout_minutes: int = _get_int("SP_AUTH_LOCKOUT_MINUTES", 15)
    auth_external_idp_enabled: bool = _get_bool("SP_AUTH_EXTERNAL_IDP_ENABLED", False)
    auth_external_idp_discovery_url: str = _get_str("SP_AUTH_EXTERNAL_IDP_DISCOVERY_URL")
    auth_external_idp_client_id: str = _get_str("SP_AUTH_EXTERNAL_IDP_CLIENT_ID")
    auth_external_idp_client_secret: str = _get_str("SP_AUTH_EXTERNAL_IDP_CLIENT_SECRET")

    message_email_enabled: bool = _get_bool("SP_MESSAGE_EMAIL_ENABLED", False)
    message_sms_enabled: bool = _get_bool("SP_MESSAGE_SMS_ENABLED", False)
    message_push_enabled: bool = _get_bool("SP_MESSAGE_PUSH_ENABLED", False)
    message_email_from: str = _get_str("SP_MESSAGE_EMAIL_FROM", "no-reply@example.invalid")

    integration_outbox_enabled: bool = _get_bool("SP_INTEGRATION_OUTBOX_ENABLED", True)
    integration_secret_key: str = _get_str(
        "SP_INTEGRATION_SECRET_KEY",
        _get_str("SP_AUTH_SESSION_SECRET", "change-me"),
    )
    integration_outbox_batch_size: int = _get_int("SP_INTEGRATION_OUTBOX_BATCH_SIZE", 25)
    integration_outbox_retry_delay_seconds: int = _get_int("SP_INTEGRATION_OUTBOX_RETRY_DELAY_SECONDS", 60)
    integration_outbox_max_attempts: int = _get_int("SP_INTEGRATION_OUTBOX_MAX_ATTEMPTS", 3)
    integration_payroll_export_enabled: bool = _get_bool(
        "SP_INTEGRATION_PAYROLL_EXPORT_ENABLED",
        False,
    )
    integration_maps_enabled: bool = _get_bool("SP_INTEGRATION_MAPS_ENABLED", False)
    security_rate_limit_enabled: bool = _get_bool("SP_SECURITY_RATE_LIMIT_ENABLED", True)
    security_rate_limit_window_seconds: int = _get_int("SP_SECURITY_RATE_LIMIT_WINDOW_SECONDS", 300)
    security_rate_limit_auth_refresh_max: int = _get_int("SP_SECURITY_RATE_LIMIT_AUTH_REFRESH_MAX", 30)
    security_rate_limit_document_download_max: int = _get_int(
        "SP_SECURITY_RATE_LIMIT_DOCUMENT_DOWNLOAD_MAX",
        60,
    )
    security_rate_limit_report_export_max: int = _get_int("SP_SECURITY_RATE_LIMIT_REPORT_EXPORT_MAX", 20)
    ai_enabled: bool = field(default_factory=lambda: _get_bool("SP_AI_ENABLED", False))
    ai_provider: str = field(default_factory=lambda: _get_str("SP_AI_PROVIDER", "mock"))
    ai_allow_mock_provider: bool = field(default_factory=lambda: _get_bool("SP_AI_ALLOW_MOCK_PROVIDER", False))
    ai_openai_api_key: str = field(default_factory=lambda: _get_str("SP_OPENAI_API_KEY"), repr=False)
    ai_response_model: str = field(
        default_factory=lambda: _get_str("SP_AI_RESPONSE_MODEL", "gpt-5.5-or-configured-model")
    )
    ai_embedding_model: str = field(
        default_factory=lambda: _get_str("SP_AI_EMBEDDING_MODEL", "text-embedding-3-small")
    )
    ai_store_responses: bool = field(default_factory=lambda: _get_bool("SP_AI_STORE_RESPONSES", False))
    ai_retrieval_mode: str = field(default_factory=lambda: _get_str("SP_AI_RETRIEVAL_MODE", "lexical"))
    ai_embeddings_enabled: bool = field(default_factory=lambda: _get_bool("SP_AI_EMBEDDINGS_ENABLED", False))
    ai_retrieval_debug: bool = field(default_factory=lambda: _get_bool("SP_AI_RETRIEVAL_DEBUG", False))
    ai_max_tool_calls: int = field(default_factory=lambda: _get_int("SP_AI_MAX_TOOL_CALLS", 8))
    ai_max_context_chunks: int = field(default_factory=lambda: _get_int("SP_AI_MAX_CONTEXT_CHUNKS", 8))
    ai_max_input_chars: int = field(default_factory=lambda: _get_int("SP_AI_MAX_INPUT_CHARS", 12000))
    ai_max_provider_input_tokens: int = field(default_factory=lambda: _get_int("SP_AI_MAX_PROVIDER_INPUT_TOKENS", 14000))
    ai_max_continuation_input_tokens: int = field(default_factory=lambda: _get_int("SP_AI_MAX_CONTINUATION_INPUT_TOKENS", 5000))
    ai_max_grounding_sources: int = field(default_factory=lambda: _get_int("SP_AI_MAX_GROUNDING_SOURCES", 8))
    ai_max_grounding_chars_per_source: int = field(default_factory=lambda: _get_int("SP_AI_MAX_GROUNDING_CHARS_PER_SOURCE", 700))
    ai_max_total_grounding_chars: int = field(default_factory=lambda: _get_int("SP_AI_MAX_TOTAL_GROUNDING_CHARS", 4500))
    ai_max_recent_messages_for_model: int = field(default_factory=lambda: _get_int("SP_AI_MAX_RECENT_MESSAGES_FOR_MODEL", 6))
    ai_max_recent_messages_for_continuation: int = field(default_factory=lambda: _get_int("SP_AI_MAX_RECENT_MESSAGES_FOR_CONTINUATION", 0))
    ai_max_tool_result_chars: int = field(default_factory=lambda: _get_int("SP_AI_MAX_TOOL_RESULT_CHARS", 1500))
    ai_max_tool_result_items: int = field(default_factory=lambda: _get_int("SP_AI_MAX_TOOL_RESULT_ITEMS", 5))
    ai_max_total_tool_result_chars: int = field(default_factory=lambda: _get_int("SP_AI_MAX_TOTAL_TOOL_RESULT_CHARS", 3500))
    ai_max_diagnostic_facts: int = field(default_factory=lambda: _get_int("SP_AI_MAX_DIAGNOSTIC_FACTS", 12))
    ai_min_structured_output_tokens: int = field(default_factory=lambda: _get_int("SP_AI_MIN_STRUCTURED_OUTPUT_TOKENS", 800))
    ai_max_output_tokens: int = field(default_factory=lambda: _get_int("SP_AI_MAX_OUTPUT_TOKENS", 1200))
    ai_continuation_max_output_tokens: int = field(default_factory=lambda: _get_int("SP_AI_CONTINUATION_MAX_OUTPUT_TOKENS", 900))
    ai_degraded_max_output_tokens: int = field(default_factory=lambda: _get_int("SP_AI_DEGRADED_MAX_OUTPUT_TOKENS", 700))
    ai_timeout_seconds: int = field(default_factory=lambda: _get_int("SP_AI_TIMEOUT_SECONDS", 45))
    ai_rate_limit_retry_seconds: int = field(default_factory=lambda: _get_int("SP_AI_RATE_LIMIT_RETRY_SECONDS", 6))
    ai_rate_limit_max_retries: int = field(default_factory=lambda: _get_int("SP_AI_RATE_LIMIT_MAX_RETRIES", 2))
    ai_fallback_response_model: str = field(default_factory=lambda: _get_str("SP_AI_FALLBACK_RESPONSE_MODEL", ""))
    ai_rate_limit_per_user_per_minute: int = field(
        default_factory=lambda: _get_int("SP_AI_RATE_LIMIT_PER_USER_PER_MINUTE", 10)
    )
    ai_rate_limit_per_tenant_per_minute: int = field(
        default_factory=lambda: _get_int("SP_AI_RATE_LIMIT_PER_TENANT_PER_MINUTE", 100)
    )
    ai_rag_quality_gate_mode: str = field(
        default_factory=lambda: _get_str("SP_AI_RAG_QUALITY_GATE_MODE", "off")
    )
    ai_redaction_enabled: bool = field(default_factory=lambda: _get_bool("SP_AI_REDACTION_ENABLED", True))
    ai_audit_enabled: bool = field(default_factory=lambda: _get_bool("SP_AI_AUDIT_ENABLED", True))

    def __post_init__(self) -> None:
        normalized_provider = self.ai_provider.strip().lower()
        object.__setattr__(self, "ai_provider", normalized_provider)
        normalized_retrieval_mode = self.ai_retrieval_mode.strip().lower()
        object.__setattr__(self, "ai_retrieval_mode", normalized_retrieval_mode)
        normalized_quality_gate_mode = self.ai_rag_quality_gate_mode.strip().lower()
        object.__setattr__(self, "ai_rag_quality_gate_mode", normalized_quality_gate_mode)

        allowed_providers = {"mock", "openai"}
        if normalized_provider not in allowed_providers:
            raise ValueError(
                "Invalid SP_AI_PROVIDER value. Expected one of: mock, openai."
            )
        allowed_retrieval_modes = {"lexical", "semantic", "hybrid"}
        if normalized_retrieval_mode not in allowed_retrieval_modes:
            raise ValueError(
                "Invalid SP_AI_RETRIEVAL_MODE value. Expected one of: lexical, semantic, hybrid."
            )
        allowed_quality_gate_modes = {"off", "log_only", "enforce_in_tests"}
        if normalized_quality_gate_mode not in allowed_quality_gate_modes:
            raise ValueError(
                "Invalid SP_AI_RAG_QUALITY_GATE_MODE value. Expected one of: off, log_only, enforce_in_tests."
            )
        if self.ai_min_structured_output_tokens < 200:
            raise ValueError(
                "SP_AI_MIN_STRUCTURED_OUTPUT_TOKENS must be at least 200."
            )
        if self.ai_max_output_tokens < self.ai_min_structured_output_tokens:
            raise ValueError(
                "SP_AI_MAX_OUTPUT_TOKENS must be greater than or equal to SP_AI_MIN_STRUCTURED_OUTPUT_TOKENS."
            )
        if self.ai_continuation_max_output_tokens < self.ai_min_structured_output_tokens:
            raise ValueError(
                "SP_AI_CONTINUATION_MAX_OUTPUT_TOKENS must be greater than or equal to SP_AI_MIN_STRUCTURED_OUTPUT_TOKENS."
            )
        if self.ai_degraded_max_output_tokens < 200:
            raise ValueError(
                "SP_AI_DEGRADED_MAX_OUTPUT_TOKENS must be at least 200."
            )

        if self.ai_enabled and normalized_provider == "openai" and not self.ai_openai_api_key.strip():
            raise ValueError(
                "SP_OPENAI_API_KEY is required when SP_AI_ENABLED=true and SP_AI_PROVIDER=openai."
            )
        if (
            self.ai_enabled
            and normalized_provider == "openai"
            and self.ai_response_model.strip() == "gpt-5.5-or-configured-model"
        ):
            raise ValueError(
                "SP_AI_RESPONSE_MODEL must be set to a real model name when SP_AI_ENABLED=true and SP_AI_PROVIDER=openai."
            )

    @property
    def allowed_origins_list(self) -> tuple[str, ...]:
        return tuple(
            origin.strip()
            for origin in self.allowed_origins.split(",")
            if origin.strip()
        )

    @property
    def database_url(self) -> str:
        if self.database_url_override:
            return self.database_url_override
        if self.alembic_database_url:
            return self.alembic_database_url
        return (
            f"postgresql+psycopg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def loaded_env_files(self) -> tuple[str, ...]:
        return tuple(str(path) for path in LOADED_ENV_FILES)

    @property
    def ai_openai_configured(self) -> bool:
        return bool(
            self.ai_openai_api_key.strip()
            and self.ai_response_model.strip()
            and self.ai_response_model.strip() != "gpt-5.5-or-configured-model"
        )

    @property
    def ai_mock_provider_allowed(self) -> bool:
        return self.env in {"test", "ci"} or self.ai_allow_mock_provider

    @property
    def ai_effective_retrieval_mode(self) -> str:
        if self.ai_retrieval_mode == "semantic" and not self.ai_embeddings_enabled:
            return "lexical"
        if self.ai_retrieval_mode == "hybrid" and not self.ai_embeddings_enabled:
            return "lexical"
        return self.ai_retrieval_mode


settings = AppSettings()
