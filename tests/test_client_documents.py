"""Tests for PaperlessClient document methods."""

from __future__ import annotations

import json

import pytest
import respx
from httpx import Response

from easypaperless.models.documents import Document, DocumentMetadata
from easypaperless.models.permissions import PermissionSet, SetPermissions

DOC_DATA = {"id": 1, "title": "Test Document", "tags": []}
DOC_LIST = {
    "count": 1,
    "next": None,
    "previous": None,
    "results": [DOC_DATA],
}

META_DATA = {
    "original_checksum": "abc123",
    "original_size": 204800,
    "original_mime_type": "application/pdf",
    "media_filename": "documents/archive/2024/invoice.pdf",
    "has_archive_version": True,
    "original_metadata": [
        {"namespace": None, "prefix": None, "key": "Producer", "value": "FancyPDF"},
    ],
    "archive_checksum": "def456",
    "archive_size": 102400,
    "archive_metadata": [],
}


async def test_get_document(client, mock_router):
    mock_router.get("/documents/1/").mock(return_value=Response(200, json=DOC_DATA))
    doc = await client.get_document(1)
    assert isinstance(doc, Document)
    assert doc.id == 1
    assert doc.title == "Test Document"
    assert doc.metadata is None


async def test_get_document_without_metadata_does_not_call_metadata_endpoint(client, mock_router):
    mock_router.get("/documents/1/").mock(return_value=Response(200, json=DOC_DATA))
    # metadata endpoint is NOT registered — would raise if called
    doc = await client.get_document(1)
    assert doc.metadata is None


async def test_get_document_with_metadata(client, mock_router):
    mock_router.get("/documents/1/").mock(return_value=Response(200, json=DOC_DATA))
    mock_router.get("/documents/1/metadata/").mock(return_value=Response(200, json=META_DATA))
    doc = await client.get_document(1, include_metadata=True)
    assert isinstance(doc, Document)
    assert doc.metadata is not None
    assert isinstance(doc.metadata, DocumentMetadata)
    assert doc.metadata.original_checksum == "abc123"
    assert doc.metadata.original_size == 204800
    assert doc.metadata.original_mime_type == "application/pdf"
    assert doc.metadata.has_archive_version is True
    assert doc.metadata.archive_checksum == "def456"
    assert len(doc.metadata.original_metadata) == 1
    assert doc.metadata.original_metadata[0].key == "Producer"
    assert doc.metadata.original_metadata[0].value == "FancyPDF"


async def test_get_document_metadata_standalone(client, mock_router):
    mock_router.get("/documents/1/metadata/").mock(return_value=Response(200, json=META_DATA))
    meta = await client.get_document_metadata(1)
    assert isinstance(meta, DocumentMetadata)
    assert meta.original_checksum == "abc123"
    assert meta.archive_checksum == "def456"
    assert meta.archive_size == 102400
    assert meta.media_filename == "documents/archive/2024/invoice.pdf"


async def test_get_document_metadata_no_archive_version(client, mock_router):
    no_archive = {
        **META_DATA,
        "has_archive_version": False,
        "archive_checksum": None,
        "archive_size": None,
        "archive_metadata": None,
    }
    mock_router.get("/documents/1/metadata/").mock(return_value=Response(200, json=no_archive))
    meta = await client.get_document_metadata(1)
    assert meta.has_archive_version is False
    assert meta.archive_checksum is None
    assert meta.archive_size is None
    assert meta.archive_metadata is None


async def test_list_documents(client, mock_router):
    mock_router.get("/documents/").mock(return_value=Response(200, json=DOC_LIST))
    docs = await client.list_documents()
    assert len(docs) == 1
    assert docs[0].id == 1


async def test_list_documents_with_search(client, mock_router):
    mock_router.get("/documents/").mock(return_value=Response(200, json=DOC_LIST))
    docs = await client.list_documents(search="invoice", search_mode="title")
    assert len(docs) == 1


