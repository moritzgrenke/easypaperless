"""Tests for HttpSession — error mapping and pagination."""

from __future__ import annotations

import httpx
import pytest
import respx
from httpx import Response

from easypaperless._internal.http import HttpSession
from easypaperless.exceptions import (
    AuthError,
    NotFoundError,
    PaperlessError,
    ServerError,
    ValidationError,
)

BASE_URL = "http://paperless.test"


@pytest.fixture
async def session():
    s = HttpSession(base_url=BASE_URL, api_key="key")
    yield s
    await s.close()


@pytest.mark.parametrize(
    "status_code,exc_class",
    [
        (401, AuthError),
        (403, AuthError),
        (404, NotFoundError),
        (422, ValidationError),
        (500, ServerError),
        (503, ServerError),
    ],
)
async def test_error_mapping(session, status_code, exc_class):
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.get("/test/").mock(return_value=Response(status_code, json={"detail": "error"}))
        with pytest.raises(exc_class) as exc_info:
            await session.get("/test/")
        assert exc_info.value.status_code == status_code


async def test_other_4xx_raises_paperless_error(session):
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.get("/test/").mock(return_value=Response(409, json={"detail": "conflict"}))
        with pytest.raises(PaperlessError) as exc_info:
            await session.get("/test/")
        assert exc_info.value.status_code == 409


async def test_successful_get(session):
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.get("/things/").mock(return_value=Response(200, json={"id": 1}))
        resp = await session.get("/things/")
        assert resp.json() == {"id": 1}


async def test_get_all_pages_single_page(session):
    data = {"count": 2, "next": None, "previous": None, "results": [{"id": 1}, {"id": 2}]}
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.get("/items/").mock(return_value=Response(200, json=data))
        results = await session.get_all_pages("/items/")
    assert len(results) == 2
    assert results[0]["id"] == 1


async def test_get_all_pages_multiple_pages(session):
    page1 = {
        "count": 4,
        "next": BASE_URL + "/api/items/?page=2",
        "previous": None,
        "results": [{"id": 1}, {"id": 2}],
    }
    page2 = {
        "count": 4,
        "next": None,
        "previous": BASE_URL + "/api/items/",
        "results": [{"id": 3}, {"id": 4}],
    }
    call_count = 0

    def side_effect(request):
        nonlocal call_count
        call_count += 1
        return Response(200, json=page1 if call_count == 1 else page2)

    with respx.mock(assert_all_called=False) as router:
        router.get(BASE_URL + "/api/items/").mock(side_effect=side_effect)
        results = await session.get_all_pages("/items/")
    assert len(results) == 4
    assert [r["id"] for r in results] == [1, 2, 3, 4]


async def test_status_code_stored_on_error(session):
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.get("/x/").mock(return_value=Response(404, json={"detail": "gone"}))
        with pytest.raises(NotFoundError) as exc_info:
            await session.get("/x/")
        assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# get_all_pages — max_results
# ---------------------------------------------------------------------------


async def test_get_all_pages_max_results_trims_single_page(session):
    """max_results smaller than one page — trims result, does not follow next."""
    data = {
        "count": 10,
        "next": BASE_URL + "/api/items/?page=2",
        "previous": None,
        "results": [{"id": i} for i in range(1, 6)],
    }
    call_count = 0

    def side_effect(request):
        nonlocal call_count
        call_count += 1
        return Response(200, json=data)

    with respx.mock(assert_all_called=False) as router:
        router.get(BASE_URL + "/api/items/").mock(side_effect=side_effect)
        results = await session.get_all_pages("/items/", max_results=3)

    assert len(results) == 3
    assert [r["id"] for r in results] == [1, 2, 3]
    assert call_count == 1  # second page must NOT be fetched


async def test_get_all_pages_max_results_exact_page_size(session):
    """max_results == page size — stops after one page even with a next URL."""
    data = {
        "count": 6,
        "next": BASE_URL + "/api/items/?page=2",
        "previous": None,
        "results": [{"id": 1}, {"id": 2}],
    }
    call_count = 0

    def side_effect(request):
        nonlocal call_count
        call_count += 1
        return Response(200, json=data)

    with respx.mock(assert_all_called=False) as router:
        router.get(BASE_URL + "/api/items/").mock(side_effect=side_effect)
        results = await session.get_all_pages("/items/", max_results=2)

    assert len(results) == 2
    assert call_count == 1


async def test_get_all_pages_max_results_across_pages(session):
    """max_results spanning two pages — fetches second page then stops."""
    page1 = {
        "count": 6,
        "next": BASE_URL + "/api/items/?page=2",
        "previous": None,
        "results": [{"id": 1}, {"id": 2}],
    }
    page2 = {
        "count": 6,
        "next": None,
        "previous": None,
        "results": [{"id": 3}, {"id": 4}],
    }
    call_count = 0

    def side_effect(request):
        nonlocal call_count
        call_count += 1
        return Response(200, json=page1 if call_count == 1 else page2)

    with respx.mock(assert_all_called=False) as router:
        router.get(BASE_URL + "/api/items/").mock(side_effect=side_effect)
        results = await session.get_all_pages("/items/", max_results=3)

    assert len(results) == 3
    assert [r["id"] for r in results] == [1, 2, 3]
    assert call_count == 2


