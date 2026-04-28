"""Deterministic field and lookup knowledge corpus for the assistant."""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
import json
from pathlib import Path
import re
from typing import Any
import unicodedata

from app.modules.assistant.page_help_seed import ASSISTANT_PAGE_HELP_SEEDS


_LEGACY_MESSAGES_PATH = Path("web/apps/web-antd/src/sicherplan-legacy/i18n/messages.ts")
_DE_LOCALE_PATH = Path("web/apps/web-antd/src/locales/langs/de-DE/sicherplan.json")
_EN_LOCALE_PATH = Path("web/apps/web-antd/src/locales/langs/en-US/sicherplan.json")
_FA_LOCALE_PATH = Path("web/apps/web-antd/src/locales/langs/fa-IR/sicherplan.json")

_LOCALE_ENTRY_RE = re.compile(r'^\s*"(?P<key>[^"]+)":\s*"(?P<value>(?:[^"\\]|\\.)*)",?\s*$')
_V_MODEL_RE = re.compile(r'v-model(?:\.[a-z]+)?="(?P<model>[^"]+)"')
_LABEL_KEY_RE = re.compile(r't\("(?P<key>[^"]+)"\)')
_INTERFACE_START_RE = re.compile(r"^\s*export interface (?P<name>\w+)\s*\{")
_TS_FIELD_RE = re.compile(r"^\s*(?P<name>[a-zA-Z_]\w*)\??:\s*(?P<type>[^;]+);")
_PY_CLASS_RE = re.compile(r"^\s*class (?P<name>\w+)\(.*\):")
_PY_FIELD_RE = re.compile(r"^\s*(?P<name>[a-zA-Z_]\w*):\s*(?P<type>.+)$")
_SQLA_FIELD_RE = re.compile(r"^\s*(?P<name>[a-zA-Z_]\w*):\s*Mapped\[(?P<type>.+)\]\s*=")
_QUESTION_PREFIXES = (
    "was bedeutet ",
    "was ist ",
    "was heißt ",
    "wofür steht ",
    "wofür ist ",
    "what does ",
    "what is ",
    "what means ",
    "explain ",
    "meaning of ",
    "معنی ",
    "یعنی ",
    "منظور از ",
)
_FIELD_HELP_VAGUE_PHRASES = (
    "dieses feld",
    "this field",
    "this form field",
    "what is this field for",
    "what does this field mean",
    "wofür ist dieses feld",
    "این فیلد",
    "این ستون",
)
_FORM_HELP_TERMS = ("field", "feld", "formularfeld", "form field", "فیلد")
_COLUMN_HELP_TERMS = ("column", "spalte", "table column", "ستون")
_TAB_ACTION_TERMS = (
    "tab",
    "registerkarte",
    "reiter",
    "button",
    "schaltfläche",
    "action",
    "aktion",
)
_LOOKUP_HELP_TERMS = ("lookup", "option", "auswahl", "selection", "catalog", "katalog", "گزینه")
_STATUS_HELP_TERMS = (
    "status",
    "statuscode",
    "freigabestatus",
    "release status",
    "release state",
    "visibility state",
    "وضعیت",
    "وضعیت انتشار",
)
_GENERIC_AMBIGUOUS_LABELS = {"status", "state", "code", "type", "name", "label"}


@dataclass(frozen=True)
class FieldSourceBasis:
    source_type: str
    source_name: str
    evidence: str
    page_id: str | None = None
    module_key: str | None = None


@dataclass
class FieldDefinition:
    field_key: str
    canonical_name: str
    module_key: str | None
    page_id: str | None
    route_names: list[str] = field(default_factory=list)
    entity_type: str | None = None
    form_contexts: list[str] = field(default_factory=list)
    input_type: str | None = None
    required: bool | None = None
    sensitive: bool = False
    labels: dict[str, list[str]] = field(default_factory=dict)
    aliases: list[str] = field(default_factory=list)
    definition_en: str | None = None
    definition_de: str | None = None
    example_values: list[str] = field(default_factory=list)
    related_fields: list[str] = field(default_factory=list)
    source_basis: list[FieldSourceBasis] = field(default_factory=list)
    confidence: str = "low"
    label_keys: list[str] = field(default_factory=list)
    binding_paths: list[str] = field(default_factory=list)
    schema_fields: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class LookupValueDefinition:
    value: str
    labels: dict[str, str] = field(default_factory=dict)
    meaning_de: str | None = None
    meaning_en: str | None = None


@dataclass
class LookupDefinition:
    lookup_key: str
    module_key: str | None
    page_id: str | None
    entity_type: str | None
    labels: dict[str, list[str]] = field(default_factory=dict)
    aliases: list[str] = field(default_factory=list)
    values: list[LookupValueDefinition] = field(default_factory=list)
    value_source_kind: str = "static"
    source_basis: list[FieldSourceBasis] = field(default_factory=list)
    confidence: str = "low"


@dataclass(frozen=True)
class FieldSearchMatch:
    field_key: str
    label: str
    entity_type: str | None
    module_key: str | None
    page_id: str | None
    definition: str | None
    required: bool | None
    confidence: str
    source_basis: list[FieldSourceBasis]
    score: float


@dataclass(frozen=True)
class LookupSearchMatch:
    lookup_key: str
    label: str
    entity_type: str | None
    module_key: str | None
    page_id: str | None
    value_source_kind: str
    source_basis: list[FieldSourceBasis]
    score: float


@dataclass(frozen=True)
class LookupResolvedMatch:
    lookup_key: str
    label: str
    entity_type: str | None
    module_key: str | None
    page_id: str | None
    value_source_kind: str
    source_basis: list[FieldSourceBasis]
    confidence: str
    values: list[LookupValueDefinition]
    matched_values: list[LookupValueDefinition]
    value_resolution: str = "static"
    score: float = 0.0


@dataclass(frozen=True)
class CorpusSignal:
    normalized_query: str
    field_matches: tuple[FieldSearchMatch, ...]
    lookup_matches: tuple[LookupSearchMatch, ...]
    ambiguous: bool
    intent_category: str
    matched_via_route_context: bool = False


@dataclass(frozen=True)
class AssistantFieldLookupCorpus:
    field_definitions: tuple[FieldDefinition, ...]
    lookup_definitions: tuple[LookupDefinition, ...]


def build_field_lookup_corpus(repo_root: Path | None = None) -> AssistantFieldLookupCorpus:
    return _build_field_lookup_corpus(str((repo_root or _repo_root()).resolve()))


