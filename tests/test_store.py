"""Tests for DocumentStore — sync, search, upsert idempotency."""

from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from easypaperless.models.correspondents import Correspondent
from easypaperless.models.custom_fields import CustomField, FieldDataType
from easypaperless.models.document_types import DocumentType
from easypaperless.models.documents import Document
from easypaperless.models.storage_paths import StoragePath
from easypaperless.models.tags import Tag
from easypaperless.store import DocumentStore


def make_doc(**kwargs) -> Document:
    defaults = {"id": 1, "title": "Test Doc", "tags": [], "created_date": "2024-03-15"}
    defaults.update(kwargs)
    return Document.model_validate(defaults)


def make_tag(id: int, name: str) -> Tag:
    return Tag.model_validate({"id": id, "name": name})


def make_correspondent(id: int, name: str) -> Correspondent:
    return Correspondent.model_validate({"id": id, "name": name})


def make_doc_type(id: int, name: str) -> DocumentType:
    return DocumentType.model_validate({"id": id, "name": name})


def make_storage_path(id: int, name: str) -> StoragePath:
    return StoragePath.model_validate({"id": id, "name": name})


def make_client(docs=None, tags=None, correspondents=None, doc_types=None, storage_paths=None):
    client = MagicMock()
    client.list_documents = AsyncMock(return_value=docs or [])
    client.list_tags = AsyncMock(return_value=tags or [])
    client.list_correspondents = AsyncMock(return_value=correspondents or [])
    client.list_document_types = AsyncMock(return_value=doc_types or [])
    client.list_storage_paths = AsyncMock(return_value=storage_paths or [])
    return client


@pytest.fixture
def store(tmp_path):
    client = make_client()
    s = DocumentStore(client, tmp_path / "test.db")
    yield s
    s.close()


async def test_sync_returns_document_count(tmp_path):
    docs = [make_doc(id=1), make_doc(id=2)]
    client = make_client(docs=docs)
    store = DocumentStore(client, tmp_path / "test.db")
    count = await store.sync()
    assert count == 2
    store.close()


async def test_sync_idempotent(tmp_path):
    docs = [make_doc(id=1, title="Original")]
    client = make_client(docs=docs)
    store = DocumentStore(client, tmp_path / "test.db")

    await store.sync()
    await store.sync()

    results = store.search_documents()
    assert len(results) == 1
    store.close()


async def test_sync_upserts_updated_title(tmp_path):
    client = make_client(docs=[make_doc(id=1, title="Old Title")])
    store = DocumentStore(client, tmp_path / "test.db")
    await store.sync()

    client.list_documents = AsyncMock(return_value=[make_doc(id=1, title="New Title")])
    await store.sync()

    results = store.search_documents()
    assert results[0].title == "New Title"
    store.close()


async def test_search_title_contains(tmp_path):
    docs = [make_doc(id=1, title="Invoice 2024"), make_doc(id=2, title="Receipt March")]
    client = make_client(docs=docs)
    store = DocumentStore(client, tmp_path / "test.db")
    await store.sync()

    results = store.search_documents(title_contains="Invoice")
    assert len(results) == 1
    assert results[0].id == 1
    store.close()


async def test_search_title_regex(tmp_path):
    docs = [make_doc(id=1, title="Invoice 2024"), make_doc(id=2, title="Receipt March")]
    client = make_client(docs=docs)
    store = DocumentStore(client, tmp_path / "test.db")
    await store.sync()

    results = store.search_documents(title_regex=r"Invoice \d{4}")
    assert len(results) == 1
    assert results[0].id == 1
    store.close()


async def test_search_created_after(tmp_path):
    docs = [
        make_doc(id=1, created_date="2024-01-15"),
        make_doc(id=2, created_date="2023-06-01"),
    ]
    client = make_client(docs=docs)
    store = DocumentStore(client, tmp_path / "test.db")
    await store.sync()

    results = store.search_documents(created_after="2024-01-01")
    assert len(results) == 1
    assert results[0].id == 1
    store.close()


async def test_search_created_before(tmp_path):
    docs = [
        make_doc(id=1, created_date="2024-01-15"),
        make_doc(id=2, created_date="2023-06-01"),
    ]
    client = make_client(docs=docs)
    store = DocumentStore(client, tmp_path / "test.db")
    await store.sync()

    results = store.search_documents(created_before="2024-01-01")
    assert len(results) == 1
    assert results[0].id == 2
    store.close()


async def test_search_by_tag_id(tmp_path):
    tag = make_tag(3, "invoice")
    docs = [
        make_doc(id=1, tags=[3]),
        make_doc(id=2, tags=[]),
    ]
    client = make_client(docs=docs, tags=[tag])
    store = DocumentStore(client, tmp_path / "test.db")
    await store.sync()

    results = store.search_documents(tags=[3])
    assert len(results) == 1
    assert results[0].id == 1
    store.close()


async def test_search_by_tag_name(tmp_path):
    tag = make_tag(3, "invoice")
    docs = [
        make_doc(id=1, tags=[3]),
        make_doc(id=2, tags=[]),
    ]
    client = make_client(docs=docs, tags=[tag])
    store = DocumentStore(client, tmp_path / "test.db")
    await store.sync()

    results = store.search_documents(tags=["invoice"])
    assert len(results) == 1
    assert results[0].id == 1
    store.close()


async def test_search_by_correspondent_name(tmp_path):
    corr = make_correspondent(5, "ACME")
    docs = [
        make_doc(id=1, correspondent=5),
        make_doc(id=2, correspondent=None),
    ]
    client = make_client(docs=docs, correspondents=[corr])
    store = DocumentStore(client, tmp_path / "test.db")
    await store.sync()

    results = store.search_documents(correspondent="ACME")
    assert len(results) == 1
    assert results[0].id == 1
    store.close()


async def test_search_no_filters_returns_all(tmp_path):
    docs = [make_doc(id=i) for i in range(1, 6)]
    client = make_client(docs=docs)
    store = DocumentStore(client, tmp_path / "test.db")
    await store.sync()

    results = store.search_documents()
    assert len(results) == 5
    store.close()


async def test_search_content_regex(tmp_path):
    docs = [
        Document.model_validate({"id": 1, "title": "A", "content": "Total amount: 150 EUR", "tags": []}),
        Document.model_validate({"id": 2, "title": "B", "content": "No numbers here", "tags": []}),
    ]
    client = make_client(docs=docs)
    store = DocumentStore(client, tmp_path / "test.db")
    await store.sync()

    results = store.search_documents(content_regex=r"\d+ EUR")
    assert len(results) == 1
    assert results[0].id == 1
    store.close()