async def test_get_all_pages_no_max_results_fetches_all(session):
    """Without max_results, all pages are still fetched (regression guard)."""
    page1 = {
        "count": 4,
        "next": BASE_URL + "/api/items/?page=2",
        "previous": None,
        "results": [{"id": 1}, {"id": 2}],
    }
    page2 = {
        "count": 4,
        "next": None,
        "previous": None,
        "results": [{"id": 3}, {"id": 4}],
    }
    call_count = 0

    def side_effect(request):
        nonlocal call_count
        call_count += 1
        return Response(200, json=page1 if call_count == 1 else page2)

    with respx.mock(assert_all_called=False) as router:
        router.get(BASE_URL + "/api/items/").mock(side_effect=side_effect)
        results = await session.get_all_pages("/items/")

    assert len(results) == 4
    assert call_count == 2


# ---------------------------------------------------------------------------
# get_download
# ---------------------------------------------------------------------------


async def test_get_download_simple(session):
    """get_download returns response for a non-redirected download."""
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.get("/documents/1/download/").mock(
            return_value=Response(200, content=b"file-bytes"),
        )
        resp = await session.get_download("/documents/1/download/")
    assert resp.status_code == 200
    assert resp.content == b"file-bytes"


async def test_get_download_follows_redirects(session):
    """get_download follows redirect hops and re-attaches auth."""
    call_count = 0

    def side_effect(request):
        nonlocal call_count
        call_count += 1
        # Verify auth header is present on every hop
        assert "Authorization" in request.headers
        if call_count == 1:
            return Response(302, headers={"location": BASE_URL + "/media/doc.pdf"})
        return Response(200, content=b"pdf-data")

    with respx.mock(assert_all_called=False) as router:
        router.get(BASE_URL + "/api/documents/1/download/").mock(side_effect=side_effect)
        router.get(BASE_URL + "/media/doc.pdf").mock(side_effect=side_effect)
        resp = await session.get_download("/documents/1/download/")
    assert resp.status_code == 200
    assert resp.content == b"pdf-data"
    assert call_count == 2


async def test_get_download_aborts_after_5_hops(session):
    """get_download stops after 5 redirect hops and raises PaperlessError."""
    call_count = 0

    def redirect_forever(request):
        nonlocal call_count
        call_count += 1
        return Response(302, headers={"location": BASE_URL + "/api/loop/"})

    with respx.mock(assert_all_called=False) as router:
        router.get(BASE_URL + "/api/loop/").mock(side_effect=redirect_forever)
        with pytest.raises(PaperlessError) as exc_info:
            await session.get_download("/loop/")
    # 1 initial request + 5 redirect hops = 6 total calls
    assert call_count == 6
    assert exc_info.value.status_code == 302


async def test_get_download_timeout_raises_server_error(session):
    """get_download wraps TimeoutException as ServerError."""
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.get("/documents/1/download/").mock(
            side_effect=httpx.ReadTimeout("timed out"),
        )
        with pytest.raises(ServerError, match="timed out"):
            await session.get_download("/documents/1/download/")


async def test_get_download_http_error_raises_server_error(session):
    """get_download wraps generic HTTPError as ServerError."""
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.get("/documents/1/download/").mock(
            side_effect=httpx.ConnectError("connection refused"),
        )
        with pytest.raises(ServerError, match="connection refused"):
            await session.get_download("/documents/1/download/")


async def test_get_download_redirect_timeout_raises_server_error(session):
    """get_download wraps TimeoutException during a redirect hop as ServerError."""
    call_count = 0

    def side_effect(request):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return Response(302, headers={"location": BASE_URL + "/media/doc.pdf"})
        raise httpx.ReadTimeout("redirect timed out")

    with respx.mock(assert_all_called=False) as router:
        router.get(BASE_URL + "/api/documents/1/download/").mock(side_effect=side_effect)
        router.get(BASE_URL + "/media/doc.pdf").mock(side_effect=side_effect)
        with pytest.raises(ServerError, match="timed out"):
            await session.get_download("/documents/1/download/")


async def test_get_download_redirect_http_error_raises_server_error(session):
    """get_download wraps HTTPError during a redirect hop as ServerError."""
    call_count = 0

    def side_effect(request):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return Response(302, headers={"location": BASE_URL + "/media/doc.pdf"})
        raise httpx.ConnectError("connection lost")

    with respx.mock(assert_all_called=False) as router:
        router.get(BASE_URL + "/api/documents/1/download/").mock(side_effect=side_effect)
        router.get(BASE_URL + "/media/doc.pdf").mock(side_effect=side_effect)
        with pytest.raises(ServerError, match="connection lost"):
            await session.get_download("/documents/1/download/")


# ---------------------------------------------------------------------------
# Transport error paths in request()
# ---------------------------------------------------------------------------


