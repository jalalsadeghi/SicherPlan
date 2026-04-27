"""Proactive diagnostic prefetch planning for known assistant scenarios."""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any

from app.modules.assistant.diagnostics import extract_shift_visibility_input


@dataclass(frozen=True)
class AssistantDiagnosticPrefetchPlan:
    intent: str
    employee_name: str | None = None
    employee_ref: str | None = None
    assignment_ref: str | None = None
    shift_ref: str | None = None
    date_iso: str | None = None
    route_context: dict[str, Any] | None = None
    missing_inputs: tuple[str, ...] = ()
    likely_page_ids: tuple[str, ...] = ("E-01", "P-03", "P-04", "P-05", "ES-01")
    likely_module_keys: tuple[str, ...] = ("employees", "planning", "field_execution")
    generic_check_sequence: tuple[str, ...] = (
        "current_user_capabilities",
        "accessible_pages",
        "employee_mobile_access",
        "assignment_status",
        "shift_release_state",
        "shift_visibility_flags",
        "released_schedule_visibility",
    )
    checks_missing_input: tuple[str, ...] = field(default_factory=tuple)

    def to_retrieval_fields(self) -> dict[str, Any]:
        return {
            "diagnostic_intent": self.intent,
            "diagnostic_missing_inputs": list(self.missing_inputs),
            "diagnostic_checks_missing_input": list(self.checks_missing_input),
        }


_MOBILE_APP_PATTERNS: list[tuple[str, tuple[re.Pattern[str], ...]]] = [
    (
        "employee_shift_not_visible_in_mobile_app",
        (
            re.compile(
                r"(mobile(?:n|r|m|s)?\s*app|mitarbeiter(?:-|\s*)app|employee\s*app|self-service|mobile)",
                re.IGNORECASE,
            ),
            re.compile(
                r"(nicht angezeigt|not visible|nicht sichtbar|not showing|nicht zu sehen|wird .* nicht angezeigt|nicht .* angezeigt|nicht .* app|not .* app)",
                re.IGNORECASE,
            ),
            re.compile(r"(zugewiesen|assigned|assignment|assign|zuordnung|shift|schicht)", re.IGNORECASE),
        ),
    ),
    (
        "employee_assignment_visibility",
        (
            re.compile(r"(assignment|assign|zugewiesen|assigned|zuordnung)", re.IGNORECASE),
            re.compile(r"(sichtbar|visible|angezeigt|showing|displayed)", re.IGNORECASE),
            re.compile(r"(employee|mitarbeiter|app|self-service|mobile(?:n|r|m|s)?)", re.IGNORECASE),
        ),
    ),
    (
        "shift_release_visibility",
        (
            re.compile(r"(release|freigabe|freigegeben|released)", re.IGNORECASE),
            re.compile(
                r"(employee\s*app|mitarbeiter(?:-|\s*)app|mobile(?:n|r|m|s)?\s*app|self-service|mobile)",
                re.IGNORECASE,
            ),
            re.compile(r"(shift|schicht)", re.IGNORECASE),
        ),
    ),
    (
        "employee_app_schedule_visibility",
        (
            re.compile(r"(schedule|dienstplan|einsatzplan|released schedule|schicht)", re.IGNORECASE),
            re.compile(
                r"(employee\s*app|mitarbeiter(?:-|\s*)app|mobile(?:n|r|m|s)?\s*app|self-service|mobile)",
                re.IGNORECASE,
            ),
            re.compile(r"(not visible|nicht sichtbar|nicht angezeigt|not showing|nicht .* angezeigt|nicht .* app|not .* app)", re.IGNORECASE),
        ),
    ),
]

_NEGATIVE_PATTERNS = (
    re.compile(r"\b(weather|wetter|sport|sports)\b", re.IGNORECASE),
)


def detect_diagnostic_prefetch_intent(
    message: str,
    route_context: dict[str, Any] | None = None,
) -> str | None:
    lowered = message.casefold()
    if any(pattern.search(lowered) for pattern in _NEGATIVE_PATTERNS):
        return None
    route_page_id = str((route_context or {}).get("page_id") or "").strip()
    for intent, patterns in _MOBILE_APP_PATTERNS:
        score = sum(1 for pattern in patterns if pattern.search(message))
        if score >= 3:
            return intent
        if route_page_id in {"P-04", "P-05", "E-01", "ES-01"} and score >= 2:
            return intent
    return None


def plan_diagnostic_prefetch(
    *,
    message: str,
    detected_language: str,
    route_context: dict[str, Any] | None,
) -> AssistantDiagnosticPrefetchPlan | None:
    intent = detect_diagnostic_prefetch_intent(message, route_context)
    if intent is None:
        return None
    extracted = extract_shift_visibility_input(
        message=message,
        detected_language=detected_language,
        route_context=route_context,
    )
    employee_name = _clean_text(extracted.employee_name)
    employee_ref = _clean_text(extracted.employee_ref)
    assignment_ref = _clean_text(extracted.assignment_ref)
    shift_ref = _clean_text(extracted.shift_ref)
    date_iso = extracted.date.isoformat() if extracted.date is not None else None

    missing_inputs: list[str] = []
    if employee_name is None and employee_ref is None:
        missing_inputs.append("employee_name")
    if date_iso is None:
        missing_inputs.append("date")
    if shift_ref is None and assignment_ref is None:
        missing_inputs.append("shift_or_assignment_ref")

    checks_missing_input: list[str] = []
    if employee_name is None and employee_ref is None:
        checks_missing_input.extend(
            [
                "employee_search",
                "employee_mobile_access",
                "employee_operational_profile",
            ]
        )
    if date_iso is None:
        checks_missing_input.extend(
            [
                "employee_readiness",
                "planning.find_assignments",
                "planning.find_shifts",
            ]
        )
    if shift_ref is None and assignment_ref is None:
        checks_missing_input.extend(
            [
                "planning.inspect_assignment",
                "planning.inspect_shift_release_state",
                "planning.inspect_shift_visibility",
                "field.inspect_released_schedule_visibility",
            ]
        )

    return AssistantDiagnosticPrefetchPlan(
        intent=intent,
        employee_name=employee_name,
        employee_ref=employee_ref,
        assignment_ref=assignment_ref,
        shift_ref=shift_ref,
        date_iso=date_iso,
        route_context=route_context,
        missing_inputs=tuple(missing_inputs),
        checks_missing_input=tuple(dict.fromkeys(checks_missing_input)),
    )


def _clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None
