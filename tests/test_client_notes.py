"""Tests for PaperlessClient document notes methods."""

from __future__ import annotations

import pytest
from httpx import Response

from easypaperless.exceptions import NotFoundError
from easypaperless.models.documents import DocumentNote
from easypaperless.models.paged_result import PagedResult

NOTE_DATA = {
    "id": 1,
    "note": "Needs review",
    "created": "2024-01-15T10:30:00Z",
    "document": 42,
    "user": 1,
}

# Real paperless-ngx returns a nested user object rather than a plain int.
NOTE_DATA_NESTED_USER = {
    **NOTE_DATA,
    "user": {"id": 1, "username": "admin", "first_name": "", "last_name": ""},
}

PAGED_RESPONSE = {
    "count": 1,
    "next": None,
    "previous": None,
    "all": None,
    "results": [NOTE_DATA],
}

PAGED_RESPONSE_EMPTY = {
    "count": 0,
    "next": None,
    "previous": None,
    "all": None,
    "results": [],
}


async def test_get_notes(client, mock_router):
    mock_router.get("/documents/42/notes/").mock(return_value=Response(200, json=PAGED_RESPONSE))
    result = await client.documents.notes.list(42)
    assert isinstance(result, PagedResult)
    assert result.count == 1
    assert len(result.results) == 1
    assert isinstance(result.results[0], DocumentNote)
    assert result.results[0].id == 1
    assert result.results[0].note == "Needs review"
    assert result.results[0].document == 42


async def test_get_notes_empty(client, mock_router):
    mock_router.get("/documents/42/notes/").mock(
        return_value=Response(200, json=PAGED_RESPONSE_EMPTY)
    )
    result = await client.documents.notes.list(42)
    assert isinstance(result, PagedResult)
    assert result.count == 0
    assert result.results == []


async def test_get_notes_auto_pagination(client, mock_router):
    """Auto-pagination: next/previous are None, count from first page."""
    page1 = {
        "count": 2,
        "next": "http://paperless.test/api/documents/42/notes/?page=2",
        "previous": None,
        "all": None,
        "results": [NOTE_DATA],
    }
    note2 = {**NOTE_DATA, "id": 2, "note": "Second note"}
    page2 = {"count": 2, "next": None, "previous": None, "all": None, "results": [note2]}
    mock_router.get("/documents/42/notes/").mock(
        side_effect=[Response(200, json=page1), Response(200, json=page2)]
    )
    result = await client.documents.notes.list(42)
    assert isinstance(result, PagedResult)
    assert result.count == 2
    assert len(result.results) == 2
    assert result.next is None
    assert result.previous is None


async def test_get_notes_single_page(client, mock_router):
    """Single-page mode: next/previous reflect raw API values."""
    paged = {
        "count": 5,
        "next": "http://localhost/api/documents/42/notes/?page=2",
        "previous": None,
        "all": None,
        "results": [NOTE_DATA],
    }
    mock_router.get("/documents/42/notes/").mock(return_value=Response(200, json=paged))
    result = await client.documents.notes.list(42, page=1)
    assert isinstance(result, PagedResult)
    assert result.count == 5
    assert result.next == "http://localhost/api/documents/42/notes/?page=2"
    assert result.previous is None
    assert len(result.results) == 1


async def test_get_notes_all_field(client, mock_router):
    """'all' field is included when present in the API response."""
    paged = {
        "count": 1,
        "next": None,
        "previous": None,
        "all": [1],
        "results": [NOTE_DATA],
    }
    mock_router.get("/documents/42/notes/").mock(return_value=Response(200, json=paged))
    result = await client.documents.notes.list(42)
    assert result.all == [1]


async def test_get_notes_all_field_absent(client, mock_router):
    """'all' field is None when absent from the API response."""
    paged = {"count": 1, "next": None, "previous": None, "results": [NOTE_DATA]}
    mock_router.get("/documents/42/notes/").mock(return_value=Response(200, json=paged))
    result = await client.documents.notes.list(42)
    assert result.all is None


async def test_create_note(client, mock_router):
    mock_router.post("/documents/42/notes/").mock(return_value=Response(200, json=NOTE_DATA))
    note = await client.documents.notes.create(42, note="Needs review")
    assert isinstance(note, DocumentNote)
    assert note.id == 1
    assert note.note == "Needs review"
    assert note.document == 42


async def test_get_notes_nested_user(client, mock_router):
    paged = {**PAGED_RESPONSE, "results": [NOTE_DATA_NESTED_USER]}
    mock_router.get("/documents/42/notes/").mock(return_value=Response(200, json=paged))
    result = await client.documents.notes.list(42)
    assert result.results[0].user == 1


async def test_delete_note(client, mock_router):
    # paperless-ngx DELETE uses ?id= on the list endpoint, not a detail URL.
    captured: dict = {}

    def _capture(request):
        captured["params"] = dict(request.url.params)
        return Response(200, json=[])

    mock_router.delete("/documents/42/notes/").mock(side_effect=_capture)
    result = await client.documents.notes.delete(42, 1)
    assert result is None
    assert captured["params"]["id"] == "1"


async def test_get_notes_not_found(client, mock_router):
    mock_router.get("/documents/999/notes/").mock(
        return_value=Response(404, json={"detail": "Not found."})
    )
    with pytest.raises(NotFoundError):
        await client.documents.notes.list(999)


async def test_create_note_not_found(client, mock_router):
    mock_router.post("/documents/999/notes/").mock(
        return_value=Response(404, json={"detail": "Not found."})
    )
    with pytest.raises(NotFoundError):
        await client.documents.notes.create(999, note="Test")


async def test_delete_note_not_found(client, mock_router):
    mock_router.delete("/documents/42/notes/").mock(
        return_value=Response(404, json={"detail": "Not found."})
    )
    with pytest.raises(NotFoundError):
        await client.documents.notes.delete(42, 999)


async def test_create_note_list_response(client, mock_router):
    """paperless-ngx returns the full list after creation; the last item is the new note."""
    existing = {**NOTE_DATA, "id": 1, "note": "Old note"}
    new_note = {**NOTE_DATA, "id": 2, "note": "Needs review"}
    mock_router.post("/documents/42/notes/").mock(
        return_value=Response(200, json=[existing, new_note])
    )
    note = await client.documents.notes.create(42, note="Needs review")
    assert isinstance(note, DocumentNote)
    assert note.id == 2
    assert note.note == "Needs review"
