"""Deterministic chunking for assistant knowledge sources."""

from __future__ import annotations

import re

from app.modules.assistant.lexicon import CONCEPT_EXPANSION_TERMS, DOMAIN_LEXICON, detect_domain_concepts
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
API_FAMILY_RE = re.compile(r"\b(customers|planning|platform_services|platform-docs|employees|subcontractors|finance|reporting)\b", re.IGNORECASE)
WORKFLOW_KEY_RE = re.compile(r"\b([a-z]+(?:_[a-z]+){1,5})\b")


def chunk_text(
    *,
    source_type: str | None = None,
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
            detected_language = _detect_chunk_language(
                title=title,
                content=normalized_piece,
                source_language=language_code,
            )
            workflow_keys = _extract_workflow_keys(normalized_piece)
            page_id = _preferred_page_id(
                source_type=source_type,
                title=title,
                content=normalized_piece,
                workflow_keys=workflow_keys,
            )
            module_key = _infer_module_key(page_id=page_id, source_path=source_path)
            domain_terms, language_aliases = _extract_domain_terms_and_aliases(normalized_piece)
            api_families = _extract_api_families(normalized_piece, module_key=module_key, source_type=source_type)
            chunks.append(
                ChunkedKnowledgeDocument(
                    chunk_index=chunk_index,
                    title=title,
                    content=normalized_piece,
                    metadata=ChunkMetadata(
                        title=title,
                        language_code=detected_language,
                        module_key=module_key,
                        page_id=page_id,
                        content_preview=_content_preview(normalized_piece),
                        workflow_keys=workflow_keys,
                        role_keys=[],
                        permission_keys=[],
                        api_families=api_families,
                        domain_terms=domain_terms,
                        language_aliases=language_aliases,
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


def _preferred_page_id(
    *,
    source_type: str | None,
    title: str | None,
    content: str,
    workflow_keys: list[str],
) -> str | None:
    title_page_id = _extract_page_id(title or "")
    if title_page_id:
        return title_page_id
    if source_type == "workflow_help" and workflow_keys:
        workflow_map = {
            "customer_create": "C-01",
            "customer_scoped_order_create": "C-02",
            "customer_order_create": "P-02",
            "customer_plan_create": "P-02",
            "planning_record_create": "P-02",
            "employee_create": "E-01",
            "employee_assign_to_shift": "P-04",
            "employee_assign_to_shift_workflow": "P-04",
            "order_create": "P-02",
            "contract_or_document_register": "PS-01",
            "shift_release_to_employee_app": "P-03",
            "shift_create_or_release": "P-03",
            "actuals_billing_payroll_chain": "FI-01",
        }
        for workflow_key in workflow_keys:
            page_id = workflow_map.get(workflow_key)
            if page_id:
                return page_id
    return _extract_page_id(content)


def _detect_chunk_language(*, title: str | None, content: str, source_language: str | None) -> str:
    if source_language in {"de", "en"}:
        if _has_german_signal(title or "", content) and _has_english_signal(title or "", content):
            return "mixed"
        return source_language
    if _has_german_signal(title or "", content) and _has_english_signal(title or "", content):
        return "mixed"
    return source_language or detect_message_language(content[:4000])


def _has_german_signal(title: str, content: str) -> bool:
    text = f"{title}\n{content}".casefold()
    return any(token in text for token in (" wie ", " und ", " kunden", " mitarbeiter", "auftrag", "schicht", "vertrag", "dokument"))


def _has_english_signal(title: str, content: str) -> bool:
    text = f"{title}\n{content}".casefold()
    return any(token in text for token in (" how ", " and ", " customer", " employee", "order", "shift", "contract", "document"))


def _content_preview(content: str) -> str:
    compact = re.sub(r"\s+", " ", content).strip()
    if len(compact) <= 180:
        return compact
    return compact[:177].rstrip() + "..."


def _extract_workflow_keys(content: str) -> list[str]:
    matches = [match.group(1) for match in WORKFLOW_KEY_RE.finditer(content)]
    return _dedupe_preserve_order(
        [item for item in matches if item in {
            "customer_create",
            "customer_scoped_order_create",
            "customer_order_create",
            "customer_plan_create",
            "planning_record_create",
            "employee_create",
            "employee_assign_to_shift",
            "employee_assign_to_shift_workflow",
            "order_create",
            "contract_or_document_register",
            "shift_release_to_employee_app",
            "shift_create_or_release",
            "actuals_billing_payroll_chain",
        }]
    )


def _extract_api_families(content: str, *, module_key: str | None, source_type: str | None) -> list[str]:
    families = [match.group(1).lower() for match in API_FAMILY_RE.finditer(content)]
    if module_key == "platform_services":
        families.append("platform-docs")
    if module_key:
        families.append(module_key)
    if source_type == "api_export":
        families.append("api-export")
    return _dedupe_preserve_order(families)


def _extract_domain_terms_and_aliases(content: str) -> tuple[list[str], list[str]]:
    concepts = detect_domain_concepts(content)
    domain_terms: list[str] = []
    aliases: list[str] = []
    for concept in concepts:
        domain_terms.extend(CONCEPT_EXPANSION_TERMS.get(concept, ()))
        aliases.extend(DOMAIN_LEXICON.get(concept, ()))
    return _dedupe_preserve_order(domain_terms), _dedupe_preserve_order(aliases)


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


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        cleaned = str(value).strip()
        if not cleaned:
            continue
        key = cleaned.casefold()
        if key in seen:
            continue
        seen.add(key)
        result.append(cleaned)
    return result


__all__ = ["chunk_text", "PAGE_ID_RE", "ROUTE_RE"]
