"""Tests for PaperlessClient bulk operations."""

from __future__ import annotations

import pytest
import respx
from httpx import Response


async def test_bulk_edit_raw(client, mock_router):
    mock_router.post("/documents/bulk_edit/").mock(return_value=Response(200, json={}))
    await client.bulk_edit([1, 2, 3], "delete")


async def test_bulk_delete(client, mock_router):
    mock_router.post("/documents/bulk_edit/").mock(return_value=Response(200, json={}))
    await client.bulk_delete([1, 2])


async def test_bulk_add_tag_by_id(client, mock_router):
    mock_router.post("/documents/bulk_edit/").mock(return_value=Response(200, json={}))
    await client.bulk_add_tag([1, 2], 5)


async def test_bulk_add_tag_by_name(client, mock_router):
    tags_resp = {"count": 1, "next": None, "previous": None, "results": [{"id": 5, "name": "urgent"}]}
    mock_router.get("/tags/").mock(return_value=Response(200, json=tags_resp))
    mock_router.post("/documents/bulk_edit/").mock(return_value=Response(200, json={}))
    await client.bulk_add_tag([1], "urgent")


async def test_bulk_remove_tag(client, mock_router):
    mock_router.post("/documents/bulk_edit/").mock(return_value=Response(200, json={}))
    await client.bulk_remove_tag([1, 2], 5)


async def test_bulk_modify_tags(client, mock_router):
    mock_router.post("/documents/bulk_edit/").mock(return_value=Response(200, json={}))
    await client.bulk_modify_tags([1, 2], add_tags=[3], remove_tags=[4])


async def test_bulk_edit_objects(client, mock_router):
    mock_router.post("/bulk_edit_objects/").mock(return_value=Response(200, json={}))
    await client.bulk_edit_objects("tags", [1, 2], "delete")
