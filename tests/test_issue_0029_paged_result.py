"""Tests for issue #0029: PagedResult model returned by all list() methods."""

from __future__ import annotations

import respx
from httpx import Response

from easypaperless import PagedResult
from easypaperless.models.documents import Document
from easypaperless.models.tags import Tag
from easypaperless.sync import SyncPaperlessClient

BASE_URL = "http://paperless.test"
API_KEY = "test-api-key"
API_BASE = BASE_URL + "/api"


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

DOC_DATA = {"id": 1, "title": "Invoice", "tags": []}

TAG_DATA = {"id": 1, "name": "invoice"}

SINGLE_PAGE = {
    "count": 1,
    "next": None,
    "previous": None,
    "results": [DOC_DATA],
}

MULTI_PAGE_1 = {
    "count": 3,
    "next": "http://paperless.test/api/documents/?page=2",
    "previous": None,
    "results": [
        {"id": 1, "title": "A", "tags": []},
        {"id": 2, "title": "B", "tags": []},
    ],
}
MULTI_PAGE_2 = {
    "count": 3,
    "next": None,
    "previous": "http://paperless.test/api/documents/?page=1",
    "results": [
        {"id": 3, "title": "C", "tags": []},
    ],
}

TAG_LIST_WITH_ALL = {
    "count": 2,
    "next": None,
    "previous": None,
    "all": [1, 2],
    "results": [TAG_DATA, {"id": 2, "name": "receipt"}],
}

TAG_LIST_WITHOUT_ALL = {
    "count": 1,
    "next": None,
    "previous": None,
    "results": [TAG_DATA],
}


# ---------------------------------------------------------------------------
# PagedResult model unit tests
# ---------------------------------------------------------------------------


def test_paged_result_is_exported_from_top_level():
    """AC: PagedResult is importable from the top-level easypaperless namespace."""
    import easypaperless

    assert hasattr(easypaperless, "PagedResult")
    assert easypaperless.PagedResult is PagedResult


def test_paged_result_fields():
    """AC: PagedResult has count, next, previous, all, results fields."""
    result: PagedResult[int] = PagedResult(
        count=10,
        next="http://example.com/api/?page=2",
        previous=None,
        all=[1, 2, 3],
        results=[1, 2, 3],
    )
    assert result.count == 10
    assert result.next == "http://example.com/api/?page=2"
    assert result.previous is None
    assert result.all == [1, 2, 3]
    assert result.results == [1, 2, 3]


def test_paged_result_defaults():
    """next, previous, and all default to None; results defaults to empty list."""
    result: PagedResult[int] = PagedResult(count=0)
    assert result.next is None
    assert result.previous is None
    assert result.all is None
    assert result.results == []


# ---------------------------------------------------------------------------
# Auto-pagination shape
# ---------------------------------------------------------------------------


async def test_auto_pagination_next_previous_none(client, mock_router):
    """Auto-pagination: next and previous are None in result even though API has next."""
    call_count = 0

    def side_effect(request):
        nonlocal call_count
        call_count += 1
        return Response(200, json=MULTI_PAGE_1 if call_count == 1 else MULTI_PAGE_2)

    mock_router.get("/documents/").mock(side_effect=side_effect)
    result = await client.documents.list()

    assert isinstance(result, PagedResult)
    assert result.count == 3
    assert result.next is None
    assert result.previous is None
    assert len(result.results) == 3
    assert [d.id for d in result.results] == [1, 2, 3]
    assert all(isinstance(d, Document) for d in result.results)


async def test_auto_pagination_count_from_first_page(client, mock_router):
    """Auto-pagination: count reflects the server total from the first page."""
    call_count = 0

    def side_effect(request):
        nonlocal call_count
        call_count += 1
        return Response(200, json=MULTI_PAGE_1 if call_count == 1 else MULTI_PAGE_2)

    mock_router.get("/documents/").mock(side_effect=side_effect)
    result = await client.documents.list()

    assert result.count == 3


