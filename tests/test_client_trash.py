"""Tests for PaperlessClient and SyncPaperlessClient trash resource."""

from __future__ import annotations

import json

import respx
from httpx import Response

from easypaperless import Document
from easypaperless.sync import SyncPaperlessClient

BASE_URL = "http://paperless.test"
API_BASE = BASE_URL + "/api"
API_KEY = "test-api-key"

DOCUMENT_DATA = {
    "id": 42,
    "title": "Old Invoice",
    "content": "",
    "tags": [],
    "document_type": None,
    "correspondent": None,
    "created": "2024-01-15",
    "created_date": "2024-01-15",
    "modified": "2024-06-01T10:00:00Z",
    "added": "2024-06-01T10:00:00Z",
    "archive_serial_number": None,
    "original_file_name": "invoice.pdf",
    "archived_file_name": None,
    "owner": None,
    "notes": [],
    "custom_fields": [],
    "storage_path": None,
    "is_shared_by_requester": False,
    "set_permissions": None,
    "permissions": None,
    "search_hit": None,
}
TRASH_LIST = {"count": 1, "next": None, "previous": None, "results": [DOCUMENT_DATA]}


# ---------------------------------------------------------------------------
# Async list
# ---------------------------------------------------------------------------


async def test_trash_list_default(client, mock_router):
    mock_router.get("/trash/").mock(return_value=Response(200, json=TRASH_LIST))
    result = await client.trash.list()
    assert result.count == 1
    assert isinstance(result.results[0], Document)
    assert result.results[0].id == 42


async def test_trash_list_with_pagination(client, mock_router):
    captured: dict = {}

    def _side_effect(request):
        captured["params"] = dict(request.url.params)
        return Response(200, json=TRASH_LIST)

    mock_router.get("/trash/").mock(side_effect=_side_effect)
    await client.trash.list(page=2, page_size=10)
    assert captured["params"]["page"] == "2"
    assert captured["params"]["page_size"] == "10"


async def test_trash_list_no_params_sent_by_default(client, mock_router):
    captured: dict = {}

    def _side_effect(request):
        captured["params"] = dict(request.url.params)
        return Response(200, json=TRASH_LIST)

    mock_router.get("/trash/").mock(side_effect=_side_effect)
    await client.trash.list()
    assert captured["params"] == {}


# ---------------------------------------------------------------------------
# Async restore
# ---------------------------------------------------------------------------


async def test_trash_restore(client, mock_router):
    captured: dict = {}

    def _side_effect(request):
        captured["body"] = json.loads(request.content)
        return Response(200)

    mock_router.post("/trash/").mock(side_effect=_side_effect)
    result = await client.trash.restore(document_ids=[1, 2])
    assert result is None
    assert captured["body"] == {"documents": [1, 2], "action": "restore"}


# ---------------------------------------------------------------------------
# Async empty
# ---------------------------------------------------------------------------


async def test_trash_empty(client, mock_router):
    captured: dict = {}

    def _side_effect(request):
        captured["body"] = json.loads(request.content)
        return Response(200)

    mock_router.post("/trash/").mock(side_effect=_side_effect)
    result = await client.trash.empty(document_ids=[3])
    assert result is None
    assert captured["body"] == {"documents": [3], "action": "empty"}


# ---------------------------------------------------------------------------
# Sync resource
# ---------------------------------------------------------------------------


def test_sync_trash_list():
    with respx.mock(base_url=API_BASE, assert_all_called=False) as router:
        router.get("/trash/").mock(return_value=Response(200, json=TRASH_LIST))
        with SyncPaperlessClient(url=BASE_URL, api_token=API_KEY) as client:
            result = client.trash.list()
    assert result.count == 1
    assert isinstance(result.results[0], Document)


def test_sync_trash_restore():
    with respx.mock(base_url=API_BASE, assert_all_called=False) as router:
        router.post("/trash/").mock(return_value=Response(200))
        with SyncPaperlessClient(url=BASE_URL, api_token=API_KEY) as client:
            result = client.trash.restore(document_ids=[1, 2])
    assert result is None


def test_sync_trash_empty():
    with respx.mock(base_url=API_BASE, assert_all_called=False) as router:
        router.post("/trash/").mock(return_value=Response(200))
        with SyncPaperlessClient(url=BASE_URL, api_token=API_KEY) as client:
            result = client.trash.empty(document_ids=[3])
    assert result is None


# ---------------------------------------------------------------------------
# Public API / attribute checks
# ---------------------------------------------------------------------------


def test_trash_resource_on_async_client(client):
    from easypaperless._internal.resources.trash import TrashResource

    assert isinstance(client.trash, TrashResource)


def test_trash_resource_on_sync_client():
    from easypaperless._internal.sync_resources.trash import SyncTrashResource

    with respx.mock(base_url=API_BASE, assert_all_called=False):
        with SyncPaperlessClient(url=BASE_URL, api_token=API_KEY) as client:
            assert isinstance(client.trash, SyncTrashResource)