async def test_list_documents_with_title_or_text_search(client, mock_router):
    mock_router.get("/documents/").mock(return_value=Response(200, json=DOC_LIST))
    docs = await client.list_documents(search="invoice")  # default mode
    assert len(docs) == 1


async def test_list_documents_with_asn(client, mock_router):
    mock_router.get("/documents/").mock(return_value=Response(200, json=DOC_LIST))
    docs = await client.list_documents(archive_serial_number=42)
    assert len(docs) == 1


async def test_list_documents_with_date_range(client, mock_router):
    mock_router.get("/documents/").mock(return_value=Response(200, json=DOC_LIST))
    docs = await client.list_documents(created_after="2024-01-01", created_before="2024-12-31")
    assert len(docs) == 1


async def test_update_document(client, mock_router):
    mock_router.patch("/documents/1/").mock(
        return_value=Response(200, json={**DOC_DATA, "title": "Updated"})
    )
    doc = await client.update_document(1, title="Updated")
    assert doc.title == "Updated"


async def test_delete_document(client, mock_router):
    mock_router.delete("/documents/1/").mock(return_value=Response(204))
    await client.delete_document(1)


async def test_download_document_archive(client, mock_router):
    mock_router.get("/documents/1/archive/").mock(return_value=Response(200, content=b"PDF"))
    content = await client.download_document(1)
    assert content == b"PDF"


async def test_download_document_original(client, mock_router):
    mock_router.get("/documents/1/download/").mock(return_value=Response(200, content=b"ORIG"))
    content = await client.download_document(1, original=True)
    assert content == b"ORIG"


async def test_list_documents_with_tag_id(client, mock_router):
    mock_router.get("/documents/").mock(return_value=Response(200, json=DOC_LIST))
    docs = await client.list_documents(tags=[3])
    assert len(docs) == 1


async def test_list_documents_with_tag_name(client, mock_router):
    # Resolver will fetch tags list first
    tags_resp = {"count": 1, "next": None, "previous": None, "results": [{"id": 3, "name": "invoice"}]}
    mock_router.get("/tags/").mock(return_value=Response(200, json=tags_resp))
    mock_router.get("/documents/").mock(return_value=Response(200, json=DOC_LIST))
    docs = await client.list_documents(tags=["invoice"])
    assert len(docs) == 1


async def test_update_document_with_correspondent_name(client, mock_router):
    corr_resp = {"count": 1, "next": None, "previous": None, "results": [{"id": 5, "name": "ACME"}]}
    mock_router.get("/correspondents/").mock(return_value=Response(200, json=corr_resp))
    mock_router.patch("/documents/1/").mock(
        return_value=Response(200, json={**DOC_DATA, "correspondent": 5})
    )
    doc = await client.update_document(1, correspondent="ACME")
    assert doc.correspondent == 5


def _patch_capturing_side_effect(captured: dict, response_data: dict = DOC_DATA):
    """Return a respx side-effect that stores the request JSON body."""
    def _side_effect(request):
        captured["body"] = json.loads(request.content)
        return Response(200, json=response_data)
    return _side_effect


async def test_update_document_with_owner(client, mock_router):
    captured: dict = {}
    mock_router.patch("/documents/1/").mock(
        side_effect=_patch_capturing_side_effect(captured, {**DOC_DATA, "owner": 42})
    )
    doc = await client.update_document(1, owner=42)
    assert doc.owner == 42
    assert captured["body"]["owner"] == 42


async def test_update_document_with_set_permissions(client, mock_router):
    captured: dict = {}
    mock_router.patch("/documents/1/").mock(
        side_effect=_patch_capturing_side_effect(captured, DOC_DATA)
    )
    perms = SetPermissions(
        view=PermissionSet(users=[1, 2], groups=[]),
        change=PermissionSet(users=[1], groups=[3]),
    )
    await client.update_document(1, set_permissions=perms)
    body = captured["body"]
    assert body["set_permissions"] == {
        "view": {"users": [1, 2], "groups": []},
        "change": {"users": [1], "groups": [3]},
    }


