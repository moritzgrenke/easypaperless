"""Integration tests: notes CRUD on a real document."""

from __future__ import annotations

import pytest

from easypaperless import PaperlessClient


@pytest.mark.integration
async def test_notes_crud(client: PaperlessClient) -> None:
    docs = await client.documents.list(page=1, page_size=1)
    if not docs.results:
        pytest.skip("No documents available on this instance")
    doc_id = docs.results[0].id

    note = await client.documents.notes.create(doc_id, note="__integration_note__")
    try:
        assert note.note == "__integration_note__"
        assert note.id is not None
        notes = await client.documents.notes.list(doc_id)
        note_ids = [n.id for n in notes]
        assert note.id in note_ids
    finally:
        await client.documents.notes.delete(doc_id, note.id)

    # Verify deletion
    notes_after = await client.documents.notes.list(doc_id)
    assert note.id not in [n.id for n in notes_after]
