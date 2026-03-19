from __future__ import annotations

import unittest
from dataclasses import dataclass
from types import SimpleNamespace
from uuid import uuid4

from app.errors import ApiException
from app.modules.recruiting.models import Applicant
from app.modules.recruiting.public_service import (
    PublicApplicantService,
    PublicApplicantThrottle,
    PublicRequestContext,
)
from app.modules.recruiting.repository import APPLICANT_FORM_SETTING_KEY
from app.modules.recruiting.schemas import PublicApplicantSubmissionCreate


@dataclass
class FakeDocument:
    id: str


class FakeDocumentService:
    def __init__(self) -> None:
        self.created_documents: list[dict[str, object]] = []
        self.created_versions: list[dict[str, object]] = []
        self.created_links: list[dict[str, object]] = []

    def create_document(self, tenant_id, payload, actor):
        document_id = f"doc-{len(self.created_documents) + 1}"
        self.created_documents.append(
            {
                "tenant_id": tenant_id,
                "payload": payload,
                "actor": actor,
                "document_id": document_id,
            }
        )
        return FakeDocument(id=document_id)

    def add_document_version(self, tenant_id, document_id, payload, actor):
        self.created_versions.append(
            {
                "tenant_id": tenant_id,
                "document_id": document_id,
                "payload": payload,
                "actor": actor,
            }
        )
        return None

    def add_document_link(self, tenant_id, document_id, payload, actor):
        self.created_links.append(
            {
                "tenant_id": tenant_id,
                "document_id": document_id,
                "payload": payload,
                "actor": actor,
            }
        )
        return None


class FakeAuditService:
    def __init__(self) -> None:
        self.events: list[dict[str, object]] = []

    def record_business_event(self, **kwargs):
        self.events.append(kwargs)
        return None


class FakeRecruitingRepository:
    def __init__(self) -> None:
        self.tenant = SimpleNamespace(
            id="tenant-1",
            code="alpha",
            name="Alpha Security",
            default_locale="de",
            archived_at=None,
            status="active",
        )
        self.settings = {
            APPLICANT_FORM_SETTING_KEY: {
                "allowed_embed_origins": ["https://jobs.example.de"],
                "required_fields": ["first_name", "last_name", "email", "desired_role"],
                "additional_fields": [
                    {
                        "key": "guard_license",
                        "type": "select",
                        "label_de": "Sachkundenachweis",
                        "label_en": "Guard license",
                        "required": True,
                        "options": [
                            {"value": "34a", "label_de": "34a vorhanden", "label_en": "34a available"},
                            {"value": "none", "label_de": "Noch nicht", "label_en": "Not yet"},
                        ],
                    }
                ],
                "gdpr_policy_ref": "privacy-2026",
                "gdpr_policy_version": "2026-03",
                "max_attachment_count": 2,
                "max_attachment_size_bytes": 1024 * 1024,
            }
        }
        self.applicants: list[Applicant] = []

    def get_tenant_by_code(self, tenant_code: str):
        return self.tenant if tenant_code == self.tenant.code else None

    def get_tenant_setting_value(self, tenant_id: str, key: str):
        if tenant_id != self.tenant.id:
            return None
        return self.settings.get(key)

    def find_applicant_by_submission_key(self, tenant_id: str, submission_key: str):
        for applicant in self.applicants:
            if applicant.tenant_id == tenant_id and applicant.submission_key == submission_key:
                return applicant
        return None

    def find_applicant_by_application_no(self, tenant_id: str, application_no: str):
        for applicant in self.applicants:
            if applicant.tenant_id == tenant_id and applicant.application_no == application_no:
                return applicant
        return None

    def create_applicant(self, row: Applicant) -> Applicant:
        if self.find_applicant_by_submission_key(row.tenant_id, row.submission_key):
            raise AssertionError("duplicate submission key should have been handled before create")
        if row.id is None:
            row.id = str(uuid4())
        self.applicants.append(row)
        return row


class PublicApplicantServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = FakeRecruitingRepository()
        self.document_service = FakeDocumentService()
        self.audit_service = FakeAuditService()
        self.service = PublicApplicantService(
            self.repository,
            document_service=self.document_service,
            audit_service=self.audit_service,
            throttle=PublicApplicantThrottle(max_attempts=5, lockout_minutes=10),
        )
        self.context = PublicRequestContext(
            request_id="req-1",
            ip_address="127.0.0.1",
            user_agent="pytest",
            request_origin="https://jobs.example.de",
        )

    def _payload(self, **overrides) -> PublicApplicantSubmissionCreate:
        base = {
            "submission_key": "submit-key-0001",
            "locale": "de",
            "first_name": "Anna",
            "last_name": "Wagner",
            "email": "anna@example.de",
            "desired_role": "Objektschutz",
            "additional_fields": {"guard_license": "34a"},
            "gdpr_consent_confirmed": True,
            "gdpr_policy_ref": "privacy-2026",
            "gdpr_policy_version": "2026-03",
            "attachments": [],
        }
        base.update(overrides)
        return PublicApplicantSubmissionCreate.model_validate(base)

    def test_get_public_form_defaults_to_german_and_returns_configured_fields(self) -> None:
        form = self.service.get_public_form("alpha", self.context)

        self.assertEqual(form.default_locale, "de")
        self.assertEqual(form.gdpr_policy_version, "2026-03")
        self.assertEqual(form.fields[0].key, "first_name")
        self.assertTrue(any(field.key == "guard_license" and field.required for field in form.fields))

    def test_submit_requires_explicit_consent(self) -> None:
        with self.assertRaises(ApiException) as ctx:
            self.service.submit_public_application(
                "alpha",
                self._payload(gdpr_consent_confirmed=False),
                self.context,
            )

        self.assertEqual(ctx.exception.message_key, "errors.recruiting.applicant.consent_required")

    def test_submit_enforces_required_custom_field(self) -> None:
        with self.assertRaises(ApiException) as ctx:
            self.service.submit_public_application(
                "alpha",
                self._payload(additional_fields={}),
                self.context,
            )

        self.assertEqual(ctx.exception.message_key, "errors.recruiting.applicant.field_required")
        self.assertEqual(ctx.exception.details["field_key"], "guard_license")

    def test_submit_rejects_request_origin_outside_allow_list(self) -> None:
        with self.assertRaises(ApiException) as ctx:
            self.service.submit_public_application(
                "alpha",
                self._payload(),
                PublicRequestContext(
                    request_id="req-2",
                    ip_address="127.0.0.1",
                    user_agent="pytest",
                    request_origin="https://evil.example",
                ),
            )

        self.assertEqual(ctx.exception.message_key, "errors.recruiting.applicant.origin_denied")

    def test_submit_links_uploaded_files_through_docs_backbone(self) -> None:
        response = self.service.submit_public_application(
            "alpha",
            self._payload(
                attachments=[
                    {
                        "kind": "cv",
                        "file_name": "anna-cv.pdf",
                        "content_type": "application/pdf",
                        "content_base64": "UERG",
                        "label": "Lebenslauf",
                    }
                ]
            ),
            self.context,
        )

        self.assertEqual(response.status, "submitted")
        self.assertEqual(len(self.document_service.created_documents), 1)
        self.assertEqual(len(self.document_service.created_versions), 1)
        self.assertEqual(len(self.document_service.created_links), 1)
        self.assertEqual(self.document_service.created_links[0]["payload"].owner_type, "hr.applicant")
        self.assertEqual(self.document_service.created_links[0]["payload"].relation_type, "cv")
        self.assertEqual(self.audit_service.events[0]["event_type"], "recruiting.applicant.submitted")

    def test_duplicate_submission_key_returns_existing_applicant_response(self) -> None:
        first = self.service.submit_public_application("alpha", self._payload(), self.context)
        second = self.service.submit_public_application("alpha", self._payload(), self.context)

        self.assertEqual(first.applicant_id, second.applicant_id)
        self.assertEqual(len(self.repository.applicants), 1)
        self.assertEqual(len(self.audit_service.events), 1)


if __name__ == "__main__":
    unittest.main()
