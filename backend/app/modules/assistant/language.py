"""Deterministic language detection and response-language helpers."""

from __future__ import annotations

import re


_PERSIAN_CHAR_RE = re.compile(r"[\u0600-\u06FF]")
_LATIN_WORD_RE = re.compile(r"[A-Za-zÄÖÜäöüß]+")

_PERSIAN_WORDS = {
    "من",
    "چطور",
    "چگونه",
    "مشکل",
    "کارمند",
    "شیفت",
    "نمایش",
    "پلتفرم",
}
_GERMAN_WORDS = {
    "ich",
    "wie",
    "was",
    "warum",
    "passiert",
    "nicht",
    "mitarbeiter",
    "schicht",
    "angezeigt",
    "freigeben",
    "für",
    "wurde",
    "gespeichert",
}
_ENGLISH_HINTS = {
    "the",
    "why",
    "how",
    "shift",
    "employee",
    "not",
    "visible",
    "message",
    "stored",
}

_TECHNICAL_UI_LOCALE_ENGLISH_TERMS = _ENGLISH_HINTS | {
    "api",
    "app",
    "assignment",
    "catalog",
    "customer",
    "customers",
    "dispatch",
    "login",
    "password",
    "planning",
    "portal",
    "registry",
    "route",
    "sdk",
    "staffing",
    "status",
    "tool",
}

_PERSIAN_RESPONSE = (
    "پیام شما ذخیره شد و ساختار پاسخ Assistant فعال است. "
    "موتور کامل پاسخ‌دهی در تسک‌های بعدی متصل می‌شود."
)
_GERMAN_RESPONSE = (
    "Ihre Nachricht wurde gespeichert und der strukturierte Antwortvertrag des Assistant ist aktiv. "
    "Die vollständige Antwortlogik wird in den nächsten Tasks angebunden."
)
_ENGLISH_RESPONSE = (
    "Your message was stored and the Assistant structured response contract is active. "
    "The full response engine will be connected in the next tasks."
)

_PERSIAN_DIAGNOSIS_FINDING = "پاسخ ساختاریافتهٔ موقت Assistant فعال است."
_PERSIAN_DIAGNOSIS_EVIDENCE = "اتصال Provider، Tool و Knowledge در این تسک هنوز فعال نشده است."
_GERMAN_DIAGNOSIS_FINDING = "Der strukturierte Platzhaltermodus des Assistant ist aktiv."
_GERMAN_DIAGNOSIS_EVIDENCE = (
    "Provider-, Tool- und Knowledge-Integrationen sind in diesem Task noch nicht angebunden."
)
_ENGLISH_DIAGNOSIS_FINDING = "Structured response placeholder active."
_ENGLISH_DIAGNOSIS_EVIDENCE = "Provider, tool, and knowledge integrations are not connected in this step."
_PERSIAN_OUT_OF_SCOPE = (
    "من فقط برای پاسخ به سوالات و مشکلات شما در خصوص پلتفرم SicherPlan طراحی شده‌ام. "
    "لطفاً سوال خود را درباره کار با پلتفرم، برنامه‌ریزی، کارکنان، شیفت‌ها، عملیات، مالی، گزارش‌ها یا پورتال‌ها مطرح کنید."
)
_GERMAN_OUT_OF_SCOPE = (
    "Ich bin nur dafür vorgesehen, Fragen und Probleme zur SicherPlan-Plattform zu beantworten. "
    "Bitte stellen Sie Ihre Frage zu Bedienung, Planung, Mitarbeitenden, Schichten, Einsätzen, "
    "Finanzen, Berichten oder Portalen in SicherPlan."
)
_ENGLISH_OUT_OF_SCOPE = (
    "I am designed only to answer questions and troubleshoot issues related to the SicherPlan platform. "
    "Please ask about platform usage, planning, employees, shifts, operations, finance, reports, or portals in SicherPlan."
)
_PERSIAN_UNSAFE = (
    "من نمی‌توانم دستورهایی را اجرا کنم که قوانین امنیتی SicherPlan، سطح دسترسی، محدوده Tenant "
    "یا سیاست‌های Assistant را دور بزند. لطفاً سوالی درباره پلتفرم و در محدوده دسترسی فعلی خود مطرح کنید."
)
_GERMAN_UNSAFE = (
    "Ich kann keine Anweisungen ausführen, die SicherPlan-Sicherheitsregeln, Berechtigungen, Tenant-Scope "
    "oder Assistant-Richtlinien umgehen. Bitte stellen Sie eine Frage zur Plattform innerhalb Ihrer aktuellen Zugriffsrechte."
)
_ENGLISH_UNSAFE = (
    "I cannot follow instructions that bypass SicherPlan security rules, permissions, tenant scope, "
    "or assistant policy. Please ask a question about the platform within your current access rights."
)


