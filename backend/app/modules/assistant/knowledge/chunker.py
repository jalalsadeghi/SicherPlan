"""Deterministic chunking for assistant knowledge sources."""

from __future__ import annotations

import re

from app.modules.assistant.knowledge.types import (
    DEFAULT_CHUNK_OVERLAP_CHARS,
    DEFAULT_MAX_CHUNK_CHARS,
    DEFAULT_MIN_CHUNK_CHARS,
    ChunkMetadata,
    ChunkedKnowledgeDocument,
    PAGE_ID_TO_MODULE_KEY,
)
from app.modules.assistant.language import detect_message_language


HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
PAGE_ID_RE = re.compile(r"\b(?:[A-Z]{1,3}-\d{2})\b")
ROUTE_RE = re.compile(r"(?:/[A-Za-z0-9._~!$&'()*+,;=:@%/-]+|[A-Za-z][A-Za-z0-9]+(?:Route|View|Page))")


def chunk_text(
    *,
    source_name: str,
    content: str,
    source_path: str,
    language_code: str | None = None,
    max_chunk_chars: int = DEFAULT_MAX_CHUNK_CHARS,
    min_chunk_chars: int = DEFAULT_MIN_CHUNK_CHARS,
    chunk_overlap_chars: int = DEFAULT_CHUNK_OVERLAP_CHARS,
) -> list[ChunkedKnowledgeDocument]:
    sections = _split_into_sections(source_name=source_name, content=content)
    chunks: list[ChunkedKnowledgeDocument] = []
    chunk_index = 0
    for title, section_content in sections:
        for piece in _split_section(
            title=title,
            content=section_content,
            max_chunk_chars=max_chunk_chars,
            min_chunk_chars=min_chunk_chars,
            chunk_overlap_chars=chunk_overlap_chars,
        ):
            normalized_piece = piece.strip()
            if not normalized_piece:
                continue
            detected_language = language_code or detect_message_language(normalized_piece[:4000])
            page_id = _extract_page_id(normalized_piece)
            chunks.append(
                ChunkedKnowledgeDocument(
                    chunk_index=chunk_index,
                    title=title,
                    content=normalized_piece,
                    metadata=ChunkMetadata(
                        title=title,
                        language_code=detected_language,
                        module_key=_infer_module_key(page_id=page_id, source_path=source_path),
                        page_id=page_id,
                        role_keys=[],
                        permission_keys=[],
                        token_count=max(len(normalized_piece) // 4, 1),
                    ),
                )
            )
            chunk_index += 1
    return chunks


def _split_into_sections(*, source_name: str, content: str) -> list[tuple[str | None, str]]:
    matches = list(HEADING_RE.finditer(content))
    if not matches:
        return [(source_name, content)]

    sections: list[tuple[str | None, str]] = []
    preamble = content[: matches[0].start()].strip()
    if preamble:
        sections.append((source_name, preamble))
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(content)
        title = match.group(2).strip()
        section_content = content[start:end].strip()
        sections.append((title, section_content))
    return sections


def _split_section(
    *,
    title: str | None,
    content: str,
    max_chunk_chars: int,
    min_chunk_chars: int,
    chunk_overlap_chars: int,
) -> list[str]:
    if len(content) <= max_chunk_chars:
        return [content]

    paragraphs = [paragraph.strip() for paragraph in re.split(r"\n\s*\n", content) if paragraph.strip()]
    if not paragraphs:
        return [content[:max_chunk_chars]]

    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= max_chunk_chars:
            current = candidate
            continue
        if current:
            chunks.append(current)
            overlap = current[-chunk_overlap_chars:] if len(current) > chunk_overlap_chars else current
            current = f"{overlap}\n\n{paragraph}".strip()
        else:
            chunks.extend(_force_split(paragraph, max_chunk_chars=max_chunk_chars, chunk_overlap_chars=chunk_overlap_chars))
            current = ""
    if current:
        chunks.append(current)

    merged: list[str] = []
    for chunk in chunks:
        if merged and len(chunk) < min_chunk_chars and len(merged[-1]) + len(chunk) + 2 <= max_chunk_chars:
            merged[-1] = f"{merged[-1]}\n\n{chunk}".strip()
        else:
            merged.append(chunk)
    if title and merged and not merged[0].lstrip().startswith("#"):
        merged[0] = f"# {title}\n\n{merged[0]}".strip()
    return merged


def _force_split(paragraph: str, *, max_chunk_chars: int, chunk_overlap_chars: int) -> list[str]:
    pieces: list[str] = []
    start = 0
    while start < len(paragraph):
        end = min(start + max_chunk_chars, len(paragraph))
        if end < len(paragraph):
            boundary = paragraph.rfind(" ", start, end)
            if boundary > start + 200:
                end = boundary
        piece = paragraph[start:end].strip()
        if piece:
            pieces.append(piece)
        if end >= len(paragraph):
            break
        start = max(end - chunk_overlap_chars, start + 1)
    return pieces


def _extract_page_id(content: str) -> str | None:
    match = PAGE_ID_RE.search(content)
    return match.group(0) if match else None


def _infer_module_key(*, page_id: str | None, source_path: str) -> str | None:
    if page_id and page_id in PAGE_ID_TO_MODULE_KEY:
        return PAGE_ID_TO_MODULE_KEY[page_id]
    normalized = source_path.lower()
    if "/employees" in normalized:
        return "employees"
    if "/planning" in normalized or "/sprint" in normalized:
        return "planning"
    if "/finance" in normalized:
        return "finance"
    if "/report" in normalized:
        return "reporting"
    if "/portal" in normalized:
        return "portal"
    return None


__all__ = ["chunk_text", "PAGE_ID_RE", "ROUTE_RE"]
