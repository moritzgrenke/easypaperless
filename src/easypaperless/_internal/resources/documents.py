"""Documents resource for PaperlessClient."""

from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from collections.abc import Callable
from datetime import date, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, List

from easypaperless._internal.sentinel import UNSET, _Unset
from easypaperless.exceptions import ServerError, TaskTimeoutError, UploadError
from easypaperless.models.documents import (
    Document,
    DocumentMetadata,
    DocumentNote,
    Task,
    TaskStatus,
)
from easypaperless.models.permissions import SetPermissions

if TYPE_CHECKING:
    from easypaperless.client import _ClientCore

logger = logging.getLogger(__name__)

_DATETIME_STR_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T")

_SEARCH_MODE_MAP = {
    "title": "title__icontains",
    "title_or_content": "search",
    "query": "query",
    "original_filename": "original_filename__icontains",
}


class NotesResource:
    """Accessor for document notes: ``client.documents.notes``."""

    def __init__(self, core: _ClientCore) -> None:
        self._core = core

    async def list(self, document_id: int) -> List[DocumentNote]:
        """Fetch all notes attached to a document.

        Args:
            document_id: Numeric ID of the document whose notes to retrieve.

        Returns:
            List of :class:`~easypaperless.models.documents.DocumentNote` objects,
            ordered by creation time.

        Raises:
            ~easypaperless.exceptions.NotFoundError: If no document exists
                with that ID.
        """
        logger.debug("Fetching notes for document id=%d", document_id)
        resp = await self._core._session.get(f"/documents/{document_id}/notes/")
        return [DocumentNote.model_validate(item) for item in resp.json()]

    async def create(self, document_id: int, *, note: str) -> DocumentNote:
        """Create a new note on a document.

        Args:
            document_id: Numeric ID of the document to annotate.
            note: Text content of the note.

        Returns:
            The newly created :class:`~easypaperless.models.documents.DocumentNote`.

        Raises:
            ~easypaperless.exceptions.NotFoundError: If no document exists
                with that ID.
        """
        logger.debug("Creating note for document id=%d", document_id)
        resp = await self._core._session.post(
            f"/documents/{document_id}/notes/",
            json={"note": note},
        )
        data = resp.json()
        if isinstance(data, list):
            return DocumentNote.model_validate(data[-1])
        return DocumentNote.model_validate(data)

    async def delete(self, document_id: int, note_id: int) -> None:
        """Delete a note from a document.

        Args:
            document_id: Numeric ID of the document that owns the note.
            note_id: Numeric ID of the note to delete.

        Raises:
            ~easypaperless.exceptions.NotFoundError: If no document or note
                exists with the given IDs.
        """
        logger.debug("Deleting note id=%d from document id=%d", note_id, document_id)
        await self._core._session.delete(f"/documents/{document_id}/notes/", params={"id": note_id})


