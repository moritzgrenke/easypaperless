"""Tests for SyncPaperlessClient."""

from __future__ import annotations

import json

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
            doc = client.documents.get(1)
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
            doc = client.documents.get(1)
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
            doc = client.documents.get(1, include_metadata=True)
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
            meta = client.documents.get_metadata(1)
    assert isinstance(meta, DocumentMetadata)
    assert meta.original_checksum == "abc"


def test_sync_list_documents():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.get("/documents/").mock(return_value=Response(200, json=DOC_LIST))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            docs = client.documents.list()
    assert len(docs) == 1
    assert docs[0].title == "Test"


def test_sync_update_document():
    updated = {**DOC_DATA, "title": "Updated"}
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.patch("/documents/1/").mock(return_value=Response(200, json=updated))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            doc = client.documents.update(1, title="Updated")
    assert doc.title == "Updated"


def test_sync_delete_document():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.delete("/documents/1/").mock(return_value=Response(204))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            client.documents.delete(1)


def test_sync_download_document():
    content = b"%PDF-1.4 fake content"
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.get("/documents/1/archive/").mock(
            return_value=Response(200, content=content, headers={"content-type": "application/pdf"})
        )
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            data = client.documents.download(1)
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
            result = client.documents.upload(pdf, title="Sync Upload")
    assert result == "sync-task-42"


# ---------------------------------------------------------------------------
# Tag methods
# ---------------------------------------------------------------------------


def test_sync_list_tags():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.get("/tags/").mock(return_value=Response(200, json=TAG_LIST))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            tags = client.tags.list()
    assert len(tags) == 1
    assert tags[0].name == "invoice"


def test_sync_get_tag():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.get("/tags/1/").mock(return_value=Response(200, json=TAG_DATA))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            tag = client.tags.get(1)
    assert tag.id == 1


def test_sync_create_tag():
    created = {**TAG_DATA, "id": 2, "name": "receipt"}
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.post("/tags/").mock(return_value=Response(201, json=created))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            tag = client.tags.create(name="receipt")
    assert tag.name == "receipt"


def test_sync_create_tag_omits_color_and_is_inbox_tag_when_not_provided():
    """Regression: color and is_inbox_tag must default to UNSET, not None (issue #0027)."""
    captured: dict = {}
    created = {**TAG_DATA, "id": 2, "name": "receipt"}

    def _capture(request):
        captured["body"] = json.loads(request.content)
        return Response(201, json=created)

    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.post("/tags/").mock(side_effect=_capture)
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            client.tags.create(name="receipt")

    assert "color" not in captured["body"]
    assert "is_inbox_tag" not in captured["body"]


def test_sync_update_tag():
    updated = {**TAG_DATA, "name": "updated-tag"}
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.patch("/tags/1/").mock(return_value=Response(200, json=updated))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            tag = client.tags.update(1, name="updated-tag")
    assert tag.name == "updated-tag"


def test_sync_delete_tag():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.delete("/tags/1/").mock(return_value=Response(204))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            client.tags.delete(1)


# ---------------------------------------------------------------------------
# Correspondent methods
# ---------------------------------------------------------------------------


def test_sync_list_correspondents():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.get("/correspondents/").mock(return_value=Response(200, json=CORRESPONDENT_LIST))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            items = client.correspondents.list()
    assert len(items) == 1
    assert items[0].name == "ACME Corp"


def test_sync_get_correspondent():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.get("/correspondents/1/").mock(return_value=Response(200, json=CORRESPONDENT_DATA))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            item = client.correspondents.get(1)
    assert item.id == 1


def test_sync_create_correspondent():
    created = {**CORRESPONDENT_DATA, "id": 2, "name": "New Corp"}
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.post("/correspondents/").mock(return_value=Response(201, json=created))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            item = client.correspondents.create(name="New Corp")
    assert item.name == "New Corp"


def test_sync_update_correspondent():
    updated = {**CORRESPONDENT_DATA, "name": "ACME Inc."}
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.patch("/correspondents/1/").mock(return_value=Response(200, json=updated))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            item = client.correspondents.update(1, name="ACME Inc.")
    assert item.name == "ACME Inc."


