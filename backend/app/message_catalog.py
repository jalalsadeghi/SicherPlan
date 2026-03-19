"""Stable message-key catalog for API/client localization."""

from __future__ import annotations

from collections.abc import Mapping

DEFAULT_LOCALE = "de"
FALLBACK_LOCALE = "en"

MESSAGES: Mapping[str, Mapping[str, str]] = {
    "de": {
        "errors.platform.internal": "Es ist ein interner Plattformfehler aufgetreten.",
    },
    "en": {
        "errors.platform.internal": "An internal platform error has occurred.",
    },
}


def translate_message(message_key: str, locale: str = DEFAULT_LOCALE) -> str:
    """Return a localized message for known API message keys."""

    normalized = locale.split("-")[0].lower()
    catalog = MESSAGES.get(normalized, MESSAGES[FALLBACK_LOCALE])
    fallback_catalog = MESSAGES[FALLBACK_LOCALE]
    return catalog.get(message_key) or fallback_catalog.get(message_key) or message_key
