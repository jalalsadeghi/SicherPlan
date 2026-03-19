"""Database metadata and declarative base exports."""

from app.db.base import Base, UUIDPrimaryKeyMixin

__all__ = ["Base", "UUIDPrimaryKeyMixin"]
