"""Safe source loading for assistant knowledge ingestion."""

from __future__ import annotations

import fnmatch
import hashlib
from pathlib import Path

from app.modules.assistant.knowledge.types import (
    DEFAULT_MAX_FILE_SIZE_BYTES,
    DEFERRED_SOURCE_TYPES,
    LoadedKnowledgeSource,
    KnowledgeSourceNotAllowedError,
    KnowledgeSourceRegistration,
    KnowledgeSourceTooLargeError,
    SUPPORTED_SOURCE_TYPES,
    UnsupportedKnowledgeSourceError,
)
from app.modules.assistant.language import detect_message_language


BLOCKED_FILE_PATTERNS = (
    ".env",
    "*.pem",
    "*.key",
    "*.p12",
    "*.pfx",
    "*secret*",
    "*token*",
    "*credential*",
    "*.sqlite",
    "*.db",
    "*.dump",
)

ALLOWED_SUFFIXES = {".md", ".txt", ".json", ".yaml", ".yml"}


class KnowledgeSourceLoader:
    def __init__(
        self,
        *,
        allowed_roots: list[Path] | tuple[Path, ...],
        max_file_size_bytes: int = DEFAULT_MAX_FILE_SIZE_BYTES,
    ) -> None:
        self.allowed_roots = tuple(path.resolve() for path in allowed_roots)
        self.max_file_size_bytes = max_file_size_bytes

    def load(self, registration: KnowledgeSourceRegistration) -> LoadedKnowledgeSource:
        if registration.source_type in DEFERRED_SOURCE_TYPES:
            raise UnsupportedKnowledgeSourceError(
                f"{registration.source_type.upper()} extraction is not implemented in this ingestion adapter yet."
            )
        if registration.source_type not in SUPPORTED_SOURCE_TYPES:
            raise UnsupportedKnowledgeSourceError(
                f"Unsupported knowledge source type: {registration.source_type}."
            )

        resolved_path = self._resolve_allowed_path(registration.path_obj)
        self._ensure_not_blocked(resolved_path)
        if resolved_path.suffix.lower() not in ALLOWED_SUFFIXES:
            raise UnsupportedKnowledgeSourceError(
                f"Unsupported knowledge file type: {resolved_path.suffix or '<none>'}."
            )

        size_bytes = resolved_path.stat().st_size
        if size_bytes > self.max_file_size_bytes:
            raise KnowledgeSourceTooLargeError(
                f"Knowledge source exceeds max size of {self.max_file_size_bytes} bytes."
            )

        raw_bytes = resolved_path.read_bytes()
        try:
            content = raw_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise UnsupportedKnowledgeSourceError("Knowledge source must be valid UTF-8 text.") from exc

        normalized_content = _normalize_content(content)
        source_hash = hashlib.sha256(normalized_content.encode("utf-8")).hexdigest()
        language_code = detect_message_language(normalized_content[:4000]) if normalized_content.strip() else None
        return LoadedKnowledgeSource(
            source_type=registration.source_type,
            source_name=registration.source_name,
            source_path=str(resolved_path),
            content=normalized_content,
            source_hash=source_hash,
            source_version=source_hash[:12],
            language_code=language_code,
        )

    def _resolve_allowed_path(self, path: Path) -> Path:
        resolved_path = path.resolve()
        if any(root == resolved_path or root in resolved_path.parents for root in self.allowed_roots):
            return resolved_path
        raise KnowledgeSourceNotAllowedError("Knowledge source path is outside allowed ingestion roots.")

    @staticmethod
    def _ensure_not_blocked(path: Path) -> None:
        normalized_name = path.name.lower()
        for pattern in BLOCKED_FILE_PATTERNS:
            if fnmatch.fnmatch(normalized_name, pattern.lower()):
                raise KnowledgeSourceNotAllowedError("Knowledge source path is blocked by policy.")


def _normalize_content(content: str) -> str:
    normalized_lines = [line.rstrip() for line in content.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    return "\n".join(normalized_lines).strip() + ("\n" if normalized_lines else "")
