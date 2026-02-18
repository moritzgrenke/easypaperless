"""Tests for PaperlessClient tag and other resource CRUD methods."""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from easypaperless.models.tags import Tag
from easypaperless.models.correspondents import Correspondent
from easypaperless.models.document_types import DocumentType
from easypaperless.models.storage_paths import StoragePath
from easypaperless.models.custom_fields import CustomField


TAG_DATA = {"id": 1, "name": "invoice"}
TAG_LIST = {"count": 1, "next": None, "previous": None, "results": [TAG_DATA]}


async def test_list_tags(client, mock_router):
    mock_router.get("/tags/").mock(return_value=Response(200, json=TAG_LIST))
    tags = await client.list_tags()
    assert len(tags) == 1
    assert isinstance(tags[0], Tag)
    assert tags[0].name == "invoice"


async def test_get_tag(client, mock_router):
    mock_router.get("/tags/1/").mock(return_value=Response(200, json=TAG_DATA))
    tag = await client.get_tag(1)
    assert tag.id == 1


async def test_create_tag(client, mock_router):
    mock_router.post("/tags/").mock(return_value=Response(201, json=TAG_DATA))
    tag = await client.create_tag(name="invoice")
    assert tag.name == "invoice"


async def test_update_tag(client, mock_router):
    mock_router.patch("/tags/1/").mock(return_value=Response(200, json={**TAG_DATA, "name": "receipt"}))
    tag = await client.update_tag(1, name="receipt")
    assert tag.name == "receipt"


async def test_delete_tag(client, mock_router):
    mock_router.delete("/tags/1/").mock(return_value=Response(204))
    await client.delete_tag(1)


async def test_create_tag_invalidates_cache(client, mock_router):
    mock_router.get("/tags/").mock(return_value=Response(200, json=TAG_LIST))
    mock_router.post("/tags/").mock(return_value=Response(201, json={"id": 2, "name": "new"}))
    # Load cache
    await client.list_tags()
    # Create invalidates
    await client.create_tag(name="new")
    assert "tags" not in client._resolver._cache


# Correspondents
CORR_DATA = {"id": 1, "name": "ACME"}
CORR_LIST = {"count": 1, "next": None, "previous": None, "results": [CORR_DATA]}


async def test_list_correspondents(client, mock_router):
    mock_router.get("/correspondents/").mock(return_value=Response(200, json=CORR_LIST))
    corrs = await client.list_correspondents()
    assert isinstance(corrs[0], Correspondent)


async def test_create_correspondent(client, mock_router):
    mock_router.post("/correspondents/").mock(return_value=Response(201, json=CORR_DATA))
    c = await client.create_correspondent(name="ACME")
    assert c.name == "ACME"


# Document Types
DT_DATA = {"id": 1, "name": "Invoice"}
DT_LIST = {"count": 1, "next": None, "previous": None, "results": [DT_DATA]}


async def test_list_document_types(client, mock_router):
    mock_router.get("/document_types/").mock(return_value=Response(200, json=DT_LIST))
    dts = await client.list_document_types()
    assert isinstance(dts[0], DocumentType)


async def test_create_document_type(client, mock_router):
    mock_router.post("/document_types/").mock(return_value=Response(201, json=DT_DATA))
    dt = await client.create_document_type(name="Invoice")
    assert dt.name == "Invoice"


# Storage Paths
SP_DATA = {"id": 1, "name": "Archive", "path": "/docs/{created_year}/"}
SP_LIST = {"count": 1, "next": None, "previous": None, "results": [SP_DATA]}


async def test_list_storage_paths(client, mock_router):
    mock_router.get("/storage_paths/").mock(return_value=Response(200, json=SP_LIST))
    sps = await client.list_storage_paths()
    assert isinstance(sps[0], StoragePath)
    assert sps[0].path == "/docs/{created_year}/"


# Custom Fields
CF_DATA = {"id": 1, "name": "Amount", "data_type": "monetary"}
CF_LIST = {"count": 1, "next": None, "previous": None, "results": [CF_DATA]}


async def test_list_custom_fields(client, mock_router):
    mock_router.get("/custom_fields/").mock(return_value=Response(200, json=CF_LIST))
    cfs = await client.list_custom_fields()
    assert isinstance(cfs[0], CustomField)


async def test_create_custom_field(client, mock_router):
    mock_router.post("/custom_fields/").mock(return_value=Response(201, json=CF_DATA))
    cf = await client.create_custom_field(name="Amount", data_type="monetary")
    assert cf.data_type.value == "monetary"
