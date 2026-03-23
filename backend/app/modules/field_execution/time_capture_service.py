"""Service logic for time-capture devices, policies, and raw event ingest."""

from __future__ import annotations

import hashlib
import hmac
import ipaddress
import math
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Protocol

from app.errors import ApiException
from app.modules.field_execution.models import TimeCaptureDevice, TimeCapturePolicy, TimeEvent
from app.modules.field_execution.schemas import (
    TimeCaptureDeviceCreate,
    TimeCaptureDeviceFilter,
    TimeCaptureDeviceListItem,
    TimeCaptureDeviceRead,
    TimeCaptureDeviceUpdate,
    TimeCaptureEventCapture,
    TimeCaptureEventFilter,
    TimeCaptureEventListItem,
    TimeCaptureEventRead,
    TimeCaptureOwnEventCollectionRead,
    TimeCapturePolicyCreate,
    TimeCapturePolicyFilter,
    TimeCapturePolicyListItem,
    TimeCapturePolicyRead,
    TimeCapturePolicyUpdate,
    TimeCaptureTerminalEventCapture,
    TimeEventValidationStatusUpdate,
)
from app.modules.iam.audit_service import AuditActor, AuditService
from app.modules.iam.authz import RequestAuthorizationContext


DEVICE_TYPES = {"shared_terminal", "browser_station", "scanner_station", "mobile_shared"}
POLICY_CONTEXT_TYPES = {"site", "shift", "planning_record", "patrol_route"}
ENFORCE_MODES = {"flag", "reject"}
SOURCE_CHANNELS = {"browser", "mobile", "terminal"}
EVENT_CODES = {"clock_in", "clock_out", "break_start", "break_end"}
SCAN_MEDIA = {"manual", "qr", "barcode", "rfid", "nfc", "app_badge"}
VALIDATION_STATUSES = {"accepted", "flagged", "rejected"}


class TimeCaptureRepository(Protocol):
    def list_devices(self, tenant_id: str, filters: TimeCaptureDeviceFilter) -> list[TimeCaptureDevice]: ...
    def get_device(self, tenant_id: str, device_id: str) -> TimeCaptureDevice | None: ...
    def get_device_by_code(self, tenant_id: str, device_code: str) -> TimeCaptureDevice | None: ...
    def find_device_by_code(self, tenant_id: str, device_code: str, *, exclude_id: str | None = None) -> TimeCaptureDevice | None: ...
    def create_device(self, row: TimeCaptureDevice) -> TimeCaptureDevice: ...
    def update_device(self, row: TimeCaptureDevice) -> TimeCaptureDevice: ...
    def list_policies(self, tenant_id: str, filters: TimeCapturePolicyFilter) -> list[TimeCapturePolicy]: ...
    def get_policy(self, tenant_id: str, policy_id: str) -> TimeCapturePolicy | None: ...
    def find_policy_by_code(self, tenant_id: str, policy_code: str, *, exclude_id: str | None = None) -> TimeCapturePolicy | None: ...
    def find_active_policy_for_context(
        self,
        tenant_id: str,
        *,
        shift_id: str | None,
        planning_record_id: str | None,
        patrol_route_id: str | None,
        site_id: str | None,
    ) -> TimeCapturePolicy | None: ...
    def create_policy(self, row: TimeCapturePolicy) -> TimeCapturePolicy: ...
    def update_policy(self, row: TimeCapturePolicy) -> TimeCapturePolicy: ...
    def list_time_events(self, tenant_id: str, filters: TimeCaptureEventFilter) -> list[TimeEvent]: ...
    def list_employee_time_events(self, tenant_id: str, employee_id: str, *, limit: int = 30) -> list[TimeEvent]: ...
    def get_time_event(self, tenant_id: str, event_id: str) -> TimeEvent | None: ...
    def get_time_event_by_client_id(self, tenant_id: str, client_event_id: str) -> TimeEvent | None: ...
    def create_time_event(self, row: TimeEvent) -> TimeEvent: ...
    def save_time_event(self, row: TimeEvent) -> TimeEvent: ...
    def get_site(self, tenant_id: str, site_id: str): ...  # noqa: ANN001
    def get_shift(self, tenant_id: str, shift_id: str): ...  # noqa: ANN001
    def get_assignment(self, tenant_id: str, assignment_id: str): ...  # noqa: ANN001
    def find_assignment_for_employee(self, tenant_id: str, shift_id: str, employee_id: str): ...  # noqa: ANN001
    def find_assignment_for_worker(self, tenant_id: str, shift_id: str, worker_id: str): ...  # noqa: ANN001
    def find_employee_by_user_id(self, tenant_id: str, user_id: str): ...  # noqa: ANN001
    def find_employee_credential_by_encoded_value(self, tenant_id: str, encoded_value: str): ...  # noqa: ANN001
    def find_worker_credential_by_encoded_value(self, tenant_id: str, encoded_value: str): ...  # noqa: ANN001
    def get_planning_record(self, tenant_id: str, planning_record_id: str): ...  # noqa: ANN001
    def get_patrol_route(self, tenant_id: str, patrol_route_id: str): ...  # noqa: ANN001


@dataclass(frozen=True, slots=True)
class _CaptureIssue:
    code: str
    severity: str
    message_key: str
    details: dict[str, object]

    def to_json(self) -> dict[str, object]:
        return {
            "code": self.code,
            "severity": self.severity,
            "message_key": self.message_key,
            "details": self.details,
        }


@dataclass(frozen=True, slots=True)
class _ResolvedActor:
    actor_type_code: str
    employee_id: str | None
    subcontractor_worker_id: str | None
    source: str


@dataclass(frozen=True, slots=True)
class _ResolvedContext:
    shift_id: str | None
    assignment_id: str | None
    site_id: str | None
    planning_record_id: str | None
    patrol_route_id: str | None


