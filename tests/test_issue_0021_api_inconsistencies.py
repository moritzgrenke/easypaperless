"""Tests for issue #0021 — DocumentsResource API inconsistencies.

Covers the four fixes:
1. update() `date` renamed to `created` (accepts str or date object).
2. update() and upload() `asn` renamed to `archive_serial_number`.
3. list() `search_mode` default and map key changed from
   "title_or_text" to "title_or_content".
4. upload() `created` widened to accept date | str.
"""

from __future__ import annotations

import json
from datetime import date

import pytest
import respx
from httpx import Response

from easypaperless.sync import SyncPaperlessClient

BASE_URL = "http://paperless.test"
API_KEY = "test-api-key"
API_BASE = BASE_URL + "/api"

DOC_DATA = {"id": 1, "title": "Test", "tags": []}
DOC_LIST = {"count": 1, "next": None, "previous": None, "results": [DOC_DATA]}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _patch_capture(captured: dict):
    """respx side-effect that records the JSON request body."""

    def _side_effect(request):
        captured["body"] = json.loads(request.content)
        return Response(200, json=DOC_DATA)

    return _side_effect


def _get_capture(captured: dict):
    """respx side-effect that records the query params."""

    def _side_effect(request):
        captured["params"] = dict(request.url.params)
        return Response(200, json=DOC_LIST)

    return _side_effect


def _post_capture(captured: dict):
    """respx side-effect that records a multipart POST body as raw text."""

    def _side_effect(request):
        captured["body"] = request.content.decode("utf-8", errors="replace")
        return Response(200, text='"task-id"')

    return _side_effect


# ---------------------------------------------------------------------------
# Bug 1 & 4 — update() `created` parameter (renamed from `date`, widened type)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_created_str_sends_correct_payload(client, mock_router):
    """update(created='YYYY-MM-DD') sends 'created' in the PATCH body."""
    captured: dict = {}
    mock_router.patch("/documents/1/").mock(side_effect=_patch_capture(captured))
    await client.documents.update(1, created="2024-06-15")
    assert captured["body"]["created"] == "2024-06-15"
    assert "date" not in captured["body"]


@pytest.mark.asyncio
async def test_update_created_date_object_formats_to_iso(client, mock_router):
    """update(created=date(...)) formats the date to an ISO-8601 string."""
    captured: dict = {}
    mock_router.patch("/documents/1/").mock(side_effect=_patch_capture(captured))
    await client.documents.update(1, created=date(2024, 6, 15))
    assert captured["body"]["created"] == "2024-06-15"


@pytest.mark.asyncio
async def test_update_created_none_sends_null(client, mock_router):
    """update(created=None) sends null to clear the creation date."""
    captured: dict = {}
    mock_router.patch("/documents/1/").mock(side_effect=_patch_capture(captured))
    await client.documents.update(1, created=None)
    assert "created" in captured["body"]
    assert captured["body"]["created"] is None


@pytest.mark.asyncio
async def test_update_created_unset_omits_field(client, mock_router):
    """Omitting `created` does not include the field in the PATCH body."""
    captured: dict = {}
    mock_router.patch("/documents/1/").mock(side_effect=_patch_capture(captured))
    await client.documents.update(1, title="Only Title")
    assert "created" not in captured["body"]


# ---------------------------------------------------------------------------
# Bug 2 — update() `archive_serial_number` (renamed from `asn`)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_archive_serial_number_sends_correct_payload(client, mock_router):
    """update(archive_serial_number=42) sends the field with value 42."""
    captured: dict = {}
    mock_router.patch("/documents/1/").mock(side_effect=_patch_capture(captured))
    await client.documents.update(1, archive_serial_number=42)
    assert captured["body"]["archive_serial_number"] == 42
    assert "asn" not in captured["body"]


@pytest.mark.asyncio
async def test_update_archive_serial_number_none_sends_null(client, mock_router):
    """update(archive_serial_number=None) sends null to clear the ASN."""
    captured: dict = {}
    mock_router.patch("/documents/1/").mock(side_effect=_patch_capture(captured))
    await client.documents.update(1, archive_serial_number=None)
    assert "archive_serial_number" in captured["body"]
    assert captured["body"]["archive_serial_number"] is None


