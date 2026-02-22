"""Tests for DocumentStore — sync, search, upsert idempotency."""

from __future__ import annotations

import hashlib
import struct
from datetime import date
from unittest.mock import AsyncMock, MagicMock

import numpy as np
import pytest

from easypaperless.models.correspondents import Correspondent
from easypaperless.models.custom_fields import CustomField, FieldDataType
from easypaperless.models.document_types import DocumentType
from easypaperless.models.documents import Document, DocumentMetadata
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


# ------------------------------------------------------------------
# sync_metadata / checksum tests
# ------------------------------------------------------------------


def make_metadata(**kwargs) -> DocumentMetadata:
    return DocumentMetadata.model_validate(kwargs)


async def test_sync_metadata_upserts_checksums(tmp_path):
    doc = make_doc(id=1)
    client = make_client(docs=[doc])
    client.get_document_metadata = AsyncMock(
        return_value=make_metadata(original_checksum="abc123", archive_checksum="def456")
    )
    store = DocumentStore(client, tmp_path / "test.db")
    await store.sync()
    count = await store.sync_metadata()

    assert count == 1
    conn = store._get_conn()
    row = conn.execute(
        "SELECT original_checksum, archive_checksum FROM document_metadata WHERE document_id = 1"
    ).fetchone()
    assert row["original_checksum"] == "abc123"
    assert row["archive_checksum"] == "def456"
    store.close()


async def test_sync_metadata_skips_failed_docs(tmp_path):
    docs = [make_doc(id=1), make_doc(id=2)]
    client = make_client(docs=docs)

    async def _side_effect(doc_id):
        if doc_id == 1:
            raise RuntimeError("network error")
        return make_metadata(original_checksum="ok")

    client.get_document_metadata = AsyncMock(side_effect=_side_effect)
    store = DocumentStore(client, tmp_path / "test.db")
    await store.sync()
    count = await store.sync_metadata()

    assert count == 2  # both attempted
    conn = store._get_conn()
    rows = conn.execute("SELECT document_id FROM document_metadata").fetchall()
    assert len(rows) == 1  # only doc 2 succeeded
    assert rows[0]["document_id"] == 2
    store.close()


async def test_get_document_by_checksum_found(tmp_path):
    doc = make_doc(id=1)
    client = make_client(docs=[doc])
    client.get_document_metadata = AsyncMock(
        return_value=make_metadata(original_checksum="deadbeef")
    )
    store = DocumentStore(client, tmp_path / "test.db")
    await store.sync()
    await store.sync_metadata()

    result = store.get_document_by_checksum("deadbeef")
    assert result is not None
    assert result.id == 1
    store.close()


async def test_get_document_by_checksum_archive(tmp_path):
    doc = make_doc(id=1)
    client = make_client(docs=[doc])
    client.get_document_metadata = AsyncMock(
        return_value=make_metadata(original_checksum="aaa", archive_checksum="bbb")
    )
    store = DocumentStore(client, tmp_path / "test.db")
    await store.sync()
    await store.sync_metadata()

    assert store.get_document_by_checksum("bbb") is not None
    store.close()


async def test_get_document_by_checksum_not_found(tmp_path):
    client = make_client()
    store = DocumentStore(client, tmp_path / "test.db")
    result = store.get_document_by_checksum("nonexistent")
    assert result is None
    store.close()


