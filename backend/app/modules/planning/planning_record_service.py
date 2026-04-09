"""Service layer for planning records and explicit mode-specific detail tables."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol

from app.errors import ApiException
from app.modules.customers.models import Customer
from app.modules.iam.audit_service import AuditActor, AuditService
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.planning.commercial_link_service import PlanningCommercialLinkService
from app.modules.planning.models import CustomerOrder, EventVenue, PatrolRoute, PlanningRecord, Site, TradeFair, TradeFairZone
from app.modules.planning.schemas import (
    EventPlanDetailCreate,
    EventPlanDetailRead,
    EventPlanDetailUpdate,
    PatrolPlanDetailCreate,
    PatrolPlanDetailRead,
    PatrolPlanDetailUpdate,
    PlanningDispatcherCandidateRead,
    PlanningRecordCreate,
    PlanningRecordAttachmentCreate,
    PlanningRecordAttachmentLinkCreate,
    PlanningRecordFilter,
    PlanningRecordListItem,
    PlanningRecordRead,
    PlanningRecordReleaseStateUpdate,
    PlanningRecordUpdate,
    SitePlanDetailCreate,
    SitePlanDetailRead,
    SitePlanDetailUpdate,
    TradeFairPlanDetailCreate,
    TradeFairPlanDetailRead,
    TradeFairPlanDetailUpdate,
)
from app.modules.platform_services.docs_schemas import DocumentRead
from app.modules.platform_services.docs_schemas import DocumentCreate, DocumentLinkCreate, DocumentVersionCreate
from app.modules.platform_services.docs_service import DocumentService
from app.modules.planning.validation_service import PlanningValidationService


class PlanningRecordRepository(Protocol):
    def get_customer(self, tenant_id: str, customer_id: str) -> Customer | None: ...
    def get_user_account(self, tenant_id: str, user_id: str): ...  # noqa: ANN001
    def list_dispatcher_candidates(self, tenant_id: str) -> list[PlanningDispatcherCandidateRead]: ...
    def get_customer_order(self, tenant_id: str, order_id: str) -> CustomerOrder | None: ...
    def get_event_venue(self, tenant_id: str, row_id: str) -> EventVenue | None: ...
    def get_site(self, tenant_id: str, row_id: str) -> Site | None: ...
    def get_trade_fair(self, tenant_id: str, row_id: str) -> TradeFair | None: ...
    def get_trade_fair_zone(self, tenant_id: str, row_id: str): ...  # noqa: ANN001
    def get_patrol_route(self, tenant_id: str, row_id: str) -> PatrolRoute | None: ...
    def list_planning_records(self, tenant_id: str, filters: PlanningRecordFilter) -> list[PlanningRecord]: ...
    def get_planning_record(self, tenant_id: str, planning_record_id: str) -> PlanningRecord | None: ...
    def find_planning_record_by_name(self, tenant_id: str, order_id: str, name: str, *, exclude_id: str | None = None) -> PlanningRecord | None: ...
    def create_planning_record(self, tenant_id: str, payload: PlanningRecordCreate, actor_user_id: str | None) -> PlanningRecord: ...
    def update_planning_record(self, tenant_id: str, planning_record_id: str, payload: PlanningRecordUpdate, actor_user_id: str | None) -> PlanningRecord | None: ...
    def save_planning_record(self, row: PlanningRecord) -> PlanningRecord: ...
    def create_event_plan_detail(self, tenant_id: str, planning_record_id: str, payload: EventPlanDetailCreate): ...  # noqa: ANN001
    def update_event_plan_detail(self, tenant_id: str, planning_record_id: str, payload: EventPlanDetailUpdate): ...  # noqa: ANN001
    def get_event_plan_detail(self, tenant_id: str, planning_record_id: str): ...  # noqa: ANN001
    def create_site_plan_detail(self, tenant_id: str, planning_record_id: str, payload: SitePlanDetailCreate): ...  # noqa: ANN001
    def update_site_plan_detail(self, tenant_id: str, planning_record_id: str, payload: SitePlanDetailUpdate): ...  # noqa: ANN001
    def get_site_plan_detail(self, tenant_id: str, planning_record_id: str): ...  # noqa: ANN001
    def create_trade_fair_plan_detail(self, tenant_id: str, planning_record_id: str, payload: TradeFairPlanDetailCreate): ...  # noqa: ANN001
    def update_trade_fair_plan_detail(self, tenant_id: str, planning_record_id: str, payload: TradeFairPlanDetailUpdate): ...  # noqa: ANN001
    def get_trade_fair_plan_detail(self, tenant_id: str, planning_record_id: str): ...  # noqa: ANN001
    def create_patrol_plan_detail(self, tenant_id: str, planning_record_id: str, payload: PatrolPlanDetailCreate): ...  # noqa: ANN001
    def update_patrol_plan_detail(self, tenant_id: str, planning_record_id: str, payload: PatrolPlanDetailUpdate): ...  # noqa: ANN001
    def get_patrol_plan_detail(self, tenant_id: str, planning_record_id: str): ...  # noqa: ANN001


class PlanningRecordDocumentRepository(Protocol):
    def list_documents_for_owner(self, tenant_id: str, owner_type: str, owner_id: str) -> list[object]: ...


class PlanningRecordService:
    DISPATCHER_ROLE_KEYS = frozenset({"platform_admin", "tenant_admin", "dispatcher", "controller_qm", "accounting"})
    MODES = frozenset({"event", "site", "trade_fair", "patrol"})
    RELEASE_STATES = frozenset({"draft", "release_ready", "released"})
    RELEASE_TRANSITIONS = {
        "draft": {"draft", "release_ready"},
        "release_ready": {"draft", "release_ready", "released"},
        "released": {"release_ready", "released"},
    }

    def __init__(
        self,
        repository: PlanningRecordRepository,
        *,
        document_repository: PlanningRecordDocumentRepository,
        document_service: DocumentService | None = None,
        commercial_link_service: PlanningCommercialLinkService | None = None,
        validation_service: PlanningValidationService | None = None,
        audit_service: AuditService | None = None,
    ) -> None:
        self.repository = repository
        self.document_repository = document_repository
        self.document_service = document_service
        self.commercial_link_service = commercial_link_service
        self.validation_service = validation_service
        self.audit_service = audit_service

    def list_planning_records(self, tenant_id: str, filters: PlanningRecordFilter, _actor: RequestAuthorizationContext) -> list[PlanningRecordListItem]:
        return [PlanningRecordListItem.model_validate(row) for row in self.repository.list_planning_records(tenant_id, filters)]

    def list_dispatcher_candidates(self, tenant_id: str, actor: RequestAuthorizationContext) -> list[PlanningDispatcherCandidateRead]:
        candidates = self.repository.list_dispatcher_candidates(tenant_id)
        if any(candidate.id == actor.user_id for candidate in candidates):
            return candidates
        actor_candidate = self._build_actor_dispatcher_candidate(tenant_id, actor)
        if actor_candidate is None:
            return candidates
        return [*candidates, actor_candidate]

    def get_planning_record(self, tenant_id: str, planning_record_id: str, _actor: RequestAuthorizationContext) -> PlanningRecordRead:
        return self._read(self._require_record(tenant_id, planning_record_id))

    def create_planning_record(
        self,
        tenant_id: str,
        payload: PlanningRecordCreate,
        actor: RequestAuthorizationContext,
    ) -> PlanningRecordRead:
        self._require_mode(payload.planning_mode_code)
        order = self._require_order(tenant_id, payload.order_id)
        self._validate_window(payload.planning_from, payload.planning_to)
        self._validate_window_within_order(order, payload.planning_from, payload.planning_to)
        self._validate_dispatcher(tenant_id, payload.dispatcher_user_id)
        self._validate_parent(tenant_id, payload.planning_mode_code, payload.parent_planning_record_id, payload.order_id, payload.planning_from, payload.planning_to)
        if self.repository.find_planning_record_by_name(tenant_id, payload.order_id, payload.name) is not None:
            raise ApiException(409, "planning.planning_record.duplicate_name", "errors.planning.planning_record.duplicate_name")
        self._validate_detail_payloads(tenant_id, order, payload.planning_mode_code, payload)
        row = self.repository.create_planning_record(tenant_id, payload, actor.user_id)
        self._create_detail_for_mode(tenant_id, row.id, payload.planning_mode_code, payload)
        row = self._require_record(tenant_id, row.id)
        self._record_event(actor, "planning.planning_record.created", "ops.planning_record", row.id, tenant_id, after_json=self._snapshot(row))
        return self._read(row)

    def update_planning_record(
        self,
        tenant_id: str,
        planning_record_id: str,
        payload: PlanningRecordUpdate,
        actor: RequestAuthorizationContext,
    ) -> PlanningRecordRead:
        current = self._require_record(tenant_id, planning_record_id)
        order = self._require_order(tenant_id, current.order_id)
        before_json = self._snapshot(current)
        next_name = self._field_value(payload, "name", current.name)
        next_from = self._field_value(payload, "planning_from", current.planning_from)
        next_to = self._field_value(payload, "planning_to", current.planning_to)
        next_dispatcher_user_id = self._field_value(payload, "dispatcher_user_id", current.dispatcher_user_id)
        self._validate_window(next_from, next_to)
        self._validate_window_within_order(order, next_from, next_to)
        self._validate_dispatcher(tenant_id, next_dispatcher_user_id)
        if self.repository.find_planning_record_by_name(tenant_id, current.order_id, next_name, exclude_id=planning_record_id) is not None:
            raise ApiException(409, "planning.planning_record.duplicate_name", "errors.planning.planning_record.duplicate_name")
        self._validate_detail_payloads(tenant_id, order, current.planning_mode_code, payload)
        core_payload = self._core_update_payload(payload)
        row = self.repository.update_planning_record(tenant_id, planning_record_id, core_payload, actor.user_id)
        if row is None:
            raise self._not_found("planning_record")
        self._update_detail_for_mode(tenant_id, planning_record_id, current.planning_mode_code, payload)
        row = self._require_record(tenant_id, planning_record_id)
        self._record_event(actor, "planning.planning_record.updated", "ops.planning_record", row.id, tenant_id, before_json=before_json, after_json=self._snapshot(row))
        return self._read(row)

    def set_planning_record_release_state(
        self,
        tenant_id: str,
        planning_record_id: str,
        payload: PlanningRecordReleaseStateUpdate,
        actor: RequestAuthorizationContext,
    ) -> PlanningRecordRead:
        row = self._require_record(tenant_id, planning_record_id)
        if payload.version_no != row.version_no:
            raise ApiException(409, "planning.planning_record.stale_version", "errors.planning.planning_record.stale_version", {"current_version": row.version_no})
        self._require_release_state(payload.release_state)
        if payload.release_state not in self.RELEASE_TRANSITIONS[row.release_state]:
            raise ApiException(409, "planning.planning_record.invalid_release_transition", "errors.planning.planning_record.invalid_release_transition")
        if payload.release_state == "released" and self.commercial_link_service is not None:
            self.commercial_link_service.assert_planning_record_release_ready(tenant_id, planning_record_id)
        if payload.release_state in {"release_ready", "released"} and self.validation_service is not None:
            validations = self.validation_service.validate_planning_record_release(tenant_id, planning_record_id)
            if validations.blocking_count:
                raise ApiException(
                    409,
                    "planning.planning_record.blocked_by_validation",
                    "errors.planning.planning_record.blocked_by_validation",
                    {"issues": [issue.model_dump() for issue in validations.issues]},
                )
        before_json = self._snapshot(row)
        row.release_state = payload.release_state
        if payload.release_state == "released":
            row.released_at = datetime.now(UTC)
            row.released_by_user_id = actor.user_id
        else:
            row.released_at = None
            row.released_by_user_id = None
        row.updated_by_user_id = actor.user_id
        row.version_no += 1
        row = self.repository.save_planning_record(row)
        self._record_event(actor, "planning.planning_record.release_state.changed", "ops.planning_record", row.id, tenant_id, before_json=before_json, after_json=self._snapshot(row))
        return self._read(row)

    def list_planning_record_attachments(
        self,
        tenant_id: str,
        planning_record_id: str,
        _actor: RequestAuthorizationContext,
    ) -> list[DocumentRead]:
        self._require_record(tenant_id, planning_record_id)
        return [
            DocumentRead.model_validate(document)
            for document in self.document_repository.list_documents_for_owner(tenant_id, "ops.planning_record", planning_record_id)
        ]

    def create_planning_record_attachment(
        self,
        tenant_id: str,
        planning_record_id: str,
        payload: PlanningRecordAttachmentCreate,
        actor: RequestAuthorizationContext,
    ) -> DocumentRead:
        self._require_record(tenant_id, planning_record_id)
        if payload.tenant_id != tenant_id:
            raise ApiException(
                400,
                "planning.planning_record_attachment.scope_mismatch",
                "errors.planning.planning_record_attachment.scope_mismatch",
            )
        if self.document_service is None:
            raise ApiException(500, "platform.internal", "errors.platform.internal")
        document = self.document_service.create_document(
            tenant_id,
            DocumentCreate(
                tenant_id=tenant_id,
                title=payload.title,
                document_type_key=payload.document_type_key,
                source_module="planning",
                source_label="planning-record-attachment",
                metadata_json=payload.metadata_json,
            ),
            actor,
        )
        self.document_service.add_document_version(
            tenant_id,
            document.id,
            DocumentVersionCreate(
                file_name=payload.file_name,
                content_type=payload.content_type,
                content_base64=payload.content_base64,
                metadata_json=payload.metadata_json,
            ),
            actor,
        )
        self.document_service.add_document_link(
            tenant_id,
            document.id,
            DocumentLinkCreate(
                owner_type="ops.planning_record",
                owner_id=planning_record_id,
                relation_type=payload.relation_type,
                label=payload.label,
                metadata_json=payload.metadata_json,
            ),
            actor,
        )
        self._record_event(
            actor,
            "planning.planning_record.attachment.created",
            "ops.planning_record",
            planning_record_id,
            tenant_id,
            after_json={"document_id": document.id},
        )
        refreshed = self.document_repository.list_documents_for_owner(tenant_id, "ops.planning_record", planning_record_id)
        return DocumentRead.model_validate(next(row for row in refreshed if row.id == document.id))

    def link_planning_record_attachment(
        self,
        tenant_id: str,
        planning_record_id: str,
        payload: PlanningRecordAttachmentLinkCreate,
        actor: RequestAuthorizationContext,
    ) -> DocumentRead:
        self._require_record(tenant_id, planning_record_id)
        if payload.tenant_id != tenant_id:
            raise ApiException(
                400,
                "planning.planning_record_attachment.scope_mismatch",
                "errors.planning.planning_record_attachment.scope_mismatch",
            )
        if self.document_service is None:
            raise ApiException(500, "platform.internal", "errors.platform.internal")
        self.document_service.add_document_link(
            tenant_id,
            payload.document_id,
            DocumentLinkCreate(
                owner_type="ops.planning_record",
                owner_id=planning_record_id,
                relation_type=payload.relation_type,
                label=payload.label,
                metadata_json=payload.metadata_json,
            ),
            actor,
        )
        self._record_event(
            actor,
            "planning.planning_record.attachment.linked",
            "ops.planning_record",
            planning_record_id,
            tenant_id,
            after_json={"document_id": payload.document_id},
        )
        refreshed = self.document_repository.list_documents_for_owner(tenant_id, "ops.planning_record", planning_record_id)
        return DocumentRead.model_validate(next(row for row in refreshed if row.id == payload.document_id))

    def _validate_detail_payloads(self, tenant_id: str, order: CustomerOrder, planning_mode_code: str, payload: PlanningRecordCreate | PlanningRecordUpdate) -> None:
        detail_payloads = {
            "event": getattr(payload, "event_detail", None),
            "site": getattr(payload, "site_detail", None),
            "trade_fair": getattr(payload, "trade_fair_detail", None),
            "patrol": getattr(payload, "patrol_detail", None),
        }
        if isinstance(payload, PlanningRecordCreate):
            if sum(1 for value in detail_payloads.values() if value is not None) != 1 or detail_payloads[planning_mode_code] is None:
                raise ApiException(400, "planning.planning_record.detail_mismatch", "errors.planning.planning_record.detail_mismatch")
        elif any(value is not None for value in detail_payloads.values() if value is not detail_payloads[planning_mode_code]):
            raise ApiException(400, "planning.planning_record.detail_mismatch", "errors.planning.planning_record.detail_mismatch")

        if planning_mode_code == "event" and detail_payloads["event"] is not None:
            venue = self.repository.get_event_venue(tenant_id, detail_payloads["event"].event_venue_id)
            if venue is None:
                raise self._not_found("event_venue")
            if venue.customer_id != order.customer_id:
                raise ApiException(400, "planning.planning_record.detail_customer_mismatch", "errors.planning.planning_record.detail_customer_mismatch")
        if planning_mode_code == "site" and detail_payloads["site"] is not None:
            site = self.repository.get_site(tenant_id, detail_payloads["site"].site_id)
            if site is None:
                raise self._not_found("site")
            if site.customer_id != order.customer_id:
                raise ApiException(400, "planning.planning_record.detail_customer_mismatch", "errors.planning.planning_record.detail_customer_mismatch")
        if planning_mode_code == "trade_fair" and detail_payloads["trade_fair"] is not None:
            fair = self.repository.get_trade_fair(tenant_id, detail_payloads["trade_fair"].trade_fair_id)
            if fair is None:
                raise self._not_found("trade_fair")
            if fair.customer_id != order.customer_id:
                raise ApiException(400, "planning.planning_record.detail_customer_mismatch", "errors.planning.planning_record.detail_customer_mismatch")
            if detail_payloads["trade_fair"].trade_fair_zone_id is not None:
                zone = self.repository.get_trade_fair_zone(tenant_id, detail_payloads["trade_fair"].trade_fair_zone_id)
                if zone is None:
                    raise self._not_found("trade_fair_zone")
                if zone.trade_fair_id != fair.id:
                    raise ApiException(400, "planning.planning_record.trade_fair_zone_mismatch", "errors.planning.planning_record.trade_fair_zone_mismatch")
        if planning_mode_code == "patrol" and detail_payloads["patrol"] is not None:
            route = self.repository.get_patrol_route(tenant_id, detail_payloads["patrol"].patrol_route_id)
            if route is None:
                raise self._not_found("patrol_route")
            if route.customer_id != order.customer_id:
                raise ApiException(400, "planning.planning_record.detail_customer_mismatch", "errors.planning.planning_record.detail_customer_mismatch")

    def _create_detail_for_mode(self, tenant_id: str, planning_record_id: str, planning_mode_code: str, payload: PlanningRecordCreate) -> None:
        if planning_mode_code == "event":
            self.repository.create_event_plan_detail(tenant_id, planning_record_id, payload.event_detail)
        elif planning_mode_code == "site":
            self.repository.create_site_plan_detail(tenant_id, planning_record_id, payload.site_detail)
        elif planning_mode_code == "trade_fair":
            self.repository.create_trade_fair_plan_detail(tenant_id, planning_record_id, payload.trade_fair_detail)
        else:
            self.repository.create_patrol_plan_detail(tenant_id, planning_record_id, payload.patrol_detail)

    def _update_detail_for_mode(self, tenant_id: str, planning_record_id: str, planning_mode_code: str, payload: PlanningRecordUpdate) -> None:
        if planning_mode_code == "event" and payload.event_detail is not None:
            self.repository.update_event_plan_detail(tenant_id, planning_record_id, payload.event_detail)
        elif planning_mode_code == "site" and payload.site_detail is not None:
            self.repository.update_site_plan_detail(tenant_id, planning_record_id, payload.site_detail)
        elif planning_mode_code == "trade_fair" and payload.trade_fair_detail is not None:
            self.repository.update_trade_fair_plan_detail(tenant_id, planning_record_id, payload.trade_fair_detail)
        elif planning_mode_code == "patrol" and payload.patrol_detail is not None:
            self.repository.update_patrol_plan_detail(tenant_id, planning_record_id, payload.patrol_detail)

    def _validate_parent(
        self,
        tenant_id: str,
        planning_mode_code: str,
        parent_planning_record_id: str | None,
        order_id: str,
        planning_from,
        planning_to,
    ) -> None:
        if parent_planning_record_id is None:
            return
        if planning_mode_code != "event":
            raise ApiException(400, "planning.planning_record.parent_not_allowed", "errors.planning.planning_record.parent_not_allowed")
        parent = self._require_record(tenant_id, parent_planning_record_id)
        if parent.parent_planning_record_id is not None:
            raise ApiException(400, "planning.planning_record.parent_not_allowed", "errors.planning.planning_record.parent_not_allowed")
        if parent.order_id != order_id or parent.planning_mode_code != "event":
            raise ApiException(400, "planning.planning_record.parent_mismatch", "errors.planning.planning_record.parent_mismatch")
        if planning_from < parent.planning_from or planning_to > parent.planning_to:
            raise ApiException(400, "planning.planning_record.parent_window_mismatch", "errors.planning.planning_record.parent_window_mismatch")

    def _validate_dispatcher(self, tenant_id: str, dispatcher_user_id: str | None) -> None:
        if dispatcher_user_id is None:
            return
        user = self.repository.get_user_account(tenant_id, dispatcher_user_id)
        if user is None or user.archived_at is not None or user.status != "active":
            raise self._not_found("dispatcher_user")

    def _build_actor_dispatcher_candidate(
        self,
        tenant_id: str,
        actor: RequestAuthorizationContext,
    ) -> PlanningDispatcherCandidateRead | None:
        if actor.tenant_id != tenant_id:
            return None
        actor_role_keys = sorted(role_key for role_key in actor.role_keys if role_key in self.DISPATCHER_ROLE_KEYS)
        if not actor_role_keys:
            return None
        user = self.repository.get_user_account(tenant_id, actor.user_id)
        if user is None or user.archived_at is not None or user.status != "active":
            return None
        return PlanningDispatcherCandidateRead(
            id=user.id,
            tenant_id=user.tenant_id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            status=user.status,
            role_keys=actor_role_keys,
            archived_at=user.archived_at,
        )

    @staticmethod
    def _validate_window(planning_from, planning_to) -> None:  # noqa: ANN001
        if planning_to < planning_from:
            raise ApiException(400, "planning.planning_record.invalid_window", "errors.planning.planning_record.invalid_window")

    @staticmethod
    def _validate_window_within_order(order: CustomerOrder, planning_from, planning_to) -> None:  # noqa: ANN001
        if planning_from < order.service_from or planning_to > order.service_to:
            raise ApiException(400, "planning.planning_record.order_window_mismatch", "errors.planning.planning_record.order_window_mismatch")

    def _require_order(self, tenant_id: str, order_id: str) -> CustomerOrder:
        row = self.repository.get_customer_order(tenant_id, order_id)
        if row is None:
            raise self._not_found("customer_order")
        return row

    def _require_record(self, tenant_id: str, planning_record_id: str) -> PlanningRecord:
        row = self.repository.get_planning_record(tenant_id, planning_record_id)
        if row is None:
            raise self._not_found("planning_record")
        return row

    @classmethod
    def _require_mode(cls, planning_mode_code: str) -> None:
        if planning_mode_code not in cls.MODES:
            raise ApiException(400, "planning.planning_record.invalid_mode", "errors.planning.planning_record.invalid_mode")

    @classmethod
    def _require_release_state(cls, release_state: str) -> None:
        if release_state not in cls.RELEASE_STATES:
            raise ApiException(400, "planning.planning_record.invalid_release_state", "errors.planning.planning_record.invalid_release_state")

    def _read(self, row: PlanningRecord) -> PlanningRecordRead:
        schema = PlanningRecordRead.model_validate(row)
        return schema.model_copy(
            update={
                "attachments": [
                    DocumentRead.model_validate(document)
                    for document in self.document_repository.list_documents_for_owner(row.tenant_id, "ops.planning_record", row.id)
                ]
            }
        )

    @staticmethod
    def _field_value(payload, field_name: str, current_value):
        return payload.model_dump(exclude_unset=True).get(field_name, current_value)

    @staticmethod
    def _core_update_payload(payload: PlanningRecordUpdate) -> PlanningRecordUpdate:
        core_fields = {
            "dispatcher_user_id",
            "name",
            "planning_from",
            "planning_to",
            "notes",
            "status",
            "archived_at",
            "version_no",
        }
        return PlanningRecordUpdate(**{key: value for key, value in payload.model_dump(exclude_unset=True).items() if key in core_fields})

    def _not_found(self, resource: str) -> ApiException:
        return ApiException(404, f"planning.{resource}.not_found", f"errors.planning.{resource}.not_found")

    @staticmethod
    def _snapshot(row) -> dict[str, object]:
        return {
            key: value
            for key, value in row.__dict__.items()
            if not key.startswith("_")
            and key
            not in {
                "order",
                "parent_planning_record",
                "child_planning_records",
                "dispatcher_user",
                "event_detail",
                "site_detail",
                "trade_fair_detail",
                "patrol_detail",
            }
        }

    def _record_event(
        self,
        actor: RequestAuthorizationContext,
        event_type: str,
        entity_type: str,
        entity_id: str,
        tenant_id: str,
        *,
        before_json: dict[str, object] | None = None,
        after_json: dict[str, object] | None = None,
    ) -> None:
        if self.audit_service is None:
            return
        self.audit_service.record_business_event(
            actor=AuditActor(
                user_id=actor.user_id,
                tenant_id=tenant_id,
                request_id=actor.request_id,
                session_id=actor.session_id,
            ),
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            tenant_id=tenant_id,
            before_json=before_json,
            after_json=after_json,
        )