@lru_cache(maxsize=4)
def _build_field_lookup_corpus(repo_root_str: str) -> AssistantFieldLookupCorpus:
    repo_root = Path(repo_root_str)
    locale_labels = _extract_locale_labels(repo_root)
    vue_bindings = _extract_vue_field_bindings(repo_root)
    ts_interfaces = _extract_typescript_interfaces(repo_root)
    backend_fields = _extract_backend_fields(repo_root)

    fields: dict[str, FieldDefinition] = {}
    lookups: dict[str, LookupDefinition] = {}

    for seed in ASSISTANT_PAGE_HELP_SEEDS:
        if seed.language_code not in {"de", "en"}:
            continue
        manifest = seed.manifest_json
        route_name = seed.route_name
        workflow_keys = [str(item) for item in manifest.get("workflow_keys", []) if isinstance(item, str)]
        for section in manifest.get("form_sections", []):
            if not isinstance(section, dict):
                continue
            section_key = str(section.get("section_key") or "")
            form_context = section_key or f"{seed.page_id.lower()}_form"
            for field_item in section.get("fields", []):
                if not isinstance(field_item, dict):
                    continue
                canonical_name = _normalize_field_name(str(field_item.get("field_key") or ""))
                field_key, entity_type = _field_identity_from_page(
                    page_id=seed.page_id,
                    canonical_name=canonical_name,
                )
                definition = fields.setdefault(
                    field_key,
                    FieldDefinition(
                        field_key=field_key,
                        canonical_name=canonical_name,
                        module_key=seed.module_key,
                        page_id=seed.page_id,
                        entity_type=entity_type,
                    ),
                )
                _add_label(definition.labels, seed.language_code, str(field_item.get("label") or canonical_name))
                _append_unique(definition.route_names, route_name)
                _append_unique(definition.form_contexts, form_context)
                for workflow_key in workflow_keys:
                    _append_unique(definition.form_contexts, workflow_key)
                definition.required = bool(field_item.get("required", False))
                definition.input_type = definition.input_type or "input"
                _append_unique(definition.aliases, canonical_name)
                _append_unique(definition.aliases, str(field_item.get("label") or canonical_name))
                definition.source_basis.append(
                    FieldSourceBasis(
                        source_type="page_help_manifest",
                        source_name="Assistant Page Help Manifest",
                        page_id=seed.page_id,
                        module_key=seed.module_key,
                        evidence=(
                            f"{seed.page_id} manifest section {section_key or form_context} includes "
                            f"field {canonical_name} labeled {field_item.get('label') or canonical_name}."
                        ),
                    )
                )

    for label_key, label_bundle in locale_labels.items():
        if ".fields." in label_key:
            field_key, canonical_name, module_key, page_id, entity_type = _field_identity_from_label_key(label_key)
            if field_key is None or canonical_name is None:
                continue
            definition = fields.setdefault(
                field_key,
                FieldDefinition(
                    field_key=field_key,
                    canonical_name=canonical_name,
                    module_key=module_key,
                    page_id=page_id,
                    entity_type=entity_type,
                ),
            )
            for language_code, label in label_bundle.items():
                _add_label(definition.labels, language_code, label)
            _append_unique(definition.aliases, canonical_name)
            _append_unique(definition.aliases, label_key)
            _append_unique(definition.label_keys, label_key)
            if page_id is not None and definition.page_id is None:
                definition.page_id = page_id
            if module_key is not None and definition.module_key is None:
                definition.module_key = module_key
            definition.source_basis.append(
                FieldSourceBasis(
                    source_type="frontend_locale",
                    source_name="messages.ts / sicherplan.json",
                    page_id=page_id,
                    module_key=module_key,
                    evidence=f"{label_key} defines labels {', '.join(sorted(label_bundle.values()))}.",
                )
            )
            binding = vue_bindings.get(label_key)
            if binding is not None:
                _append_unique(definition.binding_paths, binding["model"])
                _append_unique(definition.aliases, binding["model"])
                definition.input_type = definition.input_type or binding.get("input_type")
                if binding.get("required") is True:
                    definition.required = True
                definition.source_basis.append(
                    FieldSourceBasis(
                        source_type="frontend_component",
                        source_name=binding["source_name"],
                        page_id=page_id,
                        module_key=module_key,
                        evidence=(
                            f'{binding["source_name"]} binds {binding["model"]} next to {label_key}.'
                        ),
                    )
                )

    for field_key, definition in fields.items():
        entity_candidates = [definition.entity_type or "", definition.canonical_name]
        for source_name, field_names in ts_interfaces.items():
            if definition.canonical_name in field_names:
                _append_unique(definition.schema_fields, f"{source_name}.{definition.canonical_name}")
                definition.source_basis.append(
                    FieldSourceBasis(
                        source_type="typescript_api_interface",
                        source_name=source_name,
                        page_id=definition.page_id,
                        module_key=definition.module_key,
                        evidence=f"{source_name} includes field {definition.canonical_name}.",
                    )
                )
        for source_name, field_names in backend_fields.items():
            if definition.canonical_name in field_names:
                _append_unique(definition.schema_fields, f"{source_name}.{definition.canonical_name}")
                definition.source_basis.append(
                    FieldSourceBasis(
                        source_type="backend_schema",
                        source_name=source_name,
                        page_id=definition.page_id,
                        module_key=definition.module_key,
                        evidence=f"{source_name} includes field {definition.canonical_name}.",
                    )
                )
        _append_related_fields(definition, fields)
        _set_default_field_definition_text(definition)
        definition.confidence = _field_confidence(definition)
        for label_list in definition.labels.values():
            for label in label_list:
                _append_unique(definition.aliases, label)
        for entity_candidate in entity_candidates:
            if entity_candidate:
                _append_unique(definition.aliases, entity_candidate)

    _add_manual_field_definitions(fields)
    lookups.update(_build_lookup_definitions(locale_labels, vue_bindings))
    for lookup in lookups.values():
        lookup.confidence = _lookup_confidence(lookup)

    return AssistantFieldLookupCorpus(
        field_definitions=tuple(sorted(fields.values(), key=lambda item: item.field_key)),
        lookup_definitions=tuple(sorted(lookups.values(), key=lambda item: item.lookup_key)),
    )


def detect_field_or_lookup_signal(
    text: str,
    *,
    page_id: str | None = None,
    route_name: str | None = None,
) -> CorpusSignal | None:
    normalized_query = _extract_field_probe(text)
    route_context_form_help = _is_route_context_form_help_question(
        text=text,
        page_id=page_id,
        route_name=route_name,
    )
    if normalized_query is None:
        if route_context_form_help:
            return CorpusSignal(
                normalized_query="",
                field_matches=(),
                lookup_matches=(),
                ambiguous=True,
                intent_category="form_help_question",
                matched_via_route_context=True,
            )
        return None
    field_matches = search_field_dictionary(
        query=normalized_query,
        language_code=None,
        page_id=page_id,
        route_name=route_name,
        limit=5,
    )
    lookup_matches = search_lookup_dictionary(
        query=normalized_query,
        language_code=None,
        page_id=page_id,
        route_name=route_name,
        limit=5,
    )
    if not field_matches and not lookup_matches:
        if route_context_form_help:
            return CorpusSignal(
                normalized_query=normalized_query,
                field_matches=(),
                lookup_matches=(),
                ambiguous=True,
                intent_category="form_help_question",
                matched_via_route_context=True,
            )
        return None
    ambiguous = _is_ambiguous_signal(
        normalized_query=normalized_query,
        field_matches=field_matches,
        lookup_matches=lookup_matches,
    )
    return CorpusSignal(
        normalized_query=normalized_query,
        field_matches=tuple(field_matches),
        lookup_matches=tuple(lookup_matches),
        ambiguous=ambiguous,
        intent_category=_infer_field_lookup_intent_category(
            text=text,
            normalized_query=normalized_query,
            field_matches=field_matches,
            lookup_matches=lookup_matches,
            route_context_form_help=route_context_form_help,
        ),
        matched_via_route_context=route_context_form_help and not field_matches and not lookup_matches,
    )