class TimeCaptureService:
    def __init__(
        self,
        *,
        repository: TimeCaptureRepository,
        audit_service: AuditService | None = None,
    ) -> None:
        self.repository = repository
        self.audit_service = audit_service

    def list_devices(
        self,
        tenant_id: str,
        filters: TimeCaptureDeviceFilter,
        actor: RequestAuthorizationContext,
    ) -> list[TimeCaptureDeviceListItem]:
        self._require_tenant_scope(actor, tenant_id, "field.time_capture.read")
        return [
            TimeCaptureDeviceListItem(
                id=row.id,
                device_code=row.device_code,
                label=row.label,
                device_type_code=row.device_type_code,
                site_id=row.site_id,
                fixed_ip_cidr=row.fixed_ip_cidr,
                status=row.status,
                has_access_key=bool(row.access_key_hash),
                updated_at=row.updated_at,
            )
            for row in self.repository.list_devices(tenant_id, filters)
        ]

    def get_device(self, tenant_id: str, device_id: str, actor: RequestAuthorizationContext) -> TimeCaptureDeviceRead:
        self._require_tenant_scope(actor, tenant_id, "field.time_capture.read")
        row = self.repository.get_device(tenant_id, device_id)
        if row is None:
            raise ApiException(404, "field.time_capture.device.not_found", "errors.field.time_capture.device.not_found")
        return self._map_device(row)

    def create_device(self, tenant_id: str, payload: TimeCaptureDeviceCreate, actor: RequestAuthorizationContext) -> TimeCaptureDeviceRead:
        self._require_tenant_scope(actor, tenant_id, "field.time_capture.write")
        self._validate_device_shape(payload.device_type_code, payload.status, payload.fixed_ip_cidr)
        if self.repository.find_device_by_code(tenant_id, payload.device_code) is not None:
            raise ApiException(409, "field.time_capture.device.duplicate_code", "errors.field.time_capture.device.duplicate_code")
        if payload.site_id is not None and self.repository.get_site(tenant_id, payload.site_id) is None:
            raise ApiException(404, "field.time_capture.site.not_found", "errors.field.time_capture.site.not_found")
        row = self.repository.create_device(
            TimeCaptureDevice(
                tenant_id=tenant_id,
                device_code=payload.device_code.strip(),
                label=payload.label.strip(),
                device_type_code=payload.device_type_code,
                site_id=payload.site_id,
                access_key_hash=self._hash_secret(payload.access_key) if payload.access_key else None,
                fixed_ip_cidr=payload.fixed_ip_cidr,
                notes=self._normalize_optional(payload.notes),
                status=payload.status,
                created_by_user_id=actor.user_id,
                updated_by_user_id=actor.user_id,
            )
        )
        self._record_audit(
            actor,
            tenant_id=tenant_id,
            event_type="field.time_capture.device.created",
            entity_type="field.time_capture_device",
            entity_id=row.id,
            after_json=self._device_snapshot(row),
        )
        return self._map_device(row)

    def update_device(
        self,
        tenant_id: str,
        device_id: str,
        payload: TimeCaptureDeviceUpdate,
        actor: RequestAuthorizationContext,
    ) -> TimeCaptureDeviceRead:
        self._require_tenant_scope(actor, tenant_id, "field.time_capture.write")
        row = self.repository.get_device(tenant_id, device_id)
        if row is None:
            raise ApiException(404, "field.time_capture.device.not_found", "errors.field.time_capture.device.not_found")
        before = self._device_snapshot(row)
        next_type = payload.device_type_code if payload.device_type_code is not None else row.device_type_code
        next_status = payload.status if payload.status is not None else row.status
        next_cidr = None if payload.clear_fixed_ip_cidr else payload.fixed_ip_cidr if payload.fixed_ip_cidr is not None else row.fixed_ip_cidr
        self._validate_device_shape(next_type, next_status, next_cidr)
        if payload.site_id is not None and self.repository.get_site(tenant_id, payload.site_id) is None:
            raise ApiException(404, "field.time_capture.site.not_found", "errors.field.time_capture.site.not_found")
        if payload.device_type_code is not None:
            row.device_type_code = payload.device_type_code
        if payload.label is not None:
            row.label = payload.label.strip()
        if payload.site_id is not None or payload.reset_site_link:
            row.site_id = None if payload.reset_site_link else payload.site_id
        if payload.access_key is not None:
            row.access_key_hash = self._hash_secret(payload.access_key)
        elif payload.clear_access_key:
            row.access_key_hash = None
        if payload.fixed_ip_cidr is not None or payload.clear_fixed_ip_cidr:
            row.fixed_ip_cidr = None if payload.clear_fixed_ip_cidr else payload.fixed_ip_cidr
        if payload.notes is not None:
            row.notes = self._normalize_optional(payload.notes)
        if payload.status is not None:
            row.status = payload.status
        if payload.archived_at is not None:
            row.archived_at = payload.archived_at
        self._require_version(payload.version_no, row.version_no, "field.time_capture.device")
        row.updated_by_user_id = actor.user_id
        row.version_no += 1
        updated = self.repository.update_device(row)
        self._record_audit(
            actor,
            tenant_id=tenant_id,
            event_type="field.time_capture.device.updated",
            entity_type="field.time_capture_device",
            entity_id=updated.id,
            before_json=before,
            after_json=self._device_snapshot(updated),
        )
        return self._map_device(updated)

    def list_policies(
        self,
        tenant_id: str,
        filters: TimeCapturePolicyFilter,
        actor: RequestAuthorizationContext,
    ) -> list[TimeCapturePolicyListItem]:
        self._require_tenant_scope(actor, tenant_id, "field.time_capture.read")
        return [
            TimeCapturePolicyListItem(
                id=row.id,
                policy_code=row.policy_code,
                title=row.title,
                context_type_code=row.context_type_code,
                site_id=row.site_id,
                shift_id=row.shift_id,
                planning_record_id=row.planning_record_id,
                patrol_route_id=row.patrol_route_id,
                enforce_mode_code=row.enforce_mode_code,
                status=row.status,
                updated_at=row.updated_at,
            )
            for row in self.repository.list_policies(tenant_id, filters)
        ]

    def get_policy(self, tenant_id: str, policy_id: str, actor: RequestAuthorizationContext) -> TimeCapturePolicyRead:
        self._require_tenant_scope(actor, tenant_id, "field.time_capture.read")
        row = self.repository.get_policy(tenant_id, policy_id)
        if row is None:
            raise ApiException(404, "field.time_capture.policy.not_found", "errors.field.time_capture.policy.not_found")
        return TimeCapturePolicyRead.model_validate(row)

    def create_policy(self, tenant_id: str, payload: TimeCapturePolicyCreate, actor: RequestAuthorizationContext) -> TimeCapturePolicyRead:
        self._require_tenant_scope(actor, tenant_id, "field.time_capture.write")
        self._validate_policy_shape(payload)
        if self.repository.find_policy_by_code(tenant_id, payload.policy_code) is not None:
            raise ApiException(409, "field.time_capture.policy.duplicate_code", "errors.field.time_capture.policy.duplicate_code")
        self._validate_policy_context(tenant_id, payload.context_type_code, payload.site_id, payload.shift_id, payload.planning_record_id, payload.patrol_route_id)
        existing_context_policy = self.repository.find_active_policy_for_context(
            tenant_id,
            shift_id=payload.shift_id,
            planning_record_id=payload.planning_record_id,
            patrol_route_id=payload.patrol_route_id,
            site_id=payload.site_id,
        )
        if payload.status == "active" and existing_context_policy is not None:
            raise ApiException(
                409,
                "field.time_capture.policy.duplicate_context",
                "errors.field.time_capture.policy.duplicate_context",
            )
        if payload.allowed_device_id is not None and self.repository.get_device(tenant_id, payload.allowed_device_id) is None:
            raise ApiException(404, "field.time_capture.device.not_found", "errors.field.time_capture.device.not_found")
        row = self.repository.create_policy(
            TimeCapturePolicy(
                tenant_id=tenant_id,
                policy_code=payload.policy_code.strip(),
                title=payload.title.strip(),
                context_type_code=payload.context_type_code,
                site_id=payload.site_id,
                shift_id=payload.shift_id,
                planning_record_id=payload.planning_record_id,
                patrol_route_id=payload.patrol_route_id,
                allowed_device_id=payload.allowed_device_id,
                allowed_device_type_code=payload.allowed_device_type_code,
                allow_browser_capture=payload.allow_browser_capture,
                allow_mobile_capture=payload.allow_mobile_capture,
                allow_terminal_capture=payload.allow_terminal_capture,
                allowed_ip_cidr=payload.allowed_ip_cidr,
                geofence_latitude=payload.geofence_latitude,
                geofence_longitude=payload.geofence_longitude,
                geofence_radius_meters=payload.geofence_radius_meters,
                enforce_mode_code=payload.enforce_mode_code,
                notes=self._normalize_optional(payload.notes),
                status=payload.status,
                created_by_user_id=actor.user_id,
                updated_by_user_id=actor.user_id,
            )
        )
        self._record_audit(
            actor,
            tenant_id=tenant_id,
            event_type="field.time_capture.policy.created",
            entity_type="field.time_capture_policy",
            entity_id=row.id,
            after_json=self._policy_snapshot(row),
        )
        return TimeCapturePolicyRead.model_validate(row)

    def update_policy(
        self,
        tenant_id: str,
        policy_id: str,
        payload: TimeCapturePolicyUpdate,
        actor: RequestAuthorizationContext,
    ) -> TimeCapturePolicyRead:
        self._require_tenant_scope(actor, tenant_id, "field.time_capture.write")
        row = self.repository.get_policy(tenant_id, policy_id)
        if row is None:
            raise ApiException(404, "field.time_capture.policy.not_found", "errors.field.time_capture.policy.not_found")
        before = self._policy_snapshot(row)
        next_allowed_ip = None if payload.clear_allowed_ip_cidr else payload.allowed_ip_cidr if payload.allowed_ip_cidr is not None else row.allowed_ip_cidr
        next_allowed_device_type = None if payload.clear_allowed_device_type else payload.allowed_device_type_code if payload.allowed_device_type_code is not None else row.allowed_device_type_code
        next_geofence = (
            None
            if payload.clear_geofence
            else (
                payload.geofence_latitude if payload.geofence_latitude is not None else row.geofence_latitude,
                payload.geofence_longitude if payload.geofence_longitude is not None else row.geofence_longitude,
                payload.geofence_radius_meters if payload.geofence_radius_meters is not None else row.geofence_radius_meters,
            )
        )
        self._validate_policy_shape(
            TimeCapturePolicyCreate(
                policy_code=row.policy_code,
                title=payload.title or row.title,
                context_type_code=row.context_type_code,
                site_id=row.site_id,
                shift_id=row.shift_id,
                planning_record_id=row.planning_record_id,
                patrol_route_id=row.patrol_route_id,
                allowed_device_id=None if payload.clear_allowed_device else payload.allowed_device_id if payload.allowed_device_id is not None else row.allowed_device_id,
                allowed_device_type_code=next_allowed_device_type,
                allow_browser_capture=payload.allow_browser_capture if payload.allow_browser_capture is not None else row.allow_browser_capture,
                allow_mobile_capture=payload.allow_mobile_capture if payload.allow_mobile_capture is not None else row.allow_mobile_capture,
                allow_terminal_capture=payload.allow_terminal_capture if payload.allow_terminal_capture is not None else row.allow_terminal_capture,
                allowed_ip_cidr=next_allowed_ip,
                geofence_latitude=None if next_geofence is None else next_geofence[0],
                geofence_longitude=None if next_geofence is None else next_geofence[1],
                geofence_radius_meters=None if next_geofence is None else next_geofence[2],
                enforce_mode_code=payload.enforce_mode_code or row.enforce_mode_code,
                notes=payload.notes if payload.notes is not None else row.notes,
                status=payload.status or row.status,
            )
        )
        existing_context_policy = self.repository.find_active_policy_for_context(
            tenant_id,
            shift_id=row.shift_id,
            planning_record_id=row.planning_record_id,
            patrol_route_id=row.patrol_route_id,
            site_id=row.site_id,
        )
        if (payload.status or row.status) == "active" and existing_context_policy is not None and existing_context_policy.id != row.id:
            raise ApiException(
                409,
                "field.time_capture.policy.duplicate_context",
                "errors.field.time_capture.policy.duplicate_context",
            )
        if payload.allowed_device_id is not None and self.repository.get_device(tenant_id, payload.allowed_device_id) is None:
            raise ApiException(404, "field.time_capture.device.not_found", "errors.field.time_capture.device.not_found")
        if payload.title is not None:
            row.title = payload.title.strip()
        if payload.allowed_device_id is not None or payload.clear_allowed_device:
            row.allowed_device_id = None if payload.clear_allowed_device else payload.allowed_device_id
        if payload.allowed_device_type_code is not None or payload.clear_allowed_device_type:
            row.allowed_device_type_code = None if payload.clear_allowed_device_type else payload.allowed_device_type_code
        if payload.allow_browser_capture is not None:
            row.allow_browser_capture = payload.allow_browser_capture
        if payload.allow_mobile_capture is not None:
            row.allow_mobile_capture = payload.allow_mobile_capture
        if payload.allow_terminal_capture is not None:
            row.allow_terminal_capture = payload.allow_terminal_capture
        if payload.allowed_ip_cidr is not None or payload.clear_allowed_ip_cidr:
            row.allowed_ip_cidr = None if payload.clear_allowed_ip_cidr else payload.allowed_ip_cidr
        if payload.clear_geofence:
            row.geofence_latitude = None
            row.geofence_longitude = None
            row.geofence_radius_meters = None
        else:
            if payload.geofence_latitude is not None:
                row.geofence_latitude = payload.geofence_latitude
            if payload.geofence_longitude is not None:
                row.geofence_longitude = payload.geofence_longitude
            if payload.geofence_radius_meters is not None:
                row.geofence_radius_meters = payload.geofence_radius_meters
        if payload.enforce_mode_code is not None:
            row.enforce_mode_code = payload.enforce_mode_code
        if payload.notes is not None:
            row.notes = self._normalize_optional(payload.notes)
        if payload.status is not None:
            row.status = payload.status
        if payload.archived_at is not None:
            row.archived_at = payload.archived_at
        self._require_version(payload.version_no, row.version_no, "field.time_capture.policy")
        row.updated_by_user_id = actor.user_id
        row.version_no += 1
        updated = self.repository.update_policy(row)
        self._record_audit(
            actor,
            tenant_id=tenant_id,
            event_type="field.time_capture.policy.updated",
            entity_type="field.time_capture_policy",
            entity_id=updated.id,
            before_json=before,
            after_json=self._policy_snapshot(updated),
        )
        return TimeCapturePolicyRead.model_validate(updated)

    def list_time_events(
        self,
        tenant_id: str,
        filters: TimeCaptureEventFilter,
        actor: RequestAuthorizationContext,
    ) -> list[TimeCaptureEventListItem]:
        self._require_tenant_scope(actor, tenant_id, "field.time_capture.read")
        return [self._map_time_event_list_item(row) for row in self.repository.list_time_events(tenant_id, filters)]

    def list_own_time_events(self, actor: RequestAuthorizationContext) -> TimeCaptureOwnEventCollectionRead:
        employee = self._require_employee(actor)
        return TimeCaptureOwnEventCollectionRead(
            tenant_id=actor.tenant_id,
            employee_id=employee.id,
            items=[self._map_time_event_list_item(row) for row in self.repository.list_employee_time_events(actor.tenant_id, employee.id)],
        )

    def transition_event_validation_status(
        self,
        tenant_id: str,
        event_id: str,
        payload: TimeEventValidationStatusUpdate,
        actor: RequestAuthorizationContext,
    ) -> TimeCaptureEventRead:
        self._require_tenant_scope(actor, tenant_id, "field.time_capture.write")
        row = self.repository.get_time_event(tenant_id, event_id)
        if row is None:
            raise ApiException(404, "field.time_capture.event.not_found", "errors.field.time_capture.event.not_found")
        if payload.validation_status_code not in VALIDATION_STATUSES:
            raise ApiException(400, "field.time_capture.validation_status.invalid", "errors.field.time_capture.validation_status.invalid")
        self._require_version(payload.version_no, row.version_no, "field.time_capture.validation_status")
        before = self._time_event_snapshot(row)
        details = dict(row.validation_details_json or {})
        transitions = list(details.get("transitions", []))
        transitions.append(
            {
                "from_status_code": row.validation_status_code,
                "to_status_code": payload.validation_status_code,
                "reason_code": self._normalize_optional(payload.reason_code),
                "note": self._normalize_optional(payload.note),
                "changed_at": datetime.now(UTC).isoformat(),
                "changed_by_user_id": actor.user_id,
            }
        )
        details["transitions"] = transitions
        row.validation_status_code = payload.validation_status_code
        row.validation_details_json = details
        row.updated_by_user_id = actor.user_id
        row.version_no += 1
        updated = self.repository.save_time_event(row)
        self._record_audit(
            actor,
            tenant_id=tenant_id,
            event_type="field.time_capture.event.validation_status_changed",
            entity_type="field.time_event",
            entity_id=updated.id,
            before_json=before,
            after_json=self._time_event_snapshot(updated),
        )
        return TimeCaptureEventRead.model_validate(updated)

    def capture_employee_event(
        self,
        actor: RequestAuthorizationContext,
        payload: TimeCaptureEventCapture,
        *,
        source_channel_code: str,
        source_ip: str | None,
    ) -> TimeCaptureEventRead:
        if source_channel_code not in {"browser", "mobile"}:
            raise ApiException(400, "field.time_capture.source.invalid", "errors.field.time_capture.source.invalid")
        employee = self._require_employee(actor)
        return self._capture(
            tenant_id=actor.tenant_id,
            actor=actor,
            payload=payload,
            source_channel_code=source_channel_code,
            source_ip=source_ip,
            fallback_actor=_ResolvedActor(
                actor_type_code="employee",
                employee_id=employee.id,
                subcontractor_worker_id=None,
                source="authenticated_employee",
            ),
            terminal_device=None,
        )

    def capture_terminal_event(
        self,
        tenant_id: str,
        payload: TimeCaptureTerminalEventCapture,
        *,
        source_ip: str | None,
    ) -> TimeCaptureEventRead:
        device = self.repository.get_device_by_code(tenant_id, payload.device_code)
        issues: list[_CaptureIssue] = []
        if device is None:
            issues.append(self._issue("device_not_found", "reject", "errors.field.time_capture.device.not_found", {"device_code": payload.device_code}))
        elif device.archived_at is not None or device.status != "active":
            issues.append(self._issue("device_inactive", "reject", "errors.field.time_capture.device.inactive", {"device_id": device.id}))
        elif not device.access_key_hash or not self._verify_secret(payload.access_key, device.access_key_hash):
            issues.append(self._issue("device_access_denied", "reject", "errors.field.time_capture.device.access_denied", {"device_code": payload.device_code}))
        actor_context = RequestAuthorizationContext(
            session_id="terminal",
            user_id="terminal",
            tenant_id=tenant_id,
            role_keys=frozenset({"device_terminal"}),
            permission_keys=frozenset(),
            scopes=(),
            request_id=None,
        )
        return self._capture(
            tenant_id=tenant_id,
            actor=actor_context,
            payload=payload,
            source_channel_code="terminal",
            source_ip=source_ip,
            fallback_actor=None,
            terminal_device=device,
            initial_issues=issues,
        )

    def _capture(
        self,
        *,
        tenant_id: str,
        actor: RequestAuthorizationContext,
        payload: TimeCaptureEventCapture,
        source_channel_code: str,
        source_ip: str | None,
        fallback_actor: _ResolvedActor | None,
        terminal_device,
        initial_issues: list[_CaptureIssue] | None = None,  # noqa: ANN001
    ) -> TimeCaptureEventRead:
        self._validate_capture_payload(payload, source_channel_code)
        if payload.client_event_id:
            duplicate = self.repository.get_time_event_by_client_id(tenant_id, payload.client_event_id)
            if duplicate is not None:
                return TimeCaptureEventRead.model_validate(duplicate)

        occurred_at = payload.occurred_at or datetime.now(UTC)
        issues = list(initial_issues or [])
        context = self._resolve_context(tenant_id, payload, fallback_actor, issues)
        resolved_actor = self._resolve_actor(tenant_id, payload, occurred_at.date(), fallback_actor, issues)
        if context.assignment_id is None and context.shift_id is not None and resolved_actor is not None:
            assignment = None
            if resolved_actor.employee_id is not None:
                assignment = self.repository.find_assignment_for_employee(tenant_id, context.shift_id, resolved_actor.employee_id)
            elif resolved_actor.subcontractor_worker_id is not None:
                assignment = self.repository.find_assignment_for_worker(tenant_id, context.shift_id, resolved_actor.subcontractor_worker_id)
            if assignment is not None:
                context = _ResolvedContext(
                    shift_id=context.shift_id,
                    assignment_id=assignment.id,
                    site_id=context.site_id,
                    planning_record_id=context.planning_record_id,
                    patrol_route_id=context.patrol_route_id,
                )
            else:
                issues.append(
                    self._issue(
                        "assignment_not_found",
                        "reject",
                        "errors.field.time_capture.assignment.not_found",
                        {"shift_id": context.shift_id, "actor_type_code": resolved_actor.actor_type_code},
                    )
                )
        policy = self.repository.find_active_policy_for_context(
            tenant_id,
            shift_id=context.shift_id,
            planning_record_id=context.planning_record_id,
            patrol_route_id=context.patrol_route_id,
            site_id=context.site_id or getattr(terminal_device, "site_id", None),
        )
        issues.extend(self._evaluate_policy(policy, payload, source_channel_code=source_channel_code, source_ip=source_ip, device=terminal_device, context=context))
        if terminal_device is not None and terminal_device.fixed_ip_cidr is not None and not self._ip_matches(source_ip, terminal_device.fixed_ip_cidr):
            issues.append(
                self._issue(
                    "device_ip_mismatch",
                    "reject",
                    "errors.field.time_capture.policy.ip_mismatch",
                    {"device_id": terminal_device.id, "source_ip": source_ip or ""},
                )
            )
        if terminal_device is not None and terminal_device.site_id is not None and context.site_id is not None and terminal_device.site_id != context.site_id:
            issues.append(
                self._issue(
                    "device_site_mismatch",
                    "reject",
                    "errors.field.time_capture.device.site_mismatch",
                    {"device_id": terminal_device.id, "device_site_id": terminal_device.site_id, "event_site_id": context.site_id},
                )
            )

        status_code = self._derive_validation_status(issues)
        validation_message_key = issues[0].message_key if issues else None
        raw_token = self._normalize_optional(payload.raw_token)
        event = self.repository.create_time_event(
            TimeEvent(
                tenant_id=tenant_id,
                actor_type_code=resolved_actor.actor_type_code if resolved_actor is not None else "unresolved",
                employee_id=None if resolved_actor is None else resolved_actor.employee_id,
                subcontractor_worker_id=None if resolved_actor is None else resolved_actor.subcontractor_worker_id,
                shift_id=context.shift_id,
                assignment_id=context.assignment_id,
                site_id=context.site_id or getattr(terminal_device, "site_id", None),
                planning_record_id=context.planning_record_id,
                patrol_route_id=context.patrol_route_id,
                device_id=getattr(terminal_device, "id", None),
                policy_id=policy.id if policy is not None else None,
                source_channel_code=source_channel_code,
                event_code=payload.event_code,
                occurred_at=occurred_at,
                source_ip=source_ip,
                latitude=payload.latitude,
                longitude=payload.longitude,
                scan_medium_code=payload.scan_medium_code,
                raw_token_hash=self._hash_value(raw_token) if raw_token else None,
                raw_token_suffix=self._token_suffix(raw_token),
                client_event_id=payload.client_event_id,
                note=self._normalize_optional(payload.note),
                validation_status_code=status_code,
                validation_message_key=validation_message_key,
                validation_details_json={"issues": [issue.to_json() for issue in issues]},
                metadata_json={
                    "requested_shift_id": payload.shift_id,
                    "requested_assignment_id": payload.assignment_id,
                    "actor_source": None if resolved_actor is None else resolved_actor.source,
                    "terminal_device_code": getattr(terminal_device, "device_code", None),
                },
                status="active",
                created_by_user_id=None if actor.user_id == "terminal" else actor.user_id,
                updated_by_user_id=None if actor.user_id == "terminal" else actor.user_id,
            )
        )
        read = TimeCaptureEventRead.model_validate(event)
        if status_code == "rejected":
            raise ApiException(
                409,
                "field.time_capture.capture_rejected",
                validation_message_key or "errors.field.time_capture.capture_rejected",
                {
                    "time_event_id": event.id,
                    "validation_status_code": status_code,
                    "issues": [issue.to_json() for issue in issues],
                },
            )
        return read

    def _resolve_context(
        self,
        tenant_id: str,
        payload: TimeCaptureEventCapture,
        fallback_actor: _ResolvedActor | None,
        issues: list[_CaptureIssue],
    ) -> _ResolvedContext:
        shift = self.repository.get_shift(tenant_id, payload.shift_id) if payload.shift_id else None
        assignment = None
        if payload.assignment_id:
            assignment = self.repository.get_assignment(tenant_id, payload.assignment_id)
            if assignment is None:
                issues.append(self._issue("assignment_not_found", "reject", "errors.field.time_capture.assignment.not_found", {"assignment_id": payload.assignment_id}))
            elif shift is not None and assignment.shift_id != shift.id:
                issues.append(self._issue("assignment_shift_mismatch", "reject", "errors.field.time_capture.assignment.shift_mismatch", {"assignment_id": payload.assignment_id, "shift_id": payload.shift_id or ""}))
        if shift is None:
            issues.append(self._issue("shift_not_found", "reject", "errors.field.time_capture.shift.not_found", {"shift_id": payload.shift_id or ""}))
            return _ResolvedContext(None, None, None, None, None)
        if shift.release_state != "released":
            issues.append(self._issue("shift_not_released", "reject", "errors.field.time_capture.shift.not_released", {"shift_id": shift.id}))
        if assignment is None and fallback_actor is not None:
            if fallback_actor.employee_id is not None:
                assignment = self.repository.find_assignment_for_employee(tenant_id, shift.id, fallback_actor.employee_id)
            elif fallback_actor.subcontractor_worker_id is not None:
                assignment = self.repository.find_assignment_for_worker(tenant_id, shift.id, fallback_actor.subcontractor_worker_id)
        planning_record = shift.shift_plan.planning_record if getattr(shift, "shift_plan", None) is not None else None
        order = planning_record.order if planning_record is not None else None
        patrol_route_id = None
        if getattr(planning_record, "patrol_detail", None) is not None:
            patrol_route_id = getattr(planning_record.patrol_detail, "patrol_route_id", None) or getattr(getattr(planning_record.patrol_detail, "patrol_route", None), "id", None)
        if patrol_route_id is None and order is not None:
            patrol_route_id = getattr(order, "patrol_route_id", None)
        site_id = None
        if getattr(planning_record, "site_detail", None) is not None:
            site_id = getattr(planning_record.site_detail, "site_id", None)
        if site_id is None and order is not None:
            site_id = getattr(order, "site_id", None)
        return _ResolvedContext(
            shift_id=shift.id,
            assignment_id=None if assignment is None else assignment.id,
            site_id=site_id,
            planning_record_id=None if planning_record is None else planning_record.id,
            patrol_route_id=patrol_route_id,
        )

    def _resolve_actor(
        self,
        tenant_id: str,
        payload: TimeCaptureEventCapture,
        active_on: date,
        fallback_actor: _ResolvedActor | None,
        issues: list[_CaptureIssue],
    ) -> _ResolvedActor | None:
        token = self._normalize_optional(payload.raw_token)
        if token is None:
            return fallback_actor
        employee_credential = self.repository.find_employee_credential_by_encoded_value(tenant_id, token)
        worker_credential = self.repository.find_worker_credential_by_encoded_value(tenant_id, token)
        employee_match = employee_credential if employee_credential is not None and self._credential_active(employee_credential, active_on) else None
        worker_match = worker_credential if worker_credential is not None and self._credential_active(worker_credential, active_on) else None
        if employee_match is not None and worker_match is not None:
            issues.append(self._issue("credential_ambiguous", "reject", "errors.field.time_capture.credential.ambiguous", {}))
            return None
        if employee_match is not None:
            if fallback_actor is not None and fallback_actor.employee_id is not None and fallback_actor.employee_id != employee_match.employee_id:
                issues.append(self._issue("credential_actor_mismatch", "reject", "errors.field.time_capture.credential.actor_mismatch", {}))
                return fallback_actor
            return _ResolvedActor("employee", employee_match.employee_id, None, "credential_scan")
        if worker_match is not None:
            if fallback_actor is not None and fallback_actor.subcontractor_worker_id is not None and fallback_actor.subcontractor_worker_id != worker_match.worker_id:
                issues.append(self._issue("credential_actor_mismatch", "reject", "errors.field.time_capture.credential.actor_mismatch", {}))
                return fallback_actor
            return _ResolvedActor("subcontractor_worker", None, worker_match.worker_id, "credential_scan")
        issues.append(self._issue("credential_not_found", "reject", "errors.field.time_capture.credential.not_found", {}))
        return fallback_actor

    def _evaluate_policy(
        self,
        policy: TimeCapturePolicy | None,
        payload: TimeCaptureEventCapture,
        *,
        source_channel_code: str,
        source_ip: str | None,
        device,  # noqa: ANN001
        context: _ResolvedContext,
    ) -> list[_CaptureIssue]:
        if policy is None:
            return []
        severity = policy.enforce_mode_code
        issues: list[_CaptureIssue] = []
        if source_channel_code == "browser" and not policy.allow_browser_capture:
            issues.append(self._issue("channel_not_allowed", severity, "errors.field.time_capture.policy.channel_not_allowed", {"channel": source_channel_code}))
        if source_channel_code == "mobile" and not policy.allow_mobile_capture:
            issues.append(self._issue("channel_not_allowed", severity, "errors.field.time_capture.policy.channel_not_allowed", {"channel": source_channel_code}))
        if source_channel_code == "terminal" and not policy.allow_terminal_capture:
            issues.append(self._issue("channel_not_allowed", severity, "errors.field.time_capture.policy.channel_not_allowed", {"channel": source_channel_code}))
        if policy.allowed_device_id is not None and getattr(device, "id", None) != policy.allowed_device_id:
            issues.append(self._issue("device_mismatch", severity, "errors.field.time_capture.policy.device_mismatch", {"policy_id": policy.id}))
        if policy.allowed_device_type_code is not None and getattr(device, "device_type_code", None) != policy.allowed_device_type_code:
            issues.append(self._issue("device_type_mismatch", severity, "errors.field.time_capture.policy.device_type_mismatch", {"policy_id": policy.id}))
        if policy.allowed_ip_cidr is not None and not self._ip_matches(source_ip, policy.allowed_ip_cidr):
            issues.append(self._issue("ip_mismatch", severity, "errors.field.time_capture.policy.ip_mismatch", {"policy_id": policy.id, "source_ip": source_ip or ""}))
        if policy.geofence_radius_meters is not None:
            if payload.latitude is None or payload.longitude is None:
                issues.append(self._issue("geofence_missing", severity, "errors.field.time_capture.policy.geofence_missing", {"policy_id": policy.id}))
            elif not self._within_geofence(
                payload.latitude,
                payload.longitude,
                float(policy.geofence_latitude),
                float(policy.geofence_longitude),
                policy.geofence_radius_meters,
            ):
                issues.append(self._issue("geofence_violation", severity, "errors.field.time_capture.policy.geofence_violation", {"policy_id": policy.id}))
        if policy.context_type_code == "site" and policy.site_id != context.site_id:
            issues.append(self._issue("context_mismatch", severity, "errors.field.time_capture.policy.context_mismatch", {"policy_id": policy.id, "context_type_code": "site"}))
        if policy.context_type_code == "shift" and policy.shift_id != context.shift_id:
            issues.append(self._issue("context_mismatch", severity, "errors.field.time_capture.policy.context_mismatch", {"policy_id": policy.id, "context_type_code": "shift"}))
        if policy.context_type_code == "planning_record" and policy.planning_record_id != context.planning_record_id:
            issues.append(self._issue("context_mismatch", severity, "errors.field.time_capture.policy.context_mismatch", {"policy_id": policy.id, "context_type_code": "planning_record"}))
        if policy.context_type_code == "patrol_route" and policy.patrol_route_id != context.patrol_route_id:
            issues.append(self._issue("context_mismatch", severity, "errors.field.time_capture.policy.context_mismatch", {"policy_id": policy.id, "context_type_code": "patrol_route"}))
        return issues

    def _validate_device_shape(self, device_type_code: str, status: str, fixed_ip_cidr: str | None) -> None:
        if device_type_code not in DEVICE_TYPES:
            raise ApiException(400, "field.time_capture.device.invalid_type", "errors.field.time_capture.device.invalid_type")
        if status not in {"active", "inactive"}:
            raise ApiException(400, "field.time_capture.device.invalid_status", "errors.field.time_capture.device.invalid_status")
        if fixed_ip_cidr is not None:
            self._validate_cidr(fixed_ip_cidr, "errors.field.time_capture.device.invalid_cidr")

    def _validate_policy_shape(self, payload: TimeCapturePolicyCreate) -> None:
        if payload.context_type_code not in POLICY_CONTEXT_TYPES:
            raise ApiException(400, "field.time_capture.policy.invalid_context_type", "errors.field.time_capture.policy.invalid_context_type")
        if payload.enforce_mode_code not in ENFORCE_MODES:
            raise ApiException(400, "field.time_capture.policy.invalid_enforce_mode", "errors.field.time_capture.policy.invalid_enforce_mode")
        if payload.status not in {"active", "inactive"}:
            raise ApiException(400, "field.time_capture.policy.invalid_status", "errors.field.time_capture.policy.invalid_status")
        if payload.allowed_device_type_code is not None and payload.allowed_device_type_code not in DEVICE_TYPES:
            raise ApiException(400, "field.time_capture.policy.invalid_device_type", "errors.field.time_capture.policy.invalid_device_type")
        if payload.allowed_ip_cidr is not None:
            self._validate_cidr(payload.allowed_ip_cidr, "errors.field.time_capture.policy.invalid_cidr")
        context_refs = [payload.site_id, payload.shift_id, payload.planning_record_id, payload.patrol_route_id]
        if sum(1 for value in context_refs if value is not None) != 1:
            raise ApiException(400, "field.time_capture.policy.context_required", "errors.field.time_capture.policy.context_required")
        if payload.geofence_radius_meters is not None and (payload.geofence_latitude is None or payload.geofence_longitude is None):
            raise ApiException(400, "field.time_capture.policy.invalid_geofence", "errors.field.time_capture.policy.invalid_geofence")

    def _validate_policy_context(
        self,
        tenant_id: str,
        context_type_code: str,
        site_id: str | None,
        shift_id: str | None,
        planning_record_id: str | None,
        patrol_route_id: str | None,
    ) -> None:
        if context_type_code == "site" and (site_id is None or self.repository.get_site(tenant_id, site_id) is None):
            raise ApiException(404, "field.time_capture.site.not_found", "errors.field.time_capture.site.not_found")
        if context_type_code == "shift" and (shift_id is None or self.repository.get_shift(tenant_id, shift_id) is None):
            raise ApiException(404, "field.time_capture.shift.not_found", "errors.field.time_capture.shift.not_found")
        if context_type_code == "planning_record" and (
            planning_record_id is None or self.repository.get_planning_record(tenant_id, planning_record_id) is None
        ):
            raise ApiException(404, "field.time_capture.planning_record.not_found", "errors.field.time_capture.planning_record.not_found")
        if context_type_code == "patrol_route" and (patrol_route_id is None or self.repository.get_patrol_route(tenant_id, patrol_route_id) is None):
            raise ApiException(404, "field.time_capture.patrol_route.not_found", "errors.field.time_capture.patrol_route.not_found")

    def _validate_capture_payload(self, payload: TimeCaptureEventCapture, source_channel_code: str) -> None:
        if source_channel_code not in SOURCE_CHANNELS:
            raise ApiException(400, "field.time_capture.source.invalid", "errors.field.time_capture.source.invalid")
        if payload.event_code not in EVENT_CODES:
            raise ApiException(400, "field.time_capture.event.invalid", "errors.field.time_capture.event.invalid")
        if payload.scan_medium_code is not None and payload.scan_medium_code not in SCAN_MEDIA:
            raise ApiException(400, "field.time_capture.scan_medium.invalid", "errors.field.time_capture.scan_medium.invalid")
        if payload.latitude is not None and not (-90 <= payload.latitude <= 90):
            raise ApiException(400, "field.time_capture.coordinates.invalid", "errors.field.time_capture.coordinates.invalid")
        if payload.longitude is not None and not (-180 <= payload.longitude <= 180):
            raise ApiException(400, "field.time_capture.coordinates.invalid", "errors.field.time_capture.coordinates.invalid")

    def _require_employee(self, actor: RequestAuthorizationContext):
        if "portal.employee.access" not in actor.permission_keys:
            raise ApiException(403, "iam.authorization.permission_denied", "errors.iam.authorization.permission_denied")
        employee = self.repository.find_employee_by_user_id(actor.tenant_id, actor.user_id)
        if employee is None or employee.archived_at is not None or employee.status != "active":
            raise ApiException(404, "employees.self_service.employee_not_found", "errors.employees.self_service.employee_not_found")
        return employee

    @staticmethod
    def _credential_active(credential, active_on: date) -> bool:  # noqa: ANN001
        owner = getattr(credential, "employee", None) or getattr(credential, "worker", None)
        if credential.archived_at is not None or credential.status != "active":
            return False
        if credential.valid_from > active_on:
            return False
        if credential.valid_until is not None and credential.valid_until < active_on:
            return False
        return owner is not None and owner.archived_at is None and owner.status == "active"

    @staticmethod
    def _derive_validation_status(issues: list[_CaptureIssue]) -> str:
        if any(issue.severity == "reject" for issue in issues):
            return "rejected"
        if issues:
            return "flagged"
        return "accepted"

    @staticmethod
    def _issue(code: str, severity: str, message_key: str, details: dict[str, object]) -> _CaptureIssue:
        return _CaptureIssue(code=code, severity=severity, message_key=message_key, details=details)

    @staticmethod
    def _normalize_optional(value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @staticmethod
    def _token_suffix(value: str | None) -> str | None:
        if not value:
            return None
        return value[-4:] if len(value) > 4 else value

    @staticmethod
    def _hash_value(value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    def _hash_secret(self, secret: str) -> str:
        return self._hash_value(secret.strip())

    def _verify_secret(self, secret: str, hashed: str) -> bool:
        return hmac.compare_digest(self._hash_secret(secret), hashed)

    @staticmethod
    def _validate_cidr(cidr: str, message_key: str) -> None:
        try:
            ipaddress.ip_network(cidr, strict=False)
        except ValueError as exc:
            raise ApiException(400, "field.time_capture.cidr.invalid", message_key) from exc

    @staticmethod
    def _ip_matches(source_ip: str | None, cidr: str) -> bool:
        if source_ip is None:
            return False
        try:
            return ipaddress.ip_address(source_ip) in ipaddress.ip_network(cidr, strict=False)
        except ValueError:
            return False

    @staticmethod
    def _within_geofence(latitude: float, longitude: float, target_latitude: float, target_longitude: float, radius_meters: int) -> bool:
        earth_radius = 6_371_000
        lat1 = math.radians(latitude)
        lat2 = math.radians(target_latitude)
        delta_lat = math.radians(target_latitude - latitude)
        delta_lon = math.radians(target_longitude - longitude)
        a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return earth_radius * c <= radius_meters

    @staticmethod
    def _map_device(row: TimeCaptureDevice) -> TimeCaptureDeviceRead:
        return TimeCaptureDeviceRead(
            id=row.id,
            tenant_id=row.tenant_id,
            device_code=row.device_code,
            label=row.label,
            device_type_code=row.device_type_code,
            site_id=row.site_id,
            fixed_ip_cidr=row.fixed_ip_cidr,
            notes=row.notes,
            status=row.status,
            has_access_key=bool(row.access_key_hash),
            archived_at=row.archived_at,
            version_no=row.version_no,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    @staticmethod
    def _map_time_event_list_item(row: TimeEvent) -> TimeCaptureEventListItem:
        return TimeCaptureEventListItem(
            id=row.id,
            actor_type_code=row.actor_type_code,
            employee_id=row.employee_id,
            subcontractor_worker_id=row.subcontractor_worker_id,
            shift_id=row.shift_id,
            assignment_id=row.assignment_id,
            source_channel_code=row.source_channel_code,
            event_code=row.event_code,
            occurred_at=row.occurred_at,
            device_id=row.device_id,
            validation_status_code=row.validation_status_code,
            validation_message_key=row.validation_message_key,
            raw_token_suffix=row.raw_token_suffix,
        )

    @staticmethod
    def _time_event_snapshot(row: TimeEvent) -> dict[str, object]:
        return {
            "actor_type_code": row.actor_type_code,
            "employee_id": row.employee_id,
            "subcontractor_worker_id": row.subcontractor_worker_id,
            "shift_id": row.shift_id,
            "assignment_id": row.assignment_id,
            "source_channel_code": row.source_channel_code,
            "event_code": row.event_code,
            "occurred_at": row.occurred_at.isoformat(),
            "scan_medium_code": row.scan_medium_code,
            "raw_token_suffix": row.raw_token_suffix,
            "validation_status_code": row.validation_status_code,
            "validation_message_key": row.validation_message_key,
            "validation_details_json": dict(row.validation_details_json or {}),
            "version_no": row.version_no,
        }

    @staticmethod
    def _device_snapshot(row: TimeCaptureDevice) -> dict[str, object]:
        return {
            "device_code": row.device_code,
            "device_type_code": row.device_type_code,
            "site_id": row.site_id,
            "fixed_ip_cidr": row.fixed_ip_cidr,
            "status": row.status,
            "version_no": row.version_no,
            "has_access_key": bool(row.access_key_hash),
        }

    @staticmethod
    def _policy_snapshot(row: TimeCapturePolicy) -> dict[str, object]:
        return {
            "policy_code": row.policy_code,
            "context_type_code": row.context_type_code,
            "site_id": row.site_id,
            "shift_id": row.shift_id,
            "planning_record_id": row.planning_record_id,
            "patrol_route_id": row.patrol_route_id,
            "allowed_device_id": row.allowed_device_id,
            "allowed_device_type_code": row.allowed_device_type_code,
            "allow_browser_capture": row.allow_browser_capture,
            "allow_mobile_capture": row.allow_mobile_capture,
            "allow_terminal_capture": row.allow_terminal_capture,
            "allowed_ip_cidr": row.allowed_ip_cidr,
            "geofence_radius_meters": row.geofence_radius_meters,
            "enforce_mode_code": row.enforce_mode_code,
            "status": row.status,
            "version_no": row.version_no,
        }

    @staticmethod
    def _require_version(provided: int | None, current: int, entity_key: str) -> None:
        if provided is None:
            return
        if provided != current:
            raise ApiException(409, f"{entity_key}.stale_version", f"errors.{entity_key}.stale_version")

    @staticmethod
    def _require_tenant_scope(actor: RequestAuthorizationContext, tenant_id: str, permission_key: str) -> None:
        if permission_key not in actor.permission_keys:
            raise ApiException(403, "iam.authorization.permission_denied", "errors.iam.authorization.permission_denied")
        if not actor.allows_tenant(tenant_id):
            raise ApiException(403, "iam.authorization.scope_denied", "errors.iam.authorization.scope_denied")

    def _record_audit(
        self,
        actor: RequestAuthorizationContext,
        *,
        tenant_id: str,
        event_type: str,
        entity_type: str,
        entity_id: str,
        before_json: dict[str, object] | None = None,
        after_json: dict[str, object] | None = None,
    ) -> None:
        if self.audit_service is None:
            return
        self.audit_service.record_business_event(
            actor=AuditActor(
                tenant_id=tenant_id,
                user_id=actor.user_id,
                session_id=actor.session_id,
                request_id=actor.request_id,
                source="api",
            ),
            tenant_id=tenant_id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            before_json=before_json,
            after_json=after_json,
        )
