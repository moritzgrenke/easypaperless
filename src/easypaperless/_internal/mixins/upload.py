"""Upload mixin for PaperlessClient."""

from __future__ import annotations

import asyncio
import logging
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

from easypaperless.exceptions import TaskTimeoutError, UploadError
from easypaperless.models.documents import Document, Task, TaskStatus

if TYPE_CHECKING:
    from easypaperless._internal.http import HttpSession
    from easypaperless._internal.resolvers import NameResolver

logger = logging.getLogger(__name__)


class UploadMixin:
    if TYPE_CHECKING:
        _session: HttpSession
        _resolver: NameResolver
        _poll_interval: float
        _poll_timeout: float

        async def get_document(self, id: int, *, include_metadata: bool = False) -> Document: ...

    async def upload_document(
        self,
        file: str | Path,
        *,
        title: str | None = None,
        created: str | None = None,
        correspondent: int | str | None = None,
        document_type: int | str | None = None,
        storage_path: int | str | None = None,
        tags: list[int | str] | None = None,
        asn: int | None = None,
        wait: bool = False,
        poll_interval: float | None = None,
        poll_timeout: float | None = None,
    ) -> str | Document:
        """Upload a document to paperless-ngx.

        Args:
            file: Path to the file to upload (``str`` or
                :class:`~pathlib.Path`).
            title: Title to assign to the document.  Paperless-ngx derives
                one from the file name if omitted.
            created: Creation date as an ISO-8601 string (``"YYYY-MM-DD"``).
            correspondent: Correspondent to assign, as an ID or name.
            document_type: Document type to assign, as an ID or name.
            storage_path: Storage path to assign, as an ID or name.
            tags: Tags to assign, as IDs or names.
            asn: Archive serial number to assign.
            wait: If ``False`` *(default)*, returns immediately with the
                task ID string.  If ``True``, polls the task-status endpoint
                until processing completes and returns the resulting
                :class:`~easypaperless.models.documents.Document`.
            poll_interval: Override the client-level ``poll_interval`` for
                this upload.  Only used when ``wait=True``.
            poll_timeout: Override the client-level ``poll_timeout`` for
                this upload.  Only used when ``wait=True``.

        Returns:
            The Celery task ID string when ``wait=False``, or the fully
            processed :class:`~easypaperless.models.documents.Document`
            when ``wait=True``.

        Raises:
            ~easypaperless.exceptions.UploadError: If paperless-ngx reports
                that the processing task failed.
            ~easypaperless.exceptions.TaskTimeoutError: If ``wait=True`` and
                processing does not complete within the timeout.
        """
        file_path = Path(file)
        file_bytes = file_path.read_bytes()
        logger.info("Uploading %r (%d bytes)", file_path.name, len(file_bytes))

        data: dict[str, Any] = {}
        if title is not None:
            data["title"] = title
        if created is not None:
            data["created"] = created
        if correspondent is not None:
            data["correspondent"] = await self._resolver.resolve("correspondents", correspondent)
        if document_type is not None:
            data["document_type"] = await self._resolver.resolve("document_types", document_type)
        if storage_path is not None:
            data["storage_path"] = await self._resolver.resolve("storage_paths", storage_path)
        if tags is not None:
            resolved = await self._resolver.resolve_list("tags", tags)
            data["tags"] = resolved
        if asn is not None:
            data["archive_serial_number"] = asn

        files = {"document": (file_path.name, file_bytes)}
        resp = await self._session.post("/documents/post_document/", data=data, files=files)
        task_id: str = resp.text.strip('"')
        logger.debug("Upload accepted, task_id=%r", task_id)

        if not wait:
            return task_id

        interval = poll_interval if poll_interval is not None else self._poll_interval
        timeout = poll_timeout if poll_timeout is not None else self._poll_timeout
        return await self._poll_task(task_id, poll_interval=interval, poll_timeout=timeout)

    async def _poll_task(
        self, task_id: str, *, poll_interval: float, poll_timeout: float
    ) -> Document:
        start = time.monotonic()
        deadline = start + poll_timeout
        while time.monotonic() < deadline:
            resp = await self._session.get("/tasks/", params={"task_id": task_id})
            tasks = resp.json()
            if not tasks:
                await asyncio.sleep(poll_interval)
                continue

            task = Task.model_validate(tasks[0])
            elapsed = time.monotonic() - start
            logger.debug(
                "Polling task %r (status=%s, elapsed=%.1fs)",
                task_id,
                task.status.value if task.status is not None else "unknown",
                elapsed,
            )
            if task.status == TaskStatus.SUCCESS:
                if task.related_document is None:
                    raise UploadError(
                        f"Task {task_id!r} succeeded but returned no document ID"
                    )
                doc_id = int(task.related_document)
                logger.info("Task %r succeeded, document_id=%d", task_id, doc_id)
                return await self.get_document(doc_id)
            elif task.status == TaskStatus.FAILURE:
                logger.warning("Task %r failed: %s", task_id, task.result)
                raise UploadError(f"Document processing failed: {task.result}")
            elif task.status == TaskStatus.REVOKED:
                logger.warning("Task %r was revoked", task_id)
                raise UploadError(f"Task {task_id!r} was revoked")
            await asyncio.sleep(poll_interval)

        elapsed = time.monotonic() - start
        logger.warning("Task %r timed out after %.1fs", task_id, elapsed)
        raise TaskTimeoutError(f"Task {task_id!r} did not complete within {poll_timeout}s")
