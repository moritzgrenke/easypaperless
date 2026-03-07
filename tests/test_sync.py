"""Tests for SyncPaperlessClient."""

from __future__ import annotations

import respx
from httpx import Response

from easypaperless.models.documents import DocumentMetadata
from easypaperless.sync import SyncPaperlessClient

BASE_URL = "http://paperless.test"
API_KEY = "test-key"

DOC_DATA = {"id": 1, "title": "Test", "tags": []}
DOC_LIST = {"count": 1, "next": None, "previous": None, "results": [DOC_DATA]}

TAG_DATA = {"id": 1, "name": "invoice"}
TAG_LIST = {"count": 1, "next": None, "previous": None, "results": [TAG_DATA]}

CORRESPONDENT_DATA = {"id": 1, "name": "ACME Corp"}
CORRESPONDENT_LIST = {"count": 1, "next": None, "previous": None, "results": [CORRESPONDENT_DATA]}

DOCTYPE_DATA = {"id": 1, "name": "Invoice"}
DOCTYPE_LIST = {"count": 1, "next": None, "previous": None, "results": [DOCTYPE_DATA]}

STORAGE_PATH_DATA = {"id": 1, "name": "archive", "path": "/archive/{title}"}
STORAGE_PATH_LIST = {"count": 1, "next": None, "previous": None, "results": [STORAGE_PATH_DATA]}

CUSTOM_FIELD_DATA = {"id": 1, "name": "Amount", "data_type": "string"}
CUSTOM_FIELD_LIST = {"count": 1, "next": None, "previous": None, "results": [CUSTOM_FIELD_DATA]}

NOTE_DATA = {"id": 10, "note": "hello", "created": "2024-01-01T00:00:00Z", "document": 1, "user": 1}


# ---------------------------------------------------------------------------
# Import / public API
# ---------------------------------------------------------------------------


def test_sync_client_importable_from_package():
    """AC: SyncPaperlessClient is importable directly from easypaperless."""
    from easypaperless import SyncPaperlessClient as Cls

    assert Cls is SyncPaperlessClient


# ---------------------------------------------------------------------------
# Constructor & kwargs forwarding
# ---------------------------------------------------------------------------


def test_sync_client_forwards_kwargs():
    """AC: Constructor forwards **kwargs to PaperlessClient."""
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False):
        client = SyncPaperlessClient(url=BASE_URL, api_key=API_KEY, timeout=99.0)
        assert client._async_client._session._timeout == 99.0
        client.close()


# ---------------------------------------------------------------------------
# Context manager
# ---------------------------------------------------------------------------


def test_sync_client_context_manager():
    """AC: __enter__ / __exit__; __exit__ calls close()."""
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.get("/documents/1/").mock(return_value=Response(200, json=DOC_DATA))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            doc = client.get_document(1)
    assert doc.id == 1


def test_sync_client_context_manager_returns_self():
    """AC: __enter__ returns the SyncPaperlessClient instance."""
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False):
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            assert isinstance(client, SyncPaperlessClient)


# ---------------------------------------------------------------------------
# close() idempotency
# ---------------------------------------------------------------------------


def test_close_called_twice_does_not_raise():
    """Edge case: close() called twice should not raise."""
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False):
        client = SyncPaperlessClient(url=BASE_URL, api_key=API_KEY)
        client.close()
        client.close()  # should be a no-op


# ---------------------------------------------------------------------------
# Document methods
# ---------------------------------------------------------------------------


def test_sync_get_document():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.get("/documents/1/").mock(return_value=Response(200, json=DOC_DATA))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            doc = client.get_document(1)
    assert doc.id == 1
    assert doc.title == "Test"


