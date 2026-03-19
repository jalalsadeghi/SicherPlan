"""Public applicant intake service with tenant-safe iframe checks."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol
from urllib.parse import urlparse
from uuid import uuid4

from sqlalchemy.exc import IntegrityError

from app.config import settings
from app.errors import ApiException
from app.modules.iam.audit_service import AuditActor, AuditService
from app.modules.platform_services.docs_schemas import DocumentCreate, DocumentLinkCreate, DocumentVersionCreate
from app.modules.platform_services.docs_service import DocumentService
from app.modules.recruiting.models import Applicant
from app.modules.recruiting.repository import APPLICANT_FORM_SETTING_KEY
from app.modules.recruiting.schemas import (
    ApplicantRead,
    PublicApplicantAttachmentCreate,
    PublicApplicantExtraFieldSetting,
    PublicApplicantFieldOption,
    PublicApplicantFormConfigRead,
    PublicApplicantFormFieldRead,
    PublicApplicantFormSetting,
    PublicApplicantSubmissionCreate,
    PublicApplicantSubmissionResponse,
)


class RecruitingRepository(Protocol):
    def get_tenant_by_code(self, tenant_code: str): ...  # noqa: ANN001
    def get_tenant_setting_value(self, tenant_id: str, key: str): ...  # noqa: ANN001
    def find_applicant_by_submission_key(self, tenant_id: str, submission_key: str): ...  # noqa: ANN001
    def find_applicant_by_application_no(self, tenant_id: str, application_no: str): ...  # noqa: ANN001
    def create_applicant(self, row: Applicant) -> Applicant: ...


@dataclass(frozen=True, slots=True)
class PublicRequestContext:
    request_id: str | None
    ip_address: str | None
    user_agent: str | None
    request_origin: str | None


@dataclass(frozen=True, slots=True)
class PublicDocumentActor:
    tenant_id: str
    user_id: str | None = None
    is_platform_admin: bool = False


class PublicApplicantThrottle:
    def __init__(self, max_attempts: int, lockout_minutes: int) -> None:
        self.max_attempts = max_attempts
        self.lockout_minutes = lockout_minutes
        self._entries: dict[str, tuple[int, datetime | None]] = {}

    def assert_allowed(self, key: str, now: datetime) -> None:
        attempts, locked_until = self._entries.get(key, (0, None))
        if locked_until is not None and locked_until > now:
            raise ApiException(
                429,
                "recruiting.applicant.rate_limited",
                "errors.recruiting.applicant.rate_limited",
            )
        if locked_until is not None and locked_until <= now:
            self._entries.pop(key, None)

    def register_failure(self, key: str, now: datetime) -> None:
        attempts, _ = self._entries.get(key, (0, None))
        attempts += 1
        if attempts >= self.max_attempts:
            self._entries[key] = (attempts, now.replace(microsecond=0) + settings_public_lockout_delta(self.lockout_minutes))
            return
        self._entries[key] = (attempts, None)

    def register_success(self, key: str) -> None:
        self._entries.pop(key, None)


def settings_public_lockout_delta(lockout_minutes: int):
    from datetime import timedelta

    return timedelta(minutes=lockout_minutes)


class PublicApplicantService:
    BUILTIN_FIELDS: tuple[PublicApplicantFormFieldRead, ...] = (
        PublicApplicantFormFieldRead(
            key="first_name",
            type="text",
            label_de="Vorname",
            label_en="First name",
            visible=True,
            required=True,
        ),
        PublicApplicantFormFieldRead(
            key="last_name",
            type="text",
            label_de="Nachname",
            label_en="Last name",
            visible=True,
            required=True,
        ),
        PublicApplicantFormFieldRead(
            key="email",
            type="email",
            label_de="E-Mail",
            label_en="Email",
            visible=True,
            required=True,
        ),
        PublicApplicantFormFieldRead(
            key="phone",
            type="tel",
            label_de="Telefon",
            label_en="Phone",
            visible=True,
            required=False,
        ),
        PublicApplicantFormFieldRead(
            key="desired_role",
            type="text",
            label_de="Gewuenschte Position",
            label_en="Desired role",
            visible=True,
            required=False,
        ),
        PublicApplicantFormFieldRead(
            key="availability_date",
            type="date",
            label_de="Verfuegbar ab",
            label_en="Available from",
            visible=True,
            required=False,
        ),
        PublicApplicantFormFieldRead(
            key="message",
            type="textarea",
            label_de="Nachricht",
            label_en="Message",
            visible=True,
            required=False,
        ),
    )

    def __init__(
        self,
        repository: RecruitingRepository,
        *,
        document_service: DocumentService,
        audit_service: AuditService,
        throttle: PublicApplicantThrottle,
    ) -> None:
        self.repository = repository
        self.document_service = document_service
        self.audit_service = audit_service
        self.throttle = throttle

    def get_public_form(self, tenant_code: str, request_context: PublicRequestContext) -> PublicApplicantFormConfigRead:
        tenant = self._require_tenant(tenant_code)
        config = self._load_setting(tenant.id, tenant.default_locale)
        self._ensure_public_origin_allowed(config.allowed_embed_origins, request_context.request_origin)
        return PublicApplicantFormConfigRead(
            tenant_id=tenant.id,
            tenant_code=tenant.code,
            tenant_name=tenant.name,
            default_locale=config.default_locale,
            source_channel=config.source_channel,
            source_detail=config.source_detail,
            gdpr_policy_ref=config.gdpr_policy_ref,
            gdpr_policy_version=config.gdpr_policy_version,
            gdpr_policy_url_de=config.gdpr_policy_url_de,
            gdpr_policy_url_en=config.gdpr_policy_url_en,
            max_attachment_count=config.max_attachment_count,
            max_attachment_size_bytes=config.max_attachment_size_bytes,
            allowed_attachment_types=config.allowed_attachment_types,
            allowed_embed_origins=config.allowed_embed_origins,
            fields=self._build_fields(config),
        )

    def submit_public_application(
        self,
        tenant_code: str,
        payload: PublicApplicantSubmissionCreate,
        request_context: PublicRequestContext,
    ) -> PublicApplicantSubmissionResponse:
        tenant = self._require_tenant(tenant_code)
        config = self._load_setting(tenant.id, tenant.default_locale)
        self._ensure_public_origin_allowed(config.allowed_embed_origins, request_context.request_origin)
        self._validate_submission(config, payload)

        throttle_key = f"{tenant.code}:{request_context.ip_address or 'unknown'}".lower()
        now = datetime.now(UTC)
        self.throttle.assert_allowed(throttle_key, now)

        existing = self.repository.find_applicant_by_submission_key(tenant.id, payload.submission_key)
        if existing is not None:
            self.throttle.register_success(throttle_key)
            return self._build_submission_response(existing)

        application_no = self._build_application_no(tenant.id)
        try:
            applicant = self.repository.create_applicant(
                Applicant(
                    tenant_id=tenant.id,
                    application_no=application_no,
                    submission_key=payload.submission_key.strip(),
                    source_channel=config.source_channel,
                    source_detail=config.source_detail,
                    locale=payload.locale,
                    first_name=(payload.first_name or "").strip(),
                    last_name=(payload.last_name or "").strip(),
                    email=(payload.email or "").strip().lower(),
                    phone=self._trim_optional(payload.phone),
                    desired_role=self._trim_optional(payload.desired_role),
                    availability_date=payload.availability_date,
                    message=self._trim_optional(payload.message),
                    gdpr_consent_granted=True,
                    gdpr_consent_at=now,
                    gdpr_policy_ref=payload.gdpr_policy_ref,
                    gdpr_policy_version=payload.gdpr_policy_version,
                    custom_fields_json=self._normalize_custom_fields(config.additional_fields, payload.additional_fields),
                    metadata_json={
                        "public_submission": True,
                        "attachment_count": len(payload.attachments),
                    },
                    submitted_ip=request_context.ip_address,
                    submitted_origin=request_context.request_origin,
                    submitted_user_agent=request_context.user_agent,
                    status="submitted",
                )
            )
        except IntegrityError as exc:
            self.throttle.register_failure(throttle_key, now)
            raise ApiException(
                409,
                "recruiting.applicant.duplicate_submission",
                "errors.recruiting.applicant.duplicate_submission",
            ) from exc

        self._store_attachments(tenant.id, applicant, payload.attachments, request_context.request_id)
        self.audit_service.record_business_event(
            actor=AuditActor(
                tenant_id=tenant.id,
                user_id=None,
                session_id=None,
                request_id=request_context.request_id,
                source="public_form",
            ),
            event_type="recruiting.applicant.submitted",
            entity_type="hr.applicant",
            entity_id=applicant.id,
            after_json={
                "application_no": applicant.application_no,
                "status": applicant.status,
                "source_channel": applicant.source_channel,
            },
            metadata_json={
                "gdpr_policy_ref": applicant.gdpr_policy_ref,
                "gdpr_policy_version": applicant.gdpr_policy_version,
                "attachment_count": len(payload.attachments),
                "request_origin": request_context.request_origin,
            },
        )
        self.throttle.register_success(throttle_key)
        return self._build_submission_response(applicant)

    def _require_tenant(self, tenant_code: str):
        tenant = self.repository.get_tenant_by_code(tenant_code.strip())
        if tenant is None or tenant.archived_at is not None or tenant.status != "active":
            raise ApiException(404, "recruiting.applicant.tenant_not_found", "errors.recruiting.applicant.tenant_not_found")
        return tenant

    def _load_setting(self, tenant_id: str, tenant_locale: str) -> PublicApplicantFormSetting:
        raw = self.repository.get_tenant_setting_value(tenant_id, APPLICANT_FORM_SETTING_KEY) or {}
        config = PublicApplicantFormSetting.model_validate(
            {
                "default_locale": "en" if tenant_locale == "en" else "de",
                "allowed_embed_origins": self._default_allowed_origins(),
                **raw,
            }
        )
        if not config.enabled:
            raise ApiException(403, "recruiting.applicant.form_disabled", "errors.recruiting.applicant.form_disabled")
        return config

    @staticmethod
    def _default_allowed_origins() -> list[str]:
        return [origin.strip() for origin in settings.allowed_origins.split(",") if origin.strip()]

    def _ensure_public_origin_allowed(self, allowed_origins: list[str], request_origin: str | None) -> None:
        if request_origin is None:
            return
        normalized_origin = self._normalize_origin(request_origin)
        normalized_allowed = {self._normalize_origin(origin) for origin in allowed_origins if origin}
        if normalized_origin not in normalized_allowed:
            raise ApiException(
                403,
                "recruiting.applicant.origin_denied",
                "errors.recruiting.applicant.origin_denied",
            )

    def _validate_submission(self, config: PublicApplicantFormSetting, payload: PublicApplicantSubmissionCreate) -> None:
        if not payload.gdpr_consent_confirmed:
            raise ApiException(
                400,
                "recruiting.applicant.consent_required",
                "errors.recruiting.applicant.consent_required",
            )
        if payload.gdpr_policy_ref != config.gdpr_policy_ref or payload.gdpr_policy_version != config.gdpr_policy_version:
            raise ApiException(
                409,
                "recruiting.applicant.policy_mismatch",
                "errors.recruiting.applicant.policy_mismatch",
            )
        if len(payload.attachments) > config.max_attachment_count:
            raise ApiException(
                400,
                "recruiting.applicant.too_many_attachments",
                "errors.recruiting.applicant.too_many_attachments",
                {"max_attachment_count": config.max_attachment_count},
            )

        field_values = {
            "first_name": self._trim_optional(payload.first_name),
            "last_name": self._trim_optional(payload.last_name),
            "email": self._trim_optional(payload.email),
            "phone": self._trim_optional(payload.phone),
            "desired_role": self._trim_optional(payload.desired_role),
            "availability_date": payload.availability_date.isoformat() if payload.availability_date else None,
            "message": self._trim_optional(payload.message),
        }
        hidden_fields = set(config.hidden_fields)
        for key in config.required_fields:
            if key in hidden_fields:
                continue
            if key in field_values and not field_values[key]:
                raise ApiException(
                    400,
                    "recruiting.applicant.field_required",
                    "errors.recruiting.applicant.field_required",
                    {"field_key": key},
                )
        email_value = field_values["email"]
        if email_value and "@" not in email_value:
            raise ApiException(
                400,
                "recruiting.applicant.invalid_email",
                "errors.recruiting.applicant.invalid_email",
            )

        extra_fields = {field.key: field for field in config.additional_fields if field.visible}
        for field in extra_fields.values():
            value = payload.additional_fields.get(field.key)
            if field.required and self._is_empty_value(value):
                raise ApiException(
                    400,
                    "recruiting.applicant.field_required",
                    "errors.recruiting.applicant.field_required",
                    {"field_key": field.key},
                )
            if field.type == "select" and value is not None:
                allowed_values = {option.value for option in field.options}
                if str(value) not in allowed_values:
                    raise ApiException(
                        400,
                        "recruiting.applicant.invalid_field_option",
                        "errors.recruiting.applicant.invalid_field_option",
                        {"field_key": field.key},
                    )

        allowed_content_types = set(config.allowed_attachment_types)
        for attachment in payload.attachments:
            self._validate_attachment(config, allowed_content_types, attachment)

    def _validate_attachment(
        self,
        config: PublicApplicantFormSetting,
        allowed_content_types: set[str],
        attachment: PublicApplicantAttachmentCreate,
    ) -> None:
        if attachment.content_type not in allowed_content_types:
            raise ApiException(
                400,
                "recruiting.applicant.attachment_type_not_allowed",
                "errors.recruiting.applicant.attachment_type_not_allowed",
                {"content_type": attachment.content_type},
            )
        estimated_size = (len(attachment.content_base64) * 3) // 4
        if estimated_size > config.max_attachment_size_bytes:
            raise ApiException(
                400,
                "recruiting.applicant.attachment_too_large",
                "errors.recruiting.applicant.attachment_too_large",
                {"max_attachment_size_bytes": config.max_attachment_size_bytes},
            )

    def _build_fields(self, config: PublicApplicantFormSetting) -> list[PublicApplicantFormFieldRead]:
        required_fields = set(config.required_fields)
        hidden_fields = set(config.hidden_fields)
        fields: list[PublicApplicantFormFieldRead] = []
        for field in self.BUILTIN_FIELDS:
            if field.key in hidden_fields:
                continue
            fields.append(
                field.model_copy(
                    update={
                        "visible": True,
                        "required": field.key in required_fields,
                    }
                )
            )
        for field in config.additional_fields:
            fields.append(
                PublicApplicantFormFieldRead(
                    key=field.key,
                    type=field.type,
                    label_de=field.label_de,
                    label_en=field.label_en,
                    visible=field.visible,
                    required=field.required,
                    options=[PublicApplicantFieldOption.model_validate(option) for option in field.options],
                )
            )
        return [field for field in fields if field.visible]

    def _normalize_custom_fields(
        self,
        configured_fields: list[PublicApplicantExtraFieldSetting],
        submitted_fields: dict[str, object],
    ) -> dict[str, object]:
        allowed_fields = {field.key for field in configured_fields}
        normalized: dict[str, object] = {}
        for key, value in submitted_fields.items():
            if key not in allowed_fields or self._is_empty_value(value):
                continue
            normalized[key] = value
        return normalized

    def _store_attachments(
        self,
        tenant_id: str,
        applicant: Applicant,
        attachments: list[PublicApplicantAttachmentCreate],
        request_id: str | None,
    ) -> None:
        actor = PublicDocumentActor(tenant_id=tenant_id, user_id=None, is_platform_admin=False)
        for index, attachment in enumerate(attachments, start=1):
            document = self.document_service.create_document(
                tenant_id,
                DocumentCreate(
                    tenant_id=tenant_id,
                    title=attachment.label or attachment.file_name,
                    source_module="recruiting",
                    source_label="public_applicant_submission",
                    metadata_json={
                        "owner_type": "hr.applicant",
                        "owner_id": applicant.id,
                        "attachment_kind": attachment.kind,
                        "application_no": applicant.application_no,
                        "public_submission": True,
                    },
                ),
                actor,
            )
            self.document_service.add_document_version(
                tenant_id,
                document.id,
                DocumentVersionCreate(
                    file_name=attachment.file_name,
                    content_type=attachment.content_type,
                    content_base64=attachment.content_base64,
                    metadata_json={"attachment_kind": attachment.kind, "sequence_no": index},
                ),
                actor,
            )
            self.document_service.add_document_link(
                tenant_id,
                document.id,
                DocumentLinkCreate(
                    owner_type="hr.applicant",
                    owner_id=applicant.id,
                    relation_type=attachment.kind,
                    label=attachment.label or attachment.file_name,
                    metadata_json={"request_id": request_id} if request_id else {},
                ),
                actor,
            )

    def _build_submission_response(self, applicant: Applicant) -> PublicApplicantSubmissionResponse:
        return PublicApplicantSubmissionResponse(
            applicant_id=applicant.id,
            application_no=applicant.application_no,
            status=applicant.status,
            message_key="recruitingApplicant.feedback.submitted",
        )

    def _build_application_no(self, tenant_id: str) -> str:
        for _ in range(5):
            application_no = f"APP-{datetime.now(UTC):%Y%m%d}-{uuid4().hex[:6].upper()}"
            if self.repository.find_applicant_by_application_no(tenant_id, application_no) is None:
                return application_no
        raise ApiException(500, "platform.internal", "errors.platform.internal")

    @staticmethod
    def _normalize_origin(value: str) -> str:
        parsed = urlparse(value)
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")
        return value.rstrip("/")

    @staticmethod
    def _trim_optional(value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @staticmethod
    def _is_empty_value(value: object) -> bool:
        if value is None:
            return True
        if isinstance(value, str):
            return value.strip() == ""
        if isinstance(value, list | dict):
            return len(value) == 0
        return False


def applicant_to_read(applicant: Applicant) -> ApplicantRead:
    return ApplicantRead.model_validate(applicant)
