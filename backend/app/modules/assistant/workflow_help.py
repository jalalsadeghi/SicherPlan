"""Workflow-intent detection and verified grounding facts."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AssistantWorkflowIntent:
    intent: str


@dataclass(frozen=True)
class AssistantWorkflowFactSeed:
    code: str
    title: str
    detail: str
    page_id: str | None = None
    action_key: str | None = None


@dataclass(frozen=True)
class AssistantWorkflowSeed:
    intent: str
    title: str
    facts: tuple[AssistantWorkflowFactSeed, ...]
    linked_page_ids: tuple[str, ...]


def detect_workflow_intent(message: str) -> AssistantWorkflowIntent | None:
    lowered = message.strip().casefold()
    if not lowered:
        return None

    if _is_customer_plan_create(lowered):
        return AssistantWorkflowIntent(intent="customer_plan_create")
    if _is_customer_create(lowered):
        return AssistantWorkflowIntent(intent="customer_create")
    if _is_contract_registration(lowered):
        return AssistantWorkflowIntent(intent="contract_registration")
    if _is_employee_assign_to_shift(lowered):
        return AssistantWorkflowIntent(intent="employee_assign_to_shift_workflow")
    if _is_order_create(lowered):
        return AssistantWorkflowIntent(intent="order_create")
    if _is_shift_create_or_release(lowered):
        return AssistantWorkflowIntent(intent="shift_create_or_release")
    if _is_employee_create(lowered):
        return AssistantWorkflowIntent(intent="employee_create")
    return None


WORKFLOW_HELP_SEEDS: dict[str, AssistantWorkflowSeed] = {
    "customer_create": AssistantWorkflowSeed(
        intent="customer_create",
        title="Customer creation workflow",
        facts=(
            AssistantWorkflowFactSeed(
                code="customer_workspace",
                title="Customer creation starts in the Customers workspace",
                detail="Prime customer master creation belongs to the Customers workspace inside the current tenant.",
                page_id="C-01",
            ),
        ),
        linked_page_ids=("C-01",),
    ),
    "customer_plan_create": AssistantWorkflowSeed(
        intent="customer_plan_create",
        title="Customer planning setup workflow",
        facts=(
            AssistantWorkflowFactSeed(
                code="customer_context_required",
                title="Customer context is created or selected first",
                detail="A customer context must exist before tenant staff can create planning records for that customer.",
                page_id="C-01",
            ),
            AssistantWorkflowFactSeed(
                code="planning_record_workspace",
                title="Planning records and orders are prepared next",
                detail="Customer-facing planning records and order setup continue in Orders & Planning Records.",
                page_id="P-02",
            ),
            AssistantWorkflowFactSeed(
                code="shift_followup_workspace",
                title="Detailed shift planning follows after the planning record exists",
                detail="Detailed shift structure usually continues in Shift Planning after the customer planning record is ready.",
                page_id="P-03",
            ),
        ),
        linked_page_ids=("C-01", "P-02", "P-03"),
    ),
    "employee_create": AssistantWorkflowSeed(
        intent="employee_create",
        title="Employee creation workflow",
        facts=(
            AssistantWorkflowFactSeed(
                code="employee_workspace",
                title="Employees workspace owns employee creation",
                detail="Operational employee master creation starts in the Employees workspace.",
                page_id="E-01",
            ),
            AssistantWorkflowFactSeed(
                code="employee_create_action",
                title="Verified create action exists",
                detail="The verified create action is registered as employees.create.open on the Employees workspace.",
                page_id="E-01",
                action_key="employees.create.open",
            ),
        ),
        linked_page_ids=("E-01",),
    ),
    "employee_assign_to_shift_workflow": AssistantWorkflowSeed(
        intent="employee_assign_to_shift_workflow",
        title="Employee assignment workflow",
        facts=(
            AssistantWorkflowFactSeed(
                code="employee_prerequisite",
                title="Employee record must exist first",
                detail="The employee must exist in the Employees workspace before staffing can assign that person to a shift.",
                page_id="E-01",
            ),
            AssistantWorkflowFactSeed(
                code="order_and_record_context",
                title="Order and planning record context is prepared first",
                detail="Orders and planning records are managed in the Orders & Planning Records workspace.",
                page_id="P-02",
            ),
            AssistantWorkflowFactSeed(
                code="shift_planning_context",
                title="Shift structure is prepared in Shift Planning",
                detail="Concrete shift planning lives in the Shift Planning workspace.",
                page_id="P-03",
            ),
            AssistantWorkflowFactSeed(
                code="staffing_assignment_workspace",
                title="Assignment happens in the Staffing Board",
                detail="Employee-to-shift assignment is performed in the Staffing Board & Coverage workspace.",
                page_id="P-04",
            ),
            AssistantWorkflowFactSeed(
                code="dispatch_and_release_followup",
                title="Release and downstream outputs happen after staffing",
                detail="Dispatch outputs and subcontractor release follow-up are handled in the dispatch and release workspace after staffing decisions are made.",
                page_id="P-05",
            ),
        ),
        linked_page_ids=("E-01", "P-02", "P-03", "P-04", "P-05"),
    ),
    "order_create": AssistantWorkflowSeed(
        intent="order_create",
        title="Order creation workflow",
        facts=(
            AssistantWorkflowFactSeed(
                code="order_workspace",
                title="Orders are created in planning order workspace",
                detail="Customer orders and planning records are handled in the Orders & Planning Records workspace.",
                page_id="P-02",
            ),
            AssistantWorkflowFactSeed(
                code="customer_context",
                title="Customer context is required",
                detail="Order creation depends on an existing customer context and planning record ownership inside the current tenant.",
                page_id="C-01",
            ),
            AssistantWorkflowFactSeed(
                code="followup_shift_planning",
                title="Orders lead into shift planning and staffing",
                detail="After order setup, follow-up work usually continues in Shift Planning and Staffing Board pages.",
                page_id="P-03",
            ),
        ),
        linked_page_ids=("C-01", "P-02", "P-03", "P-04"),
    ),
    "contract_registration": AssistantWorkflowSeed(
        intent="contract_registration",
        title="Contract registration workflow",
        facts=(
            AssistantWorkflowFactSeed(
                code="contract_registration_is_context_dependent",
                title="Contract registration depends on the contract domain",
                detail="The current assistant catalog does not verify one single contract-registration page for all contract types. Customer, employee, subcontractor, and platform contract handling can differ.",
                page_id="PS-01",
            ),
            AssistantWorkflowFactSeed(
                code="platform_services_reference",
                title="Platform Services is the safe shared reference workspace",
                detail="Platform Services is the conservative shared workspace candidate when the exact contract subtype is still unclear.",
                page_id="PS-01",
            ),
            AssistantWorkflowFactSeed(
                code="customer_or_order_context_may_apply",
                title="Customer or order context may still be relevant",
                detail="If the contract belongs to a customer engagement or planning record, related context may also live in Customers or Orders & Planning Records.",
                page_id="C-01",
            ),
        ),
        linked_page_ids=("PS-01", "C-01", "P-02"),
    ),
    "shift_create_or_release": AssistantWorkflowSeed(
        intent="shift_create_or_release",
        title="Shift creation and release workflow",
        facts=(
            AssistantWorkflowFactSeed(
                code="shift_planning_workspace",
                title="Shift setup lives in Shift Planning",
                detail="Concrete shifts are created and edited in the Shift Planning workspace.",
                page_id="P-03",
            ),
            AssistantWorkflowFactSeed(
                code="staffing_visibility_dependency",
                title="Employee-app visibility depends on release and staffing state",
                detail="Shift visibility for employee app depends on release state, staffing state, and downstream visibility checks.",
                page_id="P-04",
            ),
            AssistantWorkflowFactSeed(
                code="release_followup_workspace",
                title="Dispatch outputs and releases are downstream",
                detail="Dispatch outputs and release follow-up are managed in the dispatch and release workspace.",
                page_id="P-05",
            ),
        ),
        linked_page_ids=("P-03", "P-04", "P-05"),
    ),
}


def _is_employee_create(lowered: str) -> bool:
    if any(token in lowered for token in ("shift", "schicht", "شیفت", "شفت", "صیفت", "order", "auftrag", "سفارش", "پروژه")):
        return False
    return (
        ("employee" in lowered or "mitarbeiter" in lowered or "کارمند" in lowered)
        and any(token in lowered for token in ("create", "new", "anlegen", "erstellen", "ثبت", "بساز", "درست"))
    )


def _is_customer_create(lowered: str) -> bool:
    customer_terms = ("customer", "kunde", "kunden", "مشتری")
    create_terms = ("create", "new", "register", "anlegen", "erstellen", "erstelle", "ثبت", "بساز", "درست")
    plan_terms = ("plan", "planung", "planning", "پلن", "برنامه", "auftrag", "order", "سفارش")
    return (
        any(term in lowered for term in customer_terms)
        and any(term in lowered for term in create_terms)
        and not any(term in lowered for term in plan_terms)
    )


def _is_customer_plan_create(lowered: str) -> bool:
    customer_terms = ("customer", "kunde", "kunden", "مشتری")
    plan_terms = ("plan", "planung", "planning", "planning record", "auftrag", "order", "پلن", "برنامه", "سفارش")
    create_terms = ("create", "new", "register", "anlegen", "erstellen", "erstelle", "ثبت", "بساز", "درست")
    return (
        any(term in lowered for term in customer_terms)
        and any(term in lowered for term in plan_terms)
        and any(term in lowered for term in create_terms)
    )


def _is_employee_assign_to_shift(lowered: str) -> bool:
    employee_terms = ("employee", "mitarbeiter", "کارمند")
    shift_terms = ("shift", "schicht", "شیفت", "شفت", "صیفت")
    assign_terms = ("assign", "assgin", "zuweisen", "zuordnung", "اختصاص", "تخصیص", "نسبت", "نصبت")
    return any(term in lowered for term in employee_terms) and any(term in lowered for term in shift_terms) and any(
        term in lowered for term in assign_terms
    )


def _is_order_create(lowered: str) -> bool:
    order_terms = ("order", "auftrag", "سفارش", "پروژه")
    create_terms = ("create", "new", "erstellen", "erstelle", "anlegen", "ثبت", "بساز", "درست")
    return any(term in lowered for term in order_terms) and any(term in lowered for term in create_terms)


def _is_contract_registration(lowered: str) -> bool:
    contract_terms = ("contract", "vertrag", "قرارداد")
    create_terms = ("create", "new", "register", "anlegen", "erstellen", "erstelle", "ثبت", "بساز", "درست")
    return any(term in lowered for term in contract_terms) and any(term in lowered for term in create_terms)


def _is_shift_create_or_release(lowered: str) -> bool:
    shift_terms = ("shift", "schicht", "شیفت", "شفت", "صیفت")
    action_terms = ("create", "release", "freigabe", "sichtbar", "visible", "app", "employee app", "portal", "ثبت", "بساز", "freigeben")
    return any(term in lowered for term in shift_terms) and any(term in lowered for term in action_terms)