def test_sync_get_document_with_metadata():
    meta_data = {
        "original_checksum": "abc123",
        "original_size": 1024,
        "original_mime_type": "application/pdf",
        "media_filename": "test.pdf",
        "has_archive_version": True,
        "original_metadata": [],
        "archive_checksum": "def456",
        "archive_size": 2048,
        "archive_metadata": [],
    }
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.get("/documents/1/").mock(return_value=Response(200, json=DOC_DATA))
        router.get("/documents/1/metadata/").mock(return_value=Response(200, json=meta_data))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            doc = client.get_document(1, include_metadata=True)
    assert doc.metadata is not None
    assert doc.metadata.original_checksum == "abc123"


def test_sync_get_document_metadata():
    meta_data = {
        "original_checksum": "abc",
        "original_size": 100,
        "original_mime_type": "application/pdf",
        "media_filename": "f.pdf",
        "has_archive_version": False,
        "original_metadata": [],
        "archive_checksum": None,
        "archive_size": None,
        "archive_metadata": [],
    }
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.get("/documents/1/metadata/").mock(return_value=Response(200, json=meta_data))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            meta = client.get_document_metadata(1)
    assert isinstance(meta, DocumentMetadata)
    assert meta.original_checksum == "abc"


def test_sync_list_documents():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.get("/documents/").mock(return_value=Response(200, json=DOC_LIST))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            docs = client.list_documents()
    assert len(docs) == 1
    assert docs[0].title == "Test"


def test_sync_update_document():
    updated = {**DOC_DATA, "title": "Updated"}
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.patch("/documents/1/").mock(return_value=Response(200, json=updated))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            doc = client.update_document(1, title="Updated")
    assert doc.title == "Updated"


def test_sync_delete_document():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.delete("/documents/1/").mock(return_value=Response(204))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            client.delete_document(1)


def test_sync_download_document():
    content = b"%PDF-1.4 fake content"
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.get("/documents/1/archive/").mock(
            return_value=Response(200, content=content, headers={"content-type": "application/pdf"})
        )
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            data = client.download_document(1)
    assert data == content


# ---------------------------------------------------------------------------
# Upload methods
# ---------------------------------------------------------------------------


def test_sync_upload_document(tmp_path):
    pdf = tmp_path / "scan.pdf"
    pdf.write_bytes(b"%PDF-1.4 test")

    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.post("/documents/post_document/").mock(
            return_value=Response(200, text='"sync-task-42"')
        )
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            result = client.upload_document(pdf, title="Sync Upload")
    assert result == "sync-task-42"


# ---------------------------------------------------------------------------
# Tag methods
# ---------------------------------------------------------------------------


def test_sync_list_tags():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.get("/tags/").mock(return_value=Response(200, json=TAG_LIST))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            tags = client.list_tags()
    assert len(tags) == 1
    assert tags[0].name == "invoice"


def test_sync_get_tag():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.get("/tags/1/").mock(return_value=Response(200, json=TAG_DATA))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            tag = client.get_tag(1)
    assert tag.id == 1


def test_sync_create_tag():
    created = {**TAG_DATA, "id": 2, "name": "receipt"}
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.post("/tags/").mock(return_value=Response(201, json=created))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            tag = client.create_tag(name="receipt")
    assert tag.name == "receipt"


def test_sync_update_tag():
    updated = {**TAG_DATA, "name": "updated-tag"}
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.patch("/tags/1/").mock(return_value=Response(200, json=updated))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            tag = client.update_tag(1, name="updated-tag")
    assert tag.name == "updated-tag"


def test_sync_delete_tag():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.delete("/tags/1/").mock(return_value=Response(204))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            client.delete_tag(1)


# ---------------------------------------------------------------------------
# Correspondent methods
# ---------------------------------------------------------------------------


def test_sync_list_correspondents():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.get("/correspondents/").mock(return_value=Response(200, json=CORRESPONDENT_LIST))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            items = client.list_correspondents()
    assert len(items) == 1
    assert items[0].name == "ACME Corp"


def test_sync_get_correspondent():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.get("/correspondents/1/").mock(return_value=Response(200, json=CORRESPONDENT_DATA))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            item = client.get_correspondent(1)
    assert item.id == 1