class DocumentsResource:
    """Accessor for documents: ``client.documents``."""

    def __init__(self, core: _ClientCore) -> None:
        self._core = core
        self.notes = NotesResource(core)

    @staticmethod
    def _format_date_value(value: date | datetime | str) -> str:
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, date):
            return value.isoformat()
        return value

    @staticmethod
    def _is_datetime(value: date | datetime | str) -> bool:
        if isinstance(value, datetime):
            return True
        if isinstance(value, str):
            return bool(_DATETIME_STR_RE.match(value))
        return False

    async def get(self, id: int, *, include_metadata: bool = False) -> Document:
        """Fetch a single document by its ID.

        Args:
            id: Numeric paperless-ngx document ID.
            include_metadata: When ``True``, the extended file-level metadata
                is fetched concurrently and attached to the document.
                Default: ``False``.

        Returns:
            The :class:`~easypaperless.models.documents.Document` with the
            given ID.

        Raises:
            ~easypaperless.exceptions.NotFoundError: If no document exists
                with that ID.
        """
        if include_metadata:
            doc_resp, meta_resp = await asyncio.gather(
                self._core._session.get(f"/documents/{id}/"),
                self._core._session.get(f"/documents/{id}/metadata/"),
            )
            data = doc_resp.json()
            data["metadata"] = meta_resp.json()
        else:
            resp = await self._core._session.get(f"/documents/{id}/")
            data = resp.json()
        return Document.model_validate(data)

    async def get_metadata(self, id: int) -> DocumentMetadata:
        """Fetch the extended file-level metadata for a document.

        Args:
            id: Numeric paperless-ngx document ID.

        Returns:
            A :class:`~easypaperless.models.documents.DocumentMetadata` instance.

        Raises:
            ~easypaperless.exceptions.NotFoundError: If no document exists
                with that ID.
        """
        resp = await self._core._session.get(f"/documents/{id}/metadata/")
        return DocumentMetadata.model_validate(resp.json())

    async def list(
        self,
        *,
        search: str | None = None,
        search_mode: str = "title_or_content",
        ids: List[int] | None = None,
        tags: List[int | str] | None = None,
        any_tags: List[int | str] | None = None,
        exclude_tags: List[int | str] | None = None,
        correspondent: int | str | None | _Unset = UNSET,
        any_correspondent: List[int | str] | None = None,
        exclude_correspondents: List[int | str] | None = None,
        document_type: int | str | None | _Unset = UNSET,
        document_type_name_contains: str | None = None,
        document_type_name_exact: str | None = None,
        any_document_type: List[int | str] | None = None,
        exclude_document_types: List[int | str] | None = None,
        storage_path: int | str | None | _Unset = UNSET,
        any_storage_paths: List[int | str] | None = None,
        exclude_storage_paths: List[int | str] | None = None,
        owner: int | None | _Unset = UNSET,
        exclude_owners: List[int] | None = None,
        custom_fields: List[int | str] | None = None,
        any_custom_fields: List[int | str] | None = None,
        exclude_custom_fields: List[int | str] | None = None,
        custom_field_query: List[Any] | None = None,
        archive_serial_number: int | None | _Unset = UNSET,
        archive_serial_number_from: int | None = None,
        archive_serial_number_till: int | None = None,
        created_after: date | str | None = None,
        created_before: date | str | None = None,
        added_after: date | datetime | str | None = None,
        added_from: date | datetime | str | None = None,
        added_before: date | datetime | str | None = None,
        added_until: date | datetime | str | None = None,
        modified_after: date | datetime | str | None = None,
        modified_from: date | datetime | str | None = None,
        modified_before: date | datetime | str | None = None,
        modified_until: date | datetime | str | None = None,
        checksum: str | None = None,
        page_size: int = 25,
        page: int | None = None,
        ordering: str | None = None,
        descending: bool = False,
        max_results: int | None = None,
        on_page: Callable[[int, int | None], None] | None = None,
    ) -> List[Document]:
        """Return a filtered list of documents.

        All tag, correspondent, document-type, storage-path, and custom-field
        parameters accept either integer IDs or string names.

        Args:
            search: Search string.  Behaviour depends on ``search_mode``.
            search_mode: How ``search`` is applied.  One of:
                ``"title_or_content"`` *(default)*, ``"title"``, ``"query"``,
                ``"original_filename"``.
            ids: Return only documents whose ID is in this list.
            tags: Documents must have **all** of these tags (AND semantics).
            any_tags: Documents must have **at least one** of these tags.
            exclude_tags: Documents must have **none** of these tags.
            correspondent: Filter to documents assigned to this correspondent.
                Pass ``None`` to return only documents with no correspondent set.
            any_correspondent: Filter to documents assigned to any of these.
            exclude_correspondents: Exclude documents assigned to any of these.
            document_type: Filter to documents of exactly this type.
                Pass ``None`` to return only documents with no document type set.
            document_type_name_contains: Case-insensitive substring filter on document type name.
            document_type_name_exact: Case-insensitive exact match on document type name.
            any_document_type: Filter to documents whose type is any of these.
            exclude_document_types: Exclude documents whose type is any of these.
            storage_path: Filter to documents assigned to this storage path.
                Pass ``None`` to return only documents with no storage path set.
            any_storage_paths: Filter to documents assigned to any of these paths.
            exclude_storage_paths: Exclude documents assigned to any of these paths.
            owner: Filter to documents owned by this user ID.
                Pass ``None`` to return only documents with no owner set.
            exclude_owners: Exclude documents owned by any of these user IDs.
            custom_fields: Documents must have **all** of these custom fields set.
            any_custom_fields: Documents must have **at least one** of these fields.
            exclude_custom_fields: Documents must have **none** of these fields.
            custom_field_query: Filter documents by custom field values.
            archive_serial_number: Filter by exact archive serial number.
                Pass ``None`` to return only documents with no ASN set.
            archive_serial_number_from: Filter by ASN >= this value.
            archive_serial_number_till: Filter by ASN <= this value.
            created_after: Only documents created after this date.
            created_before: Only documents created before this date.
            added_after: Only documents added after this date/time.
            added_from: Only documents added on or after this date/time.
            added_before: Only documents added before this date/time.
            added_until: Only documents added on or before this date/time.
            modified_after: Only documents modified after this date/time.
            modified_from: Only documents modified on or after this date/time.
            modified_before: Only documents modified before this date/time.
            modified_until: Only documents modified on or before this date/time.
            checksum: MD5 checksum of the original file (exact match).
            page_size: Number of results per API page.  Default: ``25``.
            page: Return only this specific page (1-based).
            ordering: Field name to sort by.
            descending: When ``True``, reverses the sort direction.
            max_results: Stop after collecting this many documents.
            on_page: Callback invoked after each page fetch.

        Returns:
            List of :class:`~easypaperless.models.documents.Document` objects.
        """
        resolver = self._core._resolver
        params: dict[str, Any] = {"page_size": page_size}

        if search is not None:
            api_param = _SEARCH_MODE_MAP.get(search_mode, "search")
            params[api_param] = search

        if ids is not None:
            params["id__in"] = ",".join(str(i) for i in ids)

        if tags is not None:
            resolved = await resolver.resolve_list("tags", tags)
            params["tags__id__all"] = ",".join(str(t) for t in resolved)

        if any_tags is not None:
            resolved = await resolver.resolve_list("tags", any_tags)
            params["tags__id__in"] = ",".join(str(t) for t in resolved)

        if exclude_tags is not None:
            resolved = await resolver.resolve_list("tags", exclude_tags)
            params["tags__id__none"] = ",".join(str(t) for t in resolved)

        if any_correspondent is not None:
            resolved = await resolver.resolve_list("correspondents", any_correspondent)
            params["correspondent__id__in"] = ",".join(str(c) for c in resolved)
        elif not isinstance(correspondent, _Unset):
            if correspondent is None:
                params["correspondent__isnull"] = "true"
            else:
                resolved_id = await resolver.resolve("correspondents", correspondent)
                params["correspondent__id__in"] = resolved_id

        if exclude_correspondents is not None:
            resolved = await resolver.resolve_list("correspondents", exclude_correspondents)
            params["correspondent__id__none"] = ",".join(str(c) for c in resolved)

        if document_type_name_contains is not None:
            params["document_type__name__icontains"] = document_type_name_contains
        if document_type_name_exact is not None:
            params["document_type__name__iexact"] = document_type_name_exact

        if any_document_type is not None:
            resolved = await resolver.resolve_list("document_types", any_document_type)
            params["document_type__id__in"] = ",".join(str(d) for d in resolved)
        elif not isinstance(document_type, _Unset):
            if document_type is None:
                params["document_type__isnull"] = "true"
            else:
                resolved_id = await resolver.resolve("document_types", document_type)
                params["document_type"] = resolved_id

        if exclude_document_types is not None:
            resolved = await resolver.resolve_list("document_types", exclude_document_types)
            params["document_type__id__none"] = ",".join(str(d) for d in resolved)

        if any_storage_paths is not None:
            resolved = await resolver.resolve_list("storage_paths", any_storage_paths)
            params["storage_path__id__in"] = ",".join(str(s) for s in resolved)
        elif not isinstance(storage_path, _Unset):
            if storage_path is None:
                params["storage_path__isnull"] = "true"
            else:
                resolved_id = await resolver.resolve("storage_paths", storage_path)
                params["storage_path__id__in"] = resolved_id

        if exclude_storage_paths is not None:
            resolved = await resolver.resolve_list("storage_paths", exclude_storage_paths)
            params["storage_path__id__none"] = ",".join(str(s) for s in resolved)

        if not isinstance(owner, _Unset):
            if owner is None:
                params["owner__isnull"] = "true"
            else:
                params["owner__id__in"] = owner

        if exclude_owners is not None:
            params["owner__id__none"] = ",".join(str(o) for o in exclude_owners)

        if custom_fields is not None:
            resolved = await resolver.resolve_list("custom_fields", custom_fields)
            params["custom_fields__id__all"] = ",".join(str(f) for f in resolved)

        if any_custom_fields is not None:
            resolved = await resolver.resolve_list("custom_fields", any_custom_fields)
            params["custom_fields__id__in"] = ",".join(str(f) for f in resolved)

        if exclude_custom_fields is not None:
            resolved = await resolver.resolve_list("custom_fields", exclude_custom_fields)
            params["custom_fields__id__none"] = ",".join(str(f) for f in resolved)

        if custom_field_query is not None:
            params["custom_field_query"] = json.dumps(custom_field_query)

        if not isinstance(archive_serial_number, _Unset):
            if archive_serial_number is None:
                params["archive_serial_number__isnull"] = "true"
            else:
                params["archive_serial_number"] = archive_serial_number

        if archive_serial_number_from is not None:
            params["archive_serial_number__gte"] = archive_serial_number_from

        if archive_serial_number_till is not None:
            params["archive_serial_number__lte"] = archive_serial_number_till

        if created_after is not None:
            params["created__date__gt"] = self._format_date_value(created_after)

        if created_before is not None:
            params["created__date__lt"] = self._format_date_value(created_before)

        if added_after is not None:
            key = "added__gt" if self._is_datetime(added_after) else "added__date__gt"
            params[key] = self._format_date_value(added_after)

        if added_from is not None:
            key = "added__gte" if self._is_datetime(added_from) else "added__date__gte"
            params[key] = self._format_date_value(added_from)

        if added_before is not None:
            key = "added__lt" if self._is_datetime(added_before) else "added__date__lt"
            params[key] = self._format_date_value(added_before)

        if added_until is not None:
            key = "added__lte" if self._is_datetime(added_until) else "added__date__lte"
            params[key] = self._format_date_value(added_until)

        if modified_after is not None:
            key = "modified__gt" if self._is_datetime(modified_after) else "modified__date__gt"
            params[key] = self._format_date_value(modified_after)

        if modified_from is not None:
            key = "modified__gte" if self._is_datetime(modified_from) else "modified__date__gte"
            params[key] = self._format_date_value(modified_from)

        if modified_before is not None:
            key = "modified__lt" if self._is_datetime(modified_before) else "modified__date__lt"
            params[key] = self._format_date_value(modified_before)

        if modified_until is not None:
            key = "modified__lte" if self._is_datetime(modified_until) else "modified__date__lte"
            params[key] = self._format_date_value(modified_until)

        if checksum is not None:
            params["checksum__iexact"] = checksum

        if ordering is not None:
            params["ordering"] = f"-{ordering}" if descending else ordering

        if page is not None:
            params["page"] = page
            resp = await self._core._session.get("/documents/", params=params)
            items = resp.json().get("results", [])
            if max_results is not None:
                items = items[:max_results]
            return [Document.model_validate(item) for item in items]

        items = await self._core._session.get_all_pages(
            "/documents/", params, max_results=max_results, on_page=on_page
        )
        return [Document.model_validate(item) for item in items]

    async def update(
        self,
        id: int,
        *,
        title: str | None | _Unset = UNSET,
        content: str | None | _Unset = UNSET,
        created: date | str | None | _Unset = UNSET,
        correspondent: int | str | None | _Unset = UNSET,
        document_type: int | str | None | _Unset = UNSET,
        storage_path: int | str | None | _Unset = UNSET,
        tags: List[int | str] | None | _Unset = UNSET,
        archive_serial_number: int | None | _Unset = UNSET,
        custom_fields: List[dict[str, Any]] | None | _Unset = UNSET,
        owner: int | None | _Unset = UNSET,
        set_permissions: SetPermissions | None | _Unset = UNSET,
        remove_inbox_tags: bool | None | _Unset = UNSET,
    ) -> Document:
        """Partially update a document (PATCH semantics).

        Args:
            id: Numeric ID of the document to update.
            title: New document title.
            content: OCR text content of the document.
            created: Creation date as an ISO-8601 string (``"YYYY-MM-DD"``) or a
                :class:`~datetime.date` object.
            correspondent: Correspondent to assign, as an ID or name.
                Pass ``None`` to clear the correspondent.
            document_type: Document type to assign, as an ID or name.
                Pass ``None`` to clear the document type.
            storage_path: Storage path to assign, as an ID or name.
                Pass ``None`` to clear the storage path.
            tags: Full replacement list of tags (IDs or names).
            archive_serial_number: Archive serial number to assign.
                Pass ``None`` to clear the archive serial number.
            custom_fields: List of ``{"field": <field_id>, "value": ...}`` dicts.
            owner: Numeric user ID to assign as document owner.
                Pass ``None`` to clear the owner.
            set_permissions: Explicit view/change permission sets.
            remove_inbox_tags: When ``True``, removes all inbox tags from the document.

        Returns:
            The updated :class:`~easypaperless.models.documents.Document`.
        """
        logger.debug("Updating document id=%d", id)
        resolver = self._core._resolver
        payload: dict[str, Any] = {}

        if not isinstance(title, _Unset):
            payload["title"] = title
        if not isinstance(content, _Unset):
            payload["content"] = content
        if not isinstance(created, _Unset):
            payload["created"] = self._format_date_value(created) if created is not None else None
        if not isinstance(correspondent, _Unset):
            payload["correspondent"] = (
                None
                if correspondent is None
                else await resolver.resolve("correspondents", correspondent)
            )
        if not isinstance(document_type, _Unset):
            payload["document_type"] = (
                None
                if document_type is None
                else await resolver.resolve("document_types", document_type)
            )
        if not isinstance(storage_path, _Unset):
            payload["storage_path"] = (
                None
                if storage_path is None
                else await resolver.resolve("storage_paths", storage_path)
            )
        if not isinstance(tags, _Unset):
            payload["tags"] = await resolver.resolve_list("tags", tags or [])
        if not isinstance(archive_serial_number, _Unset):
            payload["archive_serial_number"] = archive_serial_number
        if not isinstance(custom_fields, _Unset):
            payload["custom_fields"] = custom_fields
        if not isinstance(owner, _Unset):
            payload["owner"] = owner
        if not isinstance(set_permissions, _Unset):
            payload["set_permissions"] = (set_permissions or SetPermissions()).model_dump()
        if not isinstance(remove_inbox_tags, _Unset):
            payload["remove_inbox_tags"] = remove_inbox_tags

        resp = await self._core._session.patch(f"/documents/{id}/", json=payload)
        return Document.model_validate(resp.json())

    async def delete(self, id: int) -> None:
        """Permanently delete a document.

        Args:
            id: Numeric ID of the document to delete.

        Raises:
            ~easypaperless.exceptions.NotFoundError: If no document exists
                with that ID.
        """
        logger.debug("Deleting document id=%d", id)
        await self._core._session.delete(f"/documents/{id}/")

    async def download(self, id: int, *, original: bool = False) -> bytes:
        """Download the binary content of a document.

        Args:
            id: Numeric ID of the document to download.
            original: If ``False`` *(default)*, returns the archived PDF.
                If ``True``, returns the original uploaded file.

        Returns:
            Raw file bytes.
        """
        endpoint = "download" if original else "archive"
        resp = await self._core._session.get_download(f"/documents/{id}/{endpoint}/")
        content_type = resp.headers.get("content-type", "")
        if "text/html" in content_type or resp.content[:9].lower().startswith(b"<!doctype"):
            raise ServerError(
                f"Download returned an HTML page (content-type: {content_type!r}). "
                "The server redirected to a login page even after re-attaching auth.",
                status_code=None,
            )
        return resp.content

    async def upload(
        self,
        file: str | Path,
        *,
        title: str | None = None,
        created: date | str | None = None,
        correspondent: int | str | None | _Unset = UNSET,
        document_type: int | str | None | _Unset = UNSET,
        storage_path: int | str | None | _Unset = UNSET,
        tags: List[int | str] | None = None,
        archive_serial_number: int | None | _Unset = UNSET,
        custom_fields: List[dict[str, Any]] | None = None,
        wait: bool = False,
        poll_interval: float | None = None,
        poll_timeout: float | None = None,
    ) -> str | Document:
        """Upload a document to paperless-ngx.

        Args:
            file: Path to the file to upload.
            title: Title to assign to the document.
            created: Creation date as an ISO-8601 string (``"YYYY-MM-DD"``) or a
                :class:`~datetime.date` object.
            correspondent: Correspondent to assign, as an ID or name.
            document_type: Document type to assign, as an ID or name.
            storage_path: Storage path to assign, as an ID or name.
            tags: Tags to assign, as IDs or names.
            archive_serial_number: Archive serial number to assign.
            custom_fields: List of ``{"field": <field_id>, "value": ...}`` dicts.
            wait: If ``False`` *(default)*, returns immediately with the task ID.
                If ``True``, polls until processing completes.
            poll_interval: Override the client-level ``poll_interval`` (in seconds).
            poll_timeout: Override the client-level ``poll_timeout`` (in seconds).

        Returns:
            The Celery task ID string when ``wait=False``, or the fully
            processed :class:`~easypaperless.models.documents.Document`
            when ``wait=True``.

        Raises:
            ~easypaperless.exceptions.UploadError: If processing fails.
            ~easypaperless.exceptions.TaskTimeoutError: If timeout is exceeded.
        """
        resolver = self._core._resolver
        file_path = Path(file)
        file_bytes = file_path.read_bytes()
        logger.info("Uploading %r (%d bytes)", file_path.name, len(file_bytes))

        data: dict[str, Any] = {}
        if title is not None:
            data["title"] = title
        if created is not None:
            data["created"] = self._format_date_value(created)
        if not isinstance(correspondent, _Unset) and correspondent is not None:
            data["correspondent"] = await resolver.resolve("correspondents", correspondent)
        if not isinstance(document_type, _Unset) and document_type is not None:
            data["document_type"] = await resolver.resolve("document_types", document_type)
        if not isinstance(storage_path, _Unset) and storage_path is not None:
            data["storage_path"] = await resolver.resolve("storage_paths", storage_path)
        if tags is not None:
            resolved = await resolver.resolve_list("tags", tags)
            data["tags"] = resolved
        if not isinstance(archive_serial_number, _Unset) and archive_serial_number is not None:
            data["archive_serial_number"] = archive_serial_number
        if custom_fields is not None:
            data["custom_fields"] = json.dumps(custom_fields)

        files = {"document": (file_path.name, file_bytes)}
        resp = await self._core._session.post("/documents/post_document/", data=data, files=files)
        task_id: str = resp.text.strip('"')
        logger.debug("Upload accepted, task_id=%r", task_id)

        if not wait:
            return task_id

        interval = poll_interval if poll_interval is not None else self._core._poll_interval
        timeout = poll_timeout if poll_timeout is not None else self._core._poll_timeout
        return await self._poll_task(task_id, poll_interval=interval, poll_timeout=timeout)

    async def _poll_task(
        self, task_id: str, *, poll_interval: float, poll_timeout: float
    ) -> Document:
        start = time.monotonic()
        deadline = start + poll_timeout
        while time.monotonic() < deadline:
            resp = await self._core._session.get("/tasks/", params={"task_id": task_id})
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
                    raise UploadError(f"Task {task_id!r} succeeded but returned no document ID")
                doc_id = int(task.related_document)
                logger.info("Task %r succeeded, document_id=%d", task_id, doc_id)
                return await self.get(doc_id)
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

    # -------------------------------------------------------------------------
    # Document bulk operations
    # -------------------------------------------------------------------------

    async def bulk_edit(self, document_ids: List[int], method: str, **parameters: Any) -> None:
        """Execute a bulk-edit operation on a list of documents.

        Args:
            document_ids: List of document IDs to operate on.
            method: Bulk-edit method name (e.g. ``"add_tag"``, ``"delete"``).
            **parameters: Additional keyword arguments forwarded to the API.
        """
        payload = {"documents": document_ids, "method": method, "parameters": parameters}
        await self._core._session.post("/documents/bulk_edit/", json=payload, timeout=120.0)

    async def bulk_add_tag(self, document_ids: List[int], tag: int | str) -> None:
        """Add a tag to multiple documents in a single request.

        Args:
            document_ids: List of document IDs to tag.
            tag: Tag to add, as an ID or name.
        """
        tag_id = await self._core._resolver.resolve("tags", tag)
        await self.bulk_edit(document_ids, "add_tag", tag=tag_id)

    async def bulk_remove_tag(self, document_ids: List[int], tag: int | str) -> None:
        """Remove a tag from multiple documents in a single request.

        Args:
            document_ids: List of document IDs to un-tag.
            tag: Tag to remove, as an ID or name.
        """
        tag_id = await self._core._resolver.resolve("tags", tag)
        await self.bulk_edit(document_ids, "remove_tag", tag=tag_id)

    async def bulk_modify_tags(
        self,
        document_ids: List[int],
        *,
        add_tags: List[int | str] | None = None,
        remove_tags: List[int | str] | None = None,
    ) -> None:
        """Add and/or remove tags on multiple documents atomically.

        Args:
            document_ids: List of document IDs to modify.
            add_tags: Tags to add, as IDs or names.
            remove_tags: Tags to remove, as IDs or names.
        """
        resolver = self._core._resolver
        add_ids = await resolver.resolve_list("tags", add_tags or [])
        remove_ids = await resolver.resolve_list("tags", remove_tags or [])
        await self.bulk_edit(document_ids, "modify_tags", add_tags=add_ids, remove_tags=remove_ids)

    async def bulk_delete(self, document_ids: List[int]) -> None:
        """Permanently delete multiple documents in a single request.

        Args:
            document_ids: List of document IDs to delete.
        """
        await self.bulk_edit(document_ids, "delete")

    async def bulk_set_correspondent(
        self, document_ids: List[int], correspondent: int | str | None
    ) -> None:
        """Assign a correspondent to multiple documents in a single request.

        Args:
            document_ids: List of document IDs to modify.
            correspondent: Correspondent to assign, as an ID or name.
                Pass ``None`` to clear.
        """
        cor_id: int | None = None
        if correspondent is not None:
            cor_id = await self._core._resolver.resolve("correspondents", correspondent)
        await self.bulk_edit(document_ids, "set_correspondent", correspondent=cor_id)

    async def bulk_set_document_type(
        self, document_ids: List[int], document_type: int | str | None
    ) -> None:
        """Assign a document type to multiple documents in a single request.

        Args:
            document_ids: List of document IDs to modify.
            document_type: Document type to assign, as an ID or name.
                Pass ``None`` to clear.
        """
        dt_id: int | None = None
        if document_type is not None:
            dt_id = await self._core._resolver.resolve("document_types", document_type)
        await self.bulk_edit(document_ids, "set_document_type", document_type=dt_id)

    async def bulk_set_storage_path(
        self, document_ids: List[int], storage_path: int | str | None
    ) -> None:
        """Assign a storage path to multiple documents in a single request.

        Args:
            document_ids: List of document IDs to modify.
            storage_path: Storage path to assign, as an ID or name.
                Pass ``None`` to clear.
        """
        sp_id: int | None = None
        if storage_path is not None:
            sp_id = await self._core._resolver.resolve("storage_paths", storage_path)
        await self.bulk_edit(document_ids, "set_storage_path", storage_path=sp_id)

    async def bulk_modify_custom_fields(
        self,
        document_ids: List[int],
        *,
        add_fields: List[dict[str, Any]] | None = None,
        remove_fields: List[int] | None = None,
    ) -> None:
        """Add and/or remove custom field values on multiple documents.

        Args:
            document_ids: List of document IDs to modify.
            add_fields: Custom-field value dicts to add.
            remove_fields: Custom-field IDs whose values should be removed.
        """
        await self.bulk_edit(
            document_ids,
            "modify_custom_fields",
            add_custom_fields=add_fields or [],
            remove_custom_fields=remove_fields or [],
        )

    async def bulk_set_permissions(
        self,
        document_ids: List[int],
        *,
        set_permissions: SetPermissions | None = None,
        owner: int | None = None,
        merge: bool = False,
    ) -> None:
        """Set permissions and/or owner on multiple documents.

        Args:
            document_ids: List of document IDs to modify.
            set_permissions: Explicit view/change permission sets.
            owner: Numeric user ID to assign as document owner.
            merge: When ``True``, new permissions are merged with existing ones.
        """
        params: dict[str, Any] = {"merge": merge}
        if set_permissions is not None:
            params["set_permissions"] = set_permissions.model_dump()
        if owner is not None:
            params["owner"] = owner
        await self.bulk_edit(document_ids, "set_permissions", **params)
