"""Tests for PaperlessClient document notes methods."""

from __future__ import annotations

import pytest
from httpx import Response

from easypaperless.exceptions import NotFoundError
from easypaperless.models.documents import DocumentNote

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


async def test_get_notes(client, mock_router):
    mock_router.get("/documents/42/notes/").mock(return_value=Response(200, json=[NOTE_DATA]))
    notes = await client.get_notes(42)
    assert len(notes) == 1
    assert isinstance(notes[0], DocumentNote)
    assert notes[0].id == 1
    assert notes[0].note == "Needs review"
    assert notes[0].document == 42


async def test_get_notes_empty(client, mock_router):
    mock_router.get("/documents/42/notes/").mock(return_value=Response(200, json=[]))
    notes = await client.get_notes(42)
    assert notes == []


async def test_create_note(client, mock_router):
    mock_router.post("/documents/42/notes/").mock(return_value=Response(200, json=NOTE_DATA))
    note = await client.create_note(42, note="Needs review")
    assert isinstance(note, DocumentNote)
    assert note.id == 1
    assert note.note == "Needs review"
    assert note.document == 42


async def test_get_notes_nested_user(client, mock_router):
    mock_router.get("/documents/42/notes/").mock(
        return_value=Response(200, json=[NOTE_DATA_NESTED_USER])
    )
    notes = await client.get_notes(42)
    assert notes[0].user == 1


async def test_delete_note(client, mock_router):
    # paperless-ngx DELETE uses ?id= on the list endpoint, not a detail URL.
    captured: dict = {}

    def _capture(request):
        captured["params"] = dict(request.url.params)
        return Response(200, json=[])

    mock_router.delete("/documents/42/notes/").mock(side_effect=_capture)
    result = await client.delete_note(42, 1)
    assert result is None
    assert captured["params"]["id"] == "1"


async def test_get_notes_not_found(client, mock_router):
    mock_router.get("/documents/999/notes/").mock(
        return_value=Response(404, json={"detail": "Not found."})
    )
    with pytest.raises(NotFoundError):
        await client.get_notes(999)


async def test_create_note_not_found(client, mock_router):
    mock_router.post("/documents/999/notes/").mock(
        return_value=Response(404, json={"detail": "Not found."})
    )
    with pytest.raises(NotFoundError):
        await client.create_note(999, note="Test")


async def test_delete_note_not_found(client, mock_router):
    mock_router.delete("/documents/42/notes/").mock(
        return_value=Response(404, json={"detail": "Not found."})
    )
    with pytest.raises(NotFoundError):
        await client.delete_note(42, 999)


async def test_create_note_list_response(client, mock_router):
    """paperless-ngx returns the full list after creation; the last item is the new note."""
    existing = {**NOTE_DATA, "id": 1, "note": "Old note"}
    new_note = {**NOTE_DATA, "id": 2, "note": "Needs review"}
    mock_router.post("/documents/42/notes/").mock(
        return_value=Response(200, json=[existing, new_note])
    )
    note = await client.create_note(42, note="Needs review")
    assert isinstance(note, DocumentNote)
    assert note.id == 2
    assert note.note == "Needs review"
