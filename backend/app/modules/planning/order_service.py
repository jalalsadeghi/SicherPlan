"""Service layer for customer orders and normalized order child lines."""

from __future__ import annotations

from datetime import UTC, date, datetime, time
from decimal import Decimal
from enum import Enum
from typing import Protocol
from uuid import UUID

from sqlalchemy import inspect as sa_inspect
from sqlalchemy.exc import NoInspectionAvailable

from app.errors import ApiException
from app.modules.customers.models import Customer
from app.modules.iam.audit_service import AuditActor, AuditService
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.planning.commercial_link_service import PlanningCommercialLinkService
from app.modules.planning.models import CustomerOrder, OrderEquipmentLine, OrderRequirementLine, PatrolRoute, RequirementType, ServiceCategory
from app.modules.planning.schemas import (
    CustomerOrderAttachmentCreate,
    CustomerOrderAttachmentLinkCreate,
    CustomerOrderCreate,
    CustomerOrderFilter,
    CustomerOrderListItem,
    CustomerOrderRead,
    CustomerOrderReleaseStateUpdate,
    CustomerOrderUpdate,
    OrderAttachmentRead,
    OrderEquipmentLineCreate,
    OrderEquipmentLineRead,
    OrderEquipmentLineUpdate,
    OrderRequirementLineCreate,
    OrderRequirementLineRead,
    OrderRequirementLineUpdate,
)
from app.modules.platform_services.docs_schemas import DocumentCreate, DocumentLinkCreate, DocumentVersionCreate
from app.modules.platform_services.docs_service import DocumentService


class PlanningOrderRepository(Protocol):
    def get_customer(self, tenant_id: str, customer_id: str) -> Customer | None: ...
    def list_lookup_values(self, tenant_id: str | None, domain: str): ...  # noqa: ANN001
    def list_service_categories(self, tenant_id: str, filters): ...  # noqa: ANN001
    def get_requirement_type(self, tenant_id: str, row_id: str) -> RequirementType | None: ...
    def get_patrol_route(self, tenant_id: str, row_id: str) -> PatrolRoute | None: ...
    def get_equipment_item(self, tenant_id: str, row_id: str): ...  # noqa: ANN001
    def get_function_type(self, tenant_id: str, function_type_id: str): ...  # noqa: ANN001
    def get_qualification_type(self, tenant_id: str, qualification_type_id: str): ...  # noqa: ANN001
    def list_customer_orders(self, tenant_id: str, filters: CustomerOrderFilter) -> list[CustomerOrder]: ...
    def get_customer_order(self, tenant_id: str, order_id: str) -> CustomerOrder | None: ...
    def find_customer_order_by_no(self, tenant_id: str, order_no: str, *, exclude_id: str | None = None) -> CustomerOrder | None: ...
    def create_customer_order(self, tenant_id: str, payload: CustomerOrderCreate, actor_user_id: str | None) -> CustomerOrder: ...
    def update_customer_order(self, tenant_id: str, order_id: str, payload: CustomerOrderUpdate, actor_user_id: str | None) -> CustomerOrder | None: ...
    def save_customer_order(self, row: CustomerOrder) -> CustomerOrder: ...
    def list_order_equipment_lines(self, tenant_id: str, order_id: str) -> list[OrderEquipmentLine]: ...
    def get_order_equipment_line(self, tenant_id: str, row_id: str) -> OrderEquipmentLine | None: ...
    def create_order_equipment_line(self, tenant_id: str, payload: OrderEquipmentLineCreate, actor_user_id: str | None) -> OrderEquipmentLine: ...
    def update_order_equipment_line(self, tenant_id: str, row_id: str, payload: OrderEquipmentLineUpdate, actor_user_id: str | None) -> OrderEquipmentLine | None: ...
    def delete_order_equipment_line(self, tenant_id: str, row_id: str) -> bool: ...
    def find_order_equipment_line(self, tenant_id: str, order_id: str, equipment_item_id: str, *, exclude_id: str | None = None) -> OrderEquipmentLine | None: ...
    def list_order_requirement_lines(self, tenant_id: str, order_id: str) -> list[OrderRequirementLine]: ...
    def get_order_requirement_line(self, tenant_id: str, row_id: str) -> OrderRequirementLine | None: ...
    def create_order_requirement_line(self, tenant_id: str, payload: OrderRequirementLineCreate, actor_user_id: str | None) -> OrderRequirementLine: ...
    def update_order_requirement_line(self, tenant_id: str, row_id: str, payload: OrderRequirementLineUpdate, actor_user_id: str | None) -> OrderRequirementLine | None: ...
    def delete_order_requirement_line(self, tenant_id: str, row_id: str) -> bool: ...


