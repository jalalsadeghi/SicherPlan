"""Verified UI page-help helpers and deterministic UI-how-to rendering."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


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


def no_verified_ui_label_message(language_code: str) -> str:
    if language_code == "fa":
        return (
            "می‌توانم روند کلی را بر اساس مستندات SicherPlan توضیح بدهم، "
            "اما نام دقیق دکمه یا Action فعلی این صفحه در UI Action Catalog تأیید نشده است. "
            "برای جلوگیری از راهنمایی اشتباه، نام UI را حدس نمی‌زنم."
        )
    if language_code == "de":
        return (
            "Ich kann den allgemeinen Ablauf anhand der SicherPlan-Dokumentation erklären, "
            "aber die genaue aktuelle Schaltfläche oder UI-Aktion ist im verifizierten UI-Katalog nicht bestätigt. "
            "Ich rate den exakten UI-Label deshalb nicht."
        )
    return (
        "I can explain the workflow from SicherPlan documentation, but the exact current button or UI action "
        "is not confirmed in the verified UI catalog. I will not guess the exact label."
    )


def missing_ui_action_permission_message(language_code: str, permission: str) -> str:
    if language_code == "fa":
        return (
            "در سطح دسترسی فعلی شما، این Action به‌عنوان مجاز تأیید نشد. "
            f"برای این مسیر معمولاً دسترسی `{permission}` لازم است."
        )
    if language_code == "de":
        return (
            "In Ihrer aktuellen Berechtigungsstufe ist diese Aktion nicht als zulässig bestätigt. "
            f"Für diesen Schritt wird in der Regel `{permission}` benötigt."
        )
    return (
        "At your current permission level, this action is not confirmed as allowed. "
        f"This step typically requires `{permission}`."
    )


def render_verified_employee_create_answer(
    *,
    language_code: str,
    manifest: dict[str, Any],
    action: dict[str, Any],
) -> tuple[str, list[str]]:
    sidebar = [item["label"] for item in manifest.get("sidebar_path", []) if item.get("label")]
    sidebar_path = " > ".join(sidebar) if sidebar else manifest.get("page_title", "Employees Workspace")

    form_sections = manifest.get("form_sections", [])
    identity_section = form_sections[0] if form_sections else {}
    fields = identity_section.get("fields", [])
    field_labels = [field["label"] for field in fields if field.get("required")]
    field_summary = ", ".join(f'"{label}"' for label in field_labels[:3])
    action_label = action.get("label", "")
    location = action.get("location") or ""
    section_title = identity_section.get("title") or ""
    next_steps = [step.get("label") for step in manifest.get("post_create_steps", []) if step.get("label")]

    if language_code == "fa":
        answer = (
            f"برای ایجاد یک Employee جدید، وارد {manifest.get('page_title', 'Employees Workspace')} شوید.\n\n"
            "مراحل دقیق:\n"
            f"1. از مسیر {sidebar_path} وارد این صفحه شوید.\n"
            f'2. در {location} روی "{action_label}" کلیک کنید.\n'
            f'3. بخش "{section_title}" باز می‌شود. فیلدهای اجباری مانند {field_summary} را کامل کنید.\n'
            "4. بعد از ذخیره، بخش‌های بعدی آماده‌سازی عملیاتی را بررسی کنید."
        )
    elif language_code == "de":
        answer = (
            f"Um einen neuen Employee anzulegen, öffnen Sie den {manifest.get('page_title', 'Employees Workspace')}.\n\n"
            "Genaue Schritte:\n"
            f"1. Öffnen Sie in der Navigation {sidebar_path}.\n"
            f'2. Klicken Sie {location} auf "{action_label}".\n'
            f'3. Danach öffnen sich die Felder im Abschnitt "{section_title}". Pflichtfelder sind unter anderem {field_summary}.\n'
            "4. Prüfen Sie nach dem Speichern die operativen Folgeschritte."
        )
    else:
        answer = (
            f"To create a new Employee, open the {manifest.get('page_title', 'Employees Workspace')}.\n\n"
            "Exact steps:\n"
            f"1. Open {sidebar_path} in the left navigation.\n"
            f'2. Click "{action_label}" in the {location}.\n'
            f'3. The "{section_title}" section opens. Complete required fields such as {field_summary}.\n'
            "4. After saving, review the follow-up operational setup sections."
        )
    return answer, [step for step in next_steps[:3] if step]


def verified_ui_action_finding(language_code: str) -> str:
    if language_code == "fa":
        return "راهنمای UI بر اساس کاتالوگ تأییدشده ارائه شد."
    if language_code == "de":
        return "Die UI-Anleitung wurde aus dem verifizierten Katalog abgeleitet."
    return "The UI guidance was generated from the verified catalog."


def verified_ui_action_evidence(language_code: str, action_label: str) -> str:
    if language_code == "fa":
        return f'Action تأییدشده "{action_label}" از Page Help Manifest بازیابی شد.'
    if language_code == "de":
        return f'Die verifizierte Aktion "{action_label}" wurde aus dem Page-Help-Manifest geladen.'
    return f'The verified action "{action_label}" was loaded from the page-help manifest.'