async def test_update_document_owner_and_permissions_not_sent_when_omitted(client, mock_router):
    captured: dict = {}
    mock_router.patch("/documents/1/").mock(
        side_effect=_patch_capturing_side_effect(captured, {**DOC_DATA, "title": "New"})
    )
    await client.update_document(1, title="New")
    body = captured["body"]
    assert "owner" not in body
    assert "set_permissions" not in body
    assert body == {"title": "New"}


# ---------------------------------------------------------------------------
# Shared mock data for new-parameter tests
# ---------------------------------------------------------------------------

_CORR_RESP = {
    "count": 2, "next": None, "previous": None,
    "results": [{"id": 5, "name": "ACME"}, {"id": 6, "name": "Bank"}],
}
_DOCTYPE_RESP = {
    "count": 2, "next": None, "previous": None,
    "results": [{"id": 10, "name": "Invoice"}, {"id": 11, "name": "Receipt"}],
}


def _capturing_side_effect(captured: dict, response_data: dict = DOC_LIST):
    """Return a respx side-effect that stores the request URL params."""
    def _side_effect(request):
        captured["params"] = dict(request.url.params)
        return Response(200, json=response_data)
    return _side_effect


# ---------------------------------------------------------------------------
# any_correspondent
# ---------------------------------------------------------------------------

async def test_list_documents_any_correspondent_by_id(client, mock_router):
    captured: dict = {}
    mock_router.get("/documents/").mock(side_effect=_capturing_side_effect(captured))
    await client.list_documents(any_correspondent=[5, 6])
    assert captured["params"]["correspondent__id__in"] == "5,6"


async def test_list_documents_any_correspondent_by_name(client, mock_router):
    mock_router.get("/correspondents/").mock(return_value=Response(200, json=_CORR_RESP))
    captured: dict = {}
    mock_router.get("/documents/").mock(side_effect=_capturing_side_effect(captured))
    await client.list_documents(any_correspondent=["ACME", "Bank"])
    assert captured["params"]["correspondent__id__in"] == "5,6"


async def test_list_documents_any_correspondent_overrides_correspondent(client, mock_router):
    """When both are given, any_correspondent takes precedence."""
    captured: dict = {}
    mock_router.get("/documents/").mock(side_effect=_capturing_side_effect(captured))
    await client.list_documents(correspondent=99, any_correspondent=[5, 6])
    assert captured["params"]["correspondent__id__in"] == "5,6"


# ---------------------------------------------------------------------------
# exclude_correspondents
# ---------------------------------------------------------------------------

async def test_list_documents_exclude_correspondents_by_id(client, mock_router):
    captured: dict = {}
    mock_router.get("/documents/").mock(side_effect=_capturing_side_effect(captured))
    await client.list_documents(exclude_correspondents=[5, 6])
    assert captured["params"]["correspondent__id__none"] == "5,6"


async def test_list_documents_exclude_correspondents_by_name(client, mock_router):
    mock_router.get("/correspondents/").mock(return_value=Response(200, json=_CORR_RESP))
    captured: dict = {}
    mock_router.get("/documents/").mock(side_effect=_capturing_side_effect(captured))
    await client.list_documents(exclude_correspondents=["ACME"])
    assert captured["params"]["correspondent__id__none"] == "5"


# ---------------------------------------------------------------------------
# any_document_type
# ---------------------------------------------------------------------------

async def test_list_documents_any_document_type_by_id(client, mock_router):
    captured: dict = {}
    mock_router.get("/documents/").mock(side_effect=_capturing_side_effect(captured))
    await client.list_documents(any_document_type=[10, 11])
    assert captured["params"]["document_type__id__in"] == "10,11"


async def test_list_documents_any_document_type_by_name(client, mock_router):
    mock_router.get("/document_types/").mock(return_value=Response(200, json=_DOCTYPE_RESP))
    captured: dict = {}
    mock_router.get("/documents/").mock(side_effect=_capturing_side_effect(captured))
    await client.list_documents(any_document_type=["Invoice", "Receipt"])
    assert captured["params"]["document_type__id__in"] == "10,11"