def normalize_language_code(language_code: str | None) -> str | None:
    if language_code is None:
        return None
    cleaned = language_code.strip().lower()
    if not cleaned:
        return None
    if "-" in cleaned:
        cleaned = cleaned.split("-", 1)[0]
    if cleaned in {"fa", "de", "en"}:
        return cleaned
    return cleaned


def detect_message_language(text: str, ui_locale: str | None = None) -> str:
    cleaned = text.strip()
    if not cleaned:
        return choose_response_language("unknown", ui_locale)
    normalized_ui = normalize_language_code(ui_locale)
    latin_words = _LATIN_WORD_RE.findall(cleaned)
    normalized_latin_words = {word.lower() for word in latin_words}

    persian_chars = len(_PERSIAN_CHAR_RE.findall(cleaned))
    persian_word_hits = sum(1 for word in _PERSIAN_WORDS if word in cleaned)
    if persian_chars >= 3 or persian_word_hits > 0:
        return "fa"

    lower_text = cleaned.lower()
    german_score = 0
    if any(char in lower_text for char in ("ä", "ö", "ü", "ß")):
        german_score += 3
    german_score += sum(1 for word in _GERMAN_WORDS if word in normalized_latin_words)

    english_score = sum(1 for word in _ENGLISH_HINTS if word in normalized_latin_words)
    if (
        normalized_ui in {"fa", "de"}
        and normalized_latin_words
        and len(normalized_latin_words) <= 6
        and normalized_latin_words.issubset(_TECHNICAL_UI_LOCALE_ENGLISH_TERMS)
    ):
        return normalized_ui
    if german_score > english_score and german_score > 0:
        return "de"
    if latin_words:
        if german_score > 0:
            return "de"
        return choose_response_language("en", ui_locale)

    return choose_response_language("unknown", ui_locale)


def choose_response_language(detected_language: str, ui_locale: str | None = None) -> str:
    normalized_detected = normalize_language_code(detected_language)
    if normalized_detected in {"fa", "de", "en"}:
        return normalized_detected
    normalized_ui = normalize_language_code(ui_locale)
    if normalized_ui in {"fa", "de", "en"}:
        return normalized_ui
    if normalized_detected:
        return normalized_detected
    return "unknown"


def language_instruction(language_code: str) -> str:
    resolved = choose_response_language(language_code)
    return (
        "You must answer in the same language used by the user. "
        f"The detected language is: {resolved}. "
        "Keep technical SicherPlan terms unchanged when translation would reduce clarity."
    )


def placeholder_answer(language_code: str) -> str:
    resolved = choose_response_language(language_code)
    if resolved == "fa":
        return _PERSIAN_RESPONSE
    if resolved == "de":
        return _GERMAN_RESPONSE
    return _ENGLISH_RESPONSE


def placeholder_diagnosis(language_code: str) -> tuple[str, str]:
    resolved = choose_response_language(language_code)
    if resolved == "fa":
        return (_PERSIAN_DIAGNOSIS_FINDING, _PERSIAN_DIAGNOSIS_EVIDENCE)
    if resolved == "de":
        return (_GERMAN_DIAGNOSIS_FINDING, _GERMAN_DIAGNOSIS_EVIDENCE)
    return (_ENGLISH_DIAGNOSIS_FINDING, _ENGLISH_DIAGNOSIS_EVIDENCE)


def out_of_scope_refusal(language_code: str) -> str:
    resolved = choose_response_language(language_code)
    if resolved == "fa":
        return _PERSIAN_OUT_OF_SCOPE
    if resolved == "de":
        return _GERMAN_OUT_OF_SCOPE
    return _ENGLISH_OUT_OF_SCOPE


def unsafe_refusal(language_code: str) -> str:
    resolved = choose_response_language(language_code)
    if resolved == "fa":
        return _PERSIAN_UNSAFE
    if resolved == "de":
        return _GERMAN_UNSAFE
    return _ENGLISH_UNSAFE