def test_sync_create_correspondent():
    created = {**CORRESPONDENT_DATA, "id": 2, "name": "New Corp"}
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.post("/correspondents/").mock(return_value=Response(201, json=created))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            item = client.create_correspondent(name="New Corp")
    assert item.name == "New Corp"


def test_sync_delete_correspondent():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.delete("/correspondents/1/").mock(return_value=Response(204))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            client.delete_correspondent(1)


# ---------------------------------------------------------------------------
# Document type methods
# ---------------------------------------------------------------------------


def test_sync_list_document_types():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.get("/document_types/").mock(return_value=Response(200, json=DOCTYPE_LIST))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            items = client.list_document_types()
    assert len(items) == 1
    assert items[0].name == "Invoice"


def test_sync_get_document_type():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.get("/document_types/1/").mock(return_value=Response(200, json=DOCTYPE_DATA))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            item = client.get_document_type(1)
    assert item.id == 1


def test_sync_create_document_type():
    created = {**DOCTYPE_DATA, "id": 2, "name": "Contract"}
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.post("/document_types/").mock(return_value=Response(201, json=created))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            item = client.create_document_type(name="Contract")
    assert item.name == "Contract"


def test_sync_delete_document_type():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.delete("/document_types/1/").mock(return_value=Response(204))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            client.delete_document_type(1)


# ---------------------------------------------------------------------------
# Storage path methods
# ---------------------------------------------------------------------------


def test_sync_list_storage_paths():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.get("/storage_paths/").mock(return_value=Response(200, json=STORAGE_PATH_LIST))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            items = client.list_storage_paths()
    assert len(items) == 1
    assert items[0].name == "archive"


def test_sync_get_storage_path():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.get("/storage_paths/1/").mock(return_value=Response(200, json=STORAGE_PATH_DATA))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            item = client.get_storage_path(1)
    assert item.id == 1


def test_sync_create_storage_path():
    created = {**STORAGE_PATH_DATA, "id": 2, "name": "backup", "path": "/backup/{title}"}
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.post("/storage_paths/").mock(return_value=Response(201, json=created))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            item = client.create_storage_path(name="backup", path="/backup/{title}")
    assert item.name == "backup"


def test_sync_delete_storage_path():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.delete("/storage_paths/1/").mock(return_value=Response(204))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            client.delete_storage_path(1)


# ---------------------------------------------------------------------------
# Custom field methods
# ---------------------------------------------------------------------------


def test_sync_list_custom_fields():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.get("/custom_fields/").mock(return_value=Response(200, json=CUSTOM_FIELD_LIST))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            items = client.list_custom_fields()
    assert len(items) == 1
    assert items[0].name == "Amount"


def test_sync_get_custom_field():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.get("/custom_fields/1/").mock(return_value=Response(200, json=CUSTOM_FIELD_DATA))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            item = client.get_custom_field(1)
    assert item.id == 1


def test_sync_create_custom_field():
    created = {**CUSTOM_FIELD_DATA, "id": 2, "name": "Total"}
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.post("/custom_fields/").mock(return_value=Response(201, json=created))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            item = client.create_custom_field(name="Total", data_type="string")
    assert item.name == "Total"


def test_sync_delete_custom_field():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.delete("/custom_fields/1/").mock(return_value=Response(204))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            client.delete_custom_field(1)


# ---------------------------------------------------------------------------
# Notes methods
# ---------------------------------------------------------------------------


def test_sync_get_notes():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.get("/documents/1/notes/").mock(return_value=Response(200, json=[NOTE_DATA]))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            notes = client.get_notes(1)
    assert len(notes) == 1
    assert notes[0].note == "hello"


def test_sync_create_note():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.post("/documents/1/notes/").mock(return_value=Response(201, json=NOTE_DATA))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            note = client.create_note(1, note="hello")
    assert note.note == "hello"


def test_sync_delete_note():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.delete("/documents/1/notes/").mock(return_value=Response(204))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            client.delete_note(1, note_id=10)


