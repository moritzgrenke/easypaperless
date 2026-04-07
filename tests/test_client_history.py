"""Tests for PaperlessClient document history method."""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from easypaperless.exceptions import NotFoundError
from easypaperless.models.documents import AuditLogActor, AuditLogEntry
from easypaperless.models.paged_result import PagedResult
from easypaperless.sync import SyncPaperlessClient

BASE_URL = "http://paperless.test"
API_KEY = "test-api-key"
API_BASE = BASE_URL + "/api"

ENTRY_WITH_ACTOR = {
    "id": 10,
    "timestamp": "2026-03-26T10:01:03.337428Z",
    "action": "update",
    "changes": {"tags": {"type": "m2m", "objects": ["API_edited"], "operation": "add"}},
    "actor": {"id": 4, "username": "claude-ki"},
}

ENTRY_NO_ACTOR = {
    "id": 1,
    "timestamp": "2026-02-20T16:36:09.921144Z",
    "action": "create",
    "changes": {"id": ["None", "1"], "title": ["None", "Some Doc"]},
    "actor": None,
}

PLAIN_ARRAY_RESPONSE = [ENTRY_WITH_ACTOR, ENTRY_NO_ACTOR]
PLAIN_ARRAY_EMPTY: list[dict] = []


# ---------------------------------------------------------------------------
# Plain-array response (actual paperless-ngx behaviour)
# ---------------------------------------------------------------------------


async def test_history_returns_paged_result(client, mock_router):
    mock_router.get("/documents/1/history/").mock(
        return_value=Response(200, json=PLAIN_ARRAY_RESPONSE)
    )
    result = await client.documents.history(1)
    assert isinstance(result, PagedResult)
    assert result.count == 2
    assert len(result.results) == 2


async def test_history_entry_with_actor(client, mock_router):
    mock_router.get("/documents/1/history/").mock(
        return_value=Response(200, json=PLAIN_ARRAY_RESPONSE)
    )
    result = await client.documents.history(1)
    entry = result.results[0]
    assert isinstance(entry, AuditLogEntry)
    assert entry.id == 10
    assert entry.action == "update"
    assert isinstance(entry.actor, AuditLogActor)
    assert entry.actor.id == 4
    assert entry.actor.username == "claude-ki"


async def test_history_entry_no_actor(client, mock_router):
    """Regression: actor=None (system-generated entry) must not raise."""
    mock_router.get("/documents/1/history/").mock(
        return_value=Response(200, json=PLAIN_ARRAY_RESPONSE)
    )
    result = await client.documents.history(1)
    entry = result.results[1]
    assert isinstance(entry, AuditLogEntry)
    assert entry.actor is None


async def test_history_empty(client, mock_router):
    mock_router.get("/documents/1/history/").mock(
        return_value=Response(200, json=PLAIN_ARRAY_EMPTY)
    )
    result = await client.documents.history(1)
    assert isinstance(result, PagedResult)
    assert result.count == 0
    assert result.results == []
    assert result.all is None


async def test_history_all_ids_populated(client, mock_router):
    mock_router.get("/documents/1/history/").mock(
        return_value=Response(200, json=PLAIN_ARRAY_RESPONSE)
    )
    result = await client.documents.history(1)
    assert result.all == [10, 1]


async def test_history_pagination_params_forwarded(client, mock_router):
    mock_router.get("/documents/1/history/").mock(
        return_value=Response(200, json=PLAIN_ARRAY_RESPONSE)
    )
    result = await client.documents.history(1, page=1, page_size=10)
    assert isinstance(result, PagedResult)
    assert result.count == 2


async def test_history_not_found(client, mock_router):
    mock_router.get("/documents/999/history/").mock(
        return_value=Response(404, json={"detail": "Not found."})
    )
    with pytest.raises(NotFoundError):
        await client.documents.history(999)


# ---------------------------------------------------------------------------
# Sync client
# ---------------------------------------------------------------------------


def test_sync_history_returns_paged_result():
    with respx.mock(base_url=API_BASE, assert_all_called=False) as router:
        router.get("/documents/1/history/").mock(
            return_value=Response(200, json=PLAIN_ARRAY_RESPONSE)
        )
        with SyncPaperlessClient(url=BASE_URL, api_token=API_KEY) as client:
            result = client.documents.history(1)
    assert isinstance(result, PagedResult)
    assert result.count == 2
    assert len(result.results) == 2


def test_sync_history_entry_no_actor():
    with respx.mock(base_url=API_BASE, assert_all_called=False) as router:
        router.get("/documents/1/history/").mock(
            return_value=Response(200, json=PLAIN_ARRAY_RESPONSE)
        )
        with SyncPaperlessClient(url=BASE_URL, api_token=API_KEY) as client:
            result = client.documents.history(1)
    assert result.results[1].actor is None


def test_sync_history_empty():
    with respx.mock(base_url=API_BASE, assert_all_called=False) as router:
        router.get("/documents/1/history/").mock(return_value=Response(200, json=PLAIN_ARRAY_EMPTY))
        with SyncPaperlessClient(url=BASE_URL, api_token=API_KEY) as client:
            result = client.documents.history(1)
    assert result.count == 0
    assert result.results == []
