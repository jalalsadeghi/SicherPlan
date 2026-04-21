"""Service layer for logical documents, immutable versions, and links."""

from __future__ import annotations

import base64
import hashlib
import re
from dataclasses import dataclass
from typing import Protocol

from sqlalchemy.exc import IntegrityError

from app.config import settings
from app.errors import ApiException
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.platform_services.docs_models import Document, DocumentLink, DocumentVersion
from app.modules.platform_services.docs_schemas import (
    DocumentCreate,
    DocumentLinkCreate,
    DocumentLinkRead,
    DocumentRead,
    DocumentVersionCreate,
    DocumentVersionRead,
)
from app.modules.platform_services.storage import (
    ObjectStorageAdapter,
    StoredObject,
    StorageObjectNotFoundError,
)


class DocumentRepository(Protocol):
    SUPPORTED_OWNER_TYPES: frozenset[str]

    def get_document_type_by_key(self, key: str): ...  # noqa: ANN001
    def create_document(self, row: Document) -> Document: ...
    def get_document(self, tenant_id: str, document_id: str) -> Document | None: ...
    def list_documents(
        self,
        tenant_id: str,
        *,
        search: str | None = None,
        document_type_key: str | None = None,
        linked_entity: str | None = None,
        limit: int = 25,
    ) -> list[Document]: ...
    def list_document_versions(self, tenant_id: str, document_id: str) -> list[DocumentVersion]: ...
    def create_document_version(self, document: Document, row: DocumentVersion) -> DocumentVersion: ...
    def get_document_version(self, tenant_id: str, document_id: str, version_no: int) -> DocumentVersion | None: ...
    def create_document_link(self, row: DocumentLink) -> DocumentLink: ...
    def owner_exists(self, tenant_id: str, owner_type: str, owner_id: str) -> bool: ...


class DocumentActorContext(Protocol):
    tenant_id: str
    user_id: str | None
    is_platform_admin: bool


@dataclass(frozen=True, slots=True)
class DocumentDownload:
    file_name: str
    content_type: str
    content: bytes
    checksum_sha256: str


