"""Tests for upload_document — task ID return and polling."""

from __future__ import annotations

import pytest
from httpx import Response

from easypaperless.exceptions import TaskTimeoutError, UploadError
from easypaperless.models.documents import Document

DOC_DATA = {"id": 10, "title": "Uploaded", "tags": []}


async def test_upload_returns_task_id(client, mock_router, tmp_path):
    pdf = tmp_path / "scan.pdf"
    pdf.write_bytes(b"%PDF-1.4 test")

    mock_router.post("/documents/post_document/").mock(
        return_value=Response(200, text='"abc-task-123"')
    )
    result = await client.documents.upload(pdf, wait=False)
    assert result == "abc-task-123"


async def test_upload_wait_true_polls_and_returns_document(client, mock_router, tmp_path):
    pdf = tmp_path / "scan.pdf"
    pdf.write_bytes(b"%PDF-1.4 test")

    task_id = "task-42"
    task_pending = [{"task_id": task_id, "status": "PENDING", "related_document": None}]
    task_success = [{"task_id": task_id, "status": "SUCCESS", "related_document": "10"}]

    mock_router.post("/documents/post_document/").mock(
        return_value=Response(200, text=f'"{task_id}"')
    )
    # First poll returns PENDING, second returns SUCCESS
    call_count = 0

    def task_side_effect(request):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return Response(200, json=task_pending)
        return Response(200, json=task_success)

    mock_router.get("/tasks/").mock(side_effect=task_side_effect)
    mock_router.get("/documents/10/").mock(return_value=Response(200, json=DOC_DATA))

    result = await client.documents.upload(pdf, wait=True, poll_interval=0.01, poll_timeout=5.0)
    assert isinstance(result, Document)
    assert result.id == 10


async def test_upload_file_not_found_raises(client):
    with pytest.raises(FileNotFoundError):
        await client.documents.upload("/nonexistent/path/doc.pdf")


async def test_upload_sends_metadata_fields(client, mock_router, tmp_path):
    pdf = tmp_path / "scan.pdf"
    pdf.write_bytes(b"%PDF-1.4 test")

    route = mock_router.post("/documents/post_document/").mock(
        return_value=Response(200, text='"meta-task"')
    )
    result = await client.documents.upload(
        pdf,
        title="My Doc",
        created="2024-01-15",
        correspondent=5,
        document_type=3,
        storage_path=2,
        tags=[1, 7],
        archive_serial_number=42,
    )
    assert result == "meta-task"

    request = route.calls.last.request
    body = request.content.decode("utf-8", errors="replace")
    assert "My Doc" in body
    assert "2024-01-15" in body
    assert "42" in body


async def test_upload_resolves_names(client, mock_router, tmp_path):
    pdf = tmp_path / "scan.pdf"
    pdf.write_bytes(b"%PDF-1.4 test")

    # The resolver fetches all items for each resource, then looks up locally
    def _page(items):
        return {"count": len(items), "next": None, "results": items}

    mock_router.get("/correspondents/").mock(
        return_value=Response(200, json=_page([{"id": 10, "name": "Acme"}]))
    )
    mock_router.get("/document_types/").mock(
        return_value=Response(200, json=_page([{"id": 20, "name": "Invoice"}]))
    )
    mock_router.get("/storage_paths/").mock(
        return_value=Response(200, json=_page([{"id": 30, "name": "Archive"}]))
    )
    mock_router.get("/tags/").mock(
        return_value=Response(200, json=_page([{"id": 40, "name": "Important"}]))
    )

    route = mock_router.post("/documents/post_document/").mock(
        return_value=Response(200, text='"resolve-task"')
    )

    result = await client.documents.upload(
        pdf,
        correspondent="Acme",
        document_type="Invoice",
        storage_path="Archive",
        tags=["Important"],
    )
    assert result == "resolve-task"

    # Verify the resolved IDs were sent in the request body
    request = route.calls.last.request
    body = request.content.decode("utf-8", errors="replace")
    assert "10" in body  # correspondent ID
    assert "20" in body  # document_type ID
    assert "30" in body  # storage_path ID
    assert "40" in body  # tag ID


async def test_upload_omits_unset_metadata(client, mock_router, tmp_path):
    """Only explicitly passed metadata is included in the request body."""
    pdf = tmp_path / "scan.pdf"
    pdf.write_bytes(b"%PDF-1.4 test")

    route = mock_router.post("/documents/post_document/").mock(
        return_value=Response(200, text='"none-task"')
    )
    await client.documents.upload(pdf, title="Only Title")

    request = route.calls.last.request
    body = request.content.decode("utf-8", errors="replace")
    assert "Only Title" in body
    # These fields were not passed (UNSET default), so they should not appear
    assert "correspondent" not in body
    assert "document_type" not in body
    assert "storage_path" not in body
    assert "archive_serial_number" not in body


async def test_upload_omits_explicit_none_metadata(client, mock_router, tmp_path):
    """Explicitly passing None for nullable upload params also omits them (form data has no null)."""
    from easypaperless._internal.sentinel import UNSET

    pdf = tmp_path / "scan.pdf"
    pdf.write_bytes(b"%PDF-1.4 test")

    route = mock_router.post("/documents/post_document/").mock(
        return_value=Response(200, text='"null-task"')
    )
    await client.documents.upload(
        pdf,
        correspondent=None,
        document_type=None,
        storage_path=None,
        archive_serial_number=None,
    )

    request = route.calls.last.request
    body = request.content.decode("utf-8", errors="replace")
    # None is the same as omitting for multipart form data
    assert "correspondent" not in body
    assert "document_type" not in body
    assert "storage_path" not in body
    assert "archive_serial_number" not in body


