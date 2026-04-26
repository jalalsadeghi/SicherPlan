from __future__ import annotations

from pathlib import Path

from app.modules.assistant.knowledge.source_loader import KnowledgeSourceLoader
from app.modules.assistant.knowledge.types import (
    KnowledgeSourceNotAllowedError,
    KnowledgeSourceRegistration,
    KnowledgeSourceTooLargeError,
)


def test_source_loader_allows_docs_root_file(tmp_path: Path) -> None:
    docs_root = tmp_path / "docs"
    docs_root.mkdir()
    source_file = docs_root / "guide.md"
    source_file.write_text("# Guide\n\nHello SicherPlan\n", encoding="utf-8")

    loader = KnowledgeSourceLoader(allowed_roots=[docs_root])
    loaded = loader.load(
        KnowledgeSourceRegistration(
            source_type="markdown",
            source_name="Guide",
            source_path=str(source_file),
        )
    )

    assert loaded.source_name == "Guide"
    assert loaded.source_path == str(source_file.resolve())
    assert loaded.source_hash


def test_source_loader_rejects_path_traversal(tmp_path: Path) -> None:
    docs_root = tmp_path / "docs"
    docs_root.mkdir()
    outside = tmp_path / "outside.md"
    outside.write_text("secret\n", encoding="utf-8")

    loader = KnowledgeSourceLoader(allowed_roots=[docs_root])
    try:
        loader.load(
            KnowledgeSourceRegistration(
                source_type="markdown",
                source_name="Outside",
                source_path=str(docs_root / "../outside.md"),
            )
        )
    except KnowledgeSourceNotAllowedError:
        pass
    else:
        raise AssertionError("Expected KnowledgeSourceNotAllowedError")


def test_source_loader_rejects_env_file(tmp_path: Path) -> None:
    docs_root = tmp_path / "docs"
    docs_root.mkdir()
    source_file = docs_root / ".env"
    source_file.write_text("SP_SECRET=x\n", encoding="utf-8")

    loader = KnowledgeSourceLoader(allowed_roots=[docs_root])
    try:
        loader.load(
            KnowledgeSourceRegistration(
                source_type="text",
                source_name="Env",
                source_path=str(source_file),
            )
        )
    except KnowledgeSourceNotAllowedError:
        pass
    else:
        raise AssertionError("Expected KnowledgeSourceNotAllowedError")


def test_source_loader_rejects_secret_like_file(tmp_path: Path) -> None:
    docs_root = tmp_path / "docs"
    docs_root.mkdir()
    source_file = docs_root / "customer-secret.txt"
    source_file.write_text("secret\n", encoding="utf-8")

    loader = KnowledgeSourceLoader(allowed_roots=[docs_root])
    try:
        loader.load(
            KnowledgeSourceRegistration(
                source_type="text",
                source_name="Secret",
                source_path=str(source_file),
            )
        )
    except KnowledgeSourceNotAllowedError:
        pass
    else:
        raise AssertionError("Expected KnowledgeSourceNotAllowedError")


def test_source_loader_rejects_oversized_file(tmp_path: Path) -> None:
    docs_root = tmp_path / "docs"
    docs_root.mkdir()
    source_file = docs_root / "large.md"
    source_file.write_text("a" * 200, encoding="utf-8")

    loader = KnowledgeSourceLoader(allowed_roots=[docs_root], max_file_size_bytes=50)
    try:
        loader.load(
            KnowledgeSourceRegistration(
                source_type="markdown",
                source_name="Large",
                source_path=str(source_file),
            )
        )
    except KnowledgeSourceTooLargeError:
        pass
    else:
        raise AssertionError("Expected KnowledgeSourceTooLargeError")


def test_source_hash_is_stable(tmp_path: Path) -> None:
    docs_root = tmp_path / "docs"
    docs_root.mkdir()
    source_file = docs_root / "guide.md"
    source_file.write_text("# Guide\n\nHello SicherPlan\n", encoding="utf-8")

    loader = KnowledgeSourceLoader(allowed_roots=[docs_root])
    registration = KnowledgeSourceRegistration(
        source_type="markdown",
        source_name="Guide",
        source_path=str(source_file),
    )
    first = loader.load(registration)
    second = loader.load(registration)

    assert first.source_hash == second.source_hash


def test_operational_data_source_is_not_allowed(tmp_path: Path) -> None:
    docs_root = tmp_path / "docs"
    docs_root.mkdir()
    operational_root = tmp_path / "backend" / "data"
    operational_root.mkdir(parents=True)
    source_file = operational_root / "employees.json"
    source_file.write_text('{"employee":"Markus"}\n', encoding="utf-8")

    loader = KnowledgeSourceLoader(allowed_roots=[docs_root])
    try:
        loader.load(
            KnowledgeSourceRegistration(
                source_type="json",
                source_name="Employees",
                source_path=str(source_file),
            )
        )
    except KnowledgeSourceNotAllowedError:
        pass
    else:
        raise AssertionError("Expected KnowledgeSourceNotAllowedError")
