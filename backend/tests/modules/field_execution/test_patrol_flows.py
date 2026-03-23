from __future__ import annotations

import base64
import unittest
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from types import SimpleNamespace
from uuid import uuid4

from app.modules.field_execution.models import PatrolRound, PatrolRoundEvent, Watchbook, WatchbookEntry
from app.modules.field_execution.patrol_service import PatrolService
from app.modules.field_execution.schemas import (
    PatrolRoundAbortRequest,
    PatrolRoundCaptureAttachment,
    PatrolRoundCaptureRequest,
    PatrolRoundCompleteRequest,
    PatrolRoundStartRequest,
    PatrolSyncEnvelope,
    WatchbookOpenRequest,
)
from app.modules.field_execution.watchbook_service import WatchbookService
from app.modules.iam.audit_service import AuditService
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext
from tests.modules.field_execution.test_watchbook_flows import _FakeAuditRepository, _FakeDocumentService


def _actor() -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id="session-1",
        user_id="user-1",
        tenant_id="tenant-1",
        role_keys=frozenset({"employee_user"}),
        permission_keys=frozenset({"portal.employee.access", "field.patrol.read", "field.patrol.write", "field.watchbook.write"}),
        scopes=(AuthenticatedRoleScope(role_key="employee_user", scope_type="tenant"),),
        request_id="req-1",
    )