# ---------------------------------------------------------------------------
# Bug 2 — upload() `archive_serial_number` (renamed from `asn`)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_upload_archive_serial_number_sent_in_body(client, mock_router, tmp_path):
    """upload(archive_serial_number=7) includes the value in the multipart body."""
    pdf = tmp_path / "doc.pdf"
    pdf.write_bytes(b"%PDF-1.4 test")
    captured: dict = {}
    mock_router.post("/documents/post_document/").mock(side_effect=_post_capture(captured))
    await client.documents.upload(pdf, archive_serial_number=7)
    assert "7" in captured["body"]
    assert "asn" not in captured["body"]


@pytest.mark.asyncio
async def test_upload_archive_serial_number_omitted_when_none(client, mock_router, tmp_path):
    """upload() without archive_serial_number does not send the field."""
    pdf = tmp_path / "doc.pdf"
    pdf.write_bytes(b"%PDF-1.4 test")
    captured: dict = {}
    mock_router.post("/documents/post_document/").mock(side_effect=_post_capture(captured))
    await client.documents.upload(pdf)
    assert "archive_serial_number" not in captured["body"]


# ---------------------------------------------------------------------------
# Bug 4 — upload() `created` accepts date object
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_upload_created_date_object_formats_to_iso(client, mock_router, tmp_path):
    """upload(created=date(...)) formats the date to ISO-8601 before sending."""
    pdf = tmp_path / "doc.pdf"
    pdf.write_bytes(b"%PDF-1.4 test")
    captured: dict = {}
    mock_router.post("/documents/post_document/").mock(side_effect=_post_capture(captured))
    await client.documents.upload(pdf, created=date(2024, 3, 5))
    assert "2024-03-05" in captured["body"]


@pytest.mark.asyncio
async def test_upload_created_str_sent_as_is(client, mock_router, tmp_path):
    """upload(created='YYYY-MM-DD') sends the string value unchanged."""
    pdf = tmp_path / "doc.pdf"
    pdf.write_bytes(b"%PDF-1.4 test")
    captured: dict = {}
    mock_router.post("/documents/post_document/").mock(side_effect=_post_capture(captured))
    await client.documents.upload(pdf, created="2024-03-05")
    assert "2024-03-05" in captured["body"]


# ---------------------------------------------------------------------------
# Bug 3 — list() search_mode "title_or_content" maps to "search" API param
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_default_search_mode_sends_search_param(client, mock_router):
    """Default search_mode='title_or_content' maps to the 'search' query param."""
    captured: dict = {}
    mock_router.get("/documents/").mock(side_effect=_get_capture(captured))
    await client.documents.list(search="invoice")
    assert captured["params"]["search"] == "invoice"
    assert "title__icontains" not in captured["params"]
    assert "title_or_text" not in captured["params"]
    assert "title_or_content" not in captured["params"]


@pytest.mark.asyncio
async def test_list_explicit_title_or_content_search_mode_sends_search_param(client, mock_router):
    """Explicit search_mode='title_or_content' maps to the 'search' query param."""
    captured: dict = {}
    mock_router.get("/documents/").mock(side_effect=_get_capture(captured))
    await client.documents.list(search="invoice", search_mode="title_or_content")
    assert captured["params"]["search"] == "invoice"
    assert "title__icontains" not in captured["params"]


@pytest.mark.asyncio
async def test_list_title_search_mode_sends_title_icontains_param(client, mock_router):
    """search_mode='title' maps to the 'title__icontains' query param."""
    captured: dict = {}
    mock_router.get("/documents/").mock(side_effect=_get_capture(captured))
    await client.documents.list(search="invoice", search_mode="title")
    assert captured["params"]["title__icontains"] == "invoice"
    assert "search" not in captured["params"]


