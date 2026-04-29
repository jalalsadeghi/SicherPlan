"""Deterministic field and lookup knowledge corpus for the assistant."""

from __future__ import annotations

from dataclasses import dataclass, field, is_dataclass
from functools import lru_cache
import hashlib
from importlib import resources
import json
import logging
from pathlib import Path
import re
from typing import Any
import unicodedata

from app.modules.assistant.page_help_seed import ASSISTANT_PAGE_HELP_SEEDS


LOGGER = logging.getLogger(__name__)
_GENERATED_PACKAGE = "app.modules.assistant.generated"
_GENERATED_CORPUS_FILENAME = "field_lookup_corpus.json"
_FIELD_LOOKUP_SCHEMA_VERSION = 1
_HASH_EXCLUDED_DIR_NAMES = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "dist",
    "build",
}
_HASH_EXCLUDED_FILE_SUFFIXES = {".pyc", ".pyo"}
_HASH_EXCLUDED_FILE_NAMES = {_GENERATED_CORPUS_FILENAME}


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
_GENERIC_PLATFORM_TERM_QUERIES = {
    "group",
    "groups",
    "type",
    "types",
    "action",
    "actions",
    "mode",
    "modes",
    "title",
    "titles",
    "status",
}
_MESSAGE_FILE_CONTEXT = {
    "planningStaffing.messages.ts": ("planning", "P-04", ["SicherPlanPlanningStaffing"], "staffing_workspace"),
    "planningShifts.messages.ts": ("planning", "P-03", ["SicherPlanPlanningShifts"], "shift_planning_workspace"),
    "planningOrders.messages.ts": ("planning", "P-02", ["SicherPlanPlanningOrders"], "planning_orders_workspace"),
    "customerAdmin.messages.ts": ("customers", "C-01", ["SicherPlanCustomers"], "customer_admin_workspace"),
    "employeeAdmin.messages.ts": ("employees", "E-01", ["SicherPlanEmployees"], "employee_admin_workspace"),
}
_TERM_SUFFIX_TYPES = (
    ("Placeholder", "filter_label"),
    ("Title", "section_title"),
    ("Empty", "empty_state"),
    ("Hint", "hint_text"),
    ("Lead", "hint_text"),
    ("Action", "action_label"),
    ("Label", "field_label"),
)
_TERM_PREFIX_TYPES = (
    ("fields", "field_label"),
    ("detailTab", "tab_title"),
    ("filters", "filter_label"),
    ("status", "status_label"),
    ("rule", "validation_rule"),
    ("column", "column_label"),
)
_EXCLUDED_PLATFORM_TERM_KEYS = {
    "title",
    "lead",
    "eyebrow",
    "refresh",
    "error",
    "saveSuccess",
    "clearFeedback",
}
_PLATFORM_TERM_OVERRIDES = {
    "planning.staffing.demand_groups": {
        "source_keys": {
            "demandGroupsTitle",
            "demandGroupsEmpty",
            "demandGroupsSetupRequired",
            "demandGroupPlaceholder",
            "demandGroupEditorTitle",
            "demandGroupCreateTitle",
            "demandGroupEditTitle",
            "demandGroupSetupLead",
            "demandGroupCreateAction",
            "demandGroupEditSelectedAction",
            "demandGroupSaveAction",
            "demandGroupUpdateAction",
            "demandGroupFunctionType",
            "demandGroupQualificationType",
            "demandGroupMinQty",
            "demandGroupTargetQty",
            "demandGroupSortOrder",
            "demandGroupSortOrderHint",
            "demandGroupMandatoryFlag",
            "demandGroupMandatoryHint",
            "demandGroupRemark",
            "fieldsDemandGroup",
            "staffingActionsDemandGroupRequired",
        },
        "canonical_name": "demand_groups",
        "module_key": "planning",
        "page_id": "P-04",
        "route_names": ["SicherPlanPlanningStaffing"],
        "concept_type": "staffing_concept",
        "ui_term_type": "domain_concept",
        "labels": {
            "de": ["Demand Groups", "Demand Group"],
            "en": ["Demand groups", "Demand group"],
        },
        "aliases": [
            "demand groups",
            "demand group",
            "demand-group",
            "demand group setup",
            "fieldsDemandGroup",
            "demandGroupsTitle",
            "demandGroupEditorTitle",
        ],
        "ui_contexts": [
            "Shift Coverage",
            "Demand and staffing tab",
            "Demand Group setup",
            "Staffing actions",
        ],
        "related_terms": [
            "shift coverage",
            "minimum quantity",
            "target quantity",
            "function type",
            "qualification",
            "mandatory demand group",
            "assignment",
        ],
        "definition_en": (
            "Demand groups are staffing requirement groups for a shift. They define which function type is needed, "
            "which qualification may be required, the minimum and target quantity, ordering, and whether the group is mandatory. "
            "A shift cannot be staffed meaningfully until at least one demand group exists."
        ),
        "definition_de": (
            "Demand Groups sind Bedarfsgruppen bzw. Staffing-Slots fuer eine Schicht. Sie definieren benoetigten Funktionstyp, "
            "optionale Qualifikation, Mindest- und Zielmenge, Sortierung und Pflichtstatus. Eine Schicht kann erst sinnvoll staffed werden, "
            "wenn mindestens eine Demand Group angelegt wurde."
        ),
    },
    "planning.staffing.staffing_actions": {
        "source_keys": {
            "staffingActionsTitle",
            "staffingActionsHint",
            "assignAction",
            "substituteAction",
            "unassignAction",
            "staffingActionsDemandGroupRequired",
        },
        "canonical_name": "staffing_actions",
        "module_key": "planning",
        "page_id": "P-04",
        "route_names": ["SicherPlanPlanningStaffing"],
        "concept_type": "staffing_concept",
        "ui_term_type": "domain_concept",
        "labels": {
            "de": ["Staffing-Aktionen", "Staffing Aktionen"],
            "en": ["Staffing actions"],
        },
        "aliases": [
            "staffing-aktionen",
            "staffing aktionen",
            "staffing actions",
            "assign",
            "substitute",
            "unassign",
        ],
        "ui_contexts": [
            "Staffing Coverage",
            "Demand and staffing tab",
            "Assignment actions",
        ],
        "related_terms": [
            "demand groups",
            "assignment",
            "substitute",
            "unassign",
            "shift coverage",
        ],
        "definition_en": (
            "Staffing actions are the verified assignment commands in Staffing Coverage. They let the user assign, substitute, "
            "or remove staffing for the selected shift and demand group after the required setup and validations are satisfied."
        ),
        "definition_de": (
            "Staffing-Aktionen sind die verifizierten Besetzungsaktionen in Staffing Coverage. Damit kann der Nutzer fuer die "
            "ausgewaehlte Schicht und Demand Group zuweisen, ersetzen oder entfernen, sobald Setup und Validierungen passen."
        ),
    },
    "planning.staffing.release_gates": {
        "source_keys": {
            "title",
            "lead",
            "validationTitle",
            "releaseStateTitle",
            "releaseAction",
            "visibilityRequiresRelease",
            "outputReleaseRequired",
            "dispatchReleaseRequired",
            "releaseBlocked",
        },
        "canonical_name": "release_gates",
        "module_key": "planning",
        "page_id": "P-04",
        "route_names": ["SicherPlanPlanningStaffing"],
        "concept_type": "staffing_concept",
        "ui_term_type": "domain_concept",
        "labels": {
            "de": ["Release-Gates", "Release Gates"],
            "en": ["Release gates", "Release-Gates"],
        },
        "aliases": [
            "release-gates",
            "release gates",
            "freigabegates",
            "freigabesperren",
        ],
        "ui_contexts": [
            "Staffing Coverage",
            "Release validations",
            "Release state and visibility",
        ],
        "related_terms": [
            "release",
            "visibility",
            "outputs",
            "dispatch messages",
            "validations",
        ],
        "definition_en": (
            "Release gates are the release-dependent checks in Staffing Coverage. They determine whether a shift may be released, "
            "made visible, used for outputs, or used for dispatch. If a gate is still failing, downstream actions stay blocked."
        ),
        "definition_de": (
            "Release-Gates sind die freigabeabhaengigen Pruefungen in Staffing Coverage. Sie steuern, ob eine Schicht freigegeben, "
            "sichtbar gemacht, fuer Outputs verwendet oder fuer Dispatch genutzt werden darf. Solange ein Gate blockiert, bleiben Folgeaktionen gesperrt."
        ),
    },
    "planning.staffing.override_evidence": {
        "source_keys": {
            "assignmentOverridesTitle",
            "assignmentOverridesEmpty",
            "overrideTitle",
            "overrideReasonLabel",
            "overrideReasonPlaceholder",
            "overrideAction",
            "overrideHint",
            "overrideUnavailable",
            "workspaceLoadingOverride",
            "saveSuccess",
        },
        "canonical_name": "override_evidence",
        "module_key": "planning",
        "page_id": "P-04",
        "route_names": ["SicherPlanPlanningStaffing"],
        "concept_type": "staffing_concept",
        "ui_term_type": "domain_concept",
        "labels": {
            "de": ["Override-Nachweise", "Override Nachweise"],
            "en": ["Override evidence"],
        },
        "aliases": [
            "override-nachweise",
            "override nachweise",
            "override evidence",
            "override proof",
            "override proofs",
        ],
        "ui_contexts": [
            "Assignment validations",
            "Override recording",
            "Append-only evidence",
        ],
        "related_terms": [
            "assignment validations",
            "override",
            "reason",
            "backend-approved blocker",
        ],
        "definition_en": (
            "Override evidence is the append-only record explaining why a backend-approved staffing blocker was overridden. "
            "It documents the reason, keeps the override auditable, and does not delete the original validation result."
        ),
        "definition_de": (
            "Override-Nachweise sind die append-only Nachweise dafuer, warum ein backend-freigegebener Staffing-Blocker uebersteuert wurde. "
            "Sie dokumentieren die Begruendung, halten den Override revisionssicher fest und loeschen das urspruengliche Validierungsergebnis nicht."
        ),
    },
    "planning.staffing.partner_releases": {
        "source_keys": {
            "detailTabTeamsReleases",
            "teamReleaseTitle",
            "subcontractorReleasesTitle",
            "subcontractorReleasesEmpty",
            "assignmentSourceSubcontractorRelease",
            "columnReleased",
        },
        "canonical_name": "partner_releases",
        "module_key": "planning",
        "page_id": "P-04",
        "route_names": ["SicherPlanPlanningStaffing"],
        "concept_type": "staffing_concept",
        "ui_term_type": "domain_concept",
        "labels": {
            "de": ["Partnerfreigaben"],
            "en": ["Partner releases", "Subcontractor releases"],
        },
        "aliases": [
            "partnerfreigaben",
            "partner freigaben",
            "partner releases",
            "subcontractor releases",
        ],
        "ui_contexts": [
            "Teams and partner releases",
            "Staffing Coverage",
            "Released partners",
        ],
        "related_terms": [
            "subcontractor releases",
            "released partners",
            "visibility",
            "team releases",
        ],
        "definition_en": (
            "Partner releases are the verified subcontractor-release records for a shift. They show which partner or partner worker "
            "has been released into the staffing flow and whether partner-side follow-up can proceed."
        ),
        "definition_de": (
            "Partnerfreigaben sind die verifizierten Subunternehmer-Freigaben fuer eine Schicht. Sie zeigen, welcher Partner oder "
            "welcher Partner-Mitarbeiter in den Staffing-Ablauf freigegeben wurde und ob die Partnerfolgeprozesse weiterlaufen duerfen."
        ),
    },
    "planning.staffing.dispatch_messages": {
        "source_keys": {
            "detailTabOutputsDispatch",
            "dispatchTitle",
            "dispatchPreviewAction",
            "dispatchQueueAction",
            "dispatchAudienceEmployees",
            "dispatchAudienceSubcontractors",
            "dispatchRecipients",
            "dispatchQueuedSuccess",
            "dispatchReleaseRequired",
            "dispatchNoRecipients",
        },
        "canonical_name": "dispatch_messages",
        "module_key": "planning",
        "page_id": "P-04",
        "route_names": ["SicherPlanPlanningStaffing"],
        "concept_type": "staffing_concept",
        "ui_term_type": "domain_concept",
        "labels": {
            "de": ["Dispatch-Nachrichten", "Dispatch Nachrichten"],
            "en": ["Dispatch messages"],
        },
        "aliases": [
            "dispatch-nachrichten",
            "dispatch nachrichten",
            "dispatch messages",
            "dispatch message",
        ],
        "ui_contexts": [
            "Outputs and dispatch",
            "Message preview",
            "Recipient queueing",
        ],
        "related_terms": [
            "dispatch",
            "release",
            "recipients",
            "outputs",
        ],
        "definition_en": (
            "Dispatch messages are the verified outbound staffing messages for the selected shift. They preview and queue messages "
            "to assigned employees or released partners after release requirements and permitted recipients are satisfied."
        ),
        "definition_de": (
            "Dispatch-Nachrichten sind die verifizierten ausgehenden Staffing-Nachrichten fuer die ausgewaehlte Schicht. Sie zeigen "
            "Vorschau und Queueing fuer zugewiesene Mitarbeiter oder freigegebene Partner, sobald Freigabevoraussetzungen und Empfaenger passen."
        ),
    },
    "planning.staffing.minimum_staffing": {
        "source_keys": {
            "ruleMinimumStaffing",
        },
        "canonical_name": "minimum_staffing",
        "module_key": "planning",
        "page_id": "P-04",
        "route_names": ["SicherPlanPlanningStaffing"],
        "concept_type": "staffing_concept",
        "ui_term_type": "domain_concept",
        "labels": {
            "de": ["Mindestbesetzung"],
            "en": ["Minimum staffing"],
        },
        "aliases": [
            "mindestbesetzung",
            "minimum staffing",
            "minimum staffing not reached",
        ],
        "ui_contexts": [
            "Release validations",
            "Coverage validations",
        ],
        "related_terms": [
            "demand groups",
            "target quantity",
            "assigned",
            "confirmed",
        ],
        "definition_en": (
            "Minimum staffing is the lower staffing threshold for the shift. If the required minimum is not met, validations can block "
            "release or indicate that the shift is still operationally under-covered."
        ),
        "definition_de": (
            "Mindestbesetzung ist die untere Besetzungsschwelle einer Schicht. Wenn das geforderte Minimum nicht erreicht ist, "
            "koennen Validierungen die Freigabe blockieren oder anzeigen, dass die Schicht operativ noch unterdeckt ist."
        ),
    },
    "planning.staffing.mandatory_proofs": {
        "source_keys": {
            "ruleMandatoryDocuments",
        },
        "canonical_name": "mandatory_proofs",
        "module_key": "planning",
        "page_id": "P-04",
        "route_names": ["SicherPlanPlanningStaffing"],
        "concept_type": "staffing_concept",
        "ui_term_type": "domain_concept",
        "labels": {
            "de": ["Pflichtnachweise"],
            "en": ["Mandatory proofs", "Mandatory documents"],
        },
        "aliases": [
            "pflichtnachweise",
            "mandatory proofs",
            "mandatory proof",
            "mandatory documents",
        ],
        "ui_contexts": [
            "Assignment validations",
            "Release validations",
        ],
        "related_terms": [
            "qualification",
            "documents",
            "assignment validations",
            "release gates",
        ],
        "definition_en": (
            "Mandatory proofs are the required qualification or document evidences for the staffing flow. If they are missing or not valid "
            "at the shift time, validations can block assignment, release, or downstream visibility."
        ),
        "definition_de": (
            "Pflichtnachweise sind die erforderlichen Qualifikations- oder Dokumentnachweise fuer den Staffing-Ablauf. Wenn sie fehlen "
            "oder zum Schichtzeitpunkt nicht gueltig sind, koennen Validierungen Zuweisung, Freigabe oder Folge-Sichtbarkeit blockieren."
        ),
    },
}


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