async def test_list_documents_any_document_type_overrides_document_type(client, mock_router):
    """When both are given, any_document_type takes precedence."""
    captured: dict = {}
    mock_router.get("/documents/").mock(side_effect=_capturing_side_effect(captured))
    await client.list_documents(document_type=99, any_document_type=[10, 11])
    assert captured["params"]["document_type__id__in"] == "10,11"
    assert "document_type" not in captured["params"]


# ---------------------------------------------------------------------------
# exclude_document_types
# ---------------------------------------------------------------------------

async def test_list_documents_exclude_document_types_by_id(client, mock_router):
    captured: dict = {}
    mock_router.get("/documents/").mock(side_effect=_capturing_side_effect(captured))
    await client.list_documents(exclude_document_types=[10, 11])
    assert captured["params"]["document_type__id__none"] == "10,11"


async def test_list_documents_exclude_document_types_by_name(client, mock_router):
    mock_router.get("/document_types/").mock(return_value=Response(200, json=_DOCTYPE_RESP))
    captured: dict = {}
    mock_router.get("/documents/").mock(side_effect=_capturing_side_effect(captured))
    await client.list_documents(exclude_document_types=["Invoice"])
    assert captured["params"]["document_type__id__none"] == "10"


# ---------------------------------------------------------------------------
# added_after / added_before
# ---------------------------------------------------------------------------

async def test_list_documents_added_date_range(client, mock_router):
    captured: dict = {}
    mock_router.get("/documents/").mock(side_effect=_capturing_side_effect(captured))
    await client.list_documents(added_after="2024-01-01", added_before="2024-12-31")
    assert captured["params"]["added__date__gt"] == "2024-01-01"
    assert captured["params"]["added__date__lt"] == "2024-12-31"


async def test_list_documents_added_after_only(client, mock_router):
    captured: dict = {}
    mock_router.get("/documents/").mock(side_effect=_capturing_side_effect(captured))
    await client.list_documents(added_after="2024-06-01")
    assert captured["params"]["added__date__gt"] == "2024-06-01"
    assert "added__date__lt" not in captured["params"]


# ---------------------------------------------------------------------------
# modified_after / modified_before
# ---------------------------------------------------------------------------

async def test_list_documents_modified_date_range(client, mock_router):
    captured: dict = {}
    mock_router.get("/documents/").mock(side_effect=_capturing_side_effect(captured))
    await client.list_documents(modified_after="2024-03-01", modified_before="2024-09-30")
    assert captured["params"]["modified__date__gt"] == "2024-03-01"
    assert captured["params"]["modified__date__lt"] == "2024-09-30"


# ---------------------------------------------------------------------------
# page_size
# ---------------------------------------------------------------------------

async def test_list_documents_default_page_size(client, mock_router):
    captured: dict = {}
    mock_router.get("/documents/").mock(side_effect=_capturing_side_effect(captured))
    await client.list_documents()
    assert captured["params"]["page_size"] == "25"


async def test_list_documents_custom_page_size(client, mock_router):
    captured: dict = {}
    mock_router.get("/documents/").mock(side_effect=_capturing_side_effect(captured))
    await client.list_documents(page_size=100)
    assert captured["params"]["page_size"] == "100"


# ---------------------------------------------------------------------------
# max_results
# ---------------------------------------------------------------------------

async def test_list_documents_max_results_within_first_page(client, mock_router):
    """max_results smaller than the page — returns only that many docs."""
    many = {
        "count": 5, "next": None, "previous": None,
        "results": [{"id": i, "title": f"Doc{i}", "tags": []} for i in range(1, 6)],
    }
    mock_router.get("/documents/").mock(return_value=Response(200, json=many))
    docs = await client.list_documents(max_results=3)
    assert len(docs) == 3
    assert [d.id for d in docs] == [1, 2, 3]