def test_sync_delete_correspondent():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.delete("/correspondents/1/").mock(return_value=Response(204))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            client.correspondents.delete(1)


# ---------------------------------------------------------------------------
# Document type methods
# ---------------------------------------------------------------------------


def test_sync_list_document_types():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.get("/document_types/").mock(return_value=Response(200, json=DOCTYPE_LIST))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            items = client.document_types.list()
    assert len(items) == 1
    assert items[0].name == "Invoice"


def test_sync_get_document_type():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.get("/document_types/1/").mock(return_value=Response(200, json=DOCTYPE_DATA))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            item = client.document_types.get(1)
    assert item.id == 1


def test_sync_create_document_type():
    created = {**DOCTYPE_DATA, "id": 2, "name": "Contract"}
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.post("/document_types/").mock(return_value=Response(201, json=created))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            item = client.document_types.create(name="Contract")
    assert item.name == "Contract"


def test_sync_update_document_type():
    updated = {**DOCTYPE_DATA, "name": "Receipt"}
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.patch("/document_types/1/").mock(return_value=Response(200, json=updated))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            item = client.document_types.update(1, name="Receipt")
    assert item.name == "Receipt"


def test_sync_delete_document_type():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.delete("/document_types/1/").mock(return_value=Response(204))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            client.document_types.delete(1)


# ---------------------------------------------------------------------------
# Storage path methods
# ---------------------------------------------------------------------------


def test_sync_list_storage_paths():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.get("/storage_paths/").mock(return_value=Response(200, json=STORAGE_PATH_LIST))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            items = client.storage_paths.list()
    assert len(items) == 1
    assert items[0].name == "archive"


def test_sync_get_storage_path():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.get("/storage_paths/1/").mock(return_value=Response(200, json=STORAGE_PATH_DATA))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            item = client.storage_paths.get(1)
    assert item.id == 1


def test_sync_create_storage_path():
    created = {**STORAGE_PATH_DATA, "id": 2, "name": "backup", "path": "/backup/{title}"}
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.post("/storage_paths/").mock(return_value=Response(201, json=created))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            item = client.storage_paths.create(name="backup", path="/backup/{title}")
    assert item.name == "backup"


def test_sync_update_storage_path():
    updated = {**STORAGE_PATH_DATA, "name": "updated-archive", "path": "/updated/{title}"}
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.patch("/storage_paths/1/").mock(return_value=Response(200, json=updated))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            item = client.storage_paths.update(1, name="updated-archive")
    assert item.name == "updated-archive"


def test_sync_delete_storage_path():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.delete("/storage_paths/1/").mock(return_value=Response(204))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            client.storage_paths.delete(1)


# ---------------------------------------------------------------------------
# Custom field methods
# ---------------------------------------------------------------------------


def test_sync_list_custom_fields():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.get("/custom_fields/").mock(return_value=Response(200, json=CUSTOM_FIELD_LIST))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            items = client.custom_fields.list()
    assert len(items) == 1
    assert items[0].name == "Amount"


def test_sync_get_custom_field():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.get("/custom_fields/1/").mock(return_value=Response(200, json=CUSTOM_FIELD_DATA))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            item = client.custom_fields.get(1)
    assert item.id == 1


def test_sync_create_custom_field():
    created = {**CUSTOM_FIELD_DATA, "id": 2, "name": "Total"}
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.post("/custom_fields/").mock(return_value=Response(201, json=created))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            item = client.custom_fields.create(name="Total", data_type="string")
    assert item.name == "Total"


def test_sync_update_custom_field():
    updated = {**CUSTOM_FIELD_DATA, "name": "Total Amount"}
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.patch("/custom_fields/1/").mock(return_value=Response(200, json=updated))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            item = client.custom_fields.update(1, name="Total Amount")
    assert item.name == "Total Amount"


def test_sync_delete_custom_field():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.delete("/custom_fields/1/").mock(return_value=Response(204))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            client.custom_fields.delete(1)


# ---------------------------------------------------------------------------
# Notes methods
# ---------------------------------------------------------------------------


def test_sync_get_notes():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.get("/documents/1/notes/").mock(return_value=Response(200, json=[NOTE_DATA]))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            notes = client.documents.notes.list(1)
    assert len(notes) == 1
    assert notes[0].note == "hello"