class PlanningOrderDocumentRepository(Protocol):
    def list_documents_for_owner(self, tenant_id: str, owner_type: str, owner_id: str) -> list[object]: ...


class CustomerOrderService:
    _SKIP_SNAPSHOT_VALUE = object()
    SERVICE_CATEGORY_DOMAIN = "service_category"
    SERVICE_CATEGORY_FALLBACK_OPTIONS: tuple[dict[str, object], ...] = (
        {
            "code": "object_security",
            "label": "Objektschutz",
            "description": "Objekt- oder standortbezogene Sicherheitsleistung",
            "sort_order": 10,
        },
        {
            "code": "event_security",
            "label": "Veranstaltungsschutz",
            "description": "Veranstaltungsbezogene Sicherheitsleistung",
            "sort_order": 20,
        },
        {
            "code": "trade_fair_security",
            "label": "Messebewachung",
            "description": "Messe- oder standbezogene Sicherheitsleistung",
            "sort_order": 30,
        },
        {
            "code": "patrol_service",
            "label": "Revier- / Patrouillendienst",
            "description": "Patrouillen-, Revier- oder Alarmfahrdienst",
            "sort_order": 40,
        },
    )
    RELEASE_STATES = frozenset({"draft", "release_ready", "released"})
    RELEASE_TRANSITIONS = {
        "draft": {"draft", "release_ready"},
        "release_ready": {"draft", "release_ready", "released"},
        "released": {"release_ready", "released"},
    }

    def __init__(
        self,
        repository: PlanningOrderRepository,
        *,
        document_repository: PlanningOrderDocumentRepository,
        document_service: DocumentService,
        commercial_link_service: PlanningCommercialLinkService | None = None,
        audit_service: AuditService | None = None,
    ) -> None:
        self.repository = repository
        self.document_repository = document_repository
        self.document_service = document_service
        self.commercial_link_service = commercial_link_service
        self.audit_service = audit_service

    def list_orders(
        self,
        tenant_id: str,
        filters: CustomerOrderFilter,
        _actor: RequestAuthorizationContext,
    ) -> list[CustomerOrderListItem]:
        return [CustomerOrderListItem.model_validate(row) for row in self.repository.list_customer_orders(tenant_id, filters)]

    def get_order(self, tenant_id: str, order_id: str, _actor: RequestAuthorizationContext) -> CustomerOrderRead:
        row = self._require_order(tenant_id, order_id)
        return self._read(row)

    def create_order(self, tenant_id: str, payload: CustomerOrderCreate, actor: RequestAuthorizationContext) -> CustomerOrderRead:
        payload = payload.model_copy(
            update={
                "customer_id": self._normalize_required_order_uuid(
                    payload.customer_id,
                    code="planning.customer_order.invalid_customer_id",
                    message_key="errors.planning.customer_order.invalid_customer_id",
                ),
                "requirement_type_id": self._normalize_required_order_uuid(
                    payload.requirement_type_id,
                    code="planning.customer_order.invalid_requirement_type_id",
                    message_key="errors.planning.customer_order.invalid_requirement_type_id",
                ),
                "patrol_route_id": self._normalize_optional_order_uuid(payload.patrol_route_id),
            }
        )
        self._validate_order_payload(
            tenant_id,
            payload.customer_id,
            payload.requirement_type_id,
            payload.patrol_route_id,
            payload.service_category_code,
            payload.service_from,
            payload.service_to,
        )
        self._require_release_state(payload.release_state)
        if self.repository.find_customer_order_by_no(tenant_id, payload.order_no) is not None:
            raise ApiException(409, "planning.customer_order.duplicate_number", "errors.planning.customer_order.duplicate_number")
        row = self.repository.create_customer_order(tenant_id, payload, actor.user_id)
        self._record_event(actor, "planning.customer_order.created", "ops.customer_order", row.id, tenant_id, after_json=self._snapshot(row))
        return self._read(row)

    def update_order(
        self,
        tenant_id: str,
        order_id: str,
        payload: CustomerOrderUpdate,
        actor: RequestAuthorizationContext,
    ) -> CustomerOrderRead:
        current = self._require_order(tenant_id, order_id)
        before_json = self._snapshot(current)
        next_customer_id = self._normalize_required_order_uuid(
            self._field_value(payload, "customer_id", current.customer_id),
            code="planning.customer_order.invalid_customer_id",
            message_key="errors.planning.customer_order.invalid_customer_id",
        )
        next_requirement_type_id = self._normalize_required_order_uuid(
            self._field_value(payload, "requirement_type_id", current.requirement_type_id),
            code="planning.customer_order.invalid_requirement_type_id",
            message_key="errors.planning.customer_order.invalid_requirement_type_id",
        )
        next_patrol_route_id = self._normalize_optional_order_uuid(self._field_value(payload, "patrol_route_id", current.patrol_route_id))
        next_service_category_code = self._field_value(payload, "service_category_code", current.service_category_code)
        next_service_from = self._field_value(payload, "service_from", current.service_from)
        next_service_to = self._field_value(payload, "service_to", current.service_to)
        self._validate_order_payload(
            tenant_id,
            next_customer_id,
            next_requirement_type_id,
            next_patrol_route_id,
            next_service_category_code,
            next_service_from,
            next_service_to,
            current_service_category_code=current.service_category_code,
        )
        payload_updates: dict[str, object | None] = {}
        if "customer_id" in payload.model_fields_set:
            payload_updates["customer_id"] = next_customer_id
        if "requirement_type_id" in payload.model_fields_set:
            payload_updates["requirement_type_id"] = next_requirement_type_id
        if "patrol_route_id" in payload.model_fields_set:
            payload_updates["patrol_route_id"] = next_patrol_route_id
        if payload_updates:
            payload = payload.model_copy(update=payload_updates)
        next_order_no = self._field_value(payload, "order_no", current.order_no)
        if self.repository.find_customer_order_by_no(tenant_id, next_order_no, exclude_id=order_id) is not None:
            raise ApiException(409, "planning.customer_order.duplicate_number", "errors.planning.customer_order.duplicate_number")
        row = self.repository.update_customer_order(tenant_id, order_id, payload, actor.user_id)
        if row is None:
            raise self._not_found("customer_order")
        self._record_event(actor, "planning.customer_order.updated", "ops.customer_order", row.id, tenant_id, before_json=before_json, after_json=self._snapshot(row))
        return self._read(row)

    def set_order_release_state(
        self,
        tenant_id: str,
        order_id: str,
        payload: CustomerOrderReleaseStateUpdate,
        actor: RequestAuthorizationContext,
    ) -> CustomerOrderRead:
        row = self._require_order(tenant_id, order_id)
        if payload.version_no != row.version_no:
            raise ApiException(409, "planning.customer_order.stale_version", "errors.planning.customer_order.stale_version", {"current_version": row.version_no})
        self._require_release_state(payload.release_state)
        if payload.release_state not in self.RELEASE_TRANSITIONS[row.release_state]:
            raise ApiException(409, "planning.customer_order.invalid_release_transition", "errors.planning.customer_order.invalid_release_transition")
        if payload.release_state == "released" and self.commercial_link_service is not None:
            self.commercial_link_service.assert_order_release_ready(tenant_id, order_id)
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
        row = self.repository.save_customer_order(row)
        self._record_event(actor, "planning.customer_order.release_state.changed", "ops.customer_order", row.id, tenant_id, before_json=before_json, after_json=self._snapshot(row))
        return self._read(row)

    def list_order_equipment_lines(self, tenant_id: str, order_id: str, _actor: RequestAuthorizationContext) -> list[OrderEquipmentLineRead]:
        self._require_order(tenant_id, order_id)
        return [OrderEquipmentLineRead.model_validate(row) for row in self.repository.list_order_equipment_lines(tenant_id, order_id)]

    def create_order_equipment_line(
        self,
        tenant_id: str,
        order_id: str,
        payload: OrderEquipmentLineCreate,
        actor: RequestAuthorizationContext,
    ) -> OrderEquipmentLineRead:
        self._require_order_match(tenant_id, order_id, payload.order_id)
        if self.repository.find_order_equipment_line(tenant_id, order_id, payload.equipment_item_id) is not None:
            raise ApiException(409, "planning.order_equipment.duplicate_item", "errors.planning.order_equipment.duplicate_item")
        if self.repository.get_equipment_item(tenant_id, payload.equipment_item_id) is None:
            raise self._not_found("equipment_item")
        row = self.repository.create_order_equipment_line(tenant_id, payload, actor.user_id)
        self._record_event(actor, "planning.order_equipment.created", "ops.order_equipment", row.id, tenant_id, after_json=self._snapshot(row))
        return OrderEquipmentLineRead.model_validate(row)

    def update_order_equipment_line(
        self,
        tenant_id: str,
        order_id: str,
        row_id: str,
        payload: OrderEquipmentLineUpdate,
        actor: RequestAuthorizationContext,
    ) -> OrderEquipmentLineRead:
        self._require_order(tenant_id, order_id)
        current = self.repository.get_order_equipment_line(tenant_id, row_id)
        if current is None or current.order_id != order_id:
            raise self._not_found("order_equipment")
        next_equipment_item_id = self._field_value(payload, "equipment_item_id", current.equipment_item_id)
        if self.repository.get_equipment_item(tenant_id, next_equipment_item_id) is None:
            raise self._not_found("equipment_item")
        if self.repository.find_order_equipment_line(tenant_id, order_id, next_equipment_item_id, exclude_id=row_id) is not None:
            raise ApiException(409, "planning.order_equipment.duplicate_item", "errors.planning.order_equipment.duplicate_item")
        before_json = self._snapshot(current)
        row = self.repository.update_order_equipment_line(tenant_id, row_id, payload, actor.user_id)
        if row is None:
            raise self._not_found("order_equipment")
        self._record_event(actor, "planning.order_equipment.updated", "ops.order_equipment", row.id, tenant_id, before_json=before_json, after_json=self._snapshot(row))
        return OrderEquipmentLineRead.model_validate(row)

    def delete_order_equipment_line(
        self,
        tenant_id: str,
        order_id: str,
        row_id: str,
        actor: RequestAuthorizationContext,
    ) -> None:
        self._require_order(tenant_id, order_id)
        current = self.repository.get_order_equipment_line(tenant_id, row_id)
        if current is None or current.order_id != order_id:
            raise self._not_found("order_equipment")
        before_json = self._snapshot(current)
        if not self.repository.delete_order_equipment_line(tenant_id, row_id):
            raise self._not_found("order_equipment")
        self._record_event(actor, "planning.order_equipment.deleted", "ops.order_equipment", row_id, tenant_id, before_json=before_json)

    def list_order_requirement_lines(self, tenant_id: str, order_id: str, _actor: RequestAuthorizationContext) -> list[OrderRequirementLineRead]:
        self._require_order(tenant_id, order_id)
        return [OrderRequirementLineRead.model_validate(row) for row in self.repository.list_order_requirement_lines(tenant_id, order_id)]

    def create_order_requirement_line(
        self,
        tenant_id: str,
        order_id: str,
        payload: OrderRequirementLineCreate,
        actor: RequestAuthorizationContext,
    ) -> OrderRequirementLineRead:
        self._require_order_match(tenant_id, order_id, payload.order_id)
        self._validate_requirement_line(tenant_id, payload.requirement_type_id, payload.function_type_id, payload.qualification_type_id, payload.min_qty, payload.target_qty)
        self._validate_requirement_line_duplicate(
            tenant_id,
            order_id,
            payload.requirement_type_id,
            payload.function_type_id,
            payload.qualification_type_id,
        )
        row = self.repository.create_order_requirement_line(tenant_id, payload, actor.user_id)
        self._record_event(actor, "planning.order_requirement_line.created", "ops.order_requirement_line", row.id, tenant_id, after_json=self._snapshot(row))
        return OrderRequirementLineRead.model_validate(row)

    def update_order_requirement_line(
        self,
        tenant_id: str,
        order_id: str,
        row_id: str,
        payload: OrderRequirementLineUpdate,
        actor: RequestAuthorizationContext,
    ) -> OrderRequirementLineRead:
        self._require_order(tenant_id, order_id)
        current = self.repository.get_order_requirement_line(tenant_id, row_id)
        if current is None or current.order_id != order_id:
            raise self._not_found("order_requirement_line")
        next_requirement_type_id = self._field_value(payload, "requirement_type_id", current.requirement_type_id)
        next_function_type_id = self._field_value(payload, "function_type_id", current.function_type_id)
        next_qualification_type_id = self._field_value(payload, "qualification_type_id", current.qualification_type_id)
        next_min_qty = self._field_value(payload, "min_qty", current.min_qty)
        next_target_qty = self._field_value(payload, "target_qty", current.target_qty)
        self._validate_requirement_line(
            tenant_id,
            next_requirement_type_id,
            next_function_type_id,
            next_qualification_type_id,
            next_min_qty,
            next_target_qty,
        )
        self._validate_requirement_line_duplicate(
            tenant_id,
            order_id,
            next_requirement_type_id,
            next_function_type_id,
            next_qualification_type_id,
            exclude_id=row_id,
        )
        before_json = self._snapshot(current)
        row = self.repository.update_order_requirement_line(tenant_id, row_id, payload, actor.user_id)
        if row is None:
            raise self._not_found("order_requirement_line")
        self._record_event(actor, "planning.order_requirement_line.updated", "ops.order_requirement_line", row.id, tenant_id, before_json=before_json, after_json=self._snapshot(row))
        return OrderRequirementLineRead.model_validate(row)

    def delete_order_requirement_line(
        self,
        tenant_id: str,
        order_id: str,
        row_id: str,
        actor: RequestAuthorizationContext,
    ) -> None:
        self._require_order(tenant_id, order_id)
        current = self.repository.get_order_requirement_line(tenant_id, row_id)
        if current is None or current.order_id != order_id:
            raise self._not_found("order_requirement_line")
        before_json = self._snapshot(current)
        if not self.repository.delete_order_requirement_line(tenant_id, row_id):
            raise self._not_found("order_requirement_line")
        self._record_event(actor, "planning.order_requirement_line.deleted", "ops.order_requirement_line", row_id, tenant_id, before_json=before_json)

    def list_order_attachments(self, tenant_id: str, order_id: str, _actor: RequestAuthorizationContext) -> list[OrderAttachmentRead]:
        self._require_order(tenant_id, order_id)
        return [
            self._read_order_attachment(row, order_id)
            for row in self.document_repository.list_documents_for_owner(tenant_id, "ops.customer_order", order_id)
        ]

    def create_order_attachment(
        self,
        tenant_id: str,
        order_id: str,
        payload: CustomerOrderAttachmentCreate,
        actor: RequestAuthorizationContext,
    ) -> OrderAttachmentRead:
        self._require_order(tenant_id, order_id)
        if payload.tenant_id != tenant_id:
            raise ApiException(400, "planning.order_attachment.scope_mismatch", "errors.planning.order_attachment.scope_mismatch")
        document = self.document_service.create_document(
            tenant_id,
            DocumentCreate(
                tenant_id=tenant_id,
                title=payload.title,
                document_type_key=payload.document_type_key,
                source_module="planning",
                source_label="customer-order-attachment",
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
                owner_type="ops.customer_order",
                owner_id=order_id,
                relation_type=payload.relation_type,
                label=payload.label,
                metadata_json=payload.metadata_json,
            ),
            actor,
        )
        self._record_event(actor, "planning.customer_order.attachment.created", "ops.customer_order", order_id, tenant_id, metadata_json={"document_id": document.id})
        refreshed = self.document_repository.list_documents_for_owner(tenant_id, "ops.customer_order", order_id)
        return self._read_order_attachment(next(row for row in refreshed if row.id == document.id), order_id)

    def link_order_attachment(
        self,
        tenant_id: str,
        order_id: str,
        payload: CustomerOrderAttachmentLinkCreate,
        actor: RequestAuthorizationContext,
    ) -> OrderAttachmentRead:
        self._require_order(tenant_id, order_id)
        if payload.tenant_id != tenant_id:
            raise ApiException(400, "planning.order_attachment.scope_mismatch", "errors.planning.order_attachment.scope_mismatch")
        self.document_service.add_document_link(
            tenant_id,
            payload.document_id,
            DocumentLinkCreate(
                owner_type="ops.customer_order",
                owner_id=order_id,
                relation_type=payload.relation_type,
                label=payload.label,
                metadata_json=payload.metadata_json,
            ),
            actor,
        )
        self._record_event(actor, "planning.customer_order.attachment.linked", "ops.customer_order", order_id, tenant_id, metadata_json={"document_id": payload.document_id})
        refreshed = self.document_repository.list_documents_for_owner(tenant_id, "ops.customer_order", order_id)
        return self._read_order_attachment(next(row for row in refreshed if row.id == payload.document_id), order_id)

    def unlink_order_attachment(
        self,
        tenant_id: str,
        order_id: str,
        document_id: str,
        actor: RequestAuthorizationContext,
    ) -> None:
        self._require_order(tenant_id, order_id)
        self.document_service.delete_document_link(tenant_id, document_id, "ops.customer_order", order_id, actor)
        self._record_event(actor, "planning.customer_order.attachment.unlinked", "ops.customer_order", order_id, tenant_id, metadata_json={"document_id": document_id})

    def _validate_order_payload(
        self,
        tenant_id: str,
        customer_id: str,
        requirement_type_id: str,
        patrol_route_id: str | None,
        service_category_code: str,
        service_from,
        service_to,
        *,
        current_service_category_code: str | None = None,
    ) -> None:
        customer = self.repository.get_customer(tenant_id, customer_id)
        if customer is None:
            raise ApiException(404, "planning.customer.not_found", "errors.planning.customer.not_found")
        requirement_type = self.repository.get_requirement_type(tenant_id, requirement_type_id)
        if requirement_type is None:
            raise self._not_found("requirement_type")
        self._validate_service_category_code(
            tenant_id,
            service_category_code,
            current_service_category_code=current_service_category_code,
        )
        if service_to < service_from:
            raise ApiException(400, "planning.customer_order.invalid_window", "errors.planning.customer_order.invalid_window")
        if patrol_route_id is not None:
            patrol_route = self.repository.get_patrol_route(tenant_id, patrol_route_id)
            if patrol_route is None:
                raise self._not_found("patrol_route")
            if patrol_route.customer_id != customer_id:
                raise ApiException(400, "planning.customer_order.patrol_route_customer_mismatch", "errors.planning.customer_order.patrol_route_customer_mismatch")

    def _validate_service_category_code(
        self,
        tenant_id: str,
        service_category_code: str,
        *,
        current_service_category_code: str | None = None,
    ) -> None:
        catalog_codes = {
            row.code
            for row in self._list_active_service_categories(tenant_id)
        }
        if catalog_codes:
            if service_category_code in catalog_codes:
                return
            if current_service_category_code is not None and service_category_code == current_service_category_code:
                return
            raise ApiException(
                400,
                "planning.customer_order.invalid_service_category_code",
                "errors.planning.customer_order.invalid_service_category_code",
            )
        canonical_codes = {row["code"] for row in self.SERVICE_CATEGORY_FALLBACK_OPTIONS}
        allowed_codes = {
            getattr(row, "code", None)
            for row in self.repository.list_lookup_values(None, self.SERVICE_CATEGORY_DOMAIN)
            if getattr(row, "code", None) in canonical_codes
        }
        allowed_codes.discard(None)
        if not allowed_codes:
            allowed_codes = canonical_codes
        if service_category_code in allowed_codes:
            return
        if current_service_category_code is not None and service_category_code == current_service_category_code:
            return
        raise ApiException(
            400,
            "planning.customer_order.invalid_service_category_code",
            "errors.planning.customer_order.invalid_service_category_code",
        )

    def _list_active_service_categories(self, tenant_id: str) -> list[ServiceCategory]:
        list_service_categories = getattr(self.repository, "list_service_categories", None)
        if not callable(list_service_categories):
            return []
        from app.modules.planning.schemas import OpsMasterFilter

        return [
            row
            for row in list_service_categories(tenant_id, OpsMasterFilter(lifecycle_status="active"))
            if getattr(row, "archived_at", None) is None and getattr(row, "status", "active") == "active"
        ]

    def _validate_requirement_line(
        self,
        tenant_id: str,
        requirement_type_id: str,
        function_type_id: str | None,
        qualification_type_id: str | None,
        min_qty: int,
        target_qty: int,
    ) -> None:
        if self.repository.get_requirement_type(tenant_id, requirement_type_id) is None:
            raise self._not_found("requirement_type")
        if function_type_id is not None and self.repository.get_function_type(tenant_id, function_type_id) is None:
            raise self._not_found("function_type")
        if qualification_type_id is not None and self.repository.get_qualification_type(tenant_id, qualification_type_id) is None:
            raise self._not_found("qualification_type")
        if min_qty > target_qty:
            raise ApiException(400, "planning.order_requirement_line.invalid_qty_window", "errors.planning.order_requirement_line.invalid_qty_window")

    def _validate_requirement_line_duplicate(
        self,
        tenant_id: str,
        order_id: str,
        requirement_type_id: str,
        function_type_id: str | None,
        qualification_type_id: str | None,
        *,
        exclude_id: str | None = None,
    ) -> None:
        for row in self.repository.list_order_requirement_lines(tenant_id, order_id):
            if row.id == exclude_id:
                continue
            if row.archived_at is not None or row.status == "archived":
                continue
            if (
                row.requirement_type_id == requirement_type_id
                and row.function_type_id == function_type_id
                and row.qualification_type_id == qualification_type_id
            ):
                raise ApiException(
                    409,
                    "planning.order_requirement_line.duplicate_tuple",
                    "errors.planning.order_requirement_line.duplicate_tuple",
                )

    def _require_order(self, tenant_id: str, order_id: str) -> CustomerOrder:
        row = self.repository.get_customer_order(tenant_id, order_id)
        if row is None:
            raise self._not_found("customer_order")
        return row

    @staticmethod
    def _require_order_match(tenant_id: str, order_id: str, payload_order_id: str) -> None:
        if order_id != payload_order_id:
            raise ApiException(400, "planning.customer_order.scope_mismatch", "errors.planning.customer_order.scope_mismatch", {"tenant_id": tenant_id})

    def _read(self, row: CustomerOrder) -> CustomerOrderRead:
        schema = CustomerOrderRead.model_validate(row)
        return schema.model_copy(
            update={
                "attachments": [
                    self._read_order_attachment(document, row.id)
                    for document in self.document_repository.list_documents_for_owner(row.tenant_id, "ops.customer_order", row.id)
                ]
            }
        )

    @staticmethod
    def _read_order_attachment(document: object, order_id: str) -> OrderAttachmentRead:
        relation_label: str | None = None
        relation_type: str | None = None
        for link in getattr(document, "links", []) or []:
            if getattr(link, "owner_type", None) == "ops.customer_order" and getattr(link, "owner_id", None) == order_id:
                relation_label = getattr(link, "label", None)
                relation_type = getattr(link, "relation_type", None)
                break
        return OrderAttachmentRead.model_validate(document).model_copy(
            update={
                "relation_label": relation_label,
                "relation_type": relation_type,
            }
        )

    @classmethod
    def _require_release_state(cls, release_state: str) -> None:
        if release_state not in cls.RELEASE_STATES:
            raise ApiException(400, "planning.customer_order.invalid_release_state", "errors.planning.customer_order.invalid_release_state")

    @staticmethod
    def _normalize_optional_order_uuid(value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @classmethod
    def _normalize_required_order_uuid(cls, value: str, *, code: str, message_key: str) -> str:
        normalized = cls._normalize_optional_order_uuid(value)
        if normalized is None:
            raise ApiException(400, code, message_key)
        return normalized

    @staticmethod
    def _field_value(payload, field_name: str, current_value):
        return payload.model_dump(exclude_unset=True).get(field_name, current_value)

    def _not_found(self, resource: str) -> ApiException:
        return ApiException(404, f"planning.{resource}.not_found", f"errors.planning.{resource}.not_found")

    @classmethod
    def _snapshot(cls, row) -> dict[str, object]:
        try:
            mapper = sa_inspect(row).mapper
        except NoInspectionAvailable:
            source_items = vars(row).items()
        else:
            source_items = ((attribute.key, getattr(row, attribute.key)) for attribute in mapper.column_attrs)

        snapshot: dict[str, object] = {}
        for key, value in source_items:
            if key.startswith("_"):
                continue
            serialized = cls._json_safe_snapshot_value(value)
            if serialized is cls._SKIP_SNAPSHOT_VALUE:
                continue
            snapshot[key] = serialized
        return snapshot

    @classmethod
    def _json_safe_snapshot_value(cls, value: object) -> object:
        if value is None or isinstance(value, bool | int | float | str):
            return value
        if isinstance(value, Decimal):
            return str(value)
        if isinstance(value, datetime | date | time):
            return value.isoformat()
        if isinstance(value, UUID):
            return str(value)
        if isinstance(value, Enum):
            return cls._json_safe_snapshot_value(value.value)
        if isinstance(value, dict):
            result: dict[str, object] = {}
            for key, item in value.items():
                serialized = cls._json_safe_snapshot_value(item)
                if serialized is cls._SKIP_SNAPSHOT_VALUE:
                    continue
                result[str(key)] = serialized
            return result
        if isinstance(value, list | tuple):
            result: list[object] = []
            for item in value:
                serialized = cls._json_safe_snapshot_value(item)
                if serialized is cls._SKIP_SNAPSHOT_VALUE:
                    continue
                result.append(serialized)
            return result
        if isinstance(value, set):
            result: list[object] = []
            for item in sorted(value, key=repr):
                serialized = cls._json_safe_snapshot_value(item)
                if serialized is cls._SKIP_SNAPSHOT_VALUE:
                    continue
                result.append(serialized)
            return result
        return cls._SKIP_SNAPSHOT_VALUE

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
        metadata_json: dict[str, object] | None = None,
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
            metadata_json=metadata_json,
        )
