"""Environment-backed backend settings for development and staging."""

from __future__ import annotations

from dataclasses import dataclass
from os import getenv


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
    db_password: str = _get_str("SP_DB_PASSWORD", "")
    db_echo: bool = _get_bool("SP_DB_ECHO", False)
    alembic_database_url: str = _get_str("SP_ALEMBIC_DATABASE_URL")

    object_storage_endpoint: str = _get_str("SP_OBJECT_STORAGE_ENDPOINT")
    object_storage_region: str = _get_str("SP_OBJECT_STORAGE_REGION", "eu-central-1")
    object_storage_bucket: str = _get_str("SP_OBJECT_STORAGE_BUCKET", "sicherplan-dev")
    object_storage_access_key: str = _get_str("SP_OBJECT_STORAGE_ACCESS_KEY")
    object_storage_secret_key: str = _get_str("SP_OBJECT_STORAGE_SECRET_KEY")
    object_storage_use_ssl: bool = _get_bool("SP_OBJECT_STORAGE_USE_SSL", False)

    auth_session_secret: str = _get_str("SP_AUTH_SESSION_SECRET")
    auth_access_token_ttl_minutes: int = _get_int("SP_AUTH_ACCESS_TOKEN_TTL_MINUTES", 15)
    auth_refresh_token_ttl_minutes: int = _get_int("SP_AUTH_REFRESH_TOKEN_TTL_MINUTES", 10080)
    auth_external_idp_enabled: bool = _get_bool("SP_AUTH_EXTERNAL_IDP_ENABLED", False)
    auth_external_idp_discovery_url: str = _get_str("SP_AUTH_EXTERNAL_IDP_DISCOVERY_URL")
    auth_external_idp_client_id: str = _get_str("SP_AUTH_EXTERNAL_IDP_CLIENT_ID")
    auth_external_idp_client_secret: str = _get_str("SP_AUTH_EXTERNAL_IDP_CLIENT_SECRET")

    message_email_enabled: bool = _get_bool("SP_MESSAGE_EMAIL_ENABLED", False)
    message_sms_enabled: bool = _get_bool("SP_MESSAGE_SMS_ENABLED", False)
    message_push_enabled: bool = _get_bool("SP_MESSAGE_PUSH_ENABLED", False)
    message_email_from: str = _get_str("SP_MESSAGE_EMAIL_FROM", "no-reply@example.invalid")

    integration_outbox_enabled: bool = _get_bool("SP_INTEGRATION_OUTBOX_ENABLED", True)
    integration_payroll_export_enabled: bool = _get_bool(
        "SP_INTEGRATION_PAYROLL_EXPORT_ENABLED",
        False,
    )
    integration_maps_enabled: bool = _get_bool("SP_INTEGRATION_MAPS_ENABLED", False)

    @property
    def database_url(self) -> str:
        if self.alembic_database_url:
            return self.alembic_database_url
        return (
            f"postgresql+psycopg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


settings = AppSettings()