@dataclass
class _FakeRepo:
    tenant_id: str = "tenant-1"
    watchbooks: dict[str, Watchbook] = field(default_factory=dict)
    watchbook_entries: dict[str, list[WatchbookEntry]] = field(default_factory=dict)
    patrol_rounds: dict[str, PatrolRound] = field(default_factory=dict)
    patrol_events: dict[str, list[PatrolRoundEvent]] = field(default_factory=dict)
    owner_documents: dict[tuple[str, str, str], list[SimpleNamespace]] = field(default_factory=dict)
    documents: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.employee = SimpleNamespace(id="employee-1", tenant_id=self.tenant_id, user_id="user-1", archived_at=None)
        self.checkpoints = [
            SimpleNamespace(
                id="checkpoint-1",
                tenant_id=self.tenant_id,
                patrol_route_id="route-1",
                sequence_no=1,
                checkpoint_code="CP-1",
                label="Gate",
                scan_type_code="qr",
                expected_token_value="qr-1",
                minimum_dwell_seconds=0,
                archived_at=None,
                latitude=52.5,
                longitude=13.4,
            ),
            SimpleNamespace(
                id="checkpoint-2",
                tenant_id=self.tenant_id,
                patrol_route_id="route-1",
                sequence_no=2,
                checkpoint_code="CP-2",
                label="Fence",
                scan_type_code="nfc",
                expected_token_value="nfc-2",
                minimum_dwell_seconds=0,
                archived_at=None,
                latitude=52.6,
                longitude=13.5,
            ),
        ]
        self.route = SimpleNamespace(
            id="route-1",
            tenant_id=self.tenant_id,
            route_no="ROUTE-1",
            name="Night round",
            checkpoints=self.checkpoints,
        )
        planning_record = SimpleNamespace(
            id="planning-1",
            tenant_id=self.tenant_id,
            patrol_detail=SimpleNamespace(patrol_route=self.route),
            order=SimpleNamespace(id="order-1", customer_id="customer-1", patrol_route=self.route),
            site_detail=SimpleNamespace(site_id="site-1"),
        )
        shift_plan = SimpleNamespace(planning_record_id="planning-1", planning_record=planning_record)
        assignment = SimpleNamespace(id="assignment-1", employee_id="employee-1", assignment_status_code="assigned")
        self.shift = SimpleNamespace(
            id="shift-1",
            tenant_id=self.tenant_id,
            release_state="released",
            starts_at=datetime(2026, 4, 2, 20, 0, tzinfo=UTC),
            ends_at=datetime(2026, 4, 3, 4, 0, tzinfo=UTC),
            shift_plan=shift_plan,
            assignments=[assignment],
            meeting_point="Gate A",
            location_text="Harbor North",
            archived_at=None,
        )
        self.site = SimpleNamespace(id="site-1", tenant_id=self.tenant_id, customer_id="customer-1", watchbook_enabled=True)

    def find_employee_by_user_id(self, tenant_id: str, user_id: str):
        if tenant_id == self.tenant_id and user_id == self.employee.user_id:
            return self.employee
        return None

    def list_released_employee_patrol_shifts(self, tenant_id: str, employee_id: str):
        if tenant_id == self.tenant_id and employee_id == self.employee.id:
            return [self.shift]
        return []

    def get_shift(self, tenant_id: str, row_id: str):
        if tenant_id == self.tenant_id and row_id == self.shift.id:
            return self.shift
        return None

    def get_patrol_route(self, tenant_id: str, patrol_route_id: str):
        if tenant_id == self.tenant_id and patrol_route_id == self.route.id:
            return self.route
        return None

    def list_patrol_checkpoints(self, tenant_id: str, patrol_route_id: str):
        if tenant_id == self.tenant_id and patrol_route_id == self.route.id:
            return list(self.checkpoints)
        return []

    def find_active_patrol_round(self, tenant_id: str, employee_id: str):
        for row in self.patrol_rounds.values():
            if row.tenant_id == tenant_id and row.employee_id == employee_id and row.round_status_code == "active":
                row.events = self.patrol_events.get(row.id, [])
                return row
        return None

    def find_patrol_round_by_sync_token(self, tenant_id: str, offline_sync_token: str):
        for row in self.patrol_rounds.values():
            if row.tenant_id == tenant_id and row.offline_sync_token == offline_sync_token:
                row.events = self.patrol_events.get(row.id, [])
                return row
        return None

    def create_patrol_round(self, row: PatrolRound):
        if row.id is None:
            row.id = str(uuid4())
        row.started_at = row.started_at or datetime.now(UTC)
        row.round_status_code = row.round_status_code or "active"
        row.created_at = row.created_at or datetime.now(UTC)
        row.updated_at = row.updated_at or row.created_at
        row.version_no = row.version_no or 1
        row.events = []
        row.patrol_route = self.route
        row.shift = self.shift
        self.patrol_rounds[row.id] = row
        self.patrol_events[row.id] = []
        return row

    def save_patrol_round(self, row: PatrolRound):
        row.events = self.patrol_events.get(row.id, [])
        row.patrol_route = self.route
        row.shift = self.shift
        self.patrol_rounds[row.id] = row
        return row

    def get_patrol_round(self, tenant_id: str, patrol_round_id: str):
        row = self.patrol_rounds.get(patrol_round_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        row.events = self.patrol_events.get(row.id, [])
        row.patrol_route = self.route
        row.shift = self.shift
        return row

    def get_patrol_event_by_client_id(self, tenant_id: str, patrol_round_id: str, client_event_id: str):
        for row in self.patrol_events.get(patrol_round_id, []):
            if row.tenant_id == tenant_id and row.client_event_id == client_event_id:
                return row
        return None

    def next_patrol_event_sequence(self, tenant_id: str, patrol_round_id: str) -> int:
        return len(self.patrol_events.get(patrol_round_id, [])) + 1

    def create_patrol_event(self, row: PatrolRoundEvent):
        if row.id is None:
            row.id = str(uuid4())
        row.occurred_at = row.occurred_at or datetime.now(UTC)
        row.created_at = row.created_at or row.occurred_at
        if row.checkpoint_id is not None:
            row.checkpoint = next((item for item in self.checkpoints if item.id == row.checkpoint_id), None)
        self.patrol_events.setdefault(row.patrol_round_id, []).append(row)
        self.patrol_rounds[row.patrol_round_id].events = self.patrol_events[row.patrol_round_id]
        return row

    def list_documents_for_owner(self, tenant_id: str, owner_type: str, owner_id: str):
        return self.owner_documents.get((tenant_id, owner_type, owner_id), [])

    def get_document(self, tenant_id: str, document_id: str):
        return self.documents.get(document_id)

    def list_watchbooks(self, tenant_id: str, filters):  # noqa: ANN001
        return list(self.watchbooks.values())

    def get_watchbook(self, tenant_id: str, watchbook_id: str):
        row = self.watchbooks.get(watchbook_id)
        if row is not None:
            row.entries = self.watchbook_entries.get(watchbook_id, [])
        return row

    def find_open_watchbook(self, tenant_id: str, *, context_type: str, log_date, site_id: str | None, order_id: str | None, planning_record_id: str | None):
        for row in self.watchbooks.values():
            if (
                row.tenant_id == tenant_id
                and row.context_type == context_type
                and row.log_date == log_date
                and row.site_id == site_id
                and row.order_id == order_id
                and row.planning_record_id == planning_record_id
                and row.closure_state_code == "open"
            ):
                row.entries = self.watchbook_entries.get(row.id, [])
                return row
        return None

    def create_watchbook(self, row: Watchbook):
        if row.id is None:
            row.id = str(uuid4())
        row.entries = []
        row.review_status_code = row.review_status_code or "pending"
        row.closure_state_code = row.closure_state_code or "open"
        row.customer_visibility_released = bool(row.customer_visibility_released)
        row.subcontractor_visibility_released = bool(row.subcontractor_visibility_released)
        row.customer_participation_enabled = bool(row.customer_participation_enabled)
        row.subcontractor_participation_enabled = bool(row.subcontractor_participation_enabled)
        row.customer_personal_names_released = bool(row.customer_personal_names_released)
        row.created_at = row.created_at or datetime.now(UTC)
        row.updated_at = row.updated_at or datetime.now(UTC)
        row.status = row.status or "active"
        row.version_no = row.version_no or 1
        self.watchbooks[row.id] = row
        self.watchbook_entries[row.id] = []
        return row

    def save_watchbook(self, row: Watchbook):
        row.entries = self.watchbook_entries.get(row.id, [])
        self.watchbooks[row.id] = row
        return row

    def create_entry(self, row: WatchbookEntry):
        if row.id is None:
            row.id = str(uuid4())
        row.created_at = row.created_at or datetime.now(UTC)
        self.watchbook_entries.setdefault(row.watchbook_id, []).append(row)
        self.watchbooks[row.watchbook_id].entries = self.watchbook_entries[row.watchbook_id]
        return row

    def get_site(self, tenant_id: str, row_id: str):
        return self.site if tenant_id == self.tenant_id and row_id == self.site.id else None

    def get_order(self, tenant_id: str, row_id: str):
        if tenant_id == self.tenant_id and row_id == "order-1":
            return self.shift.shift_plan.planning_record.order
        return None

    def get_planning_record(self, tenant_id: str, row_id: str):
        record = self.shift.shift_plan.planning_record
        if tenant_id == self.tenant_id and row_id == record.id:
            return record
        return None

    def get_subcontractor(self, tenant_id: str, subcontractor_id: str):
        return None

    def list_customer_released_watchbooks(self, tenant_id: str, customer_id: str):
        return []

    def list_subcontractor_released_watchbooks(self, tenant_id: str, subcontractor_id: str):
        return []


class PatrolServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = _FakeRepo()
        self.docs = _FakeDocumentService()
        self.repo.owner_documents = self.docs.owner_documents
        self.repo.documents = self.docs.documents
        self.audit_repo = _FakeAuditRepository()
        self.audit = AuditService(self.audit_repo)
        self.watchbook_service = WatchbookService(self.repo, self.docs, self.audit)
        self.service = PatrolService(self.repo, self.docs, self.audit, self.watchbook_service)
        self.actor = _actor()

    def test_start_round_creates_active_round_with_started_event(self) -> None:
        round_read = self.service.start_round(
            self.actor,
            PatrolRoundStartRequest(shift_id="shift-1", patrol_route_id="route-1", offline_sync_token="sync-1"),
        )
        self.assertEqual(round_read.round_status_code, "active")
        self.assertEqual(round_read.total_checkpoint_count, 2)
        self.assertEqual(len(round_read.events), 1)
        self.assertEqual(round_read.events[0].event_type_code, "round_started")

    def test_mismatch_then_manual_capture_keeps_append_only_event_order(self) -> None:
        round_read = self.service.start_round(self.actor, PatrolRoundStartRequest(shift_id="shift-1", patrol_route_id="route-1"))
        round_read = self.service.capture_checkpoint(
            self.actor,
            round_read.id,
            PatrolRoundCaptureRequest(
                checkpoint_id="checkpoint-1",
                scan_method_code="qr",
                token_value="wrong-token",
                client_event_id="cap-1",
            ),
        )
        round_read = self.service.capture_checkpoint(
            self.actor,
            round_read.id,
            PatrolRoundCaptureRequest(
                checkpoint_id="checkpoint-1",
                scan_method_code="manual",
                note="Guard verified checkpoint manually.",
                reason_code="device_unavailable",
                client_event_id="cap-2",
            ),
        )
        self.assertEqual([item.sequence_no for item in round_read.events], [1, 2, 3])
        self.assertEqual(round_read.events[1].event_type_code, "checkpoint_exception")
        self.assertFalse(round_read.events[1].is_policy_compliant)
        self.assertEqual(round_read.events[2].event_type_code, "checkpoint_scanned")
        self.assertEqual(round_read.completed_checkpoint_count, 1)

    def test_abort_round_persists_docs_backed_evidence(self) -> None:
        round_read = self.service.start_round(self.actor, PatrolRoundStartRequest(shift_id="shift-1", patrol_route_id="route-1"))
        aborted = self.service.abort_round(
            self.actor,
            round_read.id,
            PatrolRoundAbortRequest(
                abort_reason_code="checkpoint_blocked",
                note="Route blocked by emergency services.",
                client_event_id="abort-1",
                attachments=[
                    PatrolRoundCaptureAttachment(
                        title="Abort evidence",
                        file_name="abort.txt",
                        content_type="text/plain",
                        content_base64=base64.b64encode(b"blocked").decode("ascii"),
                    )
                ],
            ),
        )
        self.assertEqual(aborted.round_status_code, "aborted")
        final_event = aborted.events[-1]
        linked_docs = self.repo.list_documents_for_owner(self.repo.tenant_id, "field.patrol_round_event", final_event.id)
        self.assertEqual(len(linked_docs), 1)

    def test_complete_round_links_watchbook_summary_and_evaluation(self) -> None:
        round_read = self.service.start_round(self.actor, PatrolRoundStartRequest(shift_id="shift-1", patrol_route_id="route-1"))
        round_read = self.service.capture_checkpoint(
            self.actor,
            round_read.id,
            PatrolRoundCaptureRequest(
                checkpoint_id="checkpoint-1",
                scan_method_code="manual",
                note="Manual checkpoint confirmation.",
                reason_code="nfc_fallback",
                client_event_id="cap-1",
            ),
        )
        round_read = self.service.capture_checkpoint(
            self.actor,
            round_read.id,
            PatrolRoundCaptureRequest(
                checkpoint_id="checkpoint-2",
                scan_method_code="manual",
                note="Second checkpoint confirmed.",
                reason_code="nfc_fallback",
                client_event_id="cap-2",
            ),
        )
        completed = self.service.complete_round(
            self.actor,
            round_read.id,
            PatrolRoundCompleteRequest(note="All checkpoints completed.", client_event_id="done-1"),
        )
        evaluation = self.service.get_evaluation(self.actor, completed.id)
        self.assertEqual(completed.round_status_code, "completed")
        self.assertIsNotNone(completed.watchbook_id)
        self.assertIsNotNone(completed.summary_document_id)
        self.assertEqual(evaluation.compliance_status_code, "compliant")
        self.assertIsNotNone(evaluation.summary_document)
        watchbook = self.repo.get_watchbook(self.repo.tenant_id, completed.watchbook_id)
        self.assertIsNotNone(watchbook)
        self.assertEqual(len(watchbook.entries), 1)
        self.assertIn("completed", watchbook.entries[0].narrative)

    def test_capture_and_completion_replay_are_idempotent(self) -> None:
        round_read = self.service.start_round(
            self.actor,
            PatrolRoundStartRequest(shift_id="shift-1", patrol_route_id="route-1", offline_sync_token="sync-dup"),
        )
        payload = PatrolRoundCaptureRequest(
            checkpoint_id="checkpoint-1",
            scan_method_code="manual",
            note="Offline fallback.",
            reason_code="offline_manual",
            client_event_id="dup-cap-1",
        )
        first = self.service.capture_checkpoint(self.actor, round_read.id, payload)
        second = self.service.capture_checkpoint(self.actor, round_read.id, payload)
        self.assertEqual(len(first.events), len(second.events))
        done = self.service.complete_round(
            self.actor,
            round_read.id,
            PatrolRoundCompleteRequest(note="Done", client_event_id="dup-done-1"),
        )
        repeated = self.service.complete_round(
            self.actor,
            round_read.id,
            PatrolRoundCompleteRequest(note="Done", client_event_id="dup-done-1"),
        )
        self.assertEqual(done.round_status_code, "completed")
        self.assertEqual(repeated.round_status_code, "completed")
        self.assertEqual(len(done.events), len(repeated.events))

    def test_sync_round_sorts_offline_sequence_and_applies_abort(self) -> None:
        round_read = self.service.sync_round(
            self.actor,
            PatrolSyncEnvelope(
                round=PatrolRoundStartRequest(shift_id="shift-1", patrol_route_id="route-1", offline_sync_token="sync-ordered"),
                events=[
                    PatrolRoundCaptureRequest(
                        checkpoint_id="checkpoint-2",
                        scan_method_code="manual",
                        note="Second offline event.",
                        reason_code="offline_manual",
                        client_event_id="sync-cap-2",
                        offline_sequence_no=2,
                    ),
                    PatrolRoundCaptureRequest(
                        checkpoint_id="checkpoint-1",
                        scan_method_code="manual",
                        note="First offline event.",
                        reason_code="offline_manual",
                        client_event_id="sync-cap-1",
                        offline_sequence_no=1,
                    ),
                ],
                abort_request=PatrolRoundAbortRequest(
                    abort_reason_code="manual_stop",
                    note="Stopped after second checkpoint.",
                    client_event_id="sync-abort-1",
                    offline_sequence_no=3,
                ),
            ),
        )
        scanned_ids = [item.checkpoint_id for item in round_read.events if item.event_type_code == "checkpoint_scanned"]
        self.assertEqual(scanned_ids, ["checkpoint-1", "checkpoint-2"])
        self.assertEqual(round_read.round_status_code, "aborted")

    def test_patrol_round_metadata_exposes_composite_tenant_unique_key(self) -> None:
        constraints = {constraint.name for constraint in PatrolRound.__table__.constraints}
        self.assertIn("uq_field_patrol_round_tenant_id_id", constraints)


if __name__ == "__main__":
    unittest.main()