@dataclass
class PlatformTermDefinition:
    term_key: str
    canonical_name: str
    module_key: str | None
    page_id: str | None
    route_names: list[str] = field(default_factory=list)
    concept_type: str = "domain_concept"
    ui_term_type: str = "domain_concept"
    ui_contexts: list[str] = field(default_factory=list)
    labels: dict[str, list[str]] = field(default_factory=dict)
    aliases: list[str] = field(default_factory=list)
    definition_en: str | None = None
    definition_de: str | None = None
    related_terms: list[str] = field(default_factory=list)
    source_basis: list[FieldSourceBasis] = field(default_factory=list)
    confidence: str = "low"


@dataclass(frozen=True)
class PlatformTermSearchMatch:
    term_key: str
    label: str
    module_key: str | None
    page_id: str | None
    concept_type: str
    ui_term_type: str
    definition: str | None
    source_basis: list[FieldSourceBasis]
    confidence: str
    score: float


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
    term_matches: tuple[PlatformTermSearchMatch, ...] = ()
    matched_via_route_context: bool = False


@dataclass(frozen=True)
class AssistantFieldLookupCorpus:
    field_definitions: tuple[FieldDefinition, ...]
    lookup_definitions: tuple[LookupDefinition, ...]
    term_definitions: tuple[PlatformTermDefinition, ...] = ()