def search_field_dictionary(
    *,
    query: str,
    language_code: str | None,
    page_id: str | None,
    route_name: str | None,
    limit: int = 5,
    repo_root: Path | None = None,
) -> list[FieldSearchMatch]:
    normalized_query = _extract_field_probe(query) or _normalize_query(query)
    if not normalized_query:
        return []
    corpus = build_field_lookup_corpus(repo_root)
    matches: list[FieldSearchMatch] = []
    for definition in corpus.field_definitions:
        score = _score_field_definition(
            definition=definition,
            query=normalized_query,
            page_id=page_id,
            route_name=route_name,
        )
        if score <= 0:
            continue
        matches.append(
            FieldSearchMatch(
                field_key=definition.field_key,
                label=_localized_field_label(definition, language_code),
                entity_type=definition.entity_type,
                module_key=definition.module_key,
                page_id=definition.page_id,
                definition=_localized_field_definition(definition, language_code),
                required=definition.required,
                confidence=definition.confidence,
                source_basis=list(definition.source_basis),
                score=score,
            )
        )
    matches.sort(key=lambda item: (-item.score, item.field_key))
    return matches[: max(int(limit), 1)]


def search_lookup_dictionary(
    *,
    query: str,
    language_code: str | None,
    page_id: str | None,
    route_name: str | None,
    limit: int = 5,
    repo_root: Path | None = None,
) -> list[LookupSearchMatch]:
    normalized_query = _extract_field_probe(query) or _normalize_query(query)
    if not normalized_query:
        return []
    corpus = build_field_lookup_corpus(repo_root)
    matches: list[LookupSearchMatch] = []
    for definition in corpus.lookup_definitions:
        score = _score_lookup_definition(
            definition=definition,
            query=normalized_query,
            page_id=page_id,
            route_name=route_name,
        )
        if score <= 0:
            continue
        matches.append(
            LookupSearchMatch(
                lookup_key=definition.lookup_key,
                label=_localized_lookup_label(definition, language_code),
                entity_type=definition.entity_type,
                module_key=definition.module_key,
                page_id=definition.page_id,
                value_source_kind=definition.value_source_kind,
                source_basis=list(definition.source_basis),
                score=score,
            )
        )
    matches.sort(key=lambda item: (-item.score, item.lookup_key))
    return matches[: max(int(limit), 1)]


def get_lookup_definition(
    lookup_key: str,
    repo_root: Path | None = None,
) -> LookupDefinition | None:
    for definition in build_field_lookup_corpus(repo_root).lookup_definitions:
        if definition.lookup_key == lookup_key:
            return definition
    return None


def explain_lookup_query(
    *,
    query: str,
    language_code: str | None,
    page_id: str | None,
    route_name: str | None,
    limit: int = 5,
    repo_root: Path | None = None,
) -> list[LookupResolvedMatch]:
    normalized_query = _extract_field_probe(query) or _normalize_query(query)
    if not normalized_query:
        return []
    result: list[LookupResolvedMatch] = []
    for match in search_lookup_dictionary(
        query=query,
        language_code=language_code,
        page_id=page_id,
        route_name=route_name,
        limit=limit,
        repo_root=repo_root,
    ):
        definition = get_lookup_definition(match.lookup_key, repo_root)
        if definition is None:
            continue
        matched_values = _match_lookup_values(definition, normalized_query)
        result.append(
            LookupResolvedMatch(
                lookup_key=match.lookup_key,
                label=match.label,
                entity_type=match.entity_type,
                module_key=match.module_key,
                page_id=match.page_id,
                value_source_kind=match.value_source_kind,
                source_basis=list(match.source_basis),
                confidence=_lookup_confidence(definition),
                values=list(definition.values),
                matched_values=matched_values,
                value_resolution="static",
                score=match.score,
            )
        )
    return result


