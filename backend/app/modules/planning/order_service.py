"""Service layer for customer orders and normalized order child lines."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol

from app.errors import ApiException
from app.modules.customers.models import Customer
from app.modules.iam.audit_service import AuditActor, AuditService
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.planning.commercial_link_service import PlanningCommercialLinkService
from app.modules.planning.models import CustomerOrder, OrderEquipmentLine, OrderRequirementLine, PatrolRoute, RequirementType
from app.modules.planning.schemas import (
    CustomerOrderAttachmentCreate,
    CustomerOrderAttachmentLinkCreate,
    CustomerOrderCreate,
    CustomerOrderFilter,
    CustomerOrderListItem,
    CustomerOrderRead,
    CustomerOrderReleaseStateUpdate,
    CustomerOrderUpdate,
    OrderEquipmentLineCreate,
    OrderEquipmentLineRead,
    OrderEquipmentLineUpdate,
    OrderRequirementLineCreate,
    OrderRequirementLineRead,
    OrderRequirementLineUpdate,
)
from app.modules.platform_services.docs_schemas import DocumentCreate, DocumentLinkCreate, DocumentVersionCreate, DocumentRead
from app.modules.platform_services.docs_service import DocumentService


class PlanningOrderRepository(Protocol):
    def get_customer(self, tenant_id: str, customer_id: str) -> Customer | None: ...
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
    def find_order_equipment_line(self, tenant_id: str, order_id: str, equipment_item_id: str, *, exclude_id: str | None = None) -> OrderEquipmentLine | None: ...
    def list_order_requirement_lines(self, tenant_id: str, order_id: str) -> list[OrderRequirementLine]: ...
    def get_order_requirement_line(self, tenant_id: str, row_id: str) -> OrderRequirementLine | None: ...
    def create_order_requirement_line(self, tenant_id: str, payload: OrderRequirementLineCreate, actor_user_id: str | None) -> OrderRequirementLine: ...
    def update_order_requirement_line(self, tenant_id: str, row_id: str, payload: OrderRequirementLineUpdate, actor_user_id: str | None) -> OrderRequirementLine | None: ...


class PlanningOrderDocumentRepository(Protocol):
    def list_documents_for_owner(self, tenant_id: str, owner_type: str, owner_id: str) -> list[object]: ...


class CustomerOrderService:
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
        self._validate_order_payload(tenant_id, payload.customer_id, payload.requirement_type_id, payload.patrol_route_id, payload.service_from, payload.service_to)
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
        next_customer_id = self._field_value(payload, "customer_id", current.customer_id)
        next_requirement_type_id = self._field_value(payload, "requirement_type_id", current.requirement_type_id)
        next_patrol_route_id = self._field_value(payload, "patrol_route_id", current.patrol_route_id)
        next_service_from = self._field_value(payload, "service_from", current.service_from)
        next_service_to = self._field_value(payload, "service_to", current.service_to)
        self._validate_order_payload(tenant_id, next_customer_id, next_requirement_type_id, next_patrol_route_id, next_service_from, next_service_to)
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
        before_json = self._snapshot(current)
        row = self.repository.update_order_requirement_line(tenant_id, row_id, payload, actor.user_id)
        if row is None:
            raise self._not_found("order_requirement_line")
        self._record_event(actor, "planning.order_requirement_line.updated", "ops.order_requirement_line", row.id, tenant_id, before_json=before_json, after_json=self._snapshot(row))
        return OrderRequirementLineRead.model_validate(row)

    def list_order_attachments(self, tenant_id: str, order_id: str, _actor: RequestAuthorizationContext) -> list[DocumentRead]:
        self._require_order(tenant_id, order_id)
        return [DocumentRead.model_validate(row) for row in self.document_repository.list_documents_for_owner(tenant_id, "ops.customer_order", order_id)]

    def create_order_attachment(
        self,
        tenant_id: str,
        order_id: str,
        payload: CustomerOrderAttachmentCreate,
        actor: RequestAuthorizationContext,
    ) -> DocumentRead:
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
        return DocumentRead.model_validate(next(row for row in refreshed if row.id == document.id))

    def link_order_attachment(
        self,
        tenant_id: str,
        order_id: str,
        payload: CustomerOrderAttachmentLinkCreate,
        actor: RequestAuthorizationContext,
    ) -> DocumentRead:
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
        return DocumentRead.model_validate(next(row for row in refreshed if row.id == payload.document_id))

    def _validate_order_payload(
        self,
        tenant_id: str,
        customer_id: str,
        requirement_type_id: str,
        patrol_route_id: str | None,
        service_from,
        service_to,
    ) -> None:
        customer = self.repository.get_customer(tenant_id, customer_id)
        if customer is None:
            raise ApiException(404, "planning.customer.not_found", "errors.planning.customer.not_found")
        requirement_type = self.repository.get_requirement_type(tenant_id, requirement_type_id)
        if requirement_type is None:
            raise self._not_found("requirement_type")
        if requirement_type.customer_id != customer_id:
            raise ApiException(400, "planning.customer_order.requirement_type_customer_mismatch", "errors.planning.customer_order.requirement_type_customer_mismatch")
        if service_to < service_from:
            raise ApiException(400, "planning.customer_order.invalid_window", "errors.planning.customer_order.invalid_window")
        if patrol_route_id is not None:
            patrol_route = self.repository.get_patrol_route(tenant_id, patrol_route_id)
            if patrol_route is None:
                raise self._not_found("patrol_route")
            if patrol_route.customer_id != customer_id:
                raise ApiException(400, "planning.customer_order.patrol_route_customer_mismatch", "errors.planning.customer_order.patrol_route_customer_mismatch")

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
                    DocumentRead.model_validate(document)
                    for document in self.document_repository.list_documents_for_owner(row.tenant_id, "ops.customer_order", row.id)
                ]
            }
        )

    @classmethod
    def _require_release_state(cls, release_state: str) -> None:
        if release_state not in cls.RELEASE_STATES:
            raise ApiException(400, "planning.customer_order.invalid_release_state", "errors.planning.customer_order.invalid_release_state")

    @staticmethod
    def _field_value(payload, field_name: str, current_value):
        return payload.model_dump(exclude_unset=True).get(field_name, current_value)

    def _not_found(self, resource: str) -> ApiException:
        return ApiException(404, f"planning.{resource}.not_found", f"errors.planning.{resource}.not_found")

    @staticmethod
    def _snapshot(row) -> dict[str, object]:
        return {
            key: value
            for key, value in row.__dict__.items()
            if not key.startswith("_") and key not in {"customer", "requirement_type", "patrol_route", "equipment_lines", "requirement_lines", "planning_records"}
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