@dataclass(frozen=True)
class AssistantFieldLookupCorpusStatus:
    artifact_loaded: bool
    artifact_version: str | None
    field_count: int
    lookup_count: int
    term_count: int
    counts_by_module: dict[str, int]


def build_field_lookup_corpus(repo_root: Path | None = None) -> AssistantFieldLookupCorpus:
    if repo_root is not None:
        return _build_field_lookup_corpus_from_sources(str(repo_root.resolve()))
    return _load_runtime_field_lookup_corpus()


@lru_cache(maxsize=4)
def _build_field_lookup_corpus_from_sources(repo_root_str: str) -> AssistantFieldLookupCorpus:
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
    terms = _build_platform_term_definitions(
        repo_root=repo_root,
        locale_labels=locale_labels,
        backend_fields=backend_fields,
    )

    return AssistantFieldLookupCorpus(
        field_definitions=tuple(sorted(fields.values(), key=lambda item: item.field_key)),
        lookup_definitions=tuple(sorted(lookups.values(), key=lambda item: item.lookup_key)),
        term_definitions=tuple(sorted(terms.values(), key=lambda item: item.term_key)),
    )


@lru_cache(maxsize=1)
def _load_runtime_field_lookup_corpus() -> AssistantFieldLookupCorpus:
    generated_corpus = load_generated_field_lookup_corpus()
    if generated_corpus is not None:
        return generated_corpus

    repo_root = _repo_root()
    if _has_live_field_lookup_sources(repo_root):
        LOGGER.warning(
            "assistant field/lookup corpus artifact missing; falling back to live source extraction from %s",
            repo_root,
        )
        return _build_field_lookup_corpus_from_sources(str(repo_root.resolve()))

    LOGGER.warning(
        "assistant field/lookup corpus unavailable: neither packaged artifact nor live source files are present"
    )
    return AssistantFieldLookupCorpus(field_definitions=(), lookup_definitions=(), term_definitions=())


def load_generated_field_lookup_corpus() -> AssistantFieldLookupCorpus | None:
    payload = _load_generated_field_lookup_payload()
    if payload is None:
        return None
    return _deserialize_corpus(payload)


def _load_generated_field_lookup_payload() -> dict[str, Any] | None:
    try:
        package_root = resources.files(_GENERATED_PACKAGE)
    except (FileNotFoundError, ModuleNotFoundError):
        return None
    artifact_path = package_root / _GENERATED_CORPUS_FILENAME
    if not artifact_path.is_file():
        return None
    return json.loads(artifact_path.read_text(encoding="utf-8"))


def get_field_lookup_corpus_status() -> AssistantFieldLookupCorpusStatus:
    payload = _load_generated_field_lookup_payload()
    artifact_loaded = payload is not None
    corpus = load_generated_field_lookup_corpus() if artifact_loaded else _load_runtime_field_lookup_corpus()
    counts_by_module = field_definition_counts_by_module() if corpus.field_definitions else {}
    return AssistantFieldLookupCorpusStatus(
        artifact_loaded=artifact_loaded,
        artifact_version=str(payload.get("schema_version")) if isinstance(payload, dict) else None,
        field_count=len(corpus.field_definitions),
        lookup_count=len(corpus.lookup_definitions),
        term_count=len(corpus.term_definitions),
        counts_by_module=counts_by_module,
    )