async def test_request_timeout_raises_server_error(session):
    """request() wraps httpx.TimeoutException as ServerError."""
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.get("/test/").mock(side_effect=httpx.ReadTimeout("read timed out"))
        with pytest.raises(ServerError, match="Request timed out"):
            await session.get("/test/")


async def test_request_http_error_raises_server_error(session):
    """request() wraps httpx.HTTPError as ServerError."""
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.get("/test/").mock(side_effect=httpx.ConnectError("refused"))
        with pytest.raises(ServerError, match="refused"):
            await session.get("/test/")


# ---------------------------------------------------------------------------
# Non-JSON error body fallback
# ---------------------------------------------------------------------------


async def test_error_non_json_body_fallback(session):
    """_raise_for_status falls back to response.text when body is not JSON."""
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.get("/test/").mock(
            return_value=Response(500, text="Internal Server Error"),
        )
        with pytest.raises(ServerError, match="Internal Server Error"):
            await session.get("/test/")


# ---------------------------------------------------------------------------
# on_page callback in get_all_pages
# ---------------------------------------------------------------------------


async def test_get_all_pages_on_page_callback_single_page(session):
    """on_page is called with (fetched_count, total_count) on a single page."""
    data = {"count": 2, "next": None, "results": [{"id": 1}, {"id": 2}]}
    callback_calls: list[tuple[int, int | None]] = []

    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.get("/items/").mock(return_value=Response(200, json=data))
        await session.get_all_pages("/items/", on_page=lambda f, t: callback_calls.append((f, t)))

    assert callback_calls == [(2, 2)]


async def test_get_all_pages_on_page_callback_multiple_pages(session):
    """on_page is called after each page with cumulative fetched count."""
    page1 = {"count": 4, "next": BASE_URL + "/api/items/?page=2", "results": [{"id": 1}, {"id": 2}]}
    page2 = {"count": 4, "next": None, "results": [{"id": 3}, {"id": 4}]}
    call_count = 0
    callback_calls: list[tuple[int, int | None]] = []

    def side_effect(request):
        nonlocal call_count
        call_count += 1
        return Response(200, json=page1 if call_count == 1 else page2)

    with respx.mock(assert_all_called=False) as router:
        router.get(BASE_URL + "/api/items/").mock(side_effect=side_effect)
        await session.get_all_pages("/items/", on_page=lambda f, t: callback_calls.append((f, t)))

    assert callback_calls == [(2, 4), (4, 4)]


# ---------------------------------------------------------------------------
# Convenience methods: post, patch, delete
# ---------------------------------------------------------------------------


async def test_post_delegates_to_request(session):
    """post() delegates to request() correctly."""
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.post("/things/").mock(return_value=Response(201, json={"id": 1}))
        resp = await session.post("/things/", json={"name": "new"})
    assert resp.status_code == 201
    assert resp.json() == {"id": 1}


async def test_patch_delegates_to_request(session):
    """patch() delegates to request() correctly."""
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.patch("/things/1/").mock(
            return_value=Response(200, json={"id": 1, "name": "updated"}),
        )
        resp = await session.patch("/things/1/", json={"name": "updated"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "updated"


async def test_delete_delegates_to_request(session):
    """delete() delegates to request() correctly."""
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.delete("/things/1/").mock(return_value=Response(204))
        resp = await session.delete("/things/1/")
    assert resp.status_code == 204


# ---------------------------------------------------------------------------
# get_all_pages — transport errors on next-page fetch
# ---------------------------------------------------------------------------


async def test_get_all_pages_next_page_timeout(session):
    """get_all_pages wraps TimeoutException on next-page fetch as ServerError."""
    page1 = {
        "count": 4,
        "next": BASE_URL + "/api/items/?page=2",
        "results": [{"id": 1}, {"id": 2}],
    }
    call_count = 0

    def side_effect(request):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return Response(200, json=page1)
        raise httpx.ReadTimeout("next page timed out")

    with respx.mock(assert_all_called=False) as router:
        router.get(BASE_URL + "/api/items/").mock(side_effect=side_effect)
        with pytest.raises(ServerError, match="timed out"):
            await session.get_all_pages("/items/")


async def test_get_all_pages_next_page_http_error(session):
    """get_all_pages wraps HTTPError on next-page fetch as ServerError."""
    page1 = {
        "count": 4,
        "next": BASE_URL + "/api/items/?page=2",
        "results": [{"id": 1}, {"id": 2}],
    }
    call_count = 0

    def side_effect(request):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return Response(200, json=page1)
        raise httpx.ConnectError("connection lost during pagination")

    with respx.mock(assert_all_called=False) as router:
        router.get(BASE_URL + "/api/items/").mock(side_effect=side_effect)
        with pytest.raises(ServerError, match="connection lost"):
            await session.get_all_pages("/items/")


async def test_get_all_pages_with_params(session):
    """get_all_pages passes params to the first page request."""
    data = {"count": 1, "next": None, "results": [{"id": 1}]}
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        route = router.get("/items/").mock(return_value=Response(200, json=data))
        results = await session.get_all_pages("/items/", params={"ordering": "name"})
    assert len(results) == 1
    assert "ordering" in str(route.calls[0].request.url)
