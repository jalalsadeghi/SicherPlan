"""Provider-abstracted object storage helpers for document versions."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from app.config import AppSettings


class StorageObjectNotFoundError(FileNotFoundError):
    """Raised when an expected storage object does not exist."""


@dataclass(frozen=True, slots=True)
class StoredObject:
    bucket: str
    key: str
    content: bytes
    content_type: str
    metadata: dict[str, str]


class ObjectStorageAdapter(Protocol):
    def put_object(
        self,
        bucket: str,
        key: str,
        content: bytes,
        *,
        content_type: str,
        metadata: dict[str, str] | None = None,
    ) -> None: ...

    def get_object(self, bucket: str, key: str) -> StoredObject: ...


class FileSystemObjectStorageAdapter:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def put_object(
        self,
        bucket: str,
        key: str,
        content: bytes,
        *,
        content_type: str,
        metadata: dict[str, str] | None = None,
    ) -> None:
        object_path = self._resolve_path(bucket, key)
        object_path.parent.mkdir(parents=True, exist_ok=True)
        object_path.write_bytes(content)
        object_path.with_suffix(object_path.suffix + ".meta.json").write_text(
            json.dumps(
                {
                    "content_type": content_type,
                    "metadata": metadata or {},
                },
                sort_keys=True,
            ),
            encoding="utf-8",
        )

    def get_object(self, bucket: str, key: str) -> StoredObject:
        object_path = self._resolve_path(bucket, key)
        if not object_path.exists():
            raise StorageObjectNotFoundError(key)
        metadata_path = object_path.with_suffix(object_path.suffix + ".meta.json")
        payload = json.loads(metadata_path.read_text(encoding="utf-8")) if metadata_path.exists() else {}
        return StoredObject(
            bucket=bucket,
            key=key,
            content=object_path.read_bytes(),
            content_type=payload.get("content_type", "application/octet-stream"),
            metadata=payload.get("metadata", {}),
        )

    def _resolve_path(self, bucket: str, key: str) -> Path:
        candidate = (self.root / bucket / key).resolve()
        bucket_root = (self.root / bucket).resolve()
        if ".." in Path(key).parts or not str(candidate).startswith(str(bucket_root)):
            raise ValueError("Unsafe object-storage key")
        return candidate


class InMemoryObjectStorageAdapter:
    def __init__(self) -> None:
        self.objects: dict[tuple[str, str], StoredObject] = {}

    def put_object(
        self,
        bucket: str,
        key: str,
        content: bytes,
        *,
        content_type: str,
        metadata: dict[str, str] | None = None,
    ) -> None:
        self.objects[(bucket, key)] = StoredObject(
            bucket=bucket,
            key=key,
            content=content,
            content_type=content_type,
            metadata=metadata or {},
        )

    def get_object(self, bucket: str, key: str) -> StoredObject:
        stored = self.objects.get((bucket, key))
        if stored is None:
            raise StorageObjectNotFoundError(key)
        return stored


def build_object_storage_adapter(settings: AppSettings) -> ObjectStorageAdapter:
    if settings.object_storage_backend == "filesystem":
        return FileSystemObjectStorageAdapter(settings.object_storage_filesystem_root)
    raise RuntimeError(f"Unsupported object storage backend: {settings.object_storage_backend}")
