"""Subcontractor-portal access resolution based on shared IAM session state."""

from __future__ import annotations

from typing import Protocol

from app.errors import ApiException
from app.modules.iam.authz import RequestAuthorizationContext, enforce_permission
from app.modules.subcontractors.schemas import (
    SubcontractorPortalContextRead,
    SubcontractorPortalScopeRead,
)


class SubcontractorPortalRepository(Protocol):
    def get_portal_contact_for_user(self, tenant_id: str, user_id: str): ...  # noqa: ANN001
    def get_portal_subcontractor_scope_match(
        self,
        tenant_id: str,
        user_id: str,
        allowed_subcontractor_ids: list[str],
    ): ...  # noqa: ANN001


class SubcontractorPortalService:
    def __init__(self, repository: SubcontractorPortalRepository) -> None:
        self.repository = repository

    def get_context(self, actor: RequestAuthorizationContext) -> SubcontractorPortalContextRead:
        enforce_permission(actor, "portal.subcontractor.access")

        allowed_subcontractor_ids = sorted(
            {
                scope.subcontractor_id
                for scope in actor.scopes
                if scope.scope_type == "subcontractor" and scope.subcontractor_id
            }
        )
        if not allowed_subcontractor_ids:
            raise ApiException(
                403,
                "subcontractors.portal.scope_not_resolved",
                "errors.subcontractors.portal.scope_not_resolved",
            )

        linked = self.repository.get_portal_contact_for_user(actor.tenant_id, actor.user_id)
        if linked is None:
            raise ApiException(
                403,
                "subcontractors.portal.contact_not_linked",
                "errors.subcontractors.portal.contact_not_linked",
            )

        company, contact = linked
        if not contact.portal_enabled:
            raise ApiException(
                403,
                "subcontractors.portal.contact_portal_disabled",
                "errors.subcontractors.portal.contact_portal_disabled",
            )
        if contact.status != "active" or contact.archived_at is not None:
            raise ApiException(
                403,
                "subcontractors.portal.contact_inactive",
                "errors.subcontractors.portal.contact_inactive",
            )
        if company.status != "active" or company.archived_at is not None:
            raise ApiException(
                403,
                "subcontractors.portal.company_inactive",
                "errors.subcontractors.portal.company_inactive",
            )

        scoped = self.repository.get_portal_subcontractor_scope_match(
            actor.tenant_id,
            actor.user_id,
            allowed_subcontractor_ids,
        )
        if scoped is None:
            raise ApiException(
                403,
                "subcontractors.portal.scope_not_resolved",
                "errors.subcontractors.portal.scope_not_resolved",
            )

        resolved_company, resolved_contact = scoped
        scopes = [
            SubcontractorPortalScopeRead(
                role_key=scope.role_key,
                scope_type=scope.scope_type,
                subcontractor_id=scope.subcontractor_id,
            )
            for scope in actor.scopes
            if scope.scope_type == "subcontractor" and scope.subcontractor_id
        ]
        return SubcontractorPortalContextRead(
            tenant_id=actor.tenant_id,
            user_id=actor.user_id,
            subcontractor_id=resolved_company.id,
            contact_id=resolved_contact.id,
            company=resolved_company,
            contact=resolved_contact,
            scopes=scopes,
        )
