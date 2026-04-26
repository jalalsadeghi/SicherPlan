"""Verified UI page-help intent detection helpers."""

from __future__ import annotations

from dataclasses import dataclass
_CREATE_EMPLOYEE_KEYWORDS = (
    "create employee",
    "new employee",
    "employee file",
    "create a new employee",
    "create a employee",
    "mitarbeiter anlegen",
    "mitarbeiterakte",
    "neuen employee",
    "employee anlegen",
    "employee neu",
    "employee registrieren",
    "employee ثبت",
    "کارمند",
    "ثبت",
    "employee جدید",
)


def is_employee_create_question(message: str) -> bool:
    lowered = message.strip().casefold()
    if not lowered:
        return False
    if any(token in lowered for token in ("shift", "schicht", "شیفت", "شفت", "صیفت", "assign", "assgin", "اختصاص", "تخصیص", "نسبت", "نصبت", "order", "auftrag", "سفارش", "پروژه")):
        return False
    if "employee" in lowered and any(
        token in lowered
        for token in ("create", "new", "anlegen", "neuen", "register", "registrieren", "ثبت", "چطور", "wie")
    ):
        return True
    return any(keyword in lowered for keyword in _CREATE_EMPLOYEE_KEYWORDS)


@dataclass(frozen=True)
class UiHowToIntent:
    intent: str
    page_id: str


def detect_ui_howto_intent(message: str) -> UiHowToIntent | None:
    if is_employee_create_question(message):
        return UiHowToIntent(intent="create_employee", page_id="E-01")
    return None
