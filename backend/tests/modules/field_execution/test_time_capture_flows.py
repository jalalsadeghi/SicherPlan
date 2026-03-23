from __future__ import annotations

import unittest
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from types import SimpleNamespace
from uuid import uuid4

from app.errors import ApiException
from app.modules.field_execution.models import TimeCaptureDevice, TimeCapturePolicy, TimeEvent
from app.modules.field_execution.schemas import (
    TimeCaptureDeviceCreate,
    TimeCaptureDeviceFilter,
    TimeCaptureEventCapture,
    TimeCaptureEventFilter,
    TimeCapturePolicyCreate,
    TimeCaptureTerminalEventCapture,
    TimeEventValidationStatusUpdate,
)
from app.modules.field_execution.time_capture_service import TimeCaptureService
from app.modules.iam.audit_service import AuditService
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext
from tests.modules.field_execution.test_watchbook_flows import _FakeAuditRepository


def _admin_actor() -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id="session-admin",
        user_id="user-admin",
        tenant_id="tenant-1",
        role_keys=frozenset({"tenant_admin"}),
        permission_keys=frozenset({"field.time_capture.read", "field.time_capture.write"}),
        scopes=(AuthenticatedRoleScope(role_key="tenant_admin", scope_type="tenant"),),
        request_id="req-admin",
    )


def _employee_actor() -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id="session-employee",
        user_id="user-employee",
        tenant_id="tenant-1",
        role_keys=frozenset({"employee_user"}),
        permission_keys=frozenset({"portal.employee.access"}),
        scopes=(AuthenticatedRoleScope(role_key="employee_user", scope_type="tenant"),),
        request_id="req-employee",
    )


