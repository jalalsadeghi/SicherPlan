"""Assistant tools for verified workflow grounding facts."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from app.modules.assistant.schemas import (
    AssistantWorkflowHelpInput,
    AssistantWorkflowHelpRead,
    AssistantWorkflowKnowledgeRead,
    AssistantWorkflowSourceBasisRead,
    AssistantWorkflowStepRead,
)
from app.modules.assistant.tools import (
    AssistantToolClassification,
    AssistantToolDefinition,
    AssistantToolExecutionContext,
    AssistantToolResult,
    AssistantToolScopeBehavior,
)
from app.modules.assistant.workflow_help import (
    AssistantWorkflowSeed,
    resolve_workflow_key,
    search_workflow_seeds,
)


class SearchWorkflowHelpTool:
    def __init__(self, *, repository: Any | None = None) -> None:
        self.repository = repository
        self.definition = AssistantToolDefinition(
            name="assistant.search_workflow_help",
            description="Return verified workflow manifests, ordered steps, and step-level source basis for a SicherPlan workflow question.",
            input_schema=AssistantWorkflowHelpInput,
            output_schema=AssistantWorkflowHelpRead,
            required_permissions=["assistant.chat.access"],
            scope_behavior=AssistantToolScopeBehavior.CURRENT_USER,
            classification=AssistantToolClassification.READ_ONLY,
        )

    def execute(
        self,
        *,
        input_data: BaseModel,
        context: AssistantToolExecutionContext,
    ) -> AssistantToolResult:
        query = str(getattr(input_data, "query", "") or "").strip()
        language_code = str(getattr(input_data, "language_code", "") or "").strip() or None
        workflow_key = resolve_workflow_key(
            getattr(input_data, "workflow_key", None) or getattr(input_data, "intent", None)
        )
        limit = int(getattr(input_data, "limit", 5) or 5)

        matched = search_workflow_seeds(
            query=query or None,
            language_code=language_code,
            workflow_key=workflow_key,
            limit=limit,
        )
        if not matched and workflow_key is not None:
            safe_note = "No verified workflow grounding is registered for this workflow key."
        elif not matched:
            safe_note = "No verified workflow grounding matched this query."
        else:
            safe_note = None

        payload = AssistantWorkflowHelpRead(
            workflows=[_to_workflow_read(seed=seed, language_code=language_code) for seed in matched],
            matched_workflow_keys=[seed.workflow_key for seed in matched],
            safe_note=safe_note,
        ).model_dump(mode="json")
        return AssistantToolResult(ok=True, tool_name=self.definition.name, data=payload)


def _to_workflow_read(*, seed: AssistantWorkflowSeed, language_code: str | None) -> AssistantWorkflowKnowledgeRead:
    localized_title = seed.title_de if language_code == "de" else seed.title_en
    localized_summary = seed.summary_de if language_code == "de" else seed.summary_en
    source_basis = _dedupe_source_basis(
        item
        for step in seed.steps
        for item in step.source_basis
    )
    return AssistantWorkflowKnowledgeRead(
        workflow_key=seed.workflow_key,
        title=localized_title,
        title_en=seed.title_en,
        title_de=seed.title_de,
        summary=localized_summary,
        summary_en=seed.summary_en,
        summary_de=seed.summary_de,
        intent_aliases_en=list(seed.intent_aliases_en),
        intent_aliases_de=list(seed.intent_aliases_de),
        steps=[
            AssistantWorkflowStepRead(
                step_key=step.step_key,
                sequence=step.sequence,
                page_id=step.page_id,
                module_key=step.module_key,
                purpose=step.purpose_de if language_code == "de" else step.purpose_en,
                purpose_en=step.purpose_en,
                purpose_de=step.purpose_de,
                required_permissions=list(step.required_permissions),
                source_basis=[
                    AssistantWorkflowSourceBasisRead(
                        source_type=basis.source_type,
                        source_name=basis.source_name,
                        page_id=basis.page_id,
                        module_key=basis.module_key,
                        evidence=basis.evidence,
                    )
                    for basis in step.source_basis
                ],
            )
            for step in seed.steps
        ],
        linked_page_ids=list(seed.linked_page_ids),
        api_families=list(seed.api_families),
        ambiguity_notes=list(seed.ambiguity_notes),
        source_basis=source_basis,
    )


def _dedupe_source_basis(items) -> list[AssistantWorkflowSourceBasisRead]:
    seen: set[tuple[str, str, str | None, str | None, str]] = set()
    result: list[AssistantWorkflowSourceBasisRead] = []
    for item in items:
        key = (item.source_type, item.source_name, item.page_id, item.module_key, item.evidence)
        if key in seen:
            continue
        seen.add(key)
        result.append(
            AssistantWorkflowSourceBasisRead(
                source_type=item.source_type,
                source_name=item.source_name,
                page_id=item.page_id,
                module_key=item.module_key,
                evidence=item.evidence,
            )
        )
    return result