# ---------------------------------------------------------------------------
# Single-page shape
# ---------------------------------------------------------------------------


async def test_single_page_next_previous_from_api(client, mock_router):
    """Single page: next and previous come verbatim from the API response."""
    page_resp = {
        "count": 100,
        "next": "http://paperless.test/api/documents/?page=3",
        "previous": "http://paperless.test/api/documents/?page=1",
        "results": [DOC_DATA],
    }
    mock_router.get("/documents/").mock(return_value=Response(200, json=page_resp))
    result = await client.documents.list(page=2)

    assert result.count == 100
    assert result.next == "http://paperless.test/api/documents/?page=3"
    assert result.previous == "http://paperless.test/api/documents/?page=1"
    assert len(result.results) == 1


async def test_single_page_next_none_on_last_page(client, mock_router):
    """Single page: next is None when on the last page."""
    mock_router.get("/documents/").mock(return_value=Response(200, json=SINGLE_PAGE))
    result = await client.documents.list(page=1)

    assert result.next is None


# ---------------------------------------------------------------------------
# max_results truncation shape
# ---------------------------------------------------------------------------


async def test_max_results_count_is_server_total(client, mock_router):
    """max_results: count reflects the server total, not the truncated length."""
    many = {
        "count": 99,
        "next": None,
        "previous": None,
        "results": [{"id": i, "title": f"Doc{i}", "tags": []} for i in range(1, 11)],
    }
    mock_router.get("/documents/").mock(return_value=Response(200, json=many))
    result = await client.documents.list(max_results=3)

    assert result.count == 99
    assert len(result.results) == 3
    assert result.next is None
    assert result.previous is None


async def test_max_results_next_previous_none(client, mock_router):
    """max_results: next and previous are always None even during auto-pagination."""
    call_count = 0

    def side_effect(request):
        nonlocal call_count
        call_count += 1
        return Response(200, json=MULTI_PAGE_1 if call_count == 1 else MULTI_PAGE_2)

    mock_router.get("/documents/").mock(side_effect=side_effect)
    result = await client.documents.list(max_results=2)

    assert result.next is None
    assert result.previous is None
    assert len(result.results) == 2


# ---------------------------------------------------------------------------
# `all` field present vs absent
# ---------------------------------------------------------------------------


async def test_all_field_present(client, mock_router):
    """all field is populated when the API response includes it."""
    mock_router.get("/tags/").mock(return_value=Response(200, json=TAG_LIST_WITH_ALL))
    result = await client.tags.list()

    assert result.all == [1, 2]


async def test_all_field_absent(client, mock_router):
    """all field is None when the API response does not include it."""
    mock_router.get("/tags/").mock(return_value=Response(200, json=TAG_LIST_WITHOUT_ALL))
    result = await client.tags.list()

    assert result.all is None


# ---------------------------------------------------------------------------
# Return type for all resources (smoke tests)
# ---------------------------------------------------------------------------


async def test_tags_list_returns_paged_result(client, mock_router):
    mock_router.get("/tags/").mock(return_value=Response(200, json=TAG_LIST_WITHOUT_ALL))
    result = await client.tags.list()
    assert isinstance(result, PagedResult)
    assert isinstance(result.results[0], Tag)


async def test_correspondents_list_returns_paged_result(client, mock_router):
    from easypaperless.models.correspondents import Correspondent

    data = {"count": 1, "next": None, "previous": None, "results": [{"id": 1, "name": "ACME"}]}
    mock_router.get("/correspondents/").mock(return_value=Response(200, json=data))
    result = await client.correspondents.list()
    assert isinstance(result, PagedResult)
    assert isinstance(result.results[0], Correspondent)