def render_field_dictionary_markdown(repo_root: Path | None = None) -> str:
    corpus = build_field_lookup_corpus(repo_root)
    lines = ["# Assistant Field Dictionary", ""]
    for definition in corpus.field_definitions:
        lines.extend(
            [
                f"## {definition.field_key}",
                "",
                f"- canonical_name: {definition.canonical_name}",
                f"- module_key: {definition.module_key or 'unknown'}",
                f"- page_id: {definition.page_id or 'unknown'}",
                f"- entity_type: {definition.entity_type or 'unknown'}",
                f"- route_names: {', '.join(definition.route_names) or 'none'}",
                f"- form_contexts: {', '.join(definition.form_contexts) or 'none'}",
                f"- input_type: {definition.input_type or 'unknown'}",
                f"- required: {definition.required if definition.required is not None else 'unknown'}",
                f"- confidence: {definition.confidence}",
                f"- labels_de: {', '.join(definition.labels.get('de', [])) or 'none'}",
                f"- labels_en: {', '.join(definition.labels.get('en', [])) or 'none'}",
                f"- definition_de: {definition.definition_de or 'n/a'}",
                f"- definition_en: {definition.definition_en or 'n/a'}",
                f"- related_fields: {', '.join(definition.related_fields) or 'none'}",
                f"- aliases: {', '.join(definition.aliases) or 'none'}",
            ]
        )
        if definition.source_basis:
            lines.append("- source_basis:")
            for basis in definition.source_basis[:8]:
                lines.append(
                    f"  - [{basis.source_type}] {basis.source_name}: {basis.evidence}"
                )
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def render_lookup_dictionary_markdown(repo_root: Path | None = None) -> str:
    corpus = build_field_lookup_corpus(repo_root)
    lines = ["# Assistant Lookup Dictionary", ""]
    for definition in corpus.lookup_definitions:
        lines.extend(
            [
                f"## {definition.lookup_key}",
                "",
                f"- module_key: {definition.module_key or 'unknown'}",
                f"- page_id: {definition.page_id or 'unknown'}",
                f"- entity_type: {definition.entity_type or 'unknown'}",
                f"- value_source_kind: {definition.value_source_kind}",
                f"- confidence: {definition.confidence}",
                f"- labels_de: {', '.join(definition.labels.get('de', [])) or 'none'}",
                f"- labels_en: {', '.join(definition.labels.get('en', [])) or 'none'}",
                f"- aliases: {', '.join(definition.aliases) or 'none'}",
            ]
        )
        if definition.values:
            lines.append("- values:")
            for value in definition.values:
                lines.append(
                    f"  - {value.value}: de={value.labels.get('de') or 'n/a'} | en={value.labels.get('en') or 'n/a'}"
                )
        if definition.source_basis:
            lines.append("- source_basis:")
            for basis in definition.source_basis[:8]:
                lines.append(f"  - [{basis.source_type}] {basis.source_name}: {basis.evidence}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def render_form_field_catalog_markdown(repo_root: Path | None = None) -> str:
    corpus = build_field_lookup_corpus(repo_root)
    lines = ["# Assistant Form Field Catalog", ""]
    for definition in corpus.field_definitions:
        lines.append(
            f"- {definition.field_key}: page={definition.page_id or 'unknown'} "
            f"input={definition.input_type or 'unknown'} contexts={', '.join(definition.form_contexts) or 'none'}"
        )
    return "\n".join(lines).strip() + "\n"


def render_frontend_i18n_label_markdown(repo_root: Path | None = None) -> str:
    corpus = build_field_lookup_corpus(repo_root)
    lines = ["# Assistant Frontend i18n Label Catalog", ""]
    for definition in corpus.field_definitions:
        if not definition.label_keys:
            continue
        lines.append(
            f"- {definition.field_key}: keys={', '.join(definition.label_keys)} "
            f"de={', '.join(definition.labels.get('de', [])) or 'n/a'} "
            f"en={', '.join(definition.labels.get('en', [])) or 'n/a'}"
        )
    return "\n".join(lines).strip() + "\n"


def render_api_schema_field_markdown(repo_root: Path | None = None) -> str:
    corpus = build_field_lookup_corpus(repo_root)
    lines = ["# Assistant API Schema Field Catalog", ""]
    for definition in corpus.field_definitions:
        if not definition.schema_fields:
            continue
        lines.append(f"- {definition.field_key}: schemas={', '.join(definition.schema_fields)}")
    return "\n".join(lines).strip() + "\n"


def field_definition_counts_by_module(repo_root: Path | None = None) -> dict[str, int]:
    counts: dict[str, int] = {}
    for definition in build_field_lookup_corpus(repo_root).field_definitions:
        key = definition.module_key or "unknown"
        counts[key] = counts.get(key, 0) + 1
    return counts


def lookup_definition_counts_by_module(repo_root: Path | None = None) -> dict[str, int]:
    counts: dict[str, int] = {}
    for definition in build_field_lookup_corpus(repo_root).lookup_definitions:
        key = definition.module_key or "unknown"
        counts[key] = counts.get(key, 0) + 1
    return counts


def _extract_locale_labels(repo_root: Path) -> dict[str, dict[str, str]]:
    labels: dict[str, dict[str, str]] = {}
    legacy_path = repo_root / _LEGACY_MESSAGES_PATH
    if legacy_path.exists():
        legacy_text = legacy_path.read_text(encoding="utf-8")
        for language_code, body in _split_legacy_messages(legacy_text).items():
            for line in body.splitlines():
                match = _LOCALE_ENTRY_RE.match(line)
                if not match:
                    continue
                labels.setdefault(match.group("key"), {})[language_code] = _unescape_locale_value(match.group("value"))
    for language_code, relative_path in (("de", _DE_LOCALE_PATH), ("en", _EN_LOCALE_PATH), ("fa", _FA_LOCALE_PATH)):
        locale_path = repo_root / relative_path
        if not locale_path.exists():
            continue
        payload = json.loads(locale_path.read_text(encoding="utf-8"))
        for key, value in _flatten_json(payload).items():
            if isinstance(value, str):
                labels.setdefault(key, {})[language_code] = value
    return labels


def _extract_vue_field_bindings(repo_root: Path) -> dict[str, dict[str, Any]]:
    bindings: dict[str, dict[str, Any]] = {}
    for path in (repo_root / "web/apps/web-antd/src").rglob("*.vue"):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        lines = text.splitlines()
        for index, line in enumerate(lines):
            label_match = _LABEL_KEY_RE.search(line)
            if not label_match:
                continue
            label_key = label_match.group("key")
            window = "\n".join(lines[index : index + 6])
            model_match = _V_MODEL_RE.search(window)
            if not model_match:
                continue
            input_type = _infer_input_type(window)
            required = " required" in window or ":required=" in window
            bindings.setdefault(
                label_key,
                {
                    "model": model_match.group("model"),
                    "source_name": path.name,
                    "input_type": input_type,
                    "required": required,
                },
            )
    return bindings


def _extract_typescript_interfaces(repo_root: Path) -> dict[str, set[str]]:
    definitions: dict[str, set[str]] = {}
    for path in (repo_root / "web/apps/web-antd/src").rglob("*.ts"):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        current_name: str | None = None
        brace_depth = 0
        for line in text.splitlines():
            start_match = _INTERFACE_START_RE.match(line)
            if start_match:
                current_name = start_match.group("name")
                brace_depth = line.count("{") - line.count("}")
                definitions.setdefault(current_name, set())
                continue
            if current_name is None:
                continue
            brace_depth += line.count("{") - line.count("}")
            field_match = _TS_FIELD_RE.match(line)
            if field_match:
                definitions[current_name].add(_normalize_field_name(field_match.group("name")))
            if brace_depth <= 0:
                current_name = None
    return definitions


def _extract_backend_fields(repo_root: Path) -> dict[str, set[str]]:
    definitions: dict[str, set[str]] = {}
    for path in (repo_root / "backend/app/modules").rglob("*"):
        if path.suffix != ".py" or path.name not in {"schemas.py", "models.py"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        current_name: str | None = None
        for line in text.splitlines():
            class_match = _PY_CLASS_RE.match(line)
            if class_match:
                current_name = class_match.group("name")
                definitions.setdefault(current_name, set())
                continue
            if current_name is None:
                continue
            field_match = _SQLA_FIELD_RE.match(line) or _PY_FIELD_RE.match(line)
            if field_match:
                definitions[current_name].add(_normalize_field_name(field_match.group("name")))
    return definitions


def _build_lookup_definitions(
    locale_labels: dict[str, dict[str, str]],
    vue_bindings: dict[str, dict[str, Any]],
) -> dict[str, LookupDefinition]:
    lookups: dict[str, LookupDefinition] = {}
    static_groups: dict[str, dict[str, dict[str, str]]] = {}
    for key, bundle in locale_labels.items():
        if ".status." in key or ".addressType." in key:
            root, value = key.rsplit(".", 1)
            static_groups.setdefault(root, {})[value] = bundle

    customer_status = LookupDefinition(
        lookup_key="customer.lifecycle_status",
        module_key="customers",
        page_id="C-01",
        entity_type="Customer",
        labels={"de": ["Lifecycle-Status", "Status"], "en": ["Lifecycle status", "Status"]},
        aliases=["customerAdmin.fields.lifecycleStatus", "status", "lifecycle status", "lifecycle_status"],
        value_source_kind="static",
        source_basis=[
            FieldSourceBasis(
                source_type="frontend_locale",
                source_name="messages.ts",
                page_id="C-01",
                module_key="customers",
                evidence="customerAdmin.fields.lifecycleStatus and customerAdmin.status.* define the lifecycle label and its visible option labels.",
            ),
            FieldSourceBasis(
                source_type="frontend_component",
                source_name="CustomerAdminView.vue",
                page_id="C-01",
                module_key="customers",
                evidence="CustomerAdminView.vue binds customerDraft.status to a select with active and inactive options.",
            )
        ],
    )
    for value in ("active", "inactive", "archived"):
        labels = locale_labels.get(f"customerAdmin.status.{value}", {})
        customer_status.values.append(
            LookupValueDefinition(
                value=value,
                labels={"de": labels.get("de", value), "en": labels.get("en", value.title())},
                meaning_de=_default_lookup_meaning(value, "de"),
                meaning_en=_default_lookup_meaning(value, "en"),
            )
        )
    lookups[customer_status.lookup_key] = customer_status

    address_type = LookupDefinition(
        lookup_key="customer.address_type",
        module_key="customers",
        page_id="C-01",
        entity_type="CustomerAddress",
        labels={"de": ["Adresstyp"], "en": ["Address type"]},
        aliases=["customerAdmin.fields.addressType", "address type", "adresstyp", "address_type"],
        value_source_kind="static",
        source_basis=[
            FieldSourceBasis(
                source_type="frontend_locale",
                source_name="messages.ts",
                page_id="C-01",
                module_key="customers",
                evidence="customerAdmin.addressType.* labels define registered, billing, mailing, and service address options.",
            ),
            FieldSourceBasis(
                source_type="backend_schema",
                source_name="CustomerAddressCreate",
                page_id="C-01",
                module_key="customers",
                evidence="CustomerAddressCreate.address_type enforces registered|billing|mailing|service.",
            ),
        ],
    )
    for value in ("registered", "billing", "mailing", "service"):
        labels = locale_labels.get(f"customerAdmin.addressType.{value}", {})
        address_type.values.append(
            LookupValueDefinition(
                value=value,
                labels={"de": labels.get("de", value), "en": labels.get("en", value)},
            )
        )
    lookups[address_type.lookup_key] = address_type

    dynamic_lookup_specs = (
        ("customer.legal_form_lookup_id", "Legal form", "Rechtsform"),
        ("customer.classification_lookup_id", "Classification", "Klassifizierung"),
        ("customer.ranking_lookup_id", "Ranking", "Ranking"),
        ("customer.customer_status_lookup_id", "Customer status metadata", "Kundenstatus-Metadaten"),
    )
    for lookup_key, label_en, label_de in dynamic_lookup_specs:
        page_id = "C-01"
        field_name = lookup_key.split(".", 1)[1]
        aliases = [field_name, label_en, label_de]
        if lookup_key == "customer.classification_lookup_id":
            aliases.append("Klassifikation")
            aliases.extend(["طبقه‌بندی", "طبقه‌بندی مشتری"])
        if lookup_key == "customer.ranking_lookup_id":
            aliases.append("رتبه‌بندی")
        lookups[lookup_key] = LookupDefinition(
            lookup_key=lookup_key,
            module_key="customers",
            page_id=page_id,
            entity_type="Customer",
            labels={"de": [label_de], "en": [label_en]},
            aliases=aliases,
            value_source_kind="tenant_lookup",
            source_basis=[
                FieldSourceBasis(
                    source_type="typescript_api_interface",
                    source_name="CustomerReferenceDataRead",
                    page_id=page_id,
                    module_key="customers",
                    evidence=f"CustomerReferenceDataRead exposes tenant-scoped options used for {field_name}.",
                )
            ],
        )
    lookups["planning.release_state"] = LookupDefinition(
        lookup_key="planning.release_state",
        module_key="planning",
        page_id="P-03",
        entity_type="ShiftPlan",
        labels={"de": ["Freigabestatus"], "en": ["Release status"]},
        aliases=["release state", "release status", "freigabestatus", "release_ready", "released", "draft", "وضعیت انتشار"],
        value_source_kind="static",
        values=[
            LookupValueDefinition(
                value="draft",
                labels={"de": "Entwurf", "en": "Draft"},
                meaning_de="Noch nicht freigabereif oder freigegeben.",
                meaning_en="Not yet ready for release or released.",
            ),
            LookupValueDefinition(
                value="release_ready",
                labels={"de": "Freigabereif", "en": "Release ready"},
                meaning_de="Inhaltlich vorbereitet und bereit fuer den naechsten Freigabeschritt.",
                meaning_en="Prepared and ready for the next release step.",
            ),
            LookupValueDefinition(
                value="released",
                labels={"de": "Freigegeben", "en": "Released"},
                meaning_de="Fuer nachgelagerte operative Sichtbarkeit freigegeben.",
                meaning_en="Released for downstream operational visibility.",
            ),
        ],
        source_basis=[
            FieldSourceBasis(
                source_type="backend_schema",
                source_name="Planning release state catalog",
                page_id="P-03",
                module_key="planning",
                evidence="Planning services and schemas use draft, release_ready, and released as the verified release-state values.",
            )
        ],
    )
    lookups["planning.workforce_scope_code"] = LookupDefinition(
        lookup_key="planning.workforce_scope_code",
        module_key="planning",
        page_id="P-03",
        entity_type="ShiftPlan",
        labels={"de": ["Einsatzkraefte-Scope"], "en": ["Workforce scope"]},
        aliases=["workforce scope", "scope", "mixed", "internal", "subcontractor", "einsatzkraefte-scope", "نوع پوشش نیرو"],
        value_source_kind="static",
        values=[
            LookupValueDefinition(
                value="internal",
                labels={"de": "Intern", "en": "Internal"},
                meaning_de="Die Besetzung ist fuer interne Mitarbeiter vorgesehen.",
                meaning_en="The staffing scope is intended for internal employees.",
            ),
            LookupValueDefinition(
                value="subcontractor",
                labels={"de": "Subunternehmer", "en": "Subcontractor"},
                meaning_de="Die Besetzung ist fuer Partnerpersonal vorgesehen.",
                meaning_en="The staffing scope is intended for partner workforce.",
            ),
            LookupValueDefinition(
                value="mixed",
                labels={"de": "Gemischt", "en": "Mixed"},
                meaning_de="Die Besetzung kann intern oder ueber Subunternehmer erfolgen.",
                meaning_en="The staffing scope can be covered by internal staff or subcontractors.",
            ),
        ],
        source_basis=[
            FieldSourceBasis(
                source_type="backend_schema",
                source_name="Planning models",
                page_id="P-03",
                module_key="planning",
                evidence="Planning models constrain workforce_scope_code to internal, subcontractor, or mixed.",
            )
        ],
    )
    lookups["planning.customer_visible_flag"] = LookupDefinition(
        lookup_key="planning.customer_visible_flag",
        module_key="planning",
        page_id="P-03",
        entity_type="ShiftPlan",
        labels={"de": ["Kunde sichtbar"], "en": ["Customer visible"]},
        aliases=["customer visible", "kunde sichtbar", "customer visibility", "قابل مشاهده برای مشتری"],
        value_source_kind="static",
        values=[
            LookupValueDefinition(
                value="true",
                labels={"de": "Sichtbar", "en": "Visible"},
                meaning_de="Der Datensatz darf in freigegebenen Kundenansichten erscheinen.",
                meaning_en="The record may appear in released customer-facing views.",
            ),
            LookupValueDefinition(
                value="false",
                labels={"de": "Nicht sichtbar", "en": "Not visible"},
                meaning_de="Der Datensatz bleibt aus Kundenansichten ausgeblendet.",
                meaning_en="The record stays hidden from customer-facing views.",
            ),
        ],
        source_basis=[
            FieldSourceBasis(
                source_type="backend_schema",
                source_name="Planning visibility flags",
                page_id="P-03",
                module_key="planning",
                evidence="Planning read models expose customer visibility as an explicit boolean release flag.",
            )
        ],
    )
    lookups["planning.employee_visible"] = LookupDefinition(
        lookup_key="planning.employee_visible",
        module_key="planning",
        page_id="P-03",
        entity_type="Shift",
        labels={"de": ["Mitarbeiter sichtbar"], "en": ["Employee visible"]},
        aliases=["employee visible", "mitarbeiter sichtbar", "employee app visible", "app visible", "قابل مشاهده برای کارمند"],
        value_source_kind="static",
        values=[
            LookupValueDefinition(
                value="true",
                labels={"de": "Sichtbar", "en": "Visible"},
                meaning_de="Die Schicht ist im Mitarbeiterkontext oder in der Mitarbeiter-App sichtbar.",
                meaning_en="The shift is visible in the employee context or employee app.",
            ),
            LookupValueDefinition(
                value="false",
                labels={"de": "Nicht sichtbar", "en": "Not visible"},
                meaning_de="Die Schicht ist im Mitarbeiterkontext noch nicht sichtbar, zum Beispiel weil Freigabe oder Sichtbarkeitsvoraussetzungen fehlen.",
                meaning_en="The shift is not yet visible in the employee context, for example because release or visibility prerequisites are missing.",
            ),
        ],
        source_basis=[
            FieldSourceBasis(
                source_type="backend_schema",
                source_name="Planning shift read model",
                page_id="P-03",
                module_key="planning",
                evidence="Planning shift read schemas expose employee_visible as the employee-app visibility result for a shift.",
            )
        ],
    )
    return lookups


def _field_identity_from_label_key(
    label_key: str,
) -> tuple[str | None, str | None, str | None, str | None, str | None]:
    prefix, _, suffix = label_key.partition(".fields.")
    if not suffix:
        return None, None, None, None, None
    canonical_name = _normalize_field_name(suffix)
    mapping = {
        "customerAdmin": ("customer", "customers", "C-01", "Customer"),
        "employeeAdmin": ("employee", "employees", "E-01", "Employee"),
        "customerPlansWizard": ("customer_order", "customers", "C-02", "CustomerOrder"),
        "planning": ("planning", "planning", "P-02", "Planning"),
        "portalCustomer": ("customer_portal", "customers", "CP-01", "CustomerPortal"),
        "portalSubcontractor": ("subcontractor_portal", "subcontractors", "SP-01", "SubcontractorPortal"),
        "sicherplan.subcontractors.workforce": ("subcontractor_worker", "subcontractors", "S-01", "SubcontractorWorker"),
    }
    namespace, module_key, page_id, entity_type = mapping.get(prefix, (None, None, None, None))
    if namespace is None:
        return None, canonical_name, None, None, None
    return f"{namespace}.{canonical_name}", canonical_name, module_key, page_id, entity_type


def _field_identity_from_page(*, page_id: str, canonical_name: str) -> tuple[str, str | None]:
    mapping = {
        "C-01": ("customer", "Customer"),
        "C-02": ("customer_order", "CustomerOrder"),
        "E-01": ("employee", "Employee"),
        "P-02": ("planning_record", "PlanningRecord"),
        "P-03": ("shift_plan", "ShiftPlan"),
        "P-04": ("assignment", "Assignment"),
        "P-05": ("dispatch", "Dispatch"),
        "PS-01": ("document", "PlatformDocument"),
        "S-01": ("subcontractor", "Subcontractor"),
    }
    namespace, entity_type = mapping.get(page_id, ("field", None))
    return f"{namespace}.{canonical_name}", entity_type


def _add_manual_field_definitions(definitions: dict[str, FieldDefinition]) -> None:
    for field_key, aliases in {
        "customer.legal_name": ["نام قانونی"],
        "customer.customer_number": ["شماره مشتری"],
        "customer.external_ref": ["ارجاع خارجی"],
    }.items():
        definition = definitions.get(field_key)
        if definition is None:
            continue
        for alias in aliases:
            _append_unique(definition.aliases, alias)

    definitions["shift.shift_type_code"] = FieldDefinition(
        field_key="shift.shift_type_code",
        canonical_name="shift_type_code",
        module_key="planning",
        page_id="P-03",
        route_names=["SicherPlanPlanningShifts"],
        entity_type="Shift",
        form_contexts=["planning.shift", "planning_shifts.concrete_shift_and_release"],
        input_type="select",
        required=False,
        labels={"de": ["Schichttyp"], "en": ["Shift type"]},
        aliases=["Schichttyp", "shift type", "shift_type_code", "نوع شیفت"],
        definition_en="Shift type identifies what kind of shift is being planned or released and is used across templates, series, and concrete shifts.",
        definition_de="Der Schichttyp beschreibt, welche Art von Schicht geplant oder freigegeben wird, und wird in Vorlagen, Serien und konkreten Schichten verwendet.",
        source_basis=[
            FieldSourceBasis(
                source_type="frontend_locale",
                source_name="planningShifts.messages.ts",
                page_id="P-03",
                module_key="planning",
                evidence="planningShifts.messages.ts defines the verified field label Schichttyp / Shift type for the planning shifts workspace.",
            ),
            FieldSourceBasis(
                source_type="backend_schema",
                source_name="Planning schemas",
                page_id="P-03",
                module_key="planning",
                evidence="Planning schemas persist shift_type_code across templates, series, and concrete shifts.",
            ),
        ],
        confidence="high",
        label_keys=["planningShifts.fieldsShiftType"],
        schema_fields=["ShiftCreate.shift_type_code", "ShiftRead.shift_type_code"],
    )


def _append_related_fields(definition: FieldDefinition, definitions: dict[str, FieldDefinition]) -> None:
    if definition.field_key == "customer.legal_name":
        for related in ("customer.name", "customer.customer_number", "customer.external_ref"):
            if related in definitions:
                _append_unique(definition.related_fields, related)


def _set_default_field_definition_text(definition: FieldDefinition) -> None:
    if definition.field_key == "customer.legal_name":
        definition.definition_en = (
            "Official legal name of the customer or legal entity used for contracts, invoices, and formal documents."
        )
        definition.definition_de = (
            "Offizieller rechtlicher Name des Kunden oder der juristischen Einheit, der in Verträgen, Rechnungen und offiziellen Dokumenten verwendet wird."
        )
        definition.example_values = ["RheinForum Köln GmbH"]
        return
    base_label_en = next(iter(definition.labels.get("en", [])), definition.canonical_name.replace("_", " "))
    base_label_de = next(iter(definition.labels.get("de", [])), base_label_en)
    entity_en = definition.entity_type or "record"
    definition.definition_en = definition.definition_en or f"{base_label_en} field used in the {entity_en} context."
    definition.definition_de = definition.definition_de or f"Feld {base_label_de} im Kontext von {definition.entity_type or 'Datensätzen'}."


def _field_confidence(definition: FieldDefinition) -> str:
    has_label = bool(definition.labels)
    has_binding = bool(definition.binding_paths)
    has_schema = bool(definition.schema_fields)
    if has_label and has_binding and has_schema:
        return "high"
    if has_label and (has_binding or has_schema):
        return "medium"
    if has_label or has_schema:
        return "low"
    return "low"


def _lookup_confidence(definition: LookupDefinition) -> str:
    if definition.values and len(definition.source_basis) >= 2:
        return "high"
    if definition.values or definition.source_basis:
        return "medium"
    return "low"


def _localized_field_label(definition: FieldDefinition, language_code: str | None) -> str:
    if language_code and definition.labels.get(language_code):
        return definition.labels[language_code][0]
    if definition.labels.get("de"):
        return definition.labels["de"][0]
    if definition.labels.get("en"):
        return definition.labels["en"][0]
    return definition.canonical_name


def _localized_field_definition(definition: FieldDefinition, language_code: str | None) -> str | None:
    if language_code == "de":
        return definition.definition_de or definition.definition_en
    if language_code == "en":
        return definition.definition_en or definition.definition_de
    return definition.definition_de or definition.definition_en


def _localized_lookup_label(definition: LookupDefinition, language_code: str | None) -> str:
    if language_code and definition.labels.get(language_code):
        return definition.labels[language_code][0]
    if definition.labels.get("de"):
        return definition.labels["de"][0]
    if definition.labels.get("en"):
        return definition.labels["en"][0]
    return definition.lookup_key


def _score_field_definition(
    *,
    definition: FieldDefinition,
    query: str,
    page_id: str | None,
    route_name: str | None,
) -> float:
    haystacks = [definition.field_key, definition.canonical_name, *(definition.aliases or [])]
    labels = [item for values in definition.labels.values() for item in values]
    score = 0.0
    for value in [*haystacks, *labels]:
        normalized = _normalize_query(value)
        if not normalized:
            continue
        if normalized == query:
            score = max(score, 100.0)
        elif _contains_token_phrase(normalized, query):
            score = max(score, 76.0)
        elif _contains_token_phrase(query, normalized):
            score = max(score, 68.0)
    if score <= 0:
        return 0.0
    if definition.page_id and page_id == definition.page_id:
        score += 20.0 if _is_generic_label_query(query) else 12.0
    if route_name and route_name in definition.route_names:
        score += 8.0
    if definition.confidence == "high":
        score += 6.0
    elif definition.confidence == "medium":
        score += 3.0
    return score


def _score_lookup_definition(
    *,
    definition: LookupDefinition,
    query: str,
    page_id: str | None,
    route_name: str | None,
) -> float:
    haystacks = [definition.lookup_key, *(definition.aliases or [])]
    haystacks.extend(item for values in definition.labels.values() for item in values)
    for value in definition.values:
        haystacks.append(value.value)
        haystacks.extend(value.labels.values())
    score = 0.0
    for value in haystacks:
        normalized = _normalize_query(value)
        if not normalized:
            continue
        if normalized == query:
            score = max(score, 92.0)
        elif _contains_token_phrase(normalized, query):
            score = max(score, 72.0)
        elif _contains_token_phrase(query, normalized):
            score = max(score, 64.0)
    if score <= 0:
        return 0.0
    if definition.page_id and page_id == definition.page_id:
        score += 18.0 if _is_generic_label_query(query) else 10.0
    if route_name:
        score += 0.0
    if definition.confidence == "high":
        score += 5.0
    elif definition.confidence == "medium":
        score += 2.0
    return score


def _match_lookup_values(
    definition: LookupDefinition,
    normalized_query: str,
) -> list[LookupValueDefinition]:
    matches: list[LookupValueDefinition] = []
    for value in definition.values:
        haystacks = [value.value, *(value.labels.values())]
        for candidate in haystacks:
            normalized = _normalize_query(candidate)
            if not normalized:
                continue
            if normalized == normalized_query or _contains_token_phrase(normalized_query, normalized) or _contains_token_phrase(normalized, normalized_query):
                matches.append(value)
                break
    return matches


def _extract_field_probe(text: str) -> str | None:
    stripped = text.strip().strip("?؟").strip()
    lowered = stripped.casefold()
    persian_suffixes = ("یعنی چه", "یعنی چی", "چیست", "چه است")
    trailing_platform_phrases = (
        "im sicherplan",
        "in sicherplan",
        "bei sicherplan",
        "auf sicherplan",
    )
    for prefix in _QUESTION_PREFIXES:
        if lowered.startswith(prefix):
            remainder = stripped[len(prefix) :].strip(" :?-\"'“”„")
            remainder = re.sub(r"\b(mean|meaning|bedeuten|bedeutet)\b$", "", remainder, flags=re.IGNORECASE).strip()
            for suffix in persian_suffixes:
                if remainder.endswith(suffix):
                    remainder = remainder[: -len(suffix)].strip(" :?-\"'“”„")
            remainder_lowered = remainder.casefold()
            for phrase in trailing_platform_phrases:
                if remainder_lowered.endswith(phrase):
                    remainder = remainder[: -len(phrase)].strip(" :?-\"'“”„")
                    remainder_lowered = remainder.casefold()
            if remainder and 1 <= len(remainder.split()) <= 5 and len(remainder) <= 80:
                return _normalize_query(remainder)
            return None
    for suffix in persian_suffixes:
        if lowered.endswith(suffix):
            remainder = stripped[: -len(suffix)].strip(" :?-\"'“”„")
            if remainder and 1 <= len(remainder.split()) <= 5 and len(remainder) <= 80:
                return _normalize_query(remainder)
    if 1 <= len(stripped.split()) <= 4 and len(stripped) <= 80:
        return _normalize_query(stripped)
    return None


def _default_lookup_meaning(value: str, language_code: str) -> str:
    if language_code == "de":
        return {
            "active": "Der Datensatz ist aktiv nutzbar.",
            "inactive": "Der Datensatz ist vorhanden, aber nicht aktiv im Einsatz.",
            "archived": "Der Datensatz ist archiviert und nur noch historisch relevant.",
        }.get(value, f"Statuswert {value}.")
    return {
        "active": "The record is active and usable.",
        "inactive": "The record exists but is not currently active.",
        "archived": "The record is archived and mainly relevant for history.",
    }.get(value, f"Status value {value}.")


def _split_legacy_messages(text: str) -> dict[str, str]:
    de_start = text.index("  de: {")
    en_start = text.index("  en: {")
    de_body = text[de_start:en_start]
    en_body = text[en_start:]
    return {"de": de_body, "en": en_body}


def _flatten_json(value: Any, prefix: str = "") -> dict[str, Any]:
    result: dict[str, Any] = {}
    if isinstance(value, dict):
        for key, nested in value.items():
            nested_prefix = f"{prefix}.{key}" if prefix else key
            result.update(_flatten_json(nested, nested_prefix))
    else:
        result[prefix] = value
    return result


def _normalize_field_name(value: str) -> str:
    value = value.strip()
    if not value:
        return value
    if "." in value:
        value = value.split(".")[-1]
    value = value.replace("-", "_")
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value)
    return value.casefold()


def _normalize_query(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", value)
    value = value.casefold()
    value = re.sub(r"[._/\-]+", " ", value)
    value = re.sub(r"[^\w\s]+", " ", value, flags=re.UNICODE)
    return re.sub(r"\s+", " ", value).strip()


def _contains_token_phrase(haystack: str, needle: str) -> bool:
    haystack_tokens = _tokenize_query(haystack)
    needle_tokens = _tokenize_query(needle)
    if not haystack_tokens or not needle_tokens:
        return False
    if len(needle_tokens) > len(haystack_tokens):
        return False
    window_size = len(needle_tokens)
    for index in range(len(haystack_tokens) - window_size + 1):
        if haystack_tokens[index : index + window_size] == needle_tokens:
            return True
    return False


def _tokenize_query(value: str) -> list[str]:
    return re.findall(r"\w+", value.casefold(), flags=re.UNICODE)


def _is_ambiguous_signal(
    *,
    normalized_query: str,
    field_matches: list[FieldSearchMatch],
    lookup_matches: list[LookupSearchMatch],
) -> bool:
    candidates: list[tuple[str, str | None, str | None, float]] = []
    for match in field_matches[:3]:
        candidates.append((match.field_key, match.page_id, match.module_key, match.score))
    for match in lookup_matches[:3]:
        candidates.append((match.lookup_key, match.page_id, match.module_key, match.score))
    if len(candidates) <= 1:
        return False
    candidates.sort(key=lambda item: item[3], reverse=True)
    top_key, top_page_id, top_module_key, top_score = candidates[0]
    for candidate_key, candidate_page_id, candidate_module_key, candidate_score in candidates[1:]:
        if candidate_key == top_key:
            continue
        if candidate_score < top_score - 12.0:
            continue
        if candidate_page_id != top_page_id or candidate_module_key != top_module_key:
            return True
    return normalized_query in _GENERIC_AMBIGUOUS_LABELS


def _infer_field_lookup_intent_category(
    *,
    text: str,
    normalized_query: str,
    field_matches: list[FieldSearchMatch],
    lookup_matches: list[LookupSearchMatch],
    route_context_form_help: bool,
) -> str:
    lowered = _normalize_query(text)
    if route_context_form_help and not field_matches and not lookup_matches:
        return "form_help_question"
    if any(term in lowered for term in _COLUMN_HELP_TERMS):
        return "column_meaning_question"
    if any(term in lowered for term in _TAB_ACTION_TERMS):
        return "tab_action_label_question"
    if any(term in lowered for term in _FORM_HELP_TERMS):
        return "form_help_question"
    if normalized_query in {"release ready", "released", "draft"}:
        return "status_meaning_question"
    if any(term in lowered for term in _STATUS_HELP_TERMS) or any("status" in match.lookup_key for match in lookup_matches[:3]):
        return "status_meaning_question"
    if any(term in lowered for term in _LOOKUP_HELP_TERMS):
        return "lookup_meaning_question"

    top_field_score = field_matches[0].score if field_matches else -1.0
    top_lookup_score = lookup_matches[0].score if lookup_matches else -1.0
    if field_matches and lookup_matches:
        top_field_key = field_matches[0].field_key
        if top_field_key.endswith("_lookup_id") and top_lookup_score > 0:
            return "lookup_meaning_question"
    if top_lookup_score > top_field_score:
        return "lookup_meaning_question"
    return "field_meaning_question"


def _is_route_context_form_help_question(
    *,
    text: str,
    page_id: str | None,
    route_name: str | None,
) -> bool:
    if not (page_id or route_name):
        return False
    lowered = _normalize_query(text)
    if any(phrase in lowered for phrase in _FIELD_HELP_VAGUE_PHRASES):
        return True
    return False


def _is_generic_label_query(query: str) -> bool:
    tokens = _tokenize_query(query)
    return len(tokens) == 1 and tokens[0] in _GENERIC_AMBIGUOUS_LABELS


def _unescape_locale_value(value: str) -> str:
    try:
        return json.loads(f'"{value}"')
    except json.JSONDecodeError:
        return value


def _infer_input_type(window: str) -> str:
    lowered = window.casefold()
    if "<select" in lowered:
        return "select"
    if "<textarea" in lowered:
        return "textarea"
    if 'type="checkbox"' in lowered:
        return "checkbox"
    if 'type="number"' in lowered:
        return "number"
    return "text"


def _add_label(target: dict[str, list[str]], language_code: str | None, label: str) -> None:
    if language_code is None or not label.strip():
        return
    bucket = target.setdefault(language_code, [])
    _append_unique(bucket, label.strip())


def _append_unique(target: list[str], value: str | None) -> None:
    if value is None:
        return
    cleaned = str(value).strip()
    if not cleaned:
        return
    if cleaned not in target:
        target.append(cleaned)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


__all__ = [
    "AssistantFieldLookupCorpus",
    "CorpusSignal",
    "FieldDefinition",
    "FieldSearchMatch",
    "FieldSourceBasis",
    "LookupDefinition",
    "LookupSearchMatch",
    "LookupValueDefinition",
    "build_field_lookup_corpus",
    "detect_field_or_lookup_signal",
    "field_definition_counts_by_module",
    "lookup_definition_counts_by_module",
    "render_api_schema_field_markdown",
    "render_field_dictionary_markdown",
    "render_form_field_catalog_markdown",
    "render_frontend_i18n_label_markdown",
    "render_lookup_dictionary_markdown",
    "search_field_dictionary",
    "search_lookup_dictionary",
]
