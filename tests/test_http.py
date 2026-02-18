"""Tests for HttpSession — error mapping and pagination."""

from __future__ import annotations

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


@pytest.mark.parametrize("status_code,exc_class", [
    (401, AuthError),
    (403, AuthError),
    (404, NotFoundError),
    (422, ValidationError),
    (500, ServerError),
    (503, ServerError),
])
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