async def test_document_types_list_returns_paged_result(client, mock_router):
    from easypaperless.models.document_types import DocumentType

    data = {"count": 1, "next": None, "previous": None, "results": [{"id": 1, "name": "Invoice"}]}
    mock_router.get("/document_types/").mock(return_value=Response(200, json=data))
    result = await client.document_types.list()
    assert isinstance(result, PagedResult)
    assert isinstance(result.results[0], DocumentType)


async def test_storage_paths_list_returns_paged_result(client, mock_router):
    from easypaperless.models.storage_paths import StoragePath

    data = {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [{"id": 1, "name": "Archive", "path": "/archive/{title}"}],
    }
    mock_router.get("/storage_paths/").mock(return_value=Response(200, json=data))
    result = await client.storage_paths.list()
    assert isinstance(result, PagedResult)
    assert isinstance(result.results[0], StoragePath)


async def test_custom_fields_list_returns_paged_result(client, mock_router):
    from easypaperless.models.custom_fields import CustomField

    data = {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [{"id": 1, "name": "Amount", "data_type": "string"}],
    }
    mock_router.get("/custom_fields/").mock(return_value=Response(200, json=data))
    result = await client.custom_fields.list()
    assert isinstance(result, PagedResult)
    assert isinstance(result.results[0], CustomField)


async def test_documents_list_returns_paged_result(client, mock_router):
    mock_router.get("/documents/").mock(return_value=Response(200, json=SINGLE_PAGE))
    result = await client.documents.list()
    assert isinstance(result, PagedResult)
    assert isinstance(result.results[0], Document)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_paged_result_count_zero():
    """count=0 with empty results is a valid state (no matching items)."""
    result: PagedResult[int] = PagedResult(count=0, results=[])
    assert result.count == 0
    assert result.results == []
    assert result.next is None
    assert result.previous is None
    assert result.all is None


def test_paged_result_generic_type_variance():
    """PagedResult[Tag] is an instance of PagedResult regardless of type param."""
    tag = Tag(id=1, name="test")
    result: PagedResult[Tag] = PagedResult(count=1, results=[tag])
    assert isinstance(result, PagedResult)
    assert result.results[0] is tag


# ---------------------------------------------------------------------------
# Sync client — smoke tests (all 6 resources return PagedResult)
# ---------------------------------------------------------------------------


def test_sync_documents_list_returns_paged_result():
    with respx.mock(base_url=API_BASE, assert_all_called=False) as router:
        router.get("/documents/").mock(return_value=Response(200, json=SINGLE_PAGE))
        with SyncPaperlessClient(url=BASE_URL, api_token=API_KEY) as client:
            result = client.documents.list()
    assert isinstance(result, PagedResult)
    assert isinstance(result.results[0], Document)


def test_sync_tags_list_returns_paged_result():
    with respx.mock(base_url=API_BASE, assert_all_called=False) as router:
        router.get("/tags/").mock(return_value=Response(200, json=TAG_LIST_WITHOUT_ALL))
        with SyncPaperlessClient(url=BASE_URL, api_token=API_KEY) as client:
            result = client.tags.list()
    assert isinstance(result, PagedResult)
    assert isinstance(result.results[0], Tag)


def test_sync_correspondents_list_returns_paged_result():
    from easypaperless.models.correspondents import Correspondent

    data = {"count": 1, "next": None, "previous": None, "results": [{"id": 1, "name": "ACME"}]}
    with respx.mock(base_url=API_BASE, assert_all_called=False) as router:
        router.get("/correspondents/").mock(return_value=Response(200, json=data))
        with SyncPaperlessClient(url=BASE_URL, api_token=API_KEY) as client:
            result = client.correspondents.list()
    assert isinstance(result, PagedResult)
    assert isinstance(result.results[0], Correspondent)