@pytest.mark.asyncio
async def test_list_unknown_search_mode_falls_back_to_search_param(client, mock_router):
    """An unrecognised search_mode falls back to the 'search' query param."""
    captured: dict = {}
    mock_router.get("/documents/").mock(side_effect=_get_capture(captured))
    await client.documents.list(search="invoice", search_mode="nonexistent_mode")
    assert captured["params"]["search"] == "invoice"


# ---------------------------------------------------------------------------
# Sync wrappers — SyncDocumentsResource passes new param names through
# ---------------------------------------------------------------------------


def test_sync_update_created_str_forwarded():
    """SyncDocumentsResource.update() passes `created=str` to the async method."""
    captured: dict = {}
    with respx.mock(base_url=API_BASE, assert_all_called=False) as router:
        router.patch("/documents/1/").mock(side_effect=_patch_capture(captured))
        with SyncPaperlessClient(url=BASE_URL, api_token=API_KEY) as client:
            client.documents.update(1, created="2024-06-15")
    assert captured["body"]["created"] == "2024-06-15"


def test_sync_update_created_date_object_forwarded():
    """SyncDocumentsResource.update() passes `created=date(...)` and formats it."""
    captured: dict = {}
    with respx.mock(base_url=API_BASE, assert_all_called=False) as router:
        router.patch("/documents/1/").mock(side_effect=_patch_capture(captured))
        with SyncPaperlessClient(url=BASE_URL, api_token=API_KEY) as client:
            client.documents.update(1, created=date(2024, 6, 15))
    assert captured["body"]["created"] == "2024-06-15"


def test_sync_update_archive_serial_number_forwarded():
    """SyncDocumentsResource.update() passes `archive_serial_number` correctly."""
    captured: dict = {}
    with respx.mock(base_url=API_BASE, assert_all_called=False) as router:
        router.patch("/documents/1/").mock(side_effect=_patch_capture(captured))
        with SyncPaperlessClient(url=BASE_URL, api_token=API_KEY) as client:
            client.documents.update(1, archive_serial_number=99)
    assert captured["body"]["archive_serial_number"] == 99
    assert "asn" not in captured["body"]


def test_sync_upload_archive_serial_number_forwarded(tmp_path):
    """SyncDocumentsResource.upload() passes `archive_serial_number` in body."""
    pdf = tmp_path / "doc.pdf"
    pdf.write_bytes(b"%PDF-1.4 test")
    captured: dict = {}
    with respx.mock(base_url=API_BASE, assert_all_called=False) as router:
        router.post("/documents/post_document/").mock(side_effect=_post_capture(captured))
        with SyncPaperlessClient(url=BASE_URL, api_token=API_KEY) as client:
            client.documents.upload(pdf, archive_serial_number=5)
    assert "5" in captured["body"]
    assert "asn" not in captured["body"]


def test_sync_upload_created_date_object_forwarded(tmp_path):
    """SyncDocumentsResource.upload() passes `created=date(...)` and formats it."""
    pdf = tmp_path / "doc.pdf"
    pdf.write_bytes(b"%PDF-1.4 test")
    captured: dict = {}
    with respx.mock(base_url=API_BASE, assert_all_called=False) as router:
        router.post("/documents/post_document/").mock(side_effect=_post_capture(captured))
        with SyncPaperlessClient(url=BASE_URL, api_token=API_KEY) as client:
            client.documents.upload(pdf, created=date(2024, 1, 20))
    assert "2024-01-20" in captured["body"]


def test_sync_list_default_search_mode_is_title_or_content():
    """SyncDocumentsResource.list() default search_mode sends 'search' param."""
    captured: dict = {}
    with respx.mock(base_url=API_BASE, assert_all_called=False) as router:
        router.get("/documents/").mock(side_effect=_get_capture(captured))
        with SyncPaperlessClient(url=BASE_URL, api_token=API_KEY) as client:
            client.documents.list(search="invoice")
    assert captured["params"]["search"] == "invoice"
    assert "title_or_text" not in captured["params"]
    assert "title_or_content" not in captured["params"]
