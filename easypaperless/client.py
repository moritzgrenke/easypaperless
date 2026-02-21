"""Async PaperlessClient — the primary public interface."""

from __future__ import annotations

import asyncio
import logging
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

from easypaperless._internal.http import HttpSession
from easypaperless._internal.resolvers import NameResolver
from easypaperless.exceptions import ServerError, TaskTimeoutError, UploadError
from easypaperless.models.correspondents import Correspondent
from easypaperless.models.custom_fields import CustomField
from easypaperless.models.document_types import DocumentType
from easypaperless.models.documents import Document, DocumentMetadata, Task, TaskStatus
from easypaperless.models.storage_paths import StoragePath
from easypaperless.models.tags import Tag

_SEARCH_MODE_MAP = {
    "title": "title__icontains",
    "title_or_text": "search",
    "query": "query",
    "original_filename": "original_filename__icontains",
}

_RESOURCE_MODELS = {
    "tags": Tag,
    "correspondents": Correspondent,
    "document_types": DocumentType,
    "storage_paths": StoragePath,
    "custom_fields": CustomField,
}


class PaperlessClient:
    """Async client for the paperless-ngx API.

    All operations are flat methods on the client.  String names are resolved
    to integer IDs automatically wherever the API requires IDs (tags,
    correspondents, document types, storage paths).

    Use as an async context manager to ensure the underlying HTTP connection
    pool is closed when you are done:

    Example:
        async with PaperlessClient(url="http://localhost:8000", api_key="abc") as client:
            docs = await client.list_documents()
    """

    def __init__(
        self,
        url: str,
        api_key: str,
        *,
        poll_interval: float = 2.0,
        poll_timeout: float = 60.0,
    ) -> None:
        """Create an async paperless-ngx client.

        Args:
            url: Base URL of the paperless-ngx instance
                (e.g. ``"http://localhost:8000"``).
            api_key: API token.  Generate one in paperless-ngx under
                *Settings → API → Generate Token*.
            poll_interval: Seconds between status checks when ``wait=True``
                is passed to :meth:`upload_document`.  Default: ``2.0``.
            poll_timeout: Maximum seconds to wait for a document to finish
                processing before raising
                :exc:`~easypaperless.exceptions.TaskTimeoutError`.
                Default: ``60.0``.
        """
        self._session = HttpSession(base_url=url, api_key=api_key)
        self._resolver = NameResolver(self._session)
        self._poll_interval = poll_interval
        self._poll_timeout = poll_timeout

    async def close(self) -> None:
        """Close the underlying HTTP connection pool.

        Called automatically when used as an async context manager.
        """
        await self._session.close()

    async def __aenter__(self) -> PaperlessClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    # ------------------------------------------------------------------
    # Documents
    # ------------------------------------------------------------------

    async def get_document(self, id: int, *, include_metadata: bool = False) -> Document:
        """Fetch a single document by its ID.

        Args:
            id: Numeric paperless-ngx document ID.
            include_metadata: When ``True``, the extended file-level metadata
                (checksums, sizes, MIME type) is fetched concurrently from
                ``/documents/{id}/metadata/`` and attached to
                :attr:`~easypaperless.models.documents.Document.metadata`.
                Default: ``False``.

        Returns:
            The :class:`~easypaperless.models.documents.Document` with the
            given ID.  When ``include_metadata=True`` the ``metadata``
            attribute is populated; otherwise it is ``None``.

        Raises:
            ~easypaperless.exceptions.NotFoundError: If no document exists
                with that ID.
        """
        if include_metadata:
            doc_resp, meta_resp = await asyncio.gather(
                self._session.get(f"/documents/{id}/"),
                self._session.get(f"/documents/{id}/metadata/"),
            )
            data = doc_resp.json()
            data["metadata"] = meta_resp.json()
        else:
            resp = await self._session.get(f"/documents/{id}/")
            data = resp.json()
        return Document.model_validate(data)

    async def get_document_metadata(self, id: int) -> DocumentMetadata:
        """Fetch the extended file-level metadata for a document.

        This is a lower-overhead alternative to
        ``get_document(id, include_metadata=True)`` when you only need the
        metadata and not the full document object.

        Args:
            id: Numeric paperless-ngx document ID.

        Returns:
            A :class:`~easypaperless.models.documents.DocumentMetadata`
            instance containing checksums, sizes, MIME type, and embedded
            file metadata.

        Raises:
            ~easypaperless.exceptions.NotFoundError: If no document exists
                with that ID.
        """
        resp = await self._session.get(f"/documents/{id}/metadata/")
        return DocumentMetadata.model_validate(resp.json())

    async def list_documents(
        self,
        *,
        search: str | None = None,
        search_mode: str = "title_or_text",
        tags: list[int | str] | None = None,
        any_tag: list[int | str] | None = None,
        exclude_tags: list[int | str] | None = None,
        correspondent: int | str | None = None,
        any_correspondent: list[int | str] | None = None,
        exclude_correspondents: list[int | str] | None = None,
        document_type: int | str | None = None,
        any_document_type: list[int | str] | None = None,
        exclude_document_types: list[int | str] | None = None,
        asn: int | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        added_after: str | None = None,
        added_before: str | None = None,
        modified_after: str | None = None,
        modified_before: str | None = None,
        checksum: str | None = None,
        page_size: int = 25,
        page: int | None = None,
        ordering: str | None = None,
        descending: bool = False,
        max_results: int | None = None,
    ) -> list[Document]:
        """Return a filtered list of documents.

        All tag, correspondent, and document-type parameters accept either
        integer IDs or string names — names are resolved to IDs transparently.

        Args:
            search: Search string.  Behaviour depends on ``search_mode``.
            search_mode: How ``search`` is applied.  One of:

                * ``"title_or_text"`` *(default)* — full-text search across
                  title and OCR content (Whoosh FTS, raw API ``search``
                  parameter).
                * ``"title"`` — case-insensitive substring match on title
                  only (raw API ``title__icontains``).
                * ``"query"`` — paperless query language, e.g.
                  ``"tag:invoice date:[2024 TO *]"`` (raw API ``query``).
                * ``"original_filename"`` — case-insensitive substring match
                  on the original file name (raw API
                  ``original_filename__icontains``).

            tags: Documents must have **all** of these tags (AND semantics).
                Accepts tag IDs or tag names.
            any_tag: Documents must have **at least one** of these tags
                (OR semantics).  Accepts tag IDs or tag names.
            exclude_tags: Documents must have **none** of these tags.
                Accepts tag IDs or tag names.
            correspondent: Filter to documents assigned to exactly this
                correspondent.  Accepts a correspondent ID or name.
            any_correspondent: Filter to documents assigned to **any** of
                these correspondents (OR semantics).  Accepts IDs or names.
                Takes precedence over ``correspondent`` when both are given.
            exclude_correspondents: Exclude documents assigned to any of
                these correspondents.  Accepts IDs or names.
            document_type: Filter to documents of exactly this type.
                Accepts a document-type ID or name.
            any_document_type: Filter to documents whose type is **any** of
                these (OR semantics).  Accepts IDs or names.  Takes
                precedence over ``document_type`` when both are given.
            exclude_document_types: Exclude documents whose type is any of
                these.  Accepts IDs or names.
            asn: Filter by archive serial number.
            created_after: ISO-8601 date string (``"YYYY-MM-DD"``).  Only
                documents created **after** this date are returned.
            created_before: ISO-8601 date string (``"YYYY-MM-DD"``).  Only
                documents created **before** this date are returned.
            added_after: ISO-8601 date string (``"YYYY-MM-DD"``).  Only
                documents **added** (ingested) after this date are returned.
            added_before: ISO-8601 date string (``"YYYY-MM-DD"``).  Only
                documents **added** (ingested) before this date are returned.
            modified_after: ISO-8601 date string (``"YYYY-MM-DD"``).  Only
                documents **modified** after this date are returned.
            modified_before: ISO-8601 date string (``"YYYY-MM-DD"``).  Only
                documents **modified** before this date are returned.
            checksum: MD5 checksum of the original file (exact match).
                Returns only the document whose original file matches this
                checksum.
            page_size: Number of results per API page.  Default: ``25``.
                Increase to reduce the number of HTTP requests for large
                result sets.
            page: Return only this specific page of results (1-based). When
                set, auto-pagination is disabled and only the results from
                that single page are returned. Use together with ``page_size``
                to control page size. Default: ``None`` (auto-paginate through
                all pages).
            ordering: Field name to sort by. Examples: ``"created"``,
                ``"title"``, ``"added"``. Use together with ``descending`` to
                control direction. Default: ``None`` (server default ordering).
            descending: When ``True``, reverses the sort direction of
                ``ordering``. Ignored when ``ordering`` is ``None``.
                Default: ``False``.
            max_results: Stop fetching pages once this many documents have
                been collected and return at most this many results.
                ``None`` *(default)* returns everything.

        Returns:
            List of :class:`~easypaperless.models.documents.Document`
            objects.
        """
        params: dict[str, Any] = {"page_size": page_size}

        if search is not None:
            api_param = _SEARCH_MODE_MAP.get(search_mode, "search")
            params[api_param] = search

        if tags is not None:
            resolved = await self._resolver.resolve_list("tags", tags)
            params["tags__id__all"] = ",".join(str(t) for t in resolved)

        if any_tag is not None:
            resolved = await self._resolver.resolve_list("tags", any_tag)
            params["tags__id__in"] = ",".join(str(t) for t in resolved)

        if exclude_tags is not None:
            resolved = await self._resolver.resolve_list("tags", exclude_tags)
            params["tags__id__none"] = ",".join(str(t) for t in resolved)

        if any_correspondent is not None:
            resolved = await self._resolver.resolve_list("correspondents", any_correspondent)
            params["correspondent__id__in"] = ",".join(str(c) for c in resolved)
        elif correspondent is not None:
            resolved_id = await self._resolver.resolve("correspondents", correspondent)
            params["correspondent__id__in"] = resolved_id

        if exclude_correspondents is not None:
            resolved = await self._resolver.resolve_list("correspondents", exclude_correspondents)
            params["correspondent__id__none"] = ",".join(str(c) for c in resolved)

        if any_document_type is not None:
            resolved = await self._resolver.resolve_list("document_types", any_document_type)
            params["document_type__id__in"] = ",".join(str(d) for d in resolved)
        elif document_type is not None:
            resolved_id = await self._resolver.resolve("document_types", document_type)
            params["document_type"] = resolved_id

        if exclude_document_types is not None:
            resolved = await self._resolver.resolve_list("document_types", exclude_document_types)
            params["document_type__id__none"] = ",".join(str(d) for d in resolved)

        if asn is not None:
            params["archive_serial_number"] = asn

        if created_after is not None:
            params["created__date__gt"] = created_after

        if created_before is not None:
            params["created__date__lt"] = created_before

        if added_after is not None:
            params["added__date__gt"] = added_after

        if added_before is not None:
            params["added__date__lt"] = added_before

        if modified_after is not None:
            params["modified__date__gt"] = modified_after

        if modified_before is not None:
            params["modified__date__lt"] = modified_before

        if checksum is not None:
            params["checksum"] = checksum

        if ordering is not None:
            params["ordering"] = f"-{ordering}" if descending else ordering

        if page is not None:
            params["page"] = page
            resp = await self._session.get("/documents/", params=params)
            items = resp.json().get("results", [])
            if max_results is not None:
                items = items[:max_results]
            return [Document.model_validate(item) for item in items]

        items = await self._session.get_all_pages("/documents/", params, max_results=max_results)
        return [Document.model_validate(item) for item in items]

    async def update_document(
        self,
        id: int,
        *,
        title: str | None = None,
        date: str | None = None,
        correspondent: int | str | None = None,
        document_type: int | str | None = None,
        storage_path: int | str | None = None,
        tags: list[int | str] | None = None,
        asn: int | None = None,
        custom_fields: list[dict] | None = None,
    ) -> Document:
        """Partially update a document (PATCH semantics — only passed fields change).

        Args:
            id: Numeric ID of the document to update.
            title: New document title.
            date: Creation date as an ISO-8601 string (``"YYYY-MM-DD"``).
            correspondent: Correspondent to assign, as an ID or name.
                Pass ``0`` to clear.
            document_type: Document type to assign, as an ID or name.
                Pass ``0`` to clear.
            storage_path: Storage path to assign, as an ID or name.
                Pass ``0`` to clear.
            tags: Full replacement list of tags (IDs or names).  The existing
                tag list is replaced, not merged.
            asn: Archive serial number to assign.
            custom_fields: List of ``{"field": <field_id>, "value": ...}``
                dicts.  Replaces the existing custom-field values.

        Returns:
            The updated :class:`~easypaperless.models.documents.Document`.
        """
        logger.debug("Updating document id=%d", id)
        payload: dict[str, Any] = {}

        if title is not None:
            payload["title"] = title
        if date is not None:
            payload["created"] = date
        if correspondent is not None:
            payload["correspondent"] = await self._resolver.resolve("correspondents", correspondent)
        if document_type is not None:
            payload["document_type"] = await self._resolver.resolve("document_types", document_type)
        if storage_path is not None:
            payload["storage_path"] = await self._resolver.resolve("storage_paths", storage_path)
        if tags is not None:
            payload["tags"] = await self._resolver.resolve_list("tags", tags)
        if asn is not None:
            payload["archive_serial_number"] = asn
        if custom_fields is not None:
            payload["custom_fields"] = custom_fields

        resp = await self._session.patch(f"/documents/{id}/", json=payload)
        return Document.model_validate(resp.json())

    async def delete_document(self, id: int) -> None:
        """Permanently delete a document.

        Args:
            id: Numeric ID of the document to delete.

        Raises:
            ~easypaperless.exceptions.NotFoundError: If no document exists
                with that ID.
        """
        logger.debug("Deleting document id=%d", id)
        await self._session.delete(f"/documents/{id}/")

    async def download_document(self, id: int, *, original: bool = False) -> bytes:
        """Download the binary content of a document.

        Args:
            id: Numeric ID of the document to download.
            original: If ``False`` *(default)*, returns the archived
                (post-processed) PDF.  If ``True``, returns the original
                file that was uploaded.

        Returns:
            Raw file bytes.
        """
        endpoint = "download" if original else "archive"
        resp = await self._session.get_download(f"/documents/{id}/{endpoint}/")
        content_type = resp.headers.get("content-type", "")
        if "text/html" in content_type or resp.content[:9].lower().startswith(b"<!doctype"):
            raise ServerError(
                f"Download returned an HTML page (content-type: {content_type!r}). "
                "The server redirected to a login page even after re-attaching auth. "
                "Run with --verbose to see redirect details.",
                status_code=None,
            )
        return resp.content

    # ------------------------------------------------------------------
    # Upload
    # ------------------------------------------------------------------

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
            logger.debug("Polling task %r (status=%s, elapsed=%.1fs)", task_id, task.status.value, elapsed)
            if task.status == TaskStatus.SUCCESS:
                doc_id = int(task.related_document)  # type: ignore[arg-type]
                logger.info("Task %r succeeded, document_id=%d", task_id, doc_id)
                return await self.get_document(doc_id)
            elif task.status == TaskStatus.FAILURE:
                logger.warning("Task %r failed: %s", task_id, task.result)
                raise UploadError(f"Document processing failed: {task.result}")
            await asyncio.sleep(poll_interval)

        elapsed = time.monotonic() - start
        logger.warning("Task %r timed out after %.1fs", task_id, elapsed)
        raise TaskTimeoutError(f"Task {task_id!r} did not complete within {poll_timeout}s")

    # ------------------------------------------------------------------
    # Bulk operations
    # ------------------------------------------------------------------

    async def bulk_edit(
        self, document_ids: list[int], method: str, **parameters: Any
    ) -> None:
        """Execute a bulk-edit operation on a list of documents.

        This is a low-level method; prefer the higher-level helpers such as
        :meth:`bulk_add_tag`, :meth:`bulk_remove_tag`, and
        :meth:`bulk_modify_tags`.

        Args:
            document_ids: List of document IDs to operate on.
            method: Bulk-edit method name as recognised by paperless-ngx
                (e.g. ``"add_tag"``, ``"remove_tag"``, ``"delete"``).
            **parameters: Additional keyword arguments forwarded to the API as
                the ``parameters`` object.
        """
        payload = {"documents": document_ids, "method": method, "parameters": parameters}
        await self._session.post("/documents/bulk_edit/", json=payload)

    async def bulk_add_tag(self, document_ids: list[int], tag: int | str) -> None:
        """Add a tag to multiple documents in a single request.

        Args:
            document_ids: List of document IDs to tag.
            tag: Tag to add, as an ID or name.
        """
        tag_id = await self._resolver.resolve("tags", tag)
        await self.bulk_edit(document_ids, "add_tag", tag=tag_id)

    async def bulk_remove_tag(self, document_ids: list[int], tag: int | str) -> None:
        """Remove a tag from multiple documents in a single request.

        Args:
            document_ids: List of document IDs to un-tag.
            tag: Tag to remove, as an ID or name.
        """
        tag_id = await self._resolver.resolve("tags", tag)
        await self.bulk_edit(document_ids, "remove_tag", tag=tag_id)

    async def bulk_modify_tags(
        self,
        document_ids: list[int],
        *,
        add_tags: list[int | str] | None = None,
        remove_tags: list[int | str] | None = None,
    ) -> None:
        """Add and/or remove tags on multiple documents atomically.

        Args:
            document_ids: List of document IDs to modify.
            add_tags: Tags to add, as IDs or names.
            remove_tags: Tags to remove, as IDs or names.
        """
        add_ids = await self._resolver.resolve_list("tags", add_tags or [])
        remove_ids = await self._resolver.resolve_list("tags", remove_tags or [])
        await self.bulk_edit(document_ids, "modify_tags", add_tags=add_ids, remove_tags=remove_ids)

    async def bulk_delete(self, document_ids: list[int]) -> None:
        """Permanently delete multiple documents in a single request.

        Args:
            document_ids: List of document IDs to delete.
        """
        await self.bulk_edit(document_ids, "delete")

    async def bulk_edit_objects(
        self,
        object_type: str,
        object_ids: list[int],
        operation: str,
        **parameters: Any,
    ) -> None:
        """Execute a bulk operation on non-document objects (tags, etc.).

        Args:
            object_type: The paperless-ngx object type string (e.g.
                ``"tags"``, ``"correspondents"``).
            object_ids: List of object IDs to operate on.
            operation: Operation name recognised by the
                ``/bulk_edit_objects/`` endpoint.
            **parameters: Additional keyword arguments forwarded directly to
                the API payload.
        """
        payload = {
            "objects": object_ids,
            "object_type": object_type,
            "operation": operation,
            **parameters,
        }
        await self._session.post("/bulk_edit_objects/", json=payload)

    # ------------------------------------------------------------------
    # Internal resource helpers
    # ------------------------------------------------------------------

    async def _list_resource(
        self,
        resource: str,
        model_class: type,
        params: dict[str, Any] | None = None,
    ) -> list:
        if params and "page" in params:
            resp = await self._session.get(f"/{resource}/", params=params)
            items = resp.json().get("results", [])
        else:
            items = await self._session.get_all_pages(f"/{resource}/", params)
        return [model_class.model_validate(item) for item in items]

    async def _get_resource(self, resource: str, id: int, model_class: type):
        resp = await self._session.get(f"/{resource}/{id}/")
        return model_class.model_validate(resp.json())

    async def _create_resource(self, resource: str, model_class: type, **kwargs: Any):
        logger.debug("Creating %s resource", resource)
        payload = {k: v for k, v in kwargs.items() if v is not None}
        resp = await self._session.post(f"/{resource}/", json=payload)
        self._resolver.invalidate(resource)
        return model_class.model_validate(resp.json())

    async def _update_resource(self, resource: str, id: int, model_class: type, **kwargs: Any):
        logger.debug("Updating %s resource id=%d", resource, id)
        payload = {k: v for k, v in kwargs.items() if v is not None}
        resp = await self._session.patch(f"/{resource}/{id}/", json=payload)
        self._resolver.invalidate(resource)
        return model_class.model_validate(resp.json())

    async def _delete_resource(self, resource: str, id: int) -> None:
        logger.debug("Deleting %s resource id=%d", resource, id)
        await self._session.delete(f"/{resource}/{id}/")
        self._resolver.invalidate(resource)

    # ------------------------------------------------------------------
    # Tags
    # ------------------------------------------------------------------

    async def list_tags(
        self,
        *,
        ids: list[int] | None = None,
        name_contains: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
        ordering: str | None = None,
        descending: bool = False,
    ) -> list[Tag]:
        """Return tags defined in paperless-ngx.

        Args:
            ids: Return only tags whose ID is in this list.
            name_contains: Case-insensitive substring filter on tag name
                (raw API ``name__icontains``).
            page: Return only this specific page (1-based). Disables
                auto-pagination. Default: ``None`` (return all).
            page_size: Number of results per page. When omitted, the server
                default is used.
            ordering: Field to sort by. Examples: ``"name"``, ``"id"``.
            descending: When ``True``, reverses the sort direction of
                ``ordering``. Ignored when ``ordering`` is ``None``.

        Returns:
            List of :class:`~easypaperless.models.tags.Tag` objects.
        """
        params: dict[str, Any] = {}
        if ids is not None:
            params["id__in"] = ",".join(str(i) for i in ids)
        if name_contains is not None:
            params["name__icontains"] = name_contains
        if page is not None:
            params["page"] = page
        if page_size is not None:
            params["page_size"] = page_size
        if ordering is not None:
            params["ordering"] = f"-{ordering}" if descending else ordering
        return await self._list_resource("tags", Tag, params or None)

    async def get_tag(self, id: int) -> Tag:
        """Fetch a single tag by its ID.

        Args:
            id: Numeric tag ID.

        Returns:
            The :class:`~easypaperless.models.tags.Tag` with the given ID.

        Raises:
            ~easypaperless.exceptions.NotFoundError: If no tag exists with
                that ID.
        """
        return await self._get_resource("tags", id, Tag)

    async def create_tag(
        self,
        *,
        name: str,
        color: str | None = None,
        is_inbox_tag: bool | None = None,
        match: str | None = None,
        matching_algorithm: int | None = None,
        is_insensitive: bool | None = None,
        parent: int | None = None,
    ) -> Tag:
        """Create a new tag.

        Args:
            name: Tag name. Must be unique.
            color: Background colour in the paperless-ngx UI as a CSS hex
                string (e.g. ``"#ff0000"``).
            is_inbox_tag: When ``True``, newly ingested documents receive this
                tag automatically until processed. At most one tag should be
                the inbox tag.
            match: Auto-matching pattern tested against incoming document
                content. Interpretation depends on ``matching_algorithm``.
            matching_algorithm: Controls how ``match`` is applied: ``0``=none,
                ``1``=any word, ``2``=all words, ``3``=exact, ``4``=regex,
                ``5``=fuzzy, ``6``=auto (ML).
            is_insensitive: When ``True``, ``match`` is evaluated
                case-insensitively.
            parent: ID of an existing tag to use as parent, enabling
                hierarchical tag trees. ``None`` creates a root-level tag.

        Returns:
            The newly created :class:`~easypaperless.models.tags.Tag`.
        """
        return await self._create_resource(
            "tags",
            Tag,
            name=name,
            color=color,
            is_inbox_tag=is_inbox_tag,
            match=match,
            matching_algorithm=matching_algorithm,
            is_insensitive=is_insensitive,
            parent=parent,
        )

    async def update_tag(
        self,
        id: int,
        *,
        name: str | None = None,
        color: str | None = None,
        is_inbox_tag: bool | None = None,
        match: str | None = None,
        matching_algorithm: int | None = None,
        is_insensitive: bool | None = None,
        parent: int | None = None,
    ) -> Tag:
        """Partially update a tag (PATCH semantics).

        Args:
            id: Numeric ID of the tag to update.
            name: Tag name. Must be unique.
            color: Background colour in the paperless-ngx UI as a CSS hex
                string (e.g. ``"#00ff00"``).
            is_inbox_tag: When ``True``, newly ingested documents receive this
                tag automatically until processed. At most one tag should be
                the inbox tag.
            match: Auto-matching pattern tested against incoming document
                content. Interpretation depends on ``matching_algorithm``.
            matching_algorithm: Controls how ``match`` is applied: ``0``=none,
                ``1``=any word, ``2``=all words, ``3``=exact, ``4``=regex,
                ``5``=fuzzy, ``6``=auto (ML).
            is_insensitive: When ``True``, ``match`` is evaluated
                case-insensitively.
            parent: ID of an existing tag to use as parent, enabling
                hierarchical tag trees.

        Returns:
            The updated :class:`~easypaperless.models.tags.Tag`.
        """
        return await self._update_resource(
            "tags",
            id,
            Tag,
            name=name,
            color=color,
            is_inbox_tag=is_inbox_tag,
            match=match,
            matching_algorithm=matching_algorithm,
            is_insensitive=is_insensitive,
            parent=parent,
        )

    async def delete_tag(self, id: int) -> None:
        """Delete a tag.

        Args:
            id: Numeric ID of the tag to delete.

        Raises:
            ~easypaperless.exceptions.NotFoundError: If no tag exists with
                that ID.
        """
        await self._delete_resource("tags", id)

    # ------------------------------------------------------------------
    # Correspondents
    # ------------------------------------------------------------------

    async def list_correspondents(
        self,
        *,
        ids: list[int] | None = None,
        name_contains: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
        ordering: str | None = None,
        descending: bool = False,
    ) -> list[Correspondent]:
        """Return correspondents defined in paperless-ngx.

        Args:
            ids: Return only correspondents whose ID is in this list.
            name_contains: Case-insensitive substring filter on correspondent
                name (raw API ``name__icontains``).
            page: Return only this specific page (1-based). Disables
                auto-pagination. Default: ``None`` (return all).
            page_size: Number of results per page. When omitted, the server
                default is used.
            ordering: Field to sort by. Examples: ``"name"``, ``"id"``.
            descending: When ``True``, reverses the sort direction of
                ``ordering``. Ignored when ``ordering`` is ``None``.

        Returns:
            List of
            :class:`~easypaperless.models.correspondents.Correspondent`
            objects.
        """
        params: dict[str, Any] = {}
        if ids is not None:
            params["id__in"] = ",".join(str(i) for i in ids)
        if name_contains is not None:
            params["name__icontains"] = name_contains
        if page is not None:
            params["page"] = page
        if page_size is not None:
            params["page_size"] = page_size
        if ordering is not None:
            params["ordering"] = f"-{ordering}" if descending else ordering
        return await self._list_resource("correspondents", Correspondent, params or None)

    async def get_correspondent(self, id: int) -> Correspondent:
        """Fetch a single correspondent by its ID.

        Args:
            id: Numeric correspondent ID.

        Returns:
            The :class:`~easypaperless.models.correspondents.Correspondent`
            with the given ID.

        Raises:
            ~easypaperless.exceptions.NotFoundError: If no correspondent
                exists with that ID.
        """
        return await self._get_resource("correspondents", id, Correspondent)

    async def create_correspondent(
        self,
        *,
        name: str,
        match: str | None = None,
        matching_algorithm: int | None = None,
        is_insensitive: bool | None = None,
    ) -> Correspondent:
        """Create a new correspondent.

        Args:
            name: Correspondent name (sender/recipient). Must be unique.
            match: Auto-matching pattern tested against incoming document
                content. Interpretation depends on ``matching_algorithm``.
            matching_algorithm: Controls how ``match`` is applied: ``0``=none,
                ``1``=any word, ``2``=all words, ``3``=exact, ``4``=regex,
                ``5``=fuzzy, ``6``=auto (ML).
            is_insensitive: When ``True``, ``match`` is evaluated
                case-insensitively.

        Returns:
            The newly created
            :class:`~easypaperless.models.correspondents.Correspondent`.
        """
        return await self._create_resource(
            "correspondents",
            Correspondent,
            name=name,
            match=match,
            matching_algorithm=matching_algorithm,
            is_insensitive=is_insensitive,
        )

    async def update_correspondent(
        self,
        id: int,
        *,
        name: str | None = None,
        match: str | None = None,
        matching_algorithm: int | None = None,
        is_insensitive: bool | None = None,
    ) -> Correspondent:
        """Partially update a correspondent (PATCH semantics).

        Args:
            id: Numeric ID of the correspondent to update.
            name: Correspondent name (sender/recipient). Must be unique.
            match: Auto-matching pattern tested against incoming document
                content. Interpretation depends on ``matching_algorithm``.
            matching_algorithm: Controls how ``match`` is applied: ``0``=none,
                ``1``=any word, ``2``=all words, ``3``=exact, ``4``=regex,
                ``5``=fuzzy, ``6``=auto (ML).
            is_insensitive: When ``True``, ``match`` is evaluated
                case-insensitively.

        Returns:
            The updated
            :class:`~easypaperless.models.correspondents.Correspondent`.
        """
        return await self._update_resource(
            "correspondents",
            id,
            Correspondent,
            name=name,
            match=match,
            matching_algorithm=matching_algorithm,
            is_insensitive=is_insensitive,
        )

    async def delete_correspondent(self, id: int) -> None:
        """Delete a correspondent.

        Args:
            id: Numeric ID of the correspondent to delete.

        Raises:
            ~easypaperless.exceptions.NotFoundError: If no correspondent
                exists with that ID.
        """
        await self._delete_resource("correspondents", id)

    # ------------------------------------------------------------------
    # Document Types
    # ------------------------------------------------------------------

    async def list_document_types(
        self,
        *,
        ids: list[int] | None = None,
        name_contains: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
        ordering: str | None = None,
        descending: bool = False,
    ) -> list[DocumentType]:
        """Return document types defined in paperless-ngx.

        Args:
            ids: Return only document types whose ID is in this list.
            name_contains: Case-insensitive substring filter on document-type
                name (raw API ``name__icontains``).
            page: Return only this specific page (1-based). Disables
                auto-pagination. Default: ``None`` (return all).
            page_size: Number of results per page. When omitted, the server
                default is used.
            ordering: Field to sort by. Examples: ``"name"``, ``"id"``.
            descending: When ``True``, reverses the sort direction of
                ``ordering``. Ignored when ``ordering`` is ``None``.

        Returns:
            List of
            :class:`~easypaperless.models.document_types.DocumentType`
            objects.
        """
        params: dict[str, Any] = {}
        if ids is not None:
            params["id__in"] = ",".join(str(i) for i in ids)
        if name_contains is not None:
            params["name__icontains"] = name_contains
        if page is not None:
            params["page"] = page
        if page_size is not None:
            params["page_size"] = page_size
        if ordering is not None:
            params["ordering"] = f"-{ordering}" if descending else ordering
        return await self._list_resource("document_types", DocumentType, params or None)

    async def get_document_type(self, id: int) -> DocumentType:
        """Fetch a single document type by its ID.

        Args:
            id: Numeric document-type ID.

        Returns:
            The :class:`~easypaperless.models.document_types.DocumentType`
            with the given ID.

        Raises:
            ~easypaperless.exceptions.NotFoundError: If no document type
                exists with that ID.
        """
        return await self._get_resource("document_types", id, DocumentType)

    async def create_document_type(
        self,
        *,
        name: str,
        match: str | None = None,
        matching_algorithm: int | None = None,
        is_insensitive: bool | None = None,
    ) -> DocumentType:
        """Create a new document type.

        Args:
            name: Document-type name (e.g. ``"Invoice"``, ``"Receipt"``).
                Must be unique.
            match: Auto-matching pattern tested against incoming document
                content. Interpretation depends on ``matching_algorithm``.
            matching_algorithm: Controls how ``match`` is applied: ``0``=none,
                ``1``=any word, ``2``=all words, ``3``=exact, ``4``=regex,
                ``5``=fuzzy, ``6``=auto (ML).
            is_insensitive: When ``True``, ``match`` is evaluated
                case-insensitively.

        Returns:
            The newly created
            :class:`~easypaperless.models.document_types.DocumentType`.
        """
        return await self._create_resource(
            "document_types",
            DocumentType,
            name=name,
            match=match,
            matching_algorithm=matching_algorithm,
            is_insensitive=is_insensitive,
        )

    async def update_document_type(
        self,
        id: int,
        *,
        name: str | None = None,
        match: str | None = None,
        matching_algorithm: int | None = None,
        is_insensitive: bool | None = None,
    ) -> DocumentType:
        """Partially update a document type (PATCH semantics).

        Args:
            id: Numeric ID of the document type to update.
            name: Document-type name (e.g. ``"Invoice"``, ``"Receipt"``).
                Must be unique.
            match: Auto-matching pattern tested against incoming document
                content. Interpretation depends on ``matching_algorithm``.
            matching_algorithm: Controls how ``match`` is applied: ``0``=none,
                ``1``=any word, ``2``=all words, ``3``=exact, ``4``=regex,
                ``5``=fuzzy, ``6``=auto (ML).
            is_insensitive: When ``True``, ``match`` is evaluated
                case-insensitively.

        Returns:
            The updated
            :class:`~easypaperless.models.document_types.DocumentType`.
        """
        return await self._update_resource(
            "document_types",
            id,
            DocumentType,
            name=name,
            match=match,
            matching_algorithm=matching_algorithm,
            is_insensitive=is_insensitive,
        )

    async def delete_document_type(self, id: int) -> None:
        """Delete a document type.

        Args:
            id: Numeric ID of the document type to delete.

        Raises:
            ~easypaperless.exceptions.NotFoundError: If no document type
                exists with that ID.
        """
        await self._delete_resource("document_types", id)

    # ------------------------------------------------------------------
    # Storage Paths
    # ------------------------------------------------------------------

    async def list_storage_paths(
        self,
        *,
        ids: list[int] | None = None,
        name_contains: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
        ordering: str | None = None,
        descending: bool = False,
    ) -> list[StoragePath]:
        """Return storage paths defined in paperless-ngx.

        Args:
            ids: Return only storage paths whose ID is in this list.
            name_contains: Case-insensitive substring filter on storage-path
                name (raw API ``name__icontains``).
            page: Return only this specific page (1-based). Disables
                auto-pagination. Default: ``None`` (return all).
            page_size: Number of results per page. When omitted, the server
                default is used.
            ordering: Field to sort by. Examples: ``"name"``, ``"id"``.
            descending: When ``True``, reverses the sort direction of
                ``ordering``. Ignored when ``ordering`` is ``None``.

        Returns:
            List of
            :class:`~easypaperless.models.storage_paths.StoragePath`
            objects.
        """
        params: dict[str, Any] = {}
        if ids is not None:
            params["id__in"] = ",".join(str(i) for i in ids)
        if name_contains is not None:
            params["name__icontains"] = name_contains
        if page is not None:
            params["page"] = page
        if page_size is not None:
            params["page_size"] = page_size
        if ordering is not None:
            params["ordering"] = f"-{ordering}" if descending else ordering
        return await self._list_resource("storage_paths", StoragePath, params or None)

    async def get_storage_path(self, id: int) -> StoragePath:
        """Fetch a single storage path by its ID.

        Args:
            id: Numeric storage-path ID.

        Returns:
            The :class:`~easypaperless.models.storage_paths.StoragePath`
            with the given ID.

        Raises:
            ~easypaperless.exceptions.NotFoundError: If no storage path
                exists with that ID.
        """
        return await self._get_resource("storage_paths", id, StoragePath)

    async def create_storage_path(
        self,
        *,
        name: str,
        path: str | None = None,
        match: str | None = None,
        matching_algorithm: int | None = None,
        is_insensitive: bool | None = None,
    ) -> StoragePath:
        """Create a new storage path.

        Args:
            name: Storage-path name. Must be unique.
            path: Template string for the archive file path. Supported
                placeholders: ``{created_year}``, ``{created_month}``,
                ``{created_day}``, ``{correspondent}``, ``{document_type}``,
                ``{title}``, ``{asn}``. Example:
                ``"{created_year}/{correspondent}/{title}"``. When omitted,
                the server default location is used.
            match: Auto-matching pattern tested against incoming document
                content. Interpretation depends on ``matching_algorithm``.
            matching_algorithm: Controls how ``match`` is applied: ``0``=none,
                ``1``=any word, ``2``=all words, ``3``=exact, ``4``=regex,
                ``5``=fuzzy, ``6``=auto (ML).
            is_insensitive: When ``True``, ``match`` is evaluated
                case-insensitively.

        Returns:
            The newly created
            :class:`~easypaperless.models.storage_paths.StoragePath`.
        """
        return await self._create_resource(
            "storage_paths",
            StoragePath,
            name=name,
            path=path,
            match=match,
            matching_algorithm=matching_algorithm,
            is_insensitive=is_insensitive,
        )

    async def update_storage_path(
        self,
        id: int,
        *,
        name: str | None = None,
        path: str | None = None,
        match: str | None = None,
        matching_algorithm: int | None = None,
        is_insensitive: bool | None = None,
    ) -> StoragePath:
        """Partially update a storage path (PATCH semantics).

        Args:
            id: Numeric ID of the storage path to update.
            name: Storage-path name. Must be unique.
            path: Template string for the archive file path. Supported
                placeholders: ``{created_year}``, ``{created_month}``,
                ``{created_day}``, ``{correspondent}``, ``{document_type}``,
                ``{title}``, ``{asn}``. Example: ``"{title}"``.
            match: Auto-matching pattern tested against incoming document
                content. Interpretation depends on ``matching_algorithm``.
            matching_algorithm: Controls how ``match`` is applied: ``0``=none,
                ``1``=any word, ``2``=all words, ``3``=exact, ``4``=regex,
                ``5``=fuzzy, ``6``=auto (ML).
            is_insensitive: When ``True``, ``match`` is evaluated
                case-insensitively.

        Returns:
            The updated
            :class:`~easypaperless.models.storage_paths.StoragePath`.
        """
        return await self._update_resource(
            "storage_paths",
            id,
            StoragePath,
            name=name,
            path=path,
            match=match,
            matching_algorithm=matching_algorithm,
            is_insensitive=is_insensitive,
        )

    async def delete_storage_path(self, id: int) -> None:
        """Delete a storage path.

        Args:
            id: Numeric ID of the storage path to delete.

        Raises:
            ~easypaperless.exceptions.NotFoundError: If no storage path
                exists with that ID.
        """
        await self._delete_resource("storage_paths", id)

    # ------------------------------------------------------------------
    # Custom Fields
    # ------------------------------------------------------------------

    async def list_custom_fields(
        self,
        *,
        page: int | None = None,
        page_size: int | None = None,
        ordering: str | None = None,
        descending: bool = False,
    ) -> list[CustomField]:
        """Return all custom fields defined in paperless-ngx.

        Args:
            page: Return only this specific page (1-based). Disables
                auto-pagination. Default: ``None`` (return all).
            page_size: Number of results per page. When omitted, the server
                default is used.
            ordering: Field to sort by. Examples: ``"name"``, ``"id"``.
            descending: When ``True``, reverses the sort direction of
                ``ordering``. Ignored when ``ordering`` is ``None``.

        Returns:
            List of
            :class:`~easypaperless.models.custom_fields.CustomField`
            objects.
        """
        params: dict[str, Any] = {}
        if page is not None:
            params["page"] = page
        if page_size is not None:
            params["page_size"] = page_size
        if ordering is not None:
            params["ordering"] = f"-{ordering}" if descending else ordering
        return await self._list_resource("custom_fields", CustomField, params or None)

    async def get_custom_field(self, id: int) -> CustomField:
        """Fetch a single custom field by its ID.

        Args:
            id: Numeric custom-field ID.

        Returns:
            The :class:`~easypaperless.models.custom_fields.CustomField`
            with the given ID.

        Raises:
            ~easypaperless.exceptions.NotFoundError: If no custom field
                exists with that ID.
        """
        return await self._get_resource("custom_fields", id, CustomField)

    async def create_custom_field(
        self,
        *,
        name: str,
        data_type: str,
        extra_data: Any | None = None,
    ) -> CustomField:
        """Create a new custom field.

        Args:
            name: Field name shown in the UI. Must be unique.
            data_type: Value type. One of ``"string"``, ``"boolean"``,
                ``"integer"``, ``"float"``, ``"monetary"``, ``"date"``,
                ``"url"``, ``"documentlink"``, ``"select"``.
            extra_data: Additional configuration for the field type. For
                ``data_type="select"``, pass
                ``{"select_options": ["Option A", "Option B"]}``. For all
                other types, leave as ``None``.

        Returns:
            The newly created
            :class:`~easypaperless.models.custom_fields.CustomField`.
        """
        return await self._create_resource(
            "custom_fields",
            CustomField,
            name=name,
            data_type=data_type,
            extra_data=extra_data,
        )

    async def update_custom_field(
        self,
        id: int,
        *,
        name: str | None = None,
        extra_data: Any | None = None,
    ) -> CustomField:
        """Partially update a custom field (PATCH semantics).

        Note:
            ``data_type`` is intentionally excluded — the paperless-ngx API
            does not allow changing the type of an existing custom field. To
            change the type, delete and recreate the field.

        Args:
            id: Numeric ID of the custom field to update.
            name: Field name shown in the UI. Must be unique.
            extra_data: Additional configuration for the field type (e.g.
                ``{"select_options": ["Option A", "Option B"]}`` for select
                fields). Passing ``None`` is a no-op and will not clear the
                existing value.

        Returns:
            The updated
            :class:`~easypaperless.models.custom_fields.CustomField`.
        """
        return await self._update_resource(
            "custom_fields",
            id,
            CustomField,
            name=name,
            extra_data=extra_data,
        )

    async def delete_custom_field(self, id: int) -> None:
        """Delete a custom field.

        Args:
            id: Numeric ID of the custom field to delete.

        Raises:
            ~easypaperless.exceptions.NotFoundError: If no custom field
                exists with that ID.
        """
        await self._delete_resource("custom_fields", id)