def test_sync_document_types_list_returns_paged_result():
    from easypaperless.models.document_types import DocumentType

    data = {"count": 1, "next": None, "previous": None, "results": [{"id": 1, "name": "Invoice"}]}
    with respx.mock(base_url=API_BASE, assert_all_called=False) as router:
        router.get("/document_types/").mock(return_value=Response(200, json=data))
        with SyncPaperlessClient(url=BASE_URL, api_token=API_KEY) as client:
            result = client.document_types.list()
    assert isinstance(result, PagedResult)
    assert isinstance(result.results[0], DocumentType)


def test_sync_storage_paths_list_returns_paged_result():
    from easypaperless.models.storage_paths import StoragePath

    data = {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [{"id": 1, "name": "Archive", "path": "/archive/{title}"}],
    }
    with respx.mock(base_url=API_BASE, assert_all_called=False) as router:
        router.get("/storage_paths/").mock(return_value=Response(200, json=data))
        with SyncPaperlessClient(url=BASE_URL, api_token=API_KEY) as client:
            result = client.storage_paths.list()
    assert isinstance(result, PagedResult)
    assert isinstance(result.results[0], StoragePath)


def test_sync_custom_fields_list_returns_paged_result():
    from easypaperless.models.custom_fields import CustomField

    data = {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [{"id": 1, "name": "Amount", "data_type": "string"}],
    }
    with respx.mock(base_url=API_BASE, assert_all_called=False) as router:
        router.get("/custom_fields/").mock(return_value=Response(200, json=data))
        with SyncPaperlessClient(url=BASE_URL, api_token=API_KEY) as client:
            result = client.custom_fields.list()
    assert isinstance(result, PagedResult)
    assert isinstance(result.results[0], CustomField)


# ---------------------------------------------------------------------------
# Sync client — pagination shape tests
# ---------------------------------------------------------------------------


def test_sync_auto_pagination_next_previous_none():
    """Sync auto-pagination: next and previous are None even when API has next."""
    call_count = 0

    def side_effect(request):
        nonlocal call_count
        call_count += 1
        return Response(200, json=MULTI_PAGE_1 if call_count == 1 else MULTI_PAGE_2)

    with respx.mock(base_url=API_BASE, assert_all_called=False) as router:
        router.get("/documents/").mock(side_effect=side_effect)
        with SyncPaperlessClient(url=BASE_URL, api_token=API_KEY) as client:
            result = client.documents.list()

    assert isinstance(result, PagedResult)
    assert result.count == 3
    assert result.next is None
    assert result.previous is None
    assert len(result.results) == 3
    assert [d.id for d in result.results] == [1, 2, 3]


def test_sync_single_page_next_previous_from_api():
    """Sync single page: next and previous come verbatim from the API response."""
    page_resp = {
        "count": 100,
        "next": "http://paperless.test/api/documents/?page=3",
        "previous": "http://paperless.test/api/documents/?page=1",
        "results": [DOC_DATA],
    }
    with respx.mock(base_url=API_BASE, assert_all_called=False) as router:
        router.get("/documents/").mock(return_value=Response(200, json=page_resp))
        with SyncPaperlessClient(url=BASE_URL, api_token=API_KEY) as client:
            result = client.documents.list(page=2)

    assert result.count == 100
    assert result.next == "http://paperless.test/api/documents/?page=3"
    assert result.previous == "http://paperless.test/api/documents/?page=1"
    assert len(result.results) == 1


def test_sync_max_results_count_is_server_total():
    """Sync max_results: count reflects the server total, not the truncated length."""
    many = {
        "count": 99,
        "next": None,
        "previous": None,
        "results": [{"id": i, "title": f"Doc{i}", "tags": []} for i in range(1, 11)],
    }
    with respx.mock(base_url=API_BASE, assert_all_called=False) as router:
        router.get("/documents/").mock(return_value=Response(200, json=many))
        with SyncPaperlessClient(url=BASE_URL, api_token=API_KEY) as client:
            result = client.documents.list(max_results=3)

    assert result.count == 99
    assert len(result.results) == 3
    assert result.next is None
    assert result.previous is None