async def test_list_documents_max_results_stops_pagination(client, mock_router):
    """max_results spanning two pages — fetches second page then stops."""
    page1 = {
        "count": 4,
        "next": "http://paperless.test/api/documents/?page=2",
        "previous": None,
        "results": [{"id": 1, "title": "A", "tags": []}, {"id": 2, "title": "B", "tags": []}],
    }
    page2 = {
        "count": 4, "next": None, "previous": None,
        "results": [{"id": 3, "title": "C", "tags": []}, {"id": 4, "title": "D", "tags": []}],
    }
    call_count = 0

    def side_effect(request):
        nonlocal call_count
        call_count += 1
        return Response(200, json=page1 if call_count == 1 else page2)

    mock_router.get("/documents/").mock(side_effect=side_effect)
    docs = await client.list_documents(max_results=3)
    assert len(docs) == 3
    assert [d.id for d in docs] == [1, 2, 3]
    assert call_count == 2


async def test_list_documents_max_results_exact_first_page(client, mock_router):
    """max_results == first page count — second page must NOT be fetched."""
    page1 = {
        "count": 4,
        "next": "http://paperless.test/api/documents/?page=2",
        "previous": None,
        "results": [{"id": 1, "title": "A", "tags": []}, {"id": 2, "title": "B", "tags": []}],
    }
    call_count = 0

    def side_effect(request):
        nonlocal call_count
        call_count += 1
        return Response(200, json=page1)

    mock_router.get("/documents/").mock(side_effect=side_effect)
    docs = await client.list_documents(max_results=2)
    assert len(docs) == 2
    assert call_count == 1


# ---------------------------------------------------------------------------
# checksum / page / ordering / search_mode=original_filename
# ---------------------------------------------------------------------------

async def test_list_documents_checksum(client, mock_router):
    captured: dict = {}
    mock_router.get("/documents/").mock(side_effect=_capturing_side_effect(captured, DOC_LIST))
    await client.list_documents(checksum="abc123")
    assert captured["params"]["checksum"] == "abc123"


async def test_list_documents_ordering_asc(client, mock_router):
    captured: dict = {}
    mock_router.get("/documents/").mock(side_effect=_capturing_side_effect(captured, DOC_LIST))
    await client.list_documents(ordering="created")
    assert captured["params"]["ordering"] == "created"


async def test_list_documents_ordering_desc(client, mock_router):
    captured: dict = {}
    mock_router.get("/documents/").mock(side_effect=_capturing_side_effect(captured, DOC_LIST))
    await client.list_documents(ordering="created", descending=True)
    assert captured["params"]["ordering"] == "-created"


async def test_list_documents_page(client, mock_router):
    captured: dict = {}
    mock_router.get("/documents/").mock(side_effect=_capturing_side_effect(captured, DOC_LIST))
    docs = await client.list_documents(page=2)
    assert captured["params"]["page"] == "2"
    assert len(docs) == 1


async def test_list_documents_page_suppresses_autopagination(client, mock_router):
    """With page= set, only one request should be made regardless of next."""
    page_resp = {
        "count": 100,
        "next": "http://paperless.test/api/documents/?page=3",
        "previous": None,
        "results": [{"id": 1, "title": "A", "tags": []}],
    }
    call_count = 0

    def side_effect(request):
        nonlocal call_count
        call_count += 1
        return Response(200, json=page_resp)

    mock_router.get("/documents/").mock(side_effect=side_effect)
    docs = await client.list_documents(page=2)
    assert call_count == 1
    assert len(docs) == 1


async def test_list_documents_search_mode_original_filename(client, mock_router):
    captured: dict = {}
    mock_router.get("/documents/").mock(side_effect=_capturing_side_effect(captured, DOC_LIST))
    await client.list_documents(search="invoice.pdf", search_mode="original_filename")
    assert captured["params"]["original_filename__icontains"] == "invoice.pdf"