@dataclass
class _FakeRepo:
    tenant_id: str = "tenant-1"
    devices: dict[str, TimeCaptureDevice] = field(default_factory=dict)
    policies: dict[str, TimeCapturePolicy] = field(default_factory=dict)
    events: dict[str, TimeEvent] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.site = SimpleNamespace(id="site-1", tenant_id=self.tenant_id)
        self.route = SimpleNamespace(id="route-1", tenant_id=self.tenant_id)
        self.order = SimpleNamespace(id="order-1", tenant_id=self.tenant_id, site_id="site-1", patrol_route_id="route-1")
        self.planning_record = SimpleNamespace(
            id="planning-1",
            tenant_id=self.tenant_id,
            order=self.order,
            patrol_detail=SimpleNamespace(patrol_route_id="route-1", patrol_route=self.route),
            site_detail=SimpleNamespace(site_id="site-1"),
        )
        self.shift = SimpleNamespace(
            id="shift-1",
            tenant_id=self.tenant_id,
            release_state="released",
            shift_plan=SimpleNamespace(planning_record=self.planning_record),
        )
        self.employee = SimpleNamespace(id="employee-1", tenant_id=self.tenant_id, user_id="user-employee", status="active", archived_at=None)
        self.worker = SimpleNamespace(id="worker-1", tenant_id=self.tenant_id, status="active", archived_at=None)
        self.employee_assignment = SimpleNamespace(
            id="assignment-employee-1",
            tenant_id=self.tenant_id,
            shift_id="shift-1",
            employee_id="employee-1",
            subcontractor_worker_id=None,
            assignment_status_code="assigned",
            archived_at=None,
            shift=self.shift,
        )
        self.worker_assignment = SimpleNamespace(
            id="assignment-worker-1",
            tenant_id=self.tenant_id,
            shift_id="shift-1",
            employee_id=None,
            subcontractor_worker_id="worker-1",
            assignment_status_code="assigned",
            archived_at=None,
            shift=self.shift,
        )
        self.employee_credential = SimpleNamespace(
            id="cred-employee-1",
            tenant_id=self.tenant_id,
            employee_id="employee-1",
            encoded_value="EMP-TOKEN-1",
            status="active",
            valid_from=date(2026, 1, 1),
            valid_until=None,
            archived_at=None,
            employee=self.employee,
        )
        self.worker_credential = SimpleNamespace(
            id="cred-worker-1",
            tenant_id=self.tenant_id,
            worker_id="worker-1",
            encoded_value="WORKER-TOKEN-1",
            status="active",
            valid_from=date(2026, 1, 1),
            valid_until=None,
            archived_at=None,
            worker=self.worker,
        )

    def list_devices(self, tenant_id: str, filters: TimeCaptureDeviceFilter) -> list[TimeCaptureDevice]:
        rows = [row for row in self.devices.values() if row.tenant_id == tenant_id]
        if not filters.include_archived:
            rows = [row for row in rows if row.archived_at is None]
        if filters.site_id is not None:
            rows = [row for row in rows if row.site_id == filters.site_id]
        if filters.device_type_code is not None:
            rows = [row for row in rows if row.device_type_code == filters.device_type_code]
        if filters.status is not None:
            rows = [row for row in rows if row.status == filters.status]
        return rows

    def get_device(self, tenant_id: str, device_id: str) -> TimeCaptureDevice | None:
        row = self.devices.get(device_id)
        return row if row and row.tenant_id == tenant_id else None

    def get_device_by_code(self, tenant_id: str, device_code: str) -> TimeCaptureDevice | None:
        for row in self.devices.values():
            if row.tenant_id == tenant_id and row.device_code == device_code:
                return row
        return None

    def find_device_by_code(self, tenant_id: str, device_code: str, *, exclude_id: str | None = None) -> TimeCaptureDevice | None:
        for row in self.devices.values():
            if row.tenant_id == tenant_id and row.device_code == device_code and row.id != exclude_id:
                return row
        return None

    def create_device(self, row: TimeCaptureDevice) -> TimeCaptureDevice:
        row.id = row.id or str(uuid4())
        row.created_at = row.created_at or datetime.now(UTC)
        row.updated_at = row.updated_at or row.created_at
        row.version_no = row.version_no or 1
        self.devices[row.id] = row
        return row

    def update_device(self, row: TimeCaptureDevice) -> TimeCaptureDevice:
        row.updated_at = datetime.now(UTC)
        self.devices[row.id] = row
        return row

    def list_policies(self, tenant_id: str, filters) -> list[TimeCapturePolicy]:  # noqa: ANN001
        rows = [row for row in self.policies.values() if row.tenant_id == tenant_id]
        if not filters.include_archived:
            rows = [row for row in rows if row.archived_at is None]
        return rows

    def get_policy(self, tenant_id: str, policy_id: str) -> TimeCapturePolicy | None:
        row = self.policies.get(policy_id)
        return row if row and row.tenant_id == tenant_id else None

    def find_policy_by_code(self, tenant_id: str, policy_code: str, *, exclude_id: str | None = None) -> TimeCapturePolicy | None:
        for row in self.policies.values():
            if row.tenant_id == tenant_id and row.policy_code == policy_code and row.id != exclude_id:
                return row
        return None

    def find_active_policy_for_context(self, tenant_id: str, *, shift_id: str | None, planning_record_id: str | None, patrol_route_id: str | None, site_id: str | None) -> TimeCapturePolicy | None:
        for row in self.policies.values():
            if row.tenant_id != tenant_id or row.archived_at is not None or row.status != "active":
                continue
            if shift_id is not None and row.context_type_code == "shift" and row.shift_id == shift_id:
                return row
            if planning_record_id is not None and row.context_type_code == "planning_record" and row.planning_record_id == planning_record_id:
                return row
            if patrol_route_id is not None and row.context_type_code == "patrol_route" and row.patrol_route_id == patrol_route_id:
                return row
            if site_id is not None and row.context_type_code == "site" and row.site_id == site_id:
                return row
        return None

    def create_policy(self, row: TimeCapturePolicy) -> TimeCapturePolicy:
        row.id = row.id or str(uuid4())
        row.created_at = row.created_at or datetime.now(UTC)
        row.updated_at = row.updated_at or row.created_at
        row.version_no = row.version_no or 1
        self.policies[row.id] = row
        return row

    def update_policy(self, row: TimeCapturePolicy) -> TimeCapturePolicy:
        row.updated_at = datetime.now(UTC)
        self.policies[row.id] = row
        return row

    def list_time_events(self, tenant_id: str, filters: TimeCaptureEventFilter) -> list[TimeEvent]:
        rows = [row for row in self.events.values() if row.tenant_id == tenant_id]
        if not filters.include_archived:
            rows = [row for row in rows if row.archived_at is None]
        return sorted(rows, key=lambda row: row.occurred_at, reverse=True)

    def list_employee_time_events(self, tenant_id: str, employee_id: str, *, limit: int = 30) -> list[TimeEvent]:
        rows = [row for row in self.events.values() if row.tenant_id == tenant_id and row.employee_id == employee_id]
        return sorted(rows, key=lambda row: row.occurred_at, reverse=True)[:limit]

    def get_time_event(self, tenant_id: str, event_id: str) -> TimeEvent | None:
        row = self.events.get(event_id)
        return row if row and row.tenant_id == tenant_id else None

    def get_time_event_by_client_id(self, tenant_id: str, client_event_id: str) -> TimeEvent | None:
        for row in self.events.values():
            if row.tenant_id == tenant_id and row.client_event_id == client_event_id:
                return row
        return None

    def create_time_event(self, row: TimeEvent) -> TimeEvent:
        row.id = row.id or str(uuid4())
        row.created_at = row.created_at or datetime.now(UTC)
        row.updated_at = row.updated_at or row.created_at
        row.version_no = row.version_no or 1
        row.status = row.status or "active"
        self.events[row.id] = row
        return row

    def save_time_event(self, row: TimeEvent) -> TimeEvent:
        row.updated_at = datetime.now(UTC)
        self.events[row.id] = row
        return row

    def get_site(self, tenant_id: str, site_id: str):
        return self.site if tenant_id == self.tenant_id and site_id == self.site.id else None

    def get_shift(self, tenant_id: str, shift_id: str):
        return self.shift if tenant_id == self.tenant_id and shift_id == self.shift.id else None

    def get_assignment(self, tenant_id: str, assignment_id: str):
        for row in (self.employee_assignment, self.worker_assignment):
            if row.tenant_id == tenant_id and row.id == assignment_id:
                return row
        return None

    def find_assignment_for_employee(self, tenant_id: str, shift_id: str, employee_id: str):
        if tenant_id == self.tenant_id and shift_id == "shift-1" and employee_id == "employee-1":
            return self.employee_assignment
        return None

    def find_assignment_for_worker(self, tenant_id: str, shift_id: str, worker_id: str):
        if tenant_id == self.tenant_id and shift_id == "shift-1" and worker_id == "worker-1":
            return self.worker_assignment
        return None

    def find_employee_by_user_id(self, tenant_id: str, user_id: str):
        if tenant_id == self.tenant_id and user_id == "user-employee":
            return self.employee
        return None

    def find_employee_credential_by_encoded_value(self, tenant_id: str, encoded_value: str):
        if tenant_id == self.tenant_id and encoded_value == self.employee_credential.encoded_value:
            return self.employee_credential
        return None

    def find_worker_credential_by_encoded_value(self, tenant_id: str, encoded_value: str):
        if tenant_id == self.tenant_id and encoded_value == self.worker_credential.encoded_value:
            return self.worker_credential
        return None

    def get_planning_record(self, tenant_id: str, planning_record_id: str):
        return self.planning_record if tenant_id == self.tenant_id and planning_record_id == self.planning_record.id else None

    def get_patrol_route(self, tenant_id: str, patrol_route_id: str):
        return self.route if tenant_id == self.tenant_id and patrol_route_id == self.route.id else None


class TimeCaptureServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = _FakeRepo()
        self.audit_repo = _FakeAuditRepository()
        self.service = TimeCaptureService(repository=self.repo, audit_service=AuditService(self.audit_repo))

    def test_create_device_and_policy_with_tenant_context_validation(self) -> None:
        device = self.service.create_device(
            "tenant-1",
            TimeCaptureDeviceCreate(
                device_code="TERM-1",
                label="Gate terminal",
                device_type_code="shared_terminal",
                site_id="site-1",
                access_key="super-secret",
                fixed_ip_cidr="10.0.0.0/24",
            ),
            _admin_actor(),
        )
        self.assertEqual(device.device_code, "TERM-1")
        self.assertTrue(device.has_access_key)

        policy = self.service.create_policy(
            "tenant-1",
            TimeCapturePolicyCreate(
                policy_code="SHIFT-1",
                title="Shift mobile policy",
                context_type_code="shift",
                shift_id="shift-1",
                allow_browser_capture=False,
                allow_mobile_capture=True,
                allow_terminal_capture=True,
                allowed_device_id=device.id,
                enforce_mode_code="reject",
            ),
            _admin_actor(),
        )
        self.assertEqual(policy.context_type_code, "shift")
        self.assertEqual(policy.allowed_device_id, device.id)
        self.assertGreaterEqual(len(self.audit_repo.events), 2)

    def test_employee_mobile_capture_creates_accepted_raw_event(self) -> None:
        created = self.service.capture_employee_event(
            _employee_actor(),
            TimeCaptureEventCapture(
                shift_id="shift-1",
                event_code="clock_in",
                occurred_at=datetime(2026, 3, 20, 8, 0, tzinfo=UTC),
                latitude=52.5,
                longitude=13.4,
                client_event_id="evt-1",
            ),
            source_channel_code="mobile",
            source_ip="10.0.0.25",
        )
        self.assertEqual(created.actor_type_code, "employee")
        self.assertEqual(created.employee_id, "employee-1")
        self.assertEqual(created.assignment_id, "assignment-employee-1")
        self.assertEqual(created.validation_status_code, "accepted")

    def test_rejected_terminal_capture_is_still_persisted(self) -> None:
        device = self.service.create_device(
            "tenant-1",
            TimeCaptureDeviceCreate(
                device_code="TERM-1",
                label="Gate terminal",
                device_type_code="shared_terminal",
                site_id="site-1",
                access_key="secret-123",
                fixed_ip_cidr="10.0.0.0/24",
            ),
            _admin_actor(),
        )
        self.service.create_policy(
            "tenant-1",
            TimeCapturePolicyCreate(
                policy_code="SITE-1",
                title="Site terminal policy",
                context_type_code="site",
                site_id="site-1",
                allow_browser_capture=False,
                allow_mobile_capture=False,
                allow_terminal_capture=True,
                allowed_device_id=device.id,
                allowed_ip_cidr="10.0.0.0/24",
                geofence_latitude=52.5,
                geofence_longitude=13.4,
                geofence_radius_meters=100,
                enforce_mode_code="reject",
            ),
            _admin_actor(),
        )
        with self.assertRaises(ApiException) as exc:
            self.service.capture_terminal_event(
                "tenant-1",
                payload=TimeCaptureTerminalEventCapture(
                    device_code="TERM-1",
                    access_key="secret-123",
                    shift_id="shift-1",
                    event_code="clock_in",
                    raw_token="WORKER-TOKEN-1",
                    scan_medium_code="barcode",
                ),
                source_ip="192.168.1.10",
            )
        self.assertEqual(exc.exception.status_code, 409)
        self.assertEqual(len(self.repo.events), 1)
        stored = next(iter(self.repo.events.values()))
        self.assertEqual(stored.validation_status_code, "rejected")
        self.assertIsNotNone(stored.raw_token_hash)
        self.assertEqual(stored.raw_token_suffix, "EN-1")

    def test_terminal_capture_resolves_subcontractor_worker_credential(self) -> None:
        self.service.create_device(
            "tenant-1",
            TimeCaptureDeviceCreate(
                device_code="TERM-2",
                label="Worker terminal",
                device_type_code="shared_terminal",
                site_id="site-1",
                access_key="secret-456",
            ),
            _admin_actor(),
        )
        read = self.service.capture_terminal_event(
            "tenant-1",
            TimeCaptureTerminalEventCapture(
                device_code="TERM-2",
                access_key="secret-456",
                shift_id="shift-1",
                event_code="clock_in",
                raw_token="WORKER-TOKEN-1",
                scan_medium_code="rfid",
                client_event_id="worker-evt-1",
            ),
            source_ip="10.0.0.8",
        )
        self.assertEqual(read.actor_type_code, "subcontractor_worker")
        self.assertEqual(read.subcontractor_worker_id, "worker-1")
        self.assertEqual(read.assignment_id, "assignment-worker-1")

    def test_duplicate_client_event_is_replay_safe(self) -> None:
        first = self.service.capture_employee_event(
            _employee_actor(),
            TimeCaptureEventCapture(
                shift_id="shift-1",
                event_code="clock_out",
                client_event_id="dup-1",
            ),
            source_channel_code="browser",
            source_ip="10.0.0.1",
        )
        second = self.service.capture_employee_event(
            _employee_actor(),
            TimeCaptureEventCapture(
                shift_id="shift-1",
                event_code="clock_out",
                client_event_id="dup-1",
            ),
            source_channel_code="browser",
            source_ip="10.0.0.1",
        )
        self.assertEqual(first.id, second.id)
        self.assertEqual(len(self.repo.events), 1)

    def test_validation_status_transition_preserves_raw_evidence_payload(self) -> None:
        created = self.service.capture_employee_event(
            _employee_actor(),
            TimeCaptureEventCapture(
                shift_id="shift-1",
                event_code="clock_in",
                occurred_at=datetime(2026, 3, 20, 8, 0, tzinfo=UTC),
                raw_token="EMP-TOKEN-1",
                client_event_id="evt-status-1",
            ),
            source_channel_code="mobile",
            source_ip="10.0.0.25",
        )
        updated = self.service.transition_event_validation_status(
            "tenant-1",
            created.id,
            TimeEventValidationStatusUpdate(
                validation_status_code="flagged",
                reason_code="manual_review",
                note="Late sync review",
                version_no=created.version_no,
            ),
            _admin_actor(),
        )
        self.assertEqual(updated.validation_status_code, "flagged")
        self.assertEqual(updated.occurred_at, created.occurred_at)
        self.assertEqual(updated.raw_token_suffix, created.raw_token_suffix)
        self.assertEqual(updated.event_code, created.event_code)
        self.assertEqual(
            updated.validation_details_json["transitions"][-1]["reason_code"],
            "manual_review",
        )


if __name__ == "__main__":
    unittest.main()