def test_sync_create_note():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.post("/documents/1/notes/").mock(return_value=Response(201, json=NOTE_DATA))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            note = client.documents.notes.create(1, note="hello")
    assert note.note == "hello"


def test_sync_delete_note():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.delete("/documents/1/notes/").mock(return_value=Response(204))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            client.documents.notes.delete(1, note_id=10)


# ---------------------------------------------------------------------------
# Bulk operations (document)
# ---------------------------------------------------------------------------


def test_sync_bulk_add_tag():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.get("/tags/").mock(return_value=Response(200, json=TAG_LIST))
        router.post("/documents/bulk_edit/").mock(return_value=Response(200, json="OK"))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            client.documents.bulk_add_tag([1, 2], tag="invoice")


def test_sync_bulk_remove_tag():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.post("/documents/bulk_edit/").mock(return_value=Response(200, json="OK"))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            client.documents.bulk_remove_tag([1, 2], tag=1)


def test_sync_bulk_modify_tags():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.post("/documents/bulk_edit/").mock(return_value=Response(200, json="OK"))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            client.documents.bulk_modify_tags([1, 2], add_tags=[1], remove_tags=[2])


def test_sync_bulk_delete():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.post("/documents/bulk_edit/").mock(return_value=Response(200, json="OK"))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            client.documents.bulk_delete([1, 2])


def test_sync_bulk_set_correspondent():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.post("/documents/bulk_edit/").mock(return_value=Response(200, json="OK"))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            client.documents.bulk_set_correspondent([1, 2], 1)


def test_sync_bulk_set_document_type():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.post("/documents/bulk_edit/").mock(return_value=Response(200, json="OK"))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            client.documents.bulk_set_document_type([1, 2], 1)


def test_sync_bulk_set_storage_path():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.post("/documents/bulk_edit/").mock(return_value=Response(200, json="OK"))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            client.documents.bulk_set_storage_path([1, 2], 1)


def test_sync_bulk_modify_custom_fields():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.post("/documents/bulk_edit/").mock(return_value=Response(200, json="OK"))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            client.documents.bulk_modify_custom_fields(
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
            client.documents.bulk_set_permissions([1, 2], set_permissions=perms, owner=1)


# ---------------------------------------------------------------------------
# Bulk operations (non-document)
# ---------------------------------------------------------------------------


def test_sync_bulk_delete_tags():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.post("/bulk_edit_objects/").mock(return_value=Response(200, json="OK"))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            client.tags.bulk_delete([1, 2])


def test_sync_bulk_delete_correspondents():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.post("/bulk_edit_objects/").mock(return_value=Response(200, json="OK"))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            client.correspondents.bulk_delete([1, 2])


def test_sync_bulk_delete_document_types():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.post("/bulk_edit_objects/").mock(return_value=Response(200, json="OK"))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            client.document_types.bulk_delete([1, 2])


def test_sync_bulk_delete_storage_paths():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.post("/bulk_edit_objects/").mock(return_value=Response(200, json="OK"))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            client.storage_paths.bulk_delete([1, 2])


def test_sync_bulk_set_permissions_tags():
    from easypaperless.models.permissions import PermissionSet, SetPermissions

    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.post("/bulk_edit_objects/").mock(return_value=Response(200, json="OK"))
        perms = SetPermissions(
            view=PermissionSet(users=[1], groups=[]),
            change=PermissionSet(users=[1], groups=[]),
        )
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            client.tags.bulk_set_permissions([1, 2], set_permissions=perms, owner=1)


def test_sync_bulk_set_permissions_correspondents():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.post("/bulk_edit_objects/").mock(return_value=Response(200, json="OK"))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            client.correspondents.bulk_set_permissions([1, 2], owner=2, merge=True)


def test_sync_bulk_set_permissions_document_types():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.post("/bulk_edit_objects/").mock(return_value=Response(200, json="OK"))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            client.document_types.bulk_set_permissions([1], owner=3)


def test_sync_bulk_set_permissions_storage_paths():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.post("/bulk_edit_objects/").mock(return_value=Response(200, json="OK"))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            client.storage_paths.bulk_set_permissions([1, 2], merge=True)


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
                client.documents.get(999)
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
