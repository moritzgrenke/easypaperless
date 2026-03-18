"""Integration tests: notes CRUD on a real document."""

from __future__ import annotations

import pytest

from easypaperless import PaperlessClient
from easypaperless.models.documents import DocumentNote
from easypaperless.models.paged_result import PagedResult


@pytest.mark.integration
async def test_notes_crud(client: PaperlessClient, temp_documents) -> None:
    doc_id = temp_documents[0].id

    note = await client.documents.notes.create(doc_id, note="__integration_note__")
    try:
        assert note.note == "__integration_note__"
        assert note.id is not None

        notes = await client.documents.notes.list(doc_id)
        assert isinstance(notes, PagedResult), (
            "notes.list() must return PagedResult, got plain list — "
            "regression of #0034 (plain array response not wrapped)"
        )
        assert notes.count >= 1
        note_ids = [n.id for n in notes.results]
        assert note.id in note_ids
        assert all(isinstance(n, DocumentNote) for n in notes.results)
    finally:
        await client.documents.notes.delete(doc_id, note.id)

    # Verify deletion
    notes_after = await client.documents.notes.list(doc_id)
    assert isinstance(notes_after, PagedResult)
    assert note.id not in [n.id for n in notes_after.results]


@pytest.mark.integration
async def test_notes_list_returns_paged_result_on_empty_document(
    client: PaperlessClient, temp_documents
) -> None:
    """Regression #0034: notes.list() on a document with no notes must not crash."""
    doc_id = temp_documents[1].id

    notes = await client.documents.notes.list(doc_id)
    assert isinstance(notes, PagedResult), (
        "notes.list() must return PagedResult even when there are no notes"
    )
    assert notes.count == 0
    assert notes.results == []
    assert notes.next is None
    assert notes.previous is None