async def test_find_unsynced_files(tmp_path):
    files_dir = tmp_path / "files"
    files_dir.mkdir()
    file1 = files_dir / "synced.pdf"
    file2 = files_dir / "unsynced.pdf"
    file1.write_bytes(b"synced content")
    file2.write_bytes(b"unsynced content")

    checksum1 = hashlib.md5(b"synced content").hexdigest()

    doc = make_doc(id=1)
    client = make_client(docs=[doc])
    store = DocumentStore(client, tmp_path / "test.db")
    await store.sync()

    # Manually insert the checksum for file1
    conn = store._get_conn()
    conn.execute(
        """INSERT INTO document_metadata
           (document_id, original_checksum, archive_checksum, original_size,
            archive_size, original_mime_type, media_filename, has_archive_version, raw_json)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (1, checksum1, None, len(b"synced content"), None, None, None, 0, "{}"),
    )
    conn.commit()

    unsynced = store.find_unsynced_files(files_dir, pattern="*.pdf")
    assert len(unsynced) == 1
    assert unsynced[0].name == "unsynced.pdf"
    store.close()


# ------------------------------------------------------------------
# Embedding / semantic search tests
# ------------------------------------------------------------------


def make_fake_provider(vectors: list[list[float]]) -> MagicMock:
    provider = MagicMock()
    provider.embed = AsyncMock(return_value=vectors)
    return provider


async def test_embed_documents_stores_chunks(tmp_path):
    doc = make_doc(id=1, title="Invoice 2024")
    client = make_client(docs=[doc])
    store = DocumentStore(client, tmp_path / "test.db")
    await store.sync()

    provider = make_fake_provider([[0.1, 0.2, 0.3]])
    count = await store.embed_documents(provider, chunk_size=512, chunk_overlap=64)

    assert count >= 1
    conn = store._get_conn()
    rows = conn.execute("SELECT * FROM embeddings WHERE document_id = 1").fetchall()
    assert len(rows) >= 1
    store.close()


async def test_embed_documents_skips_existing_without_force(tmp_path):
    doc = make_doc(id=1, title="Test")
    client = make_client(docs=[doc])
    store = DocumentStore(client, tmp_path / "test.db")
    await store.sync()

    vec = [0.1, 0.2, 0.3]
    provider = make_fake_provider([vec])
    await store.embed_documents(provider)

    # Second call without force should skip the doc
    provider2 = make_fake_provider([vec])
    count2 = await store.embed_documents(provider2)
    assert count2 == 0
    provider2.embed.assert_not_called()
    store.close()


async def test_embed_documents_force_reembeds(tmp_path):
    doc = make_doc(id=1, title="Test")
    client = make_client(docs=[doc])
    store = DocumentStore(client, tmp_path / "test.db")
    await store.sync()

    vec = [0.1, 0.2, 0.3]
    provider = make_fake_provider([vec])
    await store.embed_documents(provider)

    provider2 = make_fake_provider([vec])
    count2 = await store.embed_documents(provider2, force=True)
    assert count2 >= 1
    provider2.embed.assert_called()
    store.close()


async def test_semantic_search_returns_top_k(tmp_path):
    docs = [
        make_doc(id=1, title="Alpha"),
        make_doc(id=2, title="Beta"),
        make_doc(id=3, title="Gamma"),
    ]
    client = make_client(docs=docs)
    store = DocumentStore(client, tmp_path / "test.db")
    await store.sync()

    # Insert fake embeddings directly: doc 2 is most similar to query
    conn = store._get_conn()
    emb_high = np.array([1.0, 0.0, 0.0], dtype=np.float32).tobytes()
    emb_mid = np.array([0.7, 0.7, 0.0], dtype=np.float32).tobytes()
    emb_low = np.array([0.0, 0.0, 1.0], dtype=np.float32).tobytes()
    conn.execute(
        "INSERT INTO embeddings (document_id, chunk_index, chunk_text, embedding) VALUES (?,?,?,?)",
        (1, 0, "alpha text", emb_mid),
    )
    conn.execute(
        "INSERT INTO embeddings (document_id, chunk_index, chunk_text, embedding) VALUES (?,?,?,?)",
        (2, 0, "beta text", emb_high),
    )
    conn.execute(
        "INSERT INTO embeddings (document_id, chunk_index, chunk_text, embedding) VALUES (?,?,?,?)",
        (3, 0, "gamma text", emb_low),
    )
    conn.commit()

    # Query vector similar to doc 2 (emb_high)
    query_vec = [1.0, 0.0, 0.0]
    provider = make_fake_provider([query_vec])

    results = await store.semantic_search("query", provider, top_k=2)
    assert len(results) == 2
    assert results[0][0].id == 2  # highest similarity
    assert results[0][1] > results[1][1]  # scores descending
    store.close()


async def test_semantic_search_empty_embeddings(tmp_path):
    client = make_client()
    store = DocumentStore(client, tmp_path / "test.db")
    provider = make_fake_provider([[0.1, 0.2]])
    results = await store.semantic_search("query", provider)
    assert results == []
    store.close()