def export_field_lookup_corpus(
    *,
    repo_root: Path,
    output_path: Path,
) -> dict[str, Any]:
    _validate_required_generation_sources(repo_root)
    corpus = build_field_lookup_corpus(repo_root)
    payload = _serialize_corpus(
        corpus,
        generated_from=[
            "frontend_i18n",
            "frontend_vue",
            "typescript_api",
            "backend_schema",
            "page_help",
        ],
        source_hashes=_collect_source_hashes(repo_root),
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {
        "field_count": len(corpus.field_definitions),
        "lookup_count": len(corpus.lookup_definitions),
        "term_count": len(corpus.term_definitions),
        "field_counts_by_module": field_definition_counts_by_module(repo_root),
        "lookup_counts_by_module": lookup_definition_counts_by_module(repo_root),
        "term_counts_by_module": term_definition_counts_by_module(repo_root),
        "warnings": _generation_warnings(repo_root, corpus),
    }


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


def detect_platform_term_signal(
    text: str,
    *,
    page_id: str | None = None,
    route_name: str | None = None,
) -> CorpusSignal | None:
    normalized_query = _extract_field_probe(text)
    if normalized_query is None:
        return None
    if normalized_query in _GENERIC_PLATFORM_TERM_QUERIES:
        return None
    term_matches = search_platform_terms(
        query=normalized_query,
        language_code=None,
        page_id=page_id,
        route_name=route_name,
        limit=5,
    )
    if not term_matches:
        return None
    return CorpusSignal(
        normalized_query=normalized_query,
        field_matches=(),
        lookup_matches=(),
        term_matches=tuple(term_matches),
        ambiguous=_is_ambiguous_term_signal(
            normalized_query=normalized_query,
            term_matches=term_matches,
        ),
        intent_category=_infer_platform_term_intent_category(term_matches[0]),
        matched_via_route_context=False,
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


def search_platform_terms(
    *,
    query: str,
    language_code: str | None,
    page_id: str | None,
    route_name: str | None,
    limit: int = 5,
    repo_root: Path | None = None,
) -> list[PlatformTermSearchMatch]:
    normalized_query = _extract_field_probe(query) or _normalize_query(query)
    if not normalized_query:
        return []
    corpus = build_field_lookup_corpus(repo_root)
    matches: list[PlatformTermSearchMatch] = []
    for definition in corpus.term_definitions:
        score = _score_platform_term_definition(
            definition=definition,
            query=normalized_query,
            page_id=page_id,
            route_name=route_name,
        )
        if score <= 0:
            continue
        matches.append(
            PlatformTermSearchMatch(
                term_key=definition.term_key,
                label=_localized_platform_term_label(definition, language_code),
                module_key=definition.module_key,
                page_id=definition.page_id,
                concept_type=definition.concept_type,
                ui_term_type=definition.ui_term_type,
                definition=_localized_platform_term_definition(definition, language_code),
                source_basis=list(definition.source_basis),
                confidence=definition.confidence,
                score=score,
            )
        )
    matches.sort(key=lambda item: (-item.score, item.term_key))
    return matches[: max(int(limit), 1)]


def get_lookup_definition(
    lookup_key: str,
    repo_root: Path | None = None,
) -> LookupDefinition | None:
    for definition in build_field_lookup_corpus(repo_root).lookup_definitions:
        if definition.lookup_key == lookup_key:
            return definition
    return None


def get_platform_term_definition(
    term_key: str,
    repo_root: Path | None = None,
) -> PlatformTermDefinition | None:
    for definition in build_field_lookup_corpus(repo_root).term_definitions:
        if definition.term_key == term_key:
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


def term_definition_counts_by_module(repo_root: Path | None = None) -> dict[str, int]:
    counts: dict[str, int] = {}
    for definition in build_field_lookup_corpus(repo_root).term_definitions:
        key = definition.module_key or "unknown"
        counts[key] = counts.get(key, 0) + 1
    return counts


def render_platform_term_dictionary_markdown(repo_root: Path | None = None) -> str:
    corpus = build_field_lookup_corpus(repo_root)
    lines = ["# Assistant Platform Term Dictionary", ""]
    for definition in corpus.term_definitions:
        lines.extend(
            [
                f"## {definition.term_key}",
                "",
                f"- canonical_name: {definition.canonical_name}",
                f"- module_key: {definition.module_key or 'unknown'}",
                f"- page_id: {definition.page_id or 'unknown'}",
                f"- concept_type: {definition.concept_type}",
                f"- ui_term_type: {definition.ui_term_type}",
                f"- route_names: {', '.join(definition.route_names) or 'none'}",
                f"- ui_contexts: {', '.join(definition.ui_contexts) or 'none'}",
                f"- labels_de: {', '.join(definition.labels.get('de', [])) or 'none'}",
                f"- labels_en: {', '.join(definition.labels.get('en', [])) or 'none'}",
                f"- definition_de: {definition.definition_de or 'n/a'}",
                f"- definition_en: {definition.definition_en or 'n/a'}",
                f"- related_terms: {', '.join(definition.related_terms) or 'none'}",
                f"- aliases: {', '.join(definition.aliases) or 'none'}",
            ]
        )
        if definition.source_basis:
            lines.append("- source_basis:")
            for basis in definition.source_basis[:8]:
                lines.append(f"  - [{basis.source_type}] {basis.source_name}: {basis.evidence}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def _build_platform_term_definitions(
    *,
    repo_root: Path,
    locale_labels: dict[str, dict[str, str]],
    backend_fields: dict[str, set[str]],
) -> dict[str, PlatformTermDefinition]:
    del locale_labels, backend_fields
    definitions: dict[str, PlatformTermDefinition] = {}
    for row in _extract_platform_term_rows(repo_root):
        override = _platform_term_override_for_source_key(row["source_key"])
        if override is not None:
            term_key = str(override["term_key"])
            definition = definitions.setdefault(
                term_key,
                PlatformTermDefinition(
                    term_key=term_key,
                    canonical_name=str(override["canonical_name"]),
                    module_key=_optional_string(override.get("module_key")),
                    page_id=_optional_string(override.get("page_id")),
                    route_names=_sorted_unique_strings(override.get("route_names", [])),
                    concept_type=str(override.get("concept_type") or "domain_concept"),
                    ui_term_type=str(override.get("ui_term_type") or "domain_concept"),
                    ui_contexts=_sorted_unique_strings(override.get("ui_contexts", [])),
                    labels={key: _sorted_unique_strings(values) for key, values in dict(override.get("labels", {})).items()},
                    aliases=_sorted_unique_strings(override.get("aliases", [])),
                    definition_en=_optional_string(override.get("definition_en")),
                    definition_de=_optional_string(override.get("definition_de")),
                    related_terms=_sorted_unique_strings(override.get("related_terms", [])),
                    source_basis=[],
                    confidence="high",
                ),
            )
        else:
            term_key = _default_platform_term_key(row)
            label_en = row["labels"].get("en", [row["canonical_name"]])[0]
            label_de = row["labels"].get("de", [label_en])[0]
            definition = definitions.setdefault(
                term_key,
                PlatformTermDefinition(
                    term_key=term_key,
                    canonical_name=row["canonical_name"],
                    module_key=row["module_key"],
                    page_id=row["page_id"],
                    route_names=list(row["route_names"]),
                    concept_type="domain_concept" if row["ui_term_type"] in {"hint_text", "empty_state"} else "ui_term",
                    ui_term_type=row["ui_term_type"],
                    ui_contexts=[],
                    labels={},
                    aliases=[],
                    definition_en=f"{label_en} is a verified visible SicherPlan UI term in the {row['file_stem']} context.",
                    definition_de=f"{label_de} ist ein verifizierter sichtbarer SicherPlan-Begriff im Kontext {row['file_stem']}.",
                    related_terms=[],
                    source_basis=[],
                    confidence="medium",
                ),
            )

        for language_code, values in row["labels"].items():
            for value in values:
                _add_label(definition.labels, language_code, value)
                _append_unique(definition.aliases, value)
        _append_unique(definition.aliases, row["source_key"])
        _append_unique(definition.ui_contexts, row["ui_context"])
        definition.source_basis.append(
            FieldSourceBasis(
                source_type=row["source_type"],
                source_name=row["source_name"],
                page_id=row["page_id"],
                module_key=row["module_key"],
                evidence=row["evidence"],
            )
        )

    _apply_platform_term_overrides(definitions)
    for definition in definitions.values():
        definition.route_names = _sorted_unique_strings(definition.route_names)
        definition.ui_contexts = _sorted_unique_strings(definition.ui_contexts)
        definition.aliases = _sorted_unique_strings(definition.aliases)
        definition.related_terms = _sorted_unique_strings(definition.related_terms)
        definition.source_basis = _sorted_unique_source_basis(definition.source_basis)
        definition.confidence = _platform_term_confidence(definition)
    return definitions


def _extract_platform_term_rows(repo_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    i18n_root = repo_root / "web/apps/web-antd/src/sicherplan-legacy/i18n"
    for path in _sorted_rglob(i18n_root, "*.messages.ts"):
        module_key, page_id, route_names, file_context = _message_file_context(path.name)
        for source_key, bundle in _parse_messages_ts_file(path).items():
            ui_term_type = _classify_platform_term_key(source_key)
            if ui_term_type is None:
                continue
            labels = {code: [text] for code, text in bundle.items() if text}
            rows.append(
                {
                    "source_key": source_key,
                    "canonical_name": _canonicalize_platform_term_key(source_key),
                    "labels": labels,
                    "module_key": module_key,
                    "page_id": page_id,
                    "route_names": route_names,
                    "ui_term_type": ui_term_type,
                    "ui_context": _humanize_platform_key(source_key),
                    "source_type": "frontend_i18n_label",
                    "source_name": path.name,
                    "evidence": f"{source_key} defines the visible UI term in {path.name}.",
                    "file_stem": file_context,
                }
            )
    locale_paths = [
        repo_root / _DE_LOCALE_PATH,
        repo_root / _EN_LOCALE_PATH,
        repo_root / _FA_LOCALE_PATH,
    ]
    for path in locale_paths:
        if not path.exists():
            continue
        language_code = "de" if "de-DE" in path.as_posix() else "en" if "en-US" in path.as_posix() else "fa"
        flattened = _flatten_json(json.loads(path.read_text(encoding="utf-8")))
        for key, value in flattened.items():
            if not isinstance(value, str):
                continue
            source_key = key.split(".")[-1]
            ui_term_type = _classify_platform_term_key(source_key)
            if ui_term_type is None:
                continue
            rows.append(
                {
                    "source_key": source_key,
                    "canonical_name": _canonicalize_platform_term_key(source_key),
                    "labels": {language_code: [value]},
                    "module_key": None,
                    "page_id": None,
                    "route_names": [],
                    "ui_term_type": ui_term_type,
                    "ui_context": _humanize_platform_key(source_key),
                    "source_type": "frontend_locale",
                    "source_name": path.name,
                    "evidence": f"{key} defines a visible localized UI term in {path.name}.",
                    "file_stem": "locale_catalog",
                }
            )
    return rows


def _parse_messages_ts_file(path: Path) -> dict[str, dict[str, str]]:
    text = path.read_text(encoding="utf-8")
    labels: dict[str, dict[str, str]] = {}
    language_code: str | None = None
    depth = 0
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("de: {"):
            language_code = "de"
            depth = 1
            continue
        if stripped.startswith("en: {"):
            language_code = "en"
            depth = 1
            continue
        if language_code is None:
            continue
        depth += line.count("{") - line.count("}")
        if depth <= 0:
            language_code = None
            depth = 0
            continue
        match = re.match(r'^\s*(?P<key>[A-Za-z0-9_]+):\s*"(?P<value>(?:[^"\\]|\\.)*)",?\s*$', line)
        if match:
            labels.setdefault(match.group("key"), {})[language_code] = _unescape_locale_value(match.group("value"))
    return labels


def _message_file_context(file_name: str) -> tuple[str | None, str | None, list[str], str]:
    module_key, page_id, route_names, file_context = _MESSAGE_FILE_CONTEXT.get(file_name, (None, None, [], Path(file_name).stem))
    return module_key, page_id, list(route_names), file_context


def _classify_platform_term_key(source_key: str) -> str | None:
    if source_key in _EXCLUDED_PLATFORM_TERM_KEYS:
        return None
    if _platform_term_override_for_source_key(source_key) is not None:
        return "domain_concept"
    for prefix, ui_term_type in _TERM_PREFIX_TYPES:
        if source_key.startswith(prefix):
            return ui_term_type
    for suffix, ui_term_type in _TERM_SUFFIX_TYPES:
        if source_key.endswith(suffix):
            return ui_term_type
    return None


def _canonicalize_platform_term_key(source_key: str) -> str:
    if source_key.startswith("fields"):
        source_key = source_key[len("fields") :]
    elif source_key.startswith("detailTab"):
        source_key = source_key[len("detailTab") :]
    elif source_key.startswith("filters"):
        source_key = source_key[len("filters") :]
    for suffix, _ in _TERM_SUFFIX_TYPES:
        if source_key.endswith(suffix):
            source_key = source_key[: -len(suffix)]
            break
    if source_key.endswith("s") and len(source_key) > 4:
        source_key = source_key[:-1]
    return _normalize_field_name(source_key)


def _default_platform_term_key(row: dict[str, Any]) -> str:
    module_key = row.get("module_key") or "platform"
    file_stem = str(row.get("file_stem") or "ui")
    return f"{module_key}.{file_stem}.{row['canonical_name']}"


def _humanize_platform_key(source_key: str) -> str:
    cleaned = source_key
    for prefix, _ in _TERM_PREFIX_TYPES:
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix) :]
            break
    cleaned = re.sub(r"(?!^)([A-Z])", r" \1", cleaned).strip()
    return cleaned or source_key


def _platform_term_override_for_source_key(source_key: str) -> dict[str, Any] | None:
    for term_key, payload in _PLATFORM_TERM_OVERRIDES.items():
        if source_key in payload["source_keys"]:
            override = dict(payload)
            override["term_key"] = term_key
            return override
    return None


def _apply_platform_term_overrides(definitions: dict[str, PlatformTermDefinition]) -> None:
    definition = definitions.get("planning.staffing.demand_groups")
    if definition is None:
        return
    definition.source_basis.extend(
        [
            FieldSourceBasis(
                source_type="frontend_component",
                source_name="PlanningStaffingCoverageView.vue",
                page_id="P-04",
                module_key="planning",
                evidence="PlanningStaffingCoverageView.vue renders Demand Groups in the Demand and staffing tab and blocks staffing actions until a demand group exists.",
            ),
            FieldSourceBasis(
                source_type="frontend_helper",
                source_name="planningStaffing.helpers.js",
                page_id="P-04",
                module_key="planning",
                evidence="planningStaffing.helpers.js treats shifts without demand_groups as setup_required coverage.",
            ),
            FieldSourceBasis(
                source_type="frontend_api",
                source_name="planningStaffing.ts",
                page_id="P-04",
                module_key="planning",
                evidence="planningStaffing.ts exposes createDemandGroup and updateDemandGroup APIs for staffing workspace demand-group setup.",
            ),
            FieldSourceBasis(
                source_type="backend_schema",
                source_name="schemas.py",
                page_id="P-04",
                module_key="planning",
                evidence="Planning schemas define demand groups with function_type_id, qualification_type_id, min_qty, target_qty, sort_order, mandatory_flag, and remark.",
            ),
            FieldSourceBasis(
                source_type="backend_service",
                source_name="staffing_service.py",
                page_id="P-04",
                module_key="planning",
                evidence="Planning staffing service enforces demand-group-backed staffing operations before shift staffing can proceed meaningfully.",
            ),
        ]
    )


def _platform_term_confidence(definition: PlatformTermDefinition) -> str:
    if definition.definition_de and definition.definition_en and len(definition.source_basis) >= 3:
        return "high"
    if definition.source_basis:
        return "medium"
    return "low"


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
    for path in _sorted_rglob(repo_root / "web/apps/web-antd/src", "*.vue"):
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
    for path in _sorted_rglob(repo_root / "web/apps/web-antd/src", "*.ts"):
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
    for path in _sorted_rglob(repo_root / "backend/app/modules", "*"):
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


def _localized_platform_term_label(definition: PlatformTermDefinition, language_code: str | None) -> str:
    if language_code and definition.labels.get(language_code):
        return _preferred_platform_term_label(definition.labels[language_code], definition.canonical_name)
    if definition.labels.get("de"):
        return _preferred_platform_term_label(definition.labels["de"], definition.canonical_name)
    if definition.labels.get("en"):
        return _preferred_platform_term_label(definition.labels["en"], definition.canonical_name)
    return definition.canonical_name


def _localized_platform_term_definition(
    definition: PlatformTermDefinition,
    language_code: str | None,
) -> str | None:
    if language_code == "de":
        return definition.definition_de or definition.definition_en
    if language_code == "en":
        return definition.definition_en or definition.definition_de
    return definition.definition_de or definition.definition_en


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


def _score_platform_term_definition(
    *,
    definition: PlatformTermDefinition,
    query: str,
    page_id: str | None,
    route_name: str | None,
) -> float:
    score = 0.0

    def _apply(values: list[str], *, exact: float, contains_query: float, query_contains: float) -> None:
        nonlocal score
        for value in values:
            normalized = _normalize_query(value)
            if not normalized:
                continue
            if normalized in _GENERIC_PLATFORM_TERM_QUERIES and normalized != query:
                continue
            if normalized == query:
                score = max(score, exact)
            elif _contains_token_phrase(normalized, query):
                score = max(score, contains_query)
            elif _contains_token_phrase(query, normalized):
                score = max(score, query_contains)

    _apply(
        [definition.term_key, definition.canonical_name],
        exact=102.0,
        contains_query=92.0,
        query_contains=84.0,
    )
    _apply(
        list(definition.aliases or []) + [item for values in definition.labels.values() for item in values],
        exact=110.0,
        contains_query=100.0,
        query_contains=90.0,
    )
    _apply(
        list(definition.related_terms or []),
        exact=86.0,
        contains_query=74.0,
        query_contains=58.0,
    )
    _apply(
        list(definition.ui_contexts or []),
        exact=72.0,
        contains_query=62.0,
        query_contains=48.0,
    )
    if score <= 0:
        return 0.0
    if definition.page_id and page_id == definition.page_id:
        score += 12.0
    if route_name and route_name in definition.route_names:
        score += 8.0
    if definition.confidence == "high":
        score += 6.0
    elif definition.confidence == "medium":
        score += 3.0
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


def _serialize_corpus(
    corpus: AssistantFieldLookupCorpus,
    *,
    generated_from: list[str],
    source_hashes: dict[str, str],
) -> dict[str, Any]:
    return {
        "schema_version": _FIELD_LOOKUP_SCHEMA_VERSION,
        "generated_from": sorted({item for item in generated_from if item}),
        "fields": [_serialize_field_definition(item) for item in corpus.field_definitions],
        "lookups": [_serialize_lookup_definition(item) for item in corpus.lookup_definitions],
        "terms": [_serialize_platform_term_definition(item) for item in corpus.term_definitions],
        "source_hashes": dict(sorted(source_hashes.items())),
    }


def _deserialize_corpus(payload: dict[str, Any]) -> AssistantFieldLookupCorpus:
    fields = tuple(
        sorted(
            (_deserialize_field_definition(item) for item in payload.get("fields", []) if isinstance(item, dict)),
            key=lambda item: item.field_key,
        )
    )
    lookups = tuple(
        sorted(
            (_deserialize_lookup_definition(item) for item in payload.get("lookups", []) if isinstance(item, dict)),
            key=lambda item: item.lookup_key,
        )
    )
    terms = tuple(
        sorted(
            (
                _deserialize_platform_term_definition(item)
                for item in payload.get("terms", [])
                if isinstance(item, dict)
            ),
            key=lambda item: item.term_key,
        )
    )
    return AssistantFieldLookupCorpus(
        field_definitions=fields,
        lookup_definitions=lookups,
        term_definitions=terms,
    )


def _serialize_field_definition(definition: FieldDefinition) -> dict[str, Any]:
    return {
        "aliases": _sorted_unique_strings(definition.aliases),
        "binding_paths": _sorted_unique_strings(definition.binding_paths),
        "canonical_name": definition.canonical_name,
        "confidence": definition.confidence,
        "definition_de": definition.definition_de,
        "definition_en": definition.definition_en,
        "entity_type": definition.entity_type,
        "example_values": _sorted_unique_strings(definition.example_values),
        "field_key": definition.field_key,
        "form_contexts": _sorted_unique_strings(definition.form_contexts),
        "input_type": definition.input_type,
        "label_keys": _sorted_unique_strings(definition.label_keys),
        "labels": {key: _sorted_unique_strings(values) for key, values in sorted(definition.labels.items())},
        "module_key": definition.module_key,
        "page_id": definition.page_id,
        "related_fields": _sorted_unique_strings(definition.related_fields),
        "required": definition.required,
        "route_names": _sorted_unique_strings(definition.route_names),
        "schema_fields": _sorted_unique_strings(definition.schema_fields),
        "sensitive": definition.sensitive,
        "source_basis": [_serialize_source_basis(item) for item in _sorted_unique_source_basis(definition.source_basis)],
    }


def _deserialize_field_definition(payload: dict[str, Any]) -> FieldDefinition:
    return FieldDefinition(
        field_key=str(payload.get("field_key") or ""),
        canonical_name=str(payload.get("canonical_name") or ""),
        module_key=_optional_string(payload.get("module_key")),
        page_id=_optional_string(payload.get("page_id")),
        route_names=_string_list(payload.get("route_names")),
        entity_type=_optional_string(payload.get("entity_type")),
        form_contexts=_string_list(payload.get("form_contexts")),
        input_type=_optional_string(payload.get("input_type")),
        required=payload.get("required") if isinstance(payload.get("required"), bool) else None,
        sensitive=bool(payload.get("sensitive", False)),
        labels=_deserialize_labels(payload.get("labels")),
        aliases=_string_list(payload.get("aliases")),
        definition_en=_optional_string(payload.get("definition_en")),
        definition_de=_optional_string(payload.get("definition_de")),
        example_values=_string_list(payload.get("example_values")),
        related_fields=_string_list(payload.get("related_fields")),
        source_basis=[_deserialize_source_basis(item) for item in payload.get("source_basis", []) if isinstance(item, dict)],
        confidence=str(payload.get("confidence") or "low"),
        label_keys=_string_list(payload.get("label_keys")),
        binding_paths=_string_list(payload.get("binding_paths")),
        schema_fields=_string_list(payload.get("schema_fields")),
    )


def _serialize_lookup_definition(definition: LookupDefinition) -> dict[str, Any]:
    return {
        "aliases": _sorted_unique_strings(definition.aliases),
        "confidence": definition.confidence,
        "entity_type": definition.entity_type,
        "labels": {key: _sorted_unique_strings(values) for key, values in sorted(definition.labels.items())},
        "lookup_key": definition.lookup_key,
        "module_key": definition.module_key,
        "page_id": definition.page_id,
        "source_basis": [_serialize_source_basis(item) for item in _sorted_unique_source_basis(definition.source_basis)],
        "value_source_kind": definition.value_source_kind,
        "values": [_serialize_lookup_value_definition(item) for item in _sorted_lookup_values(definition.values)],
    }


def _serialize_platform_term_definition(definition: PlatformTermDefinition) -> dict[str, Any]:
    return {
        "aliases": _sorted_unique_strings(definition.aliases),
        "canonical_name": definition.canonical_name,
        "concept_type": definition.concept_type,
        "confidence": definition.confidence,
        "definition_de": definition.definition_de,
        "definition_en": definition.definition_en,
        "labels": {key: _sorted_unique_strings(values) for key, values in sorted(definition.labels.items())},
        "module_key": definition.module_key,
        "page_id": definition.page_id,
        "related_terms": _sorted_unique_strings(definition.related_terms),
        "route_names": _sorted_unique_strings(definition.route_names),
        "source_basis": [_serialize_source_basis(item) for item in _sorted_unique_source_basis(definition.source_basis)],
        "term_key": definition.term_key,
        "ui_contexts": _sorted_unique_strings(definition.ui_contexts),
        "ui_term_type": definition.ui_term_type,
    }


def _deserialize_lookup_definition(payload: dict[str, Any]) -> LookupDefinition:
    return LookupDefinition(
        lookup_key=str(payload.get("lookup_key") or ""),
        module_key=_optional_string(payload.get("module_key")),
        page_id=_optional_string(payload.get("page_id")),
        entity_type=_optional_string(payload.get("entity_type")),
        labels=_deserialize_labels(payload.get("labels")),
        aliases=_string_list(payload.get("aliases")),
        values=[_deserialize_lookup_value_definition(item) for item in payload.get("values", []) if isinstance(item, dict)],
        value_source_kind=str(payload.get("value_source_kind") or "static"),
        source_basis=[_deserialize_source_basis(item) for item in payload.get("source_basis", []) if isinstance(item, dict)],
        confidence=str(payload.get("confidence") or "low"),
    )


def _deserialize_platform_term_definition(payload: dict[str, Any]) -> PlatformTermDefinition:
    return PlatformTermDefinition(
        term_key=str(payload.get("term_key") or ""),
        canonical_name=str(payload.get("canonical_name") or ""),
        module_key=_optional_string(payload.get("module_key")),
        page_id=_optional_string(payload.get("page_id")),
        route_names=_string_list(payload.get("route_names")),
        concept_type=str(payload.get("concept_type") or "domain_concept"),
        ui_term_type=str(payload.get("ui_term_type") or "domain_concept"),
        ui_contexts=_string_list(payload.get("ui_contexts")),
        labels=_deserialize_labels(payload.get("labels")),
        aliases=_string_list(payload.get("aliases")),
        definition_en=_optional_string(payload.get("definition_en")),
        definition_de=_optional_string(payload.get("definition_de")),
        related_terms=_string_list(payload.get("related_terms")),
        source_basis=[_deserialize_source_basis(item) for item in payload.get("source_basis", []) if isinstance(item, dict)],
        confidence=str(payload.get("confidence") or "low"),
    )


def _serialize_lookup_value_definition(value: LookupValueDefinition) -> dict[str, Any]:
    return {
        "labels": dict(sorted(value.labels.items())),
        "meaning_de": value.meaning_de,
        "meaning_en": value.meaning_en,
        "value": value.value,
    }


def _deserialize_lookup_value_definition(payload: dict[str, Any]) -> LookupValueDefinition:
    labels_raw = payload.get("labels")
    labels = {str(key): str(value) for key, value in labels_raw.items()} if isinstance(labels_raw, dict) else {}
    return LookupValueDefinition(
        value=str(payload.get("value") or ""),
        labels=labels,
        meaning_de=_optional_string(payload.get("meaning_de")),
        meaning_en=_optional_string(payload.get("meaning_en")),
    )


def _serialize_source_basis(basis: FieldSourceBasis) -> dict[str, Any]:
    return {
        "evidence": basis.evidence,
        "module_key": basis.module_key,
        "page_id": basis.page_id,
        "source_name": basis.source_name,
        "source_type": basis.source_type,
    }


def _deserialize_source_basis(payload: dict[str, Any]) -> FieldSourceBasis:
    return FieldSourceBasis(
        source_type=str(payload.get("source_type") or ""),
        source_name=str(payload.get("source_name") or ""),
        evidence=str(payload.get("evidence") or ""),
        page_id=_optional_string(payload.get("page_id")),
        module_key=_optional_string(payload.get("module_key")),
    )


def _deserialize_labels(payload: Any) -> dict[str, list[str]]:
    if not isinstance(payload, dict):
        return {}
    result: dict[str, list[str]] = {}
    for key, value in payload.items():
        if isinstance(value, list):
            result[str(key)] = [str(item) for item in value if str(item).strip()]
    return result


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return _sorted_unique_strings(str(item) for item in value if str(item).strip())


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _required_generation_sources(repo_root: Path) -> dict[str, Path]:
    return {
        "legacy_messages": repo_root / _LEGACY_MESSAGES_PATH,
        "de_locale": repo_root / _DE_LOCALE_PATH,
        "en_locale": repo_root / _EN_LOCALE_PATH,
        "frontend_root": repo_root / "web/apps/web-antd/src",
        "backend_modules": repo_root / "backend/app/modules",
    }


def _validate_required_generation_sources(repo_root: Path) -> None:
    missing = [f"{name}:{path}" for name, path in _required_generation_sources(repo_root).items() if not path.exists()]
    if missing:
        raise FileNotFoundError(
            "field/lookup corpus generation requires a full repository checkout; missing sources: "
            + ", ".join(missing)
        )


def _has_live_field_lookup_sources(repo_root: Path) -> bool:
    required = _required_generation_sources(repo_root)
    return required["legacy_messages"].exists() and required["de_locale"].exists() and required["frontend_root"].exists()


def _collect_source_hashes(repo_root: Path) -> dict[str, str]:
    return {
        "backend_schema_fields": _semantic_hash(_extract_backend_fields(repo_root)),
        "locale_labels": _semantic_hash(_extract_locale_labels(repo_root)),
        "page_help_seed_data": _semantic_hash(_serialize_page_help_seeds()),
        "typescript_interfaces": _semantic_hash(_extract_typescript_interfaces(repo_root)),
        "vue_field_bindings": _semantic_hash(_extract_vue_field_bindings(repo_root)),
    }


def _generation_warnings(
    repo_root: Path,
    corpus: AssistantFieldLookupCorpus,
) -> list[str]:
    warnings: list[str] = []
    if not (repo_root / _FA_LOCALE_PATH).exists():
        warnings.append("fa_locale_missing")
    if not corpus.field_definitions:
        warnings.append("no_field_definitions_extracted")
    if not corpus.lookup_definitions:
        warnings.append("no_lookup_definitions_extracted")
    if not corpus.term_definitions:
        warnings.append("no_platform_term_definitions_extracted")
    return warnings


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


def _is_ambiguous_term_signal(
    *,
    normalized_query: str,
    term_matches: list[PlatformTermSearchMatch],
) -> bool:
    if len(term_matches) <= 1:
        return False
    top_match = term_matches[0]
    for candidate in term_matches[1:3]:
        if candidate.term_key == top_match.term_key:
            continue
        if candidate.score < top_match.score - 12.0:
            continue
        if candidate.page_id != top_match.page_id or candidate.module_key != top_match.module_key:
            return True
    return normalized_query in _GENERIC_AMBIGUOUS_LABELS


def _infer_platform_term_intent_category(match: PlatformTermSearchMatch) -> str:
    if match.ui_term_type == "action_label":
        return "action_label_question"
    if match.ui_term_type == "section_title":
        return "section_title_question"
    if match.ui_term_type == "validation_rule":
        return "validation_rule_meaning_question"
    if match.ui_term_type == "status_label":
        return "status_or_option_meaning_question"
    if match.concept_type in {"staffing_concept", "domain_concept"}:
        return "platform_term_meaning_question"
    if match.ui_term_type in {"field_label", "filter_label", "tab_title", "empty_state", "hint_text"}:
        return "ui_label_meaning_question"
    return "domain_concept_question"


def _preferred_platform_term_label(labels: list[str], canonical_name: str) -> str:
    if not labels:
        return canonical_name
    canonical_tokens = set(_tokenize_query(canonical_name.replace("_", " ")))
    ranked = sorted(
        labels,
        key=lambda item: (
            0 if canonical_tokens and canonical_tokens.issubset(set(_tokenize_query(item))) else 1,
            len(item),
            item.casefold(),
        ),
    )
    return ranked[0]


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


def _sorted_unique_strings(values: Any) -> list[str]:
    return sorted({str(value).strip() for value in values if str(value).strip()})


def _source_basis_sort_key(basis: FieldSourceBasis) -> tuple[str, str, str, str, str]:
    return (
        basis.source_type,
        basis.source_name,
        basis.page_id or "",
        basis.module_key or "",
        basis.evidence,
    )


def _sorted_unique_source_basis(items: list[FieldSourceBasis]) -> list[FieldSourceBasis]:
    unique: dict[tuple[str, str, str, str, str], FieldSourceBasis] = {}
    for item in items:
        unique[_source_basis_sort_key(item)] = item
    return [unique[key] for key in sorted(unique)]


def _lookup_value_sort_key(value: LookupValueDefinition) -> tuple[str, tuple[tuple[str, str], ...], str, str]:
    return (
        value.value,
        tuple(sorted((str(key), str(label)) for key, label in value.labels.items())),
        value.meaning_de or "",
        value.meaning_en or "",
    )


def _sorted_lookup_values(values: list[LookupValueDefinition]) -> list[LookupValueDefinition]:
    unique: dict[tuple[str, tuple[tuple[str, str], ...], str, str], LookupValueDefinition] = {}
    for value in values:
        unique[_lookup_value_sort_key(value)] = value
    return [unique[key] for key in sorted(unique)]


def _sorted_rglob(root: Path, pattern: str) -> list[Path]:
    return sorted(root.rglob(pattern), key=lambda path: path.as_posix())


def _is_excluded_hash_path(path: Path, repo_root: Path) -> bool:
    relative = path.relative_to(repo_root)
    if any(part in _HASH_EXCLUDED_DIR_NAMES for part in relative.parts):
        return True
    if any(part.endswith(".egg-info") for part in relative.parts):
        return True
    if path.name in _HASH_EXCLUDED_FILE_NAMES and "generated" in relative.parts:
        return True
    if path.suffix in _HASH_EXCLUDED_FILE_SUFFIXES:
        return True
    return False


def _iter_hashable_files(root: Path, repo_root: Path) -> list[Path]:
    return [
        path
        for path in _sorted_rglob(root, "*")
        if path.is_file() and not _is_excluded_hash_path(path, repo_root)
    ]


def _semantic_hash(value: Any) -> str:
    normalized = _normalize_semantic_hash_value(value)
    payload = json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _normalize_semantic_hash_value(value: Any) -> Any:
    if is_dataclass(value):
        return _normalize_semantic_hash_value(value.__dict__)
    if isinstance(value, dict):
        return {
            str(key): _normalize_semantic_hash_value(nested)
            for key, nested in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if isinstance(value, set):
        return sorted(_normalize_semantic_hash_value(item) for item in value)
    if isinstance(value, (list, tuple)):
        return [_normalize_semantic_hash_value(item) for item in value]
    if isinstance(value, Path):
        return value.as_posix()
    return value


def _serialize_page_help_seeds() -> list[dict[str, Any]]:
    payload: list[dict[str, Any]] = []
    for seed in sorted(
        ASSISTANT_PAGE_HELP_SEEDS,
        key=lambda item: (
            item.page_id,
            item.language_code or "",
            item.route_name or "",
            item.path_template or "",
            item.module_key,
        ),
    ):
        payload.append(
            {
                "language_code": seed.language_code,
                "manifest_json": seed.manifest_json,
                "manifest_version": seed.manifest_version,
                "module_key": seed.module_key,
                "page_id": seed.page_id,
                "path_template": seed.path_template,
                "route_name": seed.route_name,
                "status": seed.status,
                "verified_from": seed.verified_from,
            }
        )
    return payload


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


__all__ = [
    "AssistantFieldLookupCorpus",
    "AssistantFieldLookupCorpusStatus",
    "CorpusSignal",
    "FieldDefinition",
    "FieldSearchMatch",
    "FieldSourceBasis",
    "LookupDefinition",
    "LookupSearchMatch",
    "LookupValueDefinition",
    "PlatformTermDefinition",
    "PlatformTermSearchMatch",
    "build_field_lookup_corpus",
    "detect_field_or_lookup_signal",
    "detect_platform_term_signal",
    "export_field_lookup_corpus",
    "field_definition_counts_by_module",
    "get_field_lookup_corpus_status",
    "get_platform_term_definition",
    "load_generated_field_lookup_corpus",
    "lookup_definition_counts_by_module",
    "render_api_schema_field_markdown",
    "render_field_dictionary_markdown",
    "render_form_field_catalog_markdown",
    "render_frontend_i18n_label_markdown",
    "render_lookup_dictionary_markdown",
    "render_platform_term_dictionary_markdown",
    "search_field_dictionary",
    "search_lookup_dictionary",
    "search_platform_terms",
    "term_definition_counts_by_module",
]
