from __future__ import annotations

import unittest
from dataclasses import dataclass
from datetime import UTC, date, datetime
from types import SimpleNamespace

from app.errors import ApiException
from app.modules.employees.mobile_read_service import EmployeeMobileReadService
from app.modules.employees.schemas import EmployeeReleasedScheduleCollectionRead, EmployeeReleasedScheduleRead, EmployeeReleasedScheduleDocumentRead
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.platform_services.docs_service import DocumentDownload
from tests.modules.employees.test_employee_self_service import FakeSelfServiceRepository


def _context() -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id='session-1',
        user_id='user-1',
        tenant_id='tenant-1',
        role_keys=frozenset({'employee_user'}),
        permission_keys=frozenset({'portal.employee.access'}),
        scopes=(AuthenticatedRoleScope(role_key='employee_user', scope_type='tenant'),),
        request_id='req-1',
    )


@dataclass
class _FakeReleasedScheduleService:
    def list_employee_schedules(self, context: RequestAuthorizationContext) -> EmployeeReleasedScheduleCollectionRead:
        return EmployeeReleasedScheduleCollectionRead(
            employee_id='employee-1',
            tenant_id=context.tenant_id,
            items=[
                EmployeeReleasedScheduleRead(
                    id='assignment-1',
                    employee_id='employee-1',
                    shift_id='shift-1',
                    schedule_date=date(2026, 4, 2),
                    shift_label='Day',
                    work_start=datetime(2026, 4, 2, 8, 0, tzinfo=UTC),
                    work_end=datetime(2026, 4, 2, 16, 0, tzinfo=UTC),
                    location_label='HQ',
                    meeting_point='Gate 1',
                    assignment_status='assigned',
                    confirmation_status='assigned',
                    documents=[
                        EmployeeReleasedScheduleDocumentRead(
                            document_id='shift-doc-1',
                            title='Deployment plan',
                            file_name='deployment.pdf',
                            content_type='application/pdf',
                            current_version_no=2,
                        )
                    ],
                )
            ],
        )


@dataclass
class _FakeDocumentService:
    def download_document_version(self, tenant_id: str, document_id: str, version_no: int, actor):  # noqa: ANN001
        return DocumentDownload(
            file_name=f'{document_id}.bin',
            content_type='application/octet-stream',
            content=b'123',
            checksum_sha256='abc',
        )


class EmployeeMobileReadServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = FakeSelfServiceRepository()
        self.repository.create_address_history  # touch to keep lint quiet
        self.repository.employees['employee-1'].user_id = 'user-1'
        self.repository.employee_credentials = [
            SimpleNamespace(
                id='cred-1',
                employee_id='employee-1',
                credential_no='CARD-1',
                credential_type='qr',
                encoded_value='EMPLOYEE-CARD',
                valid_from=date(2026, 1, 1),
                valid_until=None,
                status='issued',
            )
        ]
        employee_doc = SimpleNamespace(
            id='employee-doc-1',
            title='Badge output',
            metadata_json={'credential_id': 'cred-1'},
            current_version_no=1,
            versions=[SimpleNamespace(version_no=1, file_name='badge.txt', content_type='text/plain')],
            links=[SimpleNamespace(owner_type='hr.employee', owner_id='employee-1', relation_type='badge_output', linked_at=datetime.now(UTC))],
        )
        self.repository.owner_documents = {
            ('tenant-1', 'hr.employee', 'employee-1'): [employee_doc],
        }
        profile_photo = SimpleNamespace(
            id='employee-photo-1',
            title='Profilfoto',
            metadata_json={'kind': 'profile_photo'},
            current_version_no=1,
            versions=[SimpleNamespace(version_no=1, file_name='profile.jpg', content_type='image/jpeg')],
            links=[SimpleNamespace(owner_type='hr.employee', owner_id='employee-1', relation_type='profile_photo', linked_at=datetime.now(UTC))],
        )
        self.repository.owner_documents[('tenant-1', 'hr.employee', 'employee-1')].append(profile_photo)
        self.repository.list_credentials = lambda tenant_id, filters: [  # type: ignore[method-assign]
            row for row in self.repository.employee_credentials if row.employee_id == filters.employee_id
        ]
        self.repository.list_documents_for_owner = lambda tenant_id, owner_type, owner_id: self.repository.owner_documents.get(  # type: ignore[method-assign]
            (tenant_id, owner_type, owner_id),
            [],
        )
        self.service = EmployeeMobileReadService(
            repository=self.repository,
            released_schedule_service=_FakeReleasedScheduleService(),
            document_service=_FakeDocumentService(),
        )

    def test_lists_employee_and_shift_documents_with_scope(self) -> None:
        result = self.service.list_documents(_context())
        self.assertEqual(result.employee_id, 'employee-1')
        self.assertEqual({item.document_id for item in result.items}, {'employee-doc-1', 'shift-doc-1'})

    def test_download_rejects_unscoped_document(self) -> None:
        with self.assertRaises(ApiException) as raised:
            self.service.download_document(_context(), 'unknown-doc', 1)
        self.assertEqual(raised.exception.status_code, 404)

    def test_download_allows_owned_profile_photo(self) -> None:
        result = self.service.download_document(_context(), 'employee-photo-1', 1)
        self.assertEqual(result.file_name, 'employee-photo-1.bin')

    def test_lists_credentials_for_own_employee(self) -> None:
        result = self.service.list_credentials(_context())
        self.assertEqual(len(result.items), 1)
        self.assertEqual(result.items[0].credential_no, 'CARD-1')
        self.assertEqual(result.items[0].badge_document_id, 'employee-doc-1')


if __name__ == '__main__':
    unittest.main()
