"""Provider-safe assistant tool name mapping."""

from __future__ import annotations

import re


_PROVIDER_TOOL_NAME_RE = re.compile(r"^[a-zA-Z0-9_-]+$")
_INVALID_CHAR_RE = re.compile(r"[^a-zA-Z0-9_-]+")


def to_provider_tool_name(internal_name: str) -> str:
    candidate = _INVALID_CHAR_RE.sub("_", internal_name.strip())
    candidate = candidate.strip("_")
    if not candidate:
        return "tool"
    return candidate


def build_provider_tool_name_map(internal_tool_names: list[str]) -> dict[str, str]:
    provider_to_internal: dict[str, str] = {}
    used_names: set[str] = set()
    for internal_name in internal_tool_names:
        base_name = to_provider_tool_name(internal_name)
        provider_name = base_name
        suffix = 2
        while provider_name in used_names:
            provider_name = f"{base_name}_{suffix}"
            suffix += 1
        if not _PROVIDER_TOOL_NAME_RE.match(provider_name):
            raise ValueError(f"Invalid provider tool name generated: {provider_name}")
        used_names.add(provider_name)
        provider_to_internal[provider_name] = internal_name
    return provider_to_internal


def is_valid_provider_tool_name(name: str) -> bool:
    return bool(_PROVIDER_TOOL_NAME_RE.match(name))