# ---------------------------------------------------------------------------
# Bulk operations (document)
# ---------------------------------------------------------------------------


def test_sync_bulk_add_tag():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.get("/tags/").mock(return_value=Response(200, json=TAG_LIST))
        router.post("/documents/bulk_edit/").mock(return_value=Response(200, json="OK"))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            client.bulk_add_tag([1, 2], tag="invoice")


def test_sync_bulk_remove_tag():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.post("/documents/bulk_edit/").mock(return_value=Response(200, json="OK"))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            client.bulk_remove_tag([1, 2], tag=1)


def test_sync_bulk_modify_tags():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.post("/documents/bulk_edit/").mock(return_value=Response(200, json="OK"))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            client.bulk_modify_tags([1, 2], add_tags=[1], remove_tags=[2])


def test_sync_bulk_delete():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.post("/documents/bulk_edit/").mock(return_value=Response(200, json="OK"))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            client.bulk_delete([1, 2])


def test_sync_bulk_set_correspondent():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.post("/documents/bulk_edit/").mock(return_value=Response(200, json="OK"))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            client.bulk_set_correspondent([1, 2], 1)


def test_sync_bulk_set_document_type():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.post("/documents/bulk_edit/").mock(return_value=Response(200, json="OK"))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            client.bulk_set_document_type([1, 2], 1)


def test_sync_bulk_set_storage_path():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.post("/documents/bulk_edit/").mock(return_value=Response(200, json="OK"))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            client.bulk_set_storage_path([1, 2], 1)


def test_sync_bulk_modify_custom_fields():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.post("/documents/bulk_edit/").mock(return_value=Response(200, json="OK"))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            client.bulk_modify_custom_fields(
                [1, 2],
                add_fields=[{"field": 1, "value": "test"}],
                remove_fields=[2],
            )


def test_sync_bulk_set_permissions():
    from easypaperless.models.permissions import PermissionSet, SetPermissions

    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.post("/documents/bulk_edit/").mock(return_value=Response(200, json="OK"))
        perms = SetPermissions(
            view=PermissionSet(users=[1], groups=[]),
            change=PermissionSet(users=[1], groups=[]),
        )
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            client.bulk_set_permissions([1, 2], set_permissions=perms, owner=1)


# ---------------------------------------------------------------------------
# Bulk operations (non-document)
# ---------------------------------------------------------------------------


def test_sync_bulk_delete_tags():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.post("/bulk_edit_objects/").mock(return_value=Response(200, json="OK"))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            client.bulk_delete_tags([1, 2])


def test_sync_bulk_delete_correspondents():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.post("/bulk_edit_objects/").mock(return_value=Response(200, json="OK"))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            client.bulk_delete_correspondents([1, 2])


# ---------------------------------------------------------------------------
# Exception propagation
# ---------------------------------------------------------------------------


def test_sync_exception_propagation():
    """Edge case: exceptions from coroutines propagate to caller unchanged."""
    from easypaperless.exceptions import NotFoundError

    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.get("/documents/999/").mock(
            return_value=Response(404, json={"detail": "Not found."})
        )
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            try:
                client.get_document(999)
                assert False, "Expected NotFoundError"
            except NotFoundError:
                pass  # expected


# ---------------------------------------------------------------------------
# Background thread is daemon
# ---------------------------------------------------------------------------


def test_background_thread_is_daemon():
    """Technical requirement: background thread is a daemon thread."""
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False):
        client = SyncPaperlessClient(url=BASE_URL, api_key=API_KEY)
        assert client._thread.daemon is True
        client.close()


# ---------------------------------------------------------------------------
# No business logic in SyncPaperlessClient
# ---------------------------------------------------------------------------


def test_sync_client_delegates_to_async_client():
    """AC: No business logic — all calls delegate to _async_client."""
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False):
        client = SyncPaperlessClient(url=BASE_URL, api_key=API_KEY)
        from easypaperless.client import PaperlessClient

        assert isinstance(client._async_client, PaperlessClient)
        client.close()