class DocumentService:
    def __init__(
        self,
        repository: DocumentRepository,
        *,
        storage: ObjectStorageAdapter,
        bucket_name: str,
    ) -> None:
        self.repository = repository
        self.storage = storage
        self.bucket_name = bucket_name

    def create_document(
        self,
        tenant_id: str,
        payload: DocumentCreate,
        actor: DocumentActorContext,
    ) -> DocumentRead:
        self._ensure_tenant_scope(actor, tenant_id)
        if payload.tenant_id != tenant_id:
            raise ApiException(
                400,
                "docs.document.tenant_mismatch",
                "errors.docs.document.tenant_mismatch",
                {"tenant_id": tenant_id},
            )
        document_type_id = None
        if payload.document_type_key is not None:
            document_type = self.repository.get_document_type_by_key(payload.document_type_key)
            if document_type is None:
                raise ApiException(404, "docs.document_type.not_found", "errors.docs.document_type.not_found")
            document_type_id = document_type.id
        document = self.repository.create_document(
            Document(
                tenant_id=tenant_id,
                document_type_id=document_type_id,
                title=payload.title,
                source_module=payload.source_module,
                source_label=payload.source_label,
                metadata_json=payload.metadata_json,
                created_by_user_id=actor.user_id,
                updated_by_user_id=actor.user_id,
            )
        )
        return DocumentRead.model_validate(document)

    def get_document(self, tenant_id: str, document_id: str, actor: RequestAuthorizationContext) -> DocumentRead:
        # Existing auth contexts and anonymous public actors share the same tenant-scope attributes.
        document = self._require_document(tenant_id, document_id, actor)
        return DocumentRead.model_validate(document)

    def list_documents(
        self,
        tenant_id: str,
        actor: DocumentActorContext,
        *,
        search: str | None = None,
        document_type_key: str | None = None,
        linked_entity: str | None = None,
        limit: int = 25,
    ) -> list[DocumentRead]:
        self._ensure_tenant_scope(actor, tenant_id)
        bounded_limit = max(1, min(limit, 50))
        return [
            DocumentRead.model_validate(document)
            for document in self.repository.list_documents(
                tenant_id,
                search=search,
                document_type_key=document_type_key,
                linked_entity=linked_entity,
                limit=bounded_limit,
            )
        ]

    def add_document_version(
        self,
        tenant_id: str,
        document_id: str,
        payload: DocumentVersionCreate,
        actor: DocumentActorContext,
    ) -> DocumentVersionRead:
        document = self._require_document(tenant_id, document_id, actor)
        content = self._decode_base64(payload.content_base64)
        checksum = hashlib.sha256(content).hexdigest()
        existing_versions = self.repository.list_document_versions(tenant_id, document_id)
        duplicate_of = next(
            (
                version.version_no
                for version in existing_versions
                if version.checksum_sha256 == checksum and version.file_size_bytes == len(content)
            ),
            None,
        )
        next_version_no = document.current_version_no + 1
        object_key = self._build_object_key(tenant_id, document_id, next_version_no, payload.file_name)
        metadata_json = dict(payload.metadata_json)
        if duplicate_of is not None:
            metadata_json["duplicate_of_version_no"] = duplicate_of
        self.storage.put_object(
            self.bucket_name,
            object_key,
            content,
            content_type=payload.content_type,
            metadata={
                "tenant_id": tenant_id,
                "document_id": document_id,
                "version_no": str(next_version_no),
            },
        )
        version = self.repository.create_document_version(
            document,
            DocumentVersion(
                tenant_id=tenant_id,
                document_id=document_id,
                version_no=next_version_no,
                file_name=payload.file_name,
                content_type=payload.content_type,
                object_bucket=self.bucket_name,
                object_key=object_key,
                checksum_sha256=checksum,
                file_size_bytes=len(content),
                uploaded_by_user_id=actor.user_id,
                is_revision_safe_pdf=payload.is_revision_safe_pdf,
                metadata_json=metadata_json,
            ),
        )
        return DocumentVersionRead.model_validate(version)

    def add_document_link(
        self,
        tenant_id: str,
        document_id: str,
        payload: DocumentLinkCreate,
        actor: DocumentActorContext,
    ) -> DocumentLinkRead:
        self._require_document(tenant_id, document_id, actor)
        if payload.owner_type not in self.repository.SUPPORTED_OWNER_TYPES:
            raise ApiException(
                400,
                "docs.document_link.unsupported_owner_type",
                "errors.docs.document_link.unsupported_owner_type",
                {"owner_type": payload.owner_type},
            )
        if not self.repository.owner_exists(tenant_id, payload.owner_type, payload.owner_id):
            raise ApiException(
                404,
                "docs.document_link.owner_not_found",
                "errors.docs.document_link.owner_not_found",
                {"owner_type": payload.owner_type, "owner_id": payload.owner_id},
            )
        try:
            link = self.repository.create_document_link(
                DocumentLink(
                    tenant_id=tenant_id,
                    document_id=document_id,
                    owner_type=payload.owner_type,
                    owner_id=payload.owner_id,
                    relation_type=payload.relation_type,
                    label=payload.label,
                    linked_by_user_id=actor.user_id,
                    metadata_json=payload.metadata_json,
                )
            )
        except IntegrityError as exc:
            raise ApiException(
                409,
                "docs.document_link.duplicate",
                "errors.docs.document_link.duplicate",
            ) from exc
        return DocumentLinkRead.model_validate(link)

    def get_document_version(
        self,
        tenant_id: str,
        document_id: str,
        version_no: int,
        actor: DocumentActorContext,
    ) -> DocumentVersionRead:
        self._require_document(tenant_id, document_id, actor)
        version = self.repository.get_document_version(tenant_id, document_id, version_no)
        if version is None:
            raise ApiException(404, "docs.document_version.not_found", "errors.docs.document_version.not_found")
        return DocumentVersionRead.model_validate(version)

    def download_document_version(
        self,
        tenant_id: str,
        document_id: str,
        version_no: int,
        actor: DocumentActorContext,
    ) -> DocumentDownload:
        self._require_document(tenant_id, document_id, actor)
        version = self.repository.get_document_version(tenant_id, document_id, version_no)
        if version is None:
            raise ApiException(404, "docs.document_version.not_found", "errors.docs.document_version.not_found")
        try:
            stored = self.storage.get_object(version.object_bucket, version.object_key)
        except StorageObjectNotFoundError as exc:
            raise ApiException(404, "docs.storage.object_not_found", "errors.docs.storage.object_not_found") from exc
        self._assert_checksum(version.checksum_sha256, stored)
        return DocumentDownload(
            file_name=version.file_name,
            content_type=version.content_type,
            content=stored.content,
            checksum_sha256=version.checksum_sha256,
        )

    def _require_document(
        self,
        tenant_id: str,
        document_id: str,
        actor: DocumentActorContext,
    ) -> Document:
        self._ensure_tenant_scope(actor, tenant_id)
        document = self.repository.get_document(tenant_id, document_id)
        if document is None:
            raise ApiException(404, "docs.document.not_found", "errors.docs.document.not_found")
        return document

    @staticmethod
    def _ensure_tenant_scope(actor: DocumentActorContext, tenant_id: str) -> None:
        if actor.is_platform_admin or actor.tenant_id == tenant_id:
            return
        raise ApiException(403, "iam.authorization.scope_denied", "errors.iam.authorization.scope_denied")

    @staticmethod
    def _decode_base64(encoded: str) -> bytes:
        try:
            return base64.b64decode(encoded, validate=True)
        except Exception as exc:  # noqa: BLE001
            raise ApiException(
                400,
                "docs.document_version.invalid_content",
                "errors.docs.document_version.invalid_content",
            ) from exc

    @staticmethod
    def _build_object_key(tenant_id: str, document_id: str, version_no: int, file_name: str) -> str:
        normalized = re.sub(r"[^A-Za-z0-9._-]+", "-", file_name).strip("-") or "document.bin"
        return f"{tenant_id}/{document_id}/v{version_no}/{normalized}"

    @staticmethod
    def _assert_checksum(expected_checksum: str, stored: StoredObject) -> None:
        actual_checksum = hashlib.sha256(stored.content).hexdigest()
        if actual_checksum != expected_checksum:
            raise ApiException(500, "platform.internal", "errors.platform.internal")


def build_document_service(repository: DocumentRepository, *, storage: ObjectStorageAdapter) -> DocumentService:
    return DocumentService(repository, storage=storage, bucket_name=settings.object_storage_bucket)
