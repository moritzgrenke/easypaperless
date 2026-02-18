"""Tests for upload_document — task ID return and polling."""

from __future__ import annotations

import pytest
import respx
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
    result = await client.upload_document(pdf, wait=False)
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

    result = await client.upload_document(pdf, wait=True, poll_interval=0.01, poll_timeout=5.0)
    assert isinstance(result, Document)
    assert result.id == 10


async def test_upload_wait_true_failure_raises_upload_error(client, mock_router, tmp_path):
    pdf = tmp_path / "scan.pdf"
    pdf.write_bytes(b"%PDF-1.4 test")

    task_id = "fail-task"
    task_failure = [{"task_id": task_id, "status": "FAILURE", "result": "OCR failed", "related_document": None}]

    mock_router.post("/documents/post_document/").mock(
        return_value=Response(200, text=f'"{task_id}"')
    )
    mock_router.get("/tasks/").mock(return_value=Response(200, json=task_failure))

    with pytest.raises(UploadError):
        await client.upload_document(pdf, wait=True, poll_interval=0.01, poll_timeout=5.0)


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
        await client.upload_document(pdf, wait=True, poll_interval=0.01, poll_timeout=0.05)


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
        return Response(200, json=[{"task_id": task_id, "status": "SUCCESS", "related_document": "10"}])

    mock_router.get("/tasks/").mock(side_effect=task_side_effect)
    mock_router.get("/documents/10/").mock(return_value=Response(200, json=DOC_DATA))

    result = await client.upload_document(pdf, wait=True, poll_interval=0.01, poll_timeout=5.0)
    assert isinstance(result, Document)
