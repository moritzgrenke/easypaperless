"""Tests for PaperlessClient document methods."""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from easypaperless.models.documents import Document

DOC_DATA = {"id": 1, "title": "Test Document", "tags": []}
DOC_LIST = {
    "count": 1,
    "next": None,
    "previous": None,
    "results": [DOC_DATA],
}


async def test_get_document(client, mock_router):
    mock_router.get("/documents/1/").mock(return_value=Response(200, json=DOC_DATA))
    doc = await client.get_document(1)
    assert isinstance(doc, Document)
    assert doc.id == 1
    assert doc.title == "Test Document"


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
    docs = await client.list_documents(asn=42)
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
