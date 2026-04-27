"""Knowledge ingestion orchestration for assistant documentation sources."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from app.modules.assistant.expert_knowledge_pack import render_expert_knowledge_pack_markdown
from app.modules.assistant.page_catalog_seed import ASSISTANT_PAGE_ROUTE_SEEDS
from app.modules.assistant.page_help_seed import ASSISTANT_PAGE_HELP_SEEDS
from app.modules.assistant.workflow_help import WORKFLOW_HELP_SEEDS
from app.modules.assistant.knowledge.chunker import chunk_text
from app.modules.assistant.knowledge.repository import AssistantKnowledgeRepository
from app.modules.assistant.knowledge.source_loader import KnowledgeSourceLoader
from app.modules.assistant.knowledge.types import (
    ChunkedKnowledgeDocument,
    KnowledgeSourceRegistration,
    UnsupportedKnowledgeSourceError,
)
from app.modules.assistant.models import AssistantKnowledgeSource


@dataclass(frozen=True)
class KnowledgeIngestionFailure:
    source_path: str
    error: str


@dataclass(frozen=True)
class KnowledgeIngestionResult:
    sources_seen: int
    sources_indexed: int
    sources_skipped: int
    sources_failed: int
    chunks_created: int
    failures: list[KnowledgeIngestionFailure]


class AssistantKnowledgeIngestionService:
    def __init__(
        self,
        *,
        loader: KnowledgeSourceLoader,
        repository: AssistantKnowledgeRepository | None = None,
    ) -> None:
        self.loader = loader
        self.repository = repository

    def ingest(self, registrations: list[KnowledgeSourceRegistration]) -> KnowledgeIngestionResult:
        if self.repository is None:
            raise RuntimeError("Knowledge repository is required for ingestion.")

        sources_indexed = 0
        sources_skipped = 0
        sources_failed = 0
        chunks_created = 0
        failures: list[KnowledgeIngestionFailure] = []

        for registration in registrations:
            try:
                loaded = self.loader.load(registration)
                unchanged = self.repository.find_active_source_by_path_hash(
                    source_path=loaded.source_path,
                    source_hash=loaded.source_hash,
                )
                if unchanged is not None:
                    sources_skipped += 1
                    continue

                existing = self.repository.find_latest_source_by_path(source_path=loaded.source_path)
                source = self.repository.upsert_source(
                    existing_source=existing,
                    source_type=loaded.source_type,
                    source_name=loaded.source_name,
                    source_path=loaded.source_path,
                    source_hash=loaded.source_hash,
                    source_version=loaded.source_version,
                    source_language=loaded.language_code,
                    status="active",
                )
                chunk_rows = self._build_chunk_rows(
                    source_type=loaded.source_type,
                    source_name=loaded.source_name,
                    source_path=loaded.source_path,
                    content=loaded.content,
                    language_code=loaded.language_code,
                )
                self.repository.replace_chunks(source=source, chunks=chunk_rows)
                sources_indexed += 1
                chunks_created += len(chunk_rows)
            except Exception as exc:
                sources_failed += 1
                failures.append(
                    KnowledgeIngestionFailure(
                        source_path=registration.source_path,
                        error=str(exc),
                    )
                )
                self._mark_failed_source(registration=registration, error=exc)

        return KnowledgeIngestionResult(
            sources_seen=len(registrations),
            sources_indexed=sources_indexed,
            sources_skipped=sources_skipped,
            sources_failed=sources_failed,
            chunks_created=chunks_created,
            failures=failures,
        )

    def _mark_failed_source(self, *, registration: KnowledgeSourceRegistration, error: Exception) -> None:
        if self.repository is None:
            return
        if isinstance(error, UnsupportedKnowledgeSourceError):
            status = "failed"
        else:
            status = "failed"
        existing = self.repository.find_latest_source_by_path(source_path=str(Path(registration.source_path).resolve()))
        self.repository.upsert_source(
            existing_source=existing,
            source_type=registration.source_type,
            source_name=registration.source_name,
            source_path=str(Path(registration.source_path).resolve()),
            source_hash=hashlib.sha256(
                f"failed:{registration.source_type}:{registration.source_path}".encode("utf-8")
            ).hexdigest(),
            source_version=None,
            source_language=None,
            status=status,
        )

    @staticmethod
    def _build_chunk_rows(
        *,
        source_type: str,
        source_name: str,
        source_path: str,
        content: str,
        language_code: str | None,
    ) -> list[dict[str, object]]:
        chunks = chunk_text(
            source_type=source_type,
            source_name=source_name,
            source_path=source_path,
            content=content,
            language_code=language_code,
        )
        return [_chunk_to_row(chunk) for chunk in chunks]


def _chunk_to_row(chunk: ChunkedKnowledgeDocument) -> dict[str, object]:
    return {
        "chunk_index": chunk.chunk_index,
        "title": chunk.title,
        "content": chunk.content,
        "language_code": chunk.metadata.language_code,
        "module_key": chunk.metadata.module_key,
        "page_id": chunk.metadata.page_id,
        "content_preview": chunk.metadata.content_preview,
        "workflow_keys": chunk.metadata.workflow_keys,
        "role_keys": chunk.metadata.role_keys,
        "permission_keys": chunk.metadata.permission_keys,
        "api_families": chunk.metadata.api_families,
        "domain_terms": chunk.metadata.domain_terms,
        "language_aliases": chunk.metadata.language_aliases,
        "token_count": chunk.metadata.token_count,
    }


def build_default_knowledge_registrations(repo_root: Path) -> list[KnowledgeSourceRegistration]:
    docs_root = repo_root / "docs"
    registrations: list[KnowledgeSourceRegistration] = []
    _append_registration_if_exists(
        registrations,
        source_type="sprint_doc",
        source_name="AI Assistant Sprint Plan",
        source_path=docs_root / "sprint" / "AI-Assistant.md",
    )
    _append_registration_if_exists(
        registrations,
        source_type="engineering_doc",
        source_name="AI Assistant Architecture",
        source_path=docs_root / "engineering" / "ai-assistant-architecture.md",
    )
    _append_registration_if_exists(
        registrations,
        source_type="security_doc",
        source_name="AI Assistant Security",
        source_path=docs_root / "security" / "ai-assistant-security.md",
    )
    _append_registration_if_exists(
        registrations,
        source_type="runbook",
        source_name="AI Assistant QA Plan",
        source_path=docs_root / "qa" / "ai-assistant-test-plan.md",
    )
    _append_registration_if_exists(
        registrations,
        source_type="operational_handbook",
        source_name="Operational Handbook",
        source_path=docs_root / "support" / "hypercare-runbook.md",
    )
    _append_registration_if_exists(
        registrations,
        source_type="user_manual",
        source_name="Role Guides User Manual",
        source_path=docs_root / "training" / "us-35-role-guides.md",
    )
    _append_registration_if_exists(
        registrations,
        source_type="implementation_data_model",
        source_name="Implementation Scope Review",
        source_path=docs_root / "discovery" / "us-1-t1-scope-review.md",
    )

    generated_root = repo_root / "tmp" / "assistant-knowledge"
    generated_root.mkdir(parents=True, exist_ok=True)
    page_catalog_path = generated_root / "page-route-catalog.md"
    page_help_path = generated_root / "page-help-manifest.md"
    workflow_path = generated_root / "workflow-help.md"
    ui_action_path = generated_root / "ui-action-catalog.md"
    api_endpoint_path = generated_root / "api-endpoint-map.md"
    role_page_coverage_path = generated_root / "role-page-coverage.md"
    operational_handbook_path = generated_root / "operational-handbook-generated.md"
    user_manual_path = generated_root / "user-manual-generated.md"
    implementation_data_model_path = generated_root / "implementation-data-model-generated.md"
    expert_knowledge_pack_path = generated_root / "expert-knowledge-pack.md"

    page_catalog_lines = ["# Assistant Page Route Catalog", ""]
    for seed in ASSISTANT_PAGE_ROUTE_SEEDS:
        page_catalog_lines.append(
            f"## {seed.page_id} {seed.label}\n\n"
            f"- route_name: {seed.route_name}\n"
            f"- path_template: {seed.path_template}\n"
            f"- module_key: {seed.module_key}\n"
            f"- api_families: {', '.join(seed.api_families) or 'none'}\n"
            f"- required_permissions: {', '.join(seed.required_permissions) or 'none'}\n"
            f"- allowed_role_keys: {', '.join(seed.allowed_role_keys) or 'none'}\n"
            f"- scope_kind: {seed.scope_kind or 'none'}\n"
        )
    page_catalog_path.write_text("\n".join(page_catalog_lines), encoding="utf-8")

    page_help_lines = ["# Assistant Page Help Manifest", ""]
    for seed in ASSISTANT_PAGE_HELP_SEEDS:
        actions = seed.manifest_json.get("primary_actions") or []
        form_sections = seed.manifest_json.get("form_sections") or []
        post_steps = seed.manifest_json.get("post_create_steps") or []
        page_help_lines.append(
            f"## {seed.page_id} {seed.language_code or 'und'}\n\n"
            f"- route_name: {seed.route_name}\n"
            f"- path_template: {seed.path_template}\n"
            f"- module_key: {seed.module_key}\n"
            f"- status: {seed.status}\n"
            f"- page_title: {seed.manifest_json.get('page_title', seed.page_id)}\n"
            f"- actions_registered: {len(actions)}\n"
            f"- verified_sections: {len(form_sections)}\n"
            f"- verified_post_steps: {len(post_steps)}\n"
        )
        if actions:
            page_help_lines.append("### Actions\n")
            for action in actions:
                page_help_lines.append(
                    f"- {action.get('label') or action.get('action_key')} "
                    f"[{action.get('label_status') or ('verified' if action.get('verified') else 'unverified')}]: "
                    f"{action.get('result') or 'documented action'}"
                )
        if form_sections:
            page_help_lines.append("\n### Sections\n")
            for section in form_sections:
                page_help_lines.append(
                    f"- {section.get('title') or section.get('section_key')}: "
                    f"{', '.join(field.get('label') or field.get('field_key') for field in section.get('fields', []))}"
                )
        if post_steps:
            page_help_lines.append("\n### Follow-up\n")
            for step in post_steps:
                page_help_lines.append(f"- {step.get('label') or step.get('step_key')}")
        page_help_lines.append("")
    page_help_path.write_text("\n".join(page_help_lines), encoding="utf-8")

    ui_action_lines = ["# Assistant UI Action Catalog", ""]
    for seed in ASSISTANT_PAGE_HELP_SEEDS:
        actions = seed.manifest_json.get("primary_actions") or []
        if not actions:
            continue
        ui_action_lines.append(
            f"## {seed.page_id} — {seed.manifest_json.get('page_title', seed.page_id)} ({seed.language_code or 'und'})\n"
        )
        for action in actions:
            ui_action_lines.append(
                f"- action_key: {action.get('action_key')}\n"
                f"  label: {action.get('label')}\n"
                f"  label_status: {action.get('label_status') or ('verified' if action.get('verified') else 'unverified')}\n"
                f"  location: {action.get('location')}\n"
                f"  required_permissions: {', '.join(action.get('required_permissions') or []) or 'none'}\n"
                f"  result: {action.get('result') or 'documented action'}\n"
            )
        ui_action_lines.append("")
    ui_action_path.write_text("\n".join(ui_action_lines), encoding="utf-8")

    workflow_lines = ["# Assistant Workflow Help", ""]
    workflow_lines.append("This generated source summarizes verified workflow seeds used by the assistant.")
    workflow_lines.append("")
    seen_workflow_intents: set[str] = set()
    page_labels = {seed.page_id: seed.label for seed in ASSISTANT_PAGE_ROUTE_SEEDS}
    for seed in WORKFLOW_HELP_SEEDS.values():
        if seed.workflow_key in seen_workflow_intents:
            continue
        seen_workflow_intents.add(seed.workflow_key)
        workflow_lines.append(f"## {seed.title_en} ({seed.workflow_key})\n")
        workflow_lines.append(f"- title_de: {seed.title_de}")
        workflow_lines.append(f"- summary_en: {seed.summary_en}")
        workflow_lines.append(f"- summary_de: {seed.summary_de}")
        workflow_lines.append(f"- intent_aliases_en: {', '.join(seed.intent_aliases_en)}")
        workflow_lines.append(f"- intent_aliases_de: {', '.join(seed.intent_aliases_de)}")
        workflow_lines.append(f"- linked_page_ids: {', '.join(seed.linked_page_ids)}")
        workflow_lines.append(
            "- linked_pages_labeled: "
            + ", ".join(f"{page_id} {page_labels.get(page_id, page_id)}" for page_id in seed.linked_page_ids)
        )
        workflow_lines.append(f"- api_families: {', '.join(seed.api_families)}")
        if seed.ambiguity_notes:
            workflow_lines.append("- ambiguity_notes:")
            for note in seed.ambiguity_notes:
                workflow_lines.append(f"  - {note}")
        workflow_lines.append("")
        workflow_lines.append("### Steps\n")
        for step in seed.steps:
            workflow_lines.append(
                f"- {step.sequence}. {step.step_key} [page {step.page_id or 'none'} / module {step.module_key or 'none'}]"
            )
            workflow_lines.append(f"  purpose_en: {step.purpose_en}")
            workflow_lines.append(f"  purpose_de: {step.purpose_de}")
            workflow_lines.append(
                f"  required_permissions: {', '.join(step.required_permissions) or 'none'}"
            )
            if step.source_basis:
                workflow_lines.append("  source_basis:")
                for basis in step.source_basis:
                    workflow_lines.append(
                        f"    - {basis.source_type} / {basis.source_name}"
                        f" / {basis.page_id or 'none'} / {basis.module_key or 'none'}: {basis.evidence}"
                    )
        workflow_lines.append("")
    workflow_path.write_text("\n".join(workflow_lines), encoding="utf-8")

    api_endpoint_lines = [
        "# Assistant API Endpoint Map",
        "",
        "This generated source maps workspace pages to backend API families verified in the route catalog.",
        "",
    ]
    for seed in ASSISTANT_PAGE_ROUTE_SEEDS:
        api_endpoint_lines.append(f"## {seed.page_id} — {seed.label}\n")
        api_endpoint_lines.append(f"- module_key: {seed.module_key}")
        api_endpoint_lines.append(f"- api_families: {', '.join(seed.api_families) or 'none'}")
        api_endpoint_lines.append(f"- route_name: {seed.route_name or 'none'}")
        api_endpoint_lines.append(f"- path_template: {seed.path_template}")
        api_endpoint_lines.append("")
    api_endpoint_path.write_text("\n".join(api_endpoint_lines), encoding="utf-8")

    role_page_coverage_lines = [
        "# Role-Based Page Coverage Map",
        "",
        "This generated source summarizes which roles and permissions can reach verified assistant page IDs.",
        "",
    ]
    for seed in ASSISTANT_PAGE_ROUTE_SEEDS:
        role_page_coverage_lines.append(f"## {seed.page_id} — {seed.label}\n")
        role_page_coverage_lines.append(f"- allowed_role_keys: {', '.join(seed.allowed_role_keys) or 'none'}")
        role_page_coverage_lines.append(f"- required_permissions: {', '.join(seed.required_permissions) or 'none'}")
        role_page_coverage_lines.append(f"- scope_kind: {seed.scope_kind or 'none'}")
        role_page_coverage_lines.append("")
    role_page_coverage_path.write_text("\n".join(role_page_coverage_lines), encoding="utf-8")

    operational_handbook_lines = [
        "# Operational Handbook",
        "",
        "This generated handbook summarizes verified cross-module operational guidance for assistant grounding.",
        "",
        "## Documents and Attachments",
        "",
        "- Documents, generated outputs, and uploads are centralized in platform services while business meaning remains with the owning module.",
        "- Contract-like artifacts are treated as documents or attachments linked to the owning customer, planning record, subcontractor, or other business entity.",
        "- Planning orders and planning records include documented planning packages and attachments.",
        "",
        "## Customer and Planning Context",
        "",
        "- Customer creation and customer master context belong to the Customers workspace C-01.",
        "- Customer orders and planning records are handled in Orders & Planning Records P-02.",
        "- Detailed shift structure continues in Shift Planning P-03 after planning records are prepared.",
        "",
        "## Contract Questions",
        "",
        "- The repository does not verify a standalone contract workspace.",
        "- Platform Services PS-01 is the safe shared workspace for contract or Vertrag document create, versioning, attachment, upload, and linking when the contract subtype is unclear.",
        "- Customer-related agreements can require C-01 context; order and planning attachments can require P-02 context; subcontractor agreements can require S-01 context.",
    ]
    operational_handbook_path.write_text("\n".join(operational_handbook_lines), encoding="utf-8")

    user_manual_lines = [
        "# User Manual",
        "",
        "This generated user manual summarizes verified workflow-facing workspace guidance used by the assistant.",
        "",
        "## C-01 Customers Workspace",
        "",
        "- Customer master work starts in C-01.",
        "- Customer history and attachments remain customer-scoped and document-backed.",
        "- Order and planning flows depend on an existing customer context.",
        "",
        "## P-02 Orders & Planning Records",
        "",
        "- P-02 manages customer orders, planning records, and document packages.",
        "- Dispatch teams manage release states, notes, and documented planning packages for customer orders and operational planning records.",
        "- Customer-dependent setup items can require commercial data, sites, routes, or other planning setup before release.",
        "",
        "## PS-01 Platform Services Workspace",
        "",
        "- PS-01 is the safe shared reference when the user asks about documents, versions, attachments, contracts, Vertraege, or contract-like uploads without a clear business subtype.",
        "- Use PS-01 for document-centered create, version, upload, attach, and link workflows rather than inventing a standalone contract module.",
    ]
    user_manual_path.write_text("\n".join(user_manual_lines), encoding="utf-8")

    implementation_data_model_lines = [
        "# Implementation Data Model",
        "",
        "This generated source summarizes verified data-ownership rules for assistant grounding.",
        "",
        "- Customers own customer master and customer history truth.",
        "- Planning owns orders, planning records, shifts, staffing, releases, and document packages linked to planning context.",
        "- Platform services own centralized documents, document versions, document links, communications, notices, and integration jobs.",
        "- Other modules may reference IDs and read projections, but they must not mutate another context's master truth directly.",
        "- Contract-like content should be grounded as document ownership plus business context rather than as a fake standalone contract table or module.",
    ]
    implementation_data_model_path.write_text("\n".join(implementation_data_model_lines), encoding="utf-8")
    expert_knowledge_pack_path.write_text(render_expert_knowledge_pack_markdown(), encoding="utf-8")

    registrations.extend(
        [
            KnowledgeSourceRegistration(
                source_type="page_route_catalog",
                source_name="Assistant Page Route Catalog",
                source_path=str(page_catalog_path),
            ),
            KnowledgeSourceRegistration(
                source_type="page_help_manifest",
                source_name="Assistant Page Help Manifest",
                source_path=str(page_help_path),
            ),
            KnowledgeSourceRegistration(
                source_type="workflow_help",
                source_name="Assistant Workflow Help",
                source_path=str(workflow_path),
            ),
            KnowledgeSourceRegistration(
                source_type="ui_action_catalog",
                source_name="Assistant UI Action Catalog",
                source_path=str(ui_action_path),
            ),
            KnowledgeSourceRegistration(
                source_type="api_export",
                source_name="Assistant API Endpoint Map",
                source_path=str(api_endpoint_path),
            ),
            KnowledgeSourceRegistration(
                source_type="role_page_coverage",
                source_name="Assistant Role Page Coverage Map",
                source_path=str(role_page_coverage_path),
            ),
            KnowledgeSourceRegistration(
                source_type="operational_handbook",
                source_name="Generated Operational Handbook",
                source_path=str(operational_handbook_path),
            ),
            KnowledgeSourceRegistration(
                source_type="user_manual",
                source_name="Generated User Manual",
                source_path=str(user_manual_path),
            ),
            KnowledgeSourceRegistration(
                source_type="implementation_data_model",
                source_name="Generated Implementation Data Model",
                source_path=str(implementation_data_model_path),
            ),
            KnowledgeSourceRegistration(
                source_type="expert_knowledge_pack",
                source_name="SicherPlan Expert Knowledge Pack",
                source_path=str(expert_knowledge_pack_path),
            ),
        ]
    )
    return registrations


def _append_registration_if_exists(
    registrations: list[KnowledgeSourceRegistration],
    *,
    source_type: str,
    source_name: str,
    source_path: Path,
) -> None:
    if not source_path.is_file():
        return
    registrations.append(
        KnowledgeSourceRegistration(
            source_type=source_type,
            source_name=source_name,
            source_path=str(source_path),
        )
    )


def _build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Reindex assistant knowledge sources.")
    parser.add_argument("--reindex", action="store_true", help="Purge existing assistant knowledge before ingesting.")
    parser.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parents[5]),
        help="Repository root used to resolve docs and generated knowledge files.",
    )
    return parser


def run_reindex(
    *,
    repo_root: Path,
    session_factory,
    reindex: bool,
) -> dict[str, object]:
    registrations = build_default_knowledge_registrations(repo_root)
    loader = KnowledgeSourceLoader(allowed_roots=[repo_root / "docs", repo_root / "tmp" / "assistant-knowledge"])

    with session_factory() as session:
        repository = AssistantKnowledgeRepository(session)
        if reindex:
            repository.purge_all()
        service = AssistantKnowledgeIngestionService(loader=loader, repository=repository)
        result = service.ingest(registrations)
        active_chunks = repository.count_active_chunks()
        session.commit()

    return {
        "sources_registered": len(registrations),
        "sources_seen": result.sources_seen,
        "sources_indexed": result.sources_indexed,
        "sources_skipped": result.sources_skipped,
        "sources_skipped_unchanged": result.sources_skipped,
        "sources_failed": result.sources_failed,
        "chunks_created": result.chunks_created,
        "chunks_active": active_chunks,
        "failures": [failure.__dict__ for failure in result.failures],
    }


def main() -> int:
    from app.db.session import SessionLocal

    args = _build_argument_parser().parse_args()
    payload = run_reindex(
        repo_root=Path(args.repo_root).resolve(),
        session_factory=SessionLocal,
        reindex=args.reindex,
    )

    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if int(payload["sources_failed"]) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