async def test_upload_wait_true_failure_raises_upload_error(client, mock_router, tmp_path):
    pdf = tmp_path / "scan.pdf"
    pdf.write_bytes(b"%PDF-1.4 test")

    task_id = "fail-task"
    task_failure = [
        {"task_id": task_id, "status": "FAILURE", "result": "OCR failed", "related_document": None}
    ]

    mock_router.post("/documents/post_document/").mock(
        return_value=Response(200, text=f'"{task_id}"')
    )
    mock_router.get("/tasks/").mock(return_value=Response(200, json=task_failure))

    with pytest.raises(UploadError):
        await client.documents.upload(pdf, wait=True, poll_interval=0.01, poll_timeout=5.0)


async def test_upload_wait_timeout_raises_task_timeout_error(client, mock_router, tmp_path):
    pdf = tmp_path / "scan.pdf"
    pdf.write_bytes(b"%PDF-1.4 test")

    task_id = "slow-task"
    task_pending = [{"task_id": task_id, "status": "PENDING", "related_document": None}]

    mock_router.post("/documents/post_document/").mock(
        return_value=Response(200, text=f'"{task_id}"')
    )
    mock_router.get("/tasks/").mock(return_value=Response(200, json=task_pending))

    with pytest.raises(TaskTimeoutError):
        await client.documents.upload(pdf, wait=True, poll_interval=0.01, poll_timeout=0.05)


async def test_upload_empty_task_response_keeps_polling(client, mock_router, tmp_path):
    pdf = tmp_path / "scan.pdf"
    pdf.write_bytes(b"%PDF-1.4 test")

    task_id = "delayed-task"

    mock_router.post("/documents/post_document/").mock(
        return_value=Response(200, text=f'"{task_id}"')
    )
    call_count = 0

    def task_side_effect(request):
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            return Response(200, json=[])  # empty — not yet known
        return Response(
            200,
            json=[{"task_id": task_id, "status": "SUCCESS", "related_document": "10"}],
        )

    mock_router.get("/tasks/").mock(side_effect=task_side_effect)
    mock_router.get("/documents/10/").mock(return_value=Response(200, json=DOC_DATA))

    result = await client.documents.upload(pdf, wait=True, poll_interval=0.01, poll_timeout=5.0)
    assert isinstance(result, Document)


async def test_upload_wait_started_then_success(client, mock_router, tmp_path):
    """STARTED status keeps polling until a terminal state is reached."""
    pdf = tmp_path / "scan.pdf"
    pdf.write_bytes(b"%PDF-1.4 test")

    task_id = "started-task"
    mock_router.post("/documents/post_document/").mock(
        return_value=Response(200, text=f'"{task_id}"')
    )
    call_count = 0

    def task_side_effect(request):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return Response(
                200,
                json=[{"task_id": task_id, "status": "STARTED", "related_document": None}],
            )
        return Response(
            200,
            json=[{"task_id": task_id, "status": "SUCCESS", "related_document": "10"}],
        )

    mock_router.get("/tasks/").mock(side_effect=task_side_effect)
    mock_router.get("/documents/10/").mock(return_value=Response(200, json=DOC_DATA))

    result = await client.documents.upload(pdf, wait=True, poll_interval=0.01, poll_timeout=5.0)
    assert isinstance(result, Document)
    assert result.id == 10


async def test_upload_wait_retry_then_success(client, mock_router, tmp_path):
    """RETRY status keeps polling until a terminal state is reached."""
    pdf = tmp_path / "scan.pdf"
    pdf.write_bytes(b"%PDF-1.4 test")

    task_id = "retry-task"
    mock_router.post("/documents/post_document/").mock(
        return_value=Response(200, text=f'"{task_id}"')
    )
    call_count = 0

    def task_side_effect(request):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return Response(
                200,
                json=[{"task_id": task_id, "status": "RETRY", "related_document": None}],
            )
        return Response(
            200,
            json=[{"task_id": task_id, "status": "SUCCESS", "related_document": "10"}],
        )

    mock_router.get("/tasks/").mock(side_effect=task_side_effect)
    mock_router.get("/documents/10/").mock(return_value=Response(200, json=DOC_DATA))

    result = await client.documents.upload(pdf, wait=True, poll_interval=0.01, poll_timeout=5.0)
    assert isinstance(result, Document)
    assert result.id == 10


async def test_upload_wait_revoked_raises_upload_error(client, mock_router, tmp_path):
    """REVOKED status is treated as a terminal failure."""
    pdf = tmp_path / "scan.pdf"
    pdf.write_bytes(b"%PDF-1.4 test")

    task_id = "revoked-task"
    mock_router.post("/documents/post_document/").mock(
        return_value=Response(200, text=f'"{task_id}"')
    )
    mock_router.get("/tasks/").mock(
        return_value=Response(
            200,
            json=[{"task_id": task_id, "status": "REVOKED", "related_document": None}],
        )
    )

    with pytest.raises(UploadError, match="revoked"):
        await client.documents.upload(pdf, wait=True, poll_interval=0.01, poll_timeout=5.0)


async def test_upload_wait_success_no_related_document_raises(client, mock_router, tmp_path):
    """SUCCESS with related_document=None raises UploadError."""
    pdf = tmp_path / "scan.pdf"
    pdf.write_bytes(b"%PDF-1.4 test")

    task_id = "no-doc-task"
    mock_router.post("/documents/post_document/").mock(
        return_value=Response(200, text=f'"{task_id}"')
    )
    mock_router.get("/tasks/").mock(
        return_value=Response(
            200,
            json=[{"task_id": task_id, "status": "SUCCESS", "related_document": None}],
        )
    )

    with pytest.raises(UploadError, match="no document ID"):
        await client.documents.upload(pdf, wait=True, poll_interval=0.01, poll_timeout=5.0)
