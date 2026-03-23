from __future__ import annotations

import unittest
from dataclasses import dataclass, field
from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

from app.errors import ApiException
from app.modules.finance.models import ActualAllowance, ActualApproval, ActualComment, ActualExpense, ActualReconciliation, ActualRecord
from app.modules.finance.schemas import (
    ActualAllowanceCreate,
    ActualApprovalActionRequest,
    ActualCommentCreate,
    ActualExpenseCreate,
    ActualReconciliationCreate,
)
from app.modules.finance.service import FinanceActualService
from app.modules.iam.audit_schemas import AuditEventRead
from app.modules.iam.audit_service import AuditService
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext
from tests.modules.field_execution.test_watchbook_flows import _FakeAuditRepository


def _tenant_scope(role: str) -> AuthenticatedRoleScope:
    return AuthenticatedRoleScope(role_key=role, scope_type="tenant")


def _actor(role: str, *, user_id: str, permissions: set[str]) -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id=f"session-{role}",
        user_id=user_id,
        tenant_id="tenant-1",
        role_keys=frozenset({role}),
        permission_keys=frozenset(permissions),
        scopes=(_tenant_scope(role),),
        request_id=f"req-{role}",
    )


@dataclass
class _FakeRepo:
    actuals: dict[str, ActualRecord] = field(default_factory=dict)
    approvals: list[ActualApproval] = field(default_factory=list)
    reconciliations: list[ActualReconciliation] = field(default_factory=list)
    allowances: list[ActualAllowance] = field(default_factory=list)
    expenses: list[ActualExpense] = field(default_factory=list)
    comments: list[ActualComment] = field(default_factory=list)
    audit_events: list[AuditEventRead] = field(default_factory=list)

    def __post_init__(self) -> None:
        planning_record = SimpleNamespace(id="planning-1", dispatcher_user_id="dispatcher-user")
        shift_plan = SimpleNamespace(planning_record=planning_record)
        shift = SimpleNamespace(id="shift-1", shift_plan=shift_plan)
        employee = SimpleNamespace(id="employee-1", user_id="employee-user")
        self.actual = ActualRecord(
            id="actual-1",
            tenant_id="tenant-1",
            assignment_id="assignment-1",
            shift_id="shift-1",
            attendance_record_id="attendance-1",
            actor_type_code="employee",
            employee_id="employee-1",
            subcontractor_worker_id=None,
            planned_start_at=datetime(2026, 3, 20, 8, 0, tzinfo=UTC),
            planned_end_at=datetime(2026, 3, 20, 16, 0, tzinfo=UTC),
            actual_start_at=datetime(2026, 3, 20, 8, 2, tzinfo=UTC),
            actual_end_at=datetime(2026, 3, 20, 16, 4, tzinfo=UTC),
            planned_break_minutes=30,
            actual_break_minutes=30,
            payable_minutes=452,
            billable_minutes=452,
            customer_adjustment_minutes=0,
            discrepancy_state_code="warning",
            discrepancy_codes_json=["late_relief"],
            discrepancy_details_json={"issues": []},
            derivation_status_code="needs_review",
            approval_stage_code="draft",
            derived_at=datetime(2026, 3, 20, 16, 5, tzinfo=UTC),
            is_current=True,
            status="active",
            version_no=1,
            created_at=datetime(2026, 3, 20, 16, 5, tzinfo=UTC),
            updated_at=datetime(2026, 3, 20, 16, 5, tzinfo=UTC),
            created_by_user_id="accounting-user",
            updated_by_user_id="accounting-user",
        )
        self.actual.shift = shift
        self.actual.employee = employee
        self.actual.approvals = []
        self.actual.reconciliations = []
        self.actual.allowances = []
        self.actual.expenses = []
        self.actual.comments = []
        self.actuals[self.actual.id] = self.actual

    def get_assignment(self, tenant_id: str, assignment_id: str):
        return None

    def get_attendance_record(self, tenant_id: str, attendance_record_id: str):
        return None

    def get_current_attendance_for_assignment(self, tenant_id: str, assignment_id: str):
        return None

    def get_actual_record(self, tenant_id: str, actual_record_id: str):
        row = self.actuals.get(actual_record_id)
        return row if row and row.tenant_id == tenant_id else None

    def get_current_actual_for_assignment(self, tenant_id: str, assignment_id: str):
        for row in self.actuals.values():
            if row.tenant_id == tenant_id and row.assignment_id == assignment_id and row.is_current:
                return row
        return None

    def list_actual_records(self, tenant_id: str, filters):
        return [row for row in self.actuals.values() if row.tenant_id == tenant_id]

    def get_employee(self, tenant_id: str, employee_id: str):
        if tenant_id == "tenant-1" and employee_id == "employee-2":
            return SimpleNamespace(id="employee-2")
        return None

    def get_subcontractor_worker(self, tenant_id: str, worker_id: str):
        return None

    def create_actual_record(self, row: ActualRecord) -> ActualRecord:
        self.actuals[row.id] = row
        return row

    def save_actual_record(self, row: ActualRecord) -> ActualRecord:
        row.updated_at = datetime.now(UTC)
        self.actuals[row.id] = row
        return row

    def create_actual_approval(self, row: ActualApproval) -> ActualApproval:
        row.id = row.id or str(uuid4())
        row.created_at = row.created_at or datetime.now(UTC)
        row.updated_at = row.updated_at or row.created_at
        self.approvals.append(row)
        self.actual.approvals.append(row)
        return row

    def create_actual_reconciliation(self, row: ActualReconciliation) -> ActualReconciliation:
        row.id = row.id or str(uuid4())
        row.created_at = row.created_at or datetime.now(UTC)
        row.updated_at = row.updated_at or row.created_at
        self.reconciliations.append(row)
        self.actual.reconciliations.append(row)
        return row

    def create_actual_allowance(self, row: ActualAllowance) -> ActualAllowance:
        row.id = row.id or str(uuid4())
        row.created_at = row.created_at or datetime.now(UTC)
        row.updated_at = row.updated_at or row.created_at
        self.allowances.append(row)
        self.actual.allowances.append(row)
        return row

    def create_actual_expense(self, row: ActualExpense) -> ActualExpense:
        row.id = row.id or str(uuid4())
        row.created_at = row.created_at or datetime.now(UTC)
        row.updated_at = row.updated_at or row.created_at
        self.expenses.append(row)
        self.actual.expenses.append(row)
        return row

    def create_actual_comment(self, row: ActualComment) -> ActualComment:
        row.id = row.id or str(uuid4())
        row.created_at = row.created_at or datetime.now(UTC)
        row.updated_at = row.updated_at or row.created_at
        self.comments.append(row)
        self.actual.comments.append(row)
        return row

    def list_audit_events_for_actual_record(self, tenant_id: str, actual_record_id: str) -> list[AuditEventRead]:
        return list(self.audit_events)


class FinanceActualApprovalFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = _FakeRepo()
        self.audit_repo = _FakeAuditRepository()
        self.service = FinanceActualService(self.repo, AuditService(self.audit_repo))
        self.employee_actor = _actor("employee_user", user_id="employee-user", permissions={"portal.employee.access"})
        self.dispatcher_actor = _actor(
            "dispatcher",
            user_id="dispatcher-user",
            permissions={"finance.actual.read", "finance.actual.write", "finance.approval.write"},
        )
        self.accounting_actor = _actor(
            "accounting",
            user_id="accounting-user",
            permissions={"finance.actual.read", "finance.actual.write", "finance.approval.write", "finance.approval.signoff"},
        )

    def test_employee_can_submit_preliminary_for_own_actual(self) -> None:
        read = self.service.submit_employee_preliminary_actual(
            "actual-1",
            ActualApprovalActionRequest(note_text="Vorlaeufig bestaetigt"),
            self.employee_actor,
        )
        self.assertEqual(read.approval_stage_code, "preliminary_submitted")
        self.assertEqual(read.approvals[0].actor_scope_code, "employee_self")

    def test_dispatcher_can_operationally_confirm_with_scope(self) -> None:
        self.service.submit_preliminary_actual(
            "tenant-1",
            "actual-1",
            ActualApprovalActionRequest(note_text="Feldleitung"),
            self.dispatcher_actor,
        )
        read = self.service.confirm_operational_actual(
            "tenant-1",
            "actual-1",
            ActualApprovalActionRequest(note_text="Operativ bestaetigt"),
            self.dispatcher_actor,
        )
        self.assertEqual(read.approval_stage_code, "operational_confirmed")
        self.assertEqual(read.approvals[-1].stage_code, "operational_confirmed")

    def test_forbidden_cross_scope_preliminary_submit_is_rejected(self) -> None:
        rogue = _actor("employee_user", user_id="other-user", permissions={"portal.employee.access"})
        with self.assertRaises(ApiException) as ctx:
            self.service.submit_employee_preliminary_actual("actual-1", ActualApprovalActionRequest(), rogue)
        self.assertEqual(ctx.exception.status_code, 403)

    def test_finance_reconciliation_replacement_preserves_history_and_updates_minutes(self) -> None:
        self.service.submit_preliminary_actual("tenant-1", "actual-1", ActualApprovalActionRequest(), self.dispatcher_actor)
        self.service.confirm_operational_actual("tenant-1", "actual-1", ActualApprovalActionRequest(), self.dispatcher_actor)
        read = self.service.add_reconciliation(
            "tenant-1",
            "actual-1",
            ActualReconciliationCreate(
                reconciliation_kind_code="replacement",
                reason_code="replacement_guard",
                payroll_minutes_delta=30,
                billable_minutes_delta=15,
                replacement_actor_type_code="employee",
                replacement_employee_id="employee-2",
                note_text="Spaete Ablosung",
            ),
            self.accounting_actor,
        )
        self.assertEqual(read.payable_minutes, 482)
        self.assertEqual(read.billable_minutes, 467)
        self.assertEqual(read.reconciliations[0].replacement_employee_id, "employee-2")

    def test_allowance_expense_comment_and_finance_signoff_attach_to_actual(self) -> None:
        self.service.submit_preliminary_actual("tenant-1", "actual-1", ActualApprovalActionRequest(), self.dispatcher_actor)
        self.service.confirm_operational_actual("tenant-1", "actual-1", ActualApprovalActionRequest(), self.dispatcher_actor)
        self.service.add_allowance(
            "tenant-1",
            "actual-1",
            ActualAllowanceCreate(line_type_code="allowance", reason_code="night_bonus", amount_total=25),
            self.accounting_actor,
        )
        self.service.add_expense(
            "tenant-1",
            "actual-1",
            ActualExpenseCreate(expense_type_code="travel", reason_code="parking", amount_total=12.5),
            self.accounting_actor,
        )
        self.service.add_comment(
            "tenant-1",
            "actual-1",
            ActualCommentCreate(visibility_code="shared", note_text="Mit Kunde abgestimmt"),
            self.accounting_actor,
        )
        read = self.service.finance_signoff_actual(
            "tenant-1",
            "actual-1",
            ActualApprovalActionRequest(note_text="Final geprueft"),
            self.accounting_actor,
        )
        self.assertEqual(read.approval_stage_code, "finance_signed_off")
        self.assertEqual(len(read.allowances), 1)
        self.assertEqual(len(read.expenses), 1)
        self.assertEqual(len(read.comments), 1)


if __name__ == "__main__":
    unittest.main()
