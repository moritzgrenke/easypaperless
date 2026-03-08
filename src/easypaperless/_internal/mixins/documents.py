"""Documents resource mixin for PaperlessClient."""

from __future__ import annotations

import asyncio
import json
import logging
import re
from datetime import date, datetime
from typing import TYPE_CHECKING, Any, Callable

from easypaperless.exceptions import ServerError
from easypaperless.models.documents import Document, DocumentMetadata
from easypaperless.models.permissions import SetPermissions

if TYPE_CHECKING:
    from easypaperless._internal.http import HttpSession
    from easypaperless._internal.resolvers import NameResolver

logger = logging.getLogger(__name__)

_DATETIME_STR_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T")

_SEARCH_MODE_MAP = {
    "title": "title__icontains",
    "title_or_text": "search",
    "query": "query",
    "original_filename": "original_filename__icontains",
}


class DocumentsMixin:
    if TYPE_CHECKING:
        _session: HttpSession
        _resolver: NameResolver

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

    @staticmethod
    def _format_date_value(value: date | datetime | str) -> str:
        """Format a date/datetime/string value for API parameters."""
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, date):
            return value.isoformat()
        return value

    @staticmethod
    def _is_datetime(value: date | datetime | str) -> bool:
        """Return True if value represents a datetime (not a plain date).

        Handles ``datetime`` objects and ISO-8601 datetime strings
        (e.g. ``"2026-02-22T16:25:00+00:00"``).  Plain date strings
        (``"2026-02-22"``) and ``date`` objects return ``False``.
        """
        if isinstance(value, datetime):
            return True
        if isinstance(value, str):
            return bool(_DATETIME_STR_RE.match(value))
        return False

    async def list_documents(
        self,
        *,
        search: str | None = None,
        search_mode: str = "title_or_text",
        ids: list[int] | None = None,
        tags: list[int | str] | None = None,
        any_tags: list[int | str] | None = None,
        exclude_tags: list[int | str] | None = None,
        correspondent: int | str | None = None,
        any_correspondent: list[int | str] | None = None,
        exclude_correspondents: list[int | str] | None = None,
        document_type: int | str | None = None,
        any_document_type: list[int | str] | None = None,
        exclude_document_types: list[int | str] | None = None,
        storage_path: int | str | None = None,
        any_storage_paths: list[int | str] | None = None,
        exclude_storage_paths: list[int | str] | None = None,
        owner: int | None = None,
        exclude_owners: list[int] | None = None,
        custom_fields: list[int | str] | None = None,
        any_custom_fields: list[int | str] | None = None,
        exclude_custom_fields: list[int | str] | None = None,
        custom_field_query: list[Any] | None = None,
        archive_serial_number: int | None = None,
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
    ) -> list[Document]:
        """Return a filtered list of documents.

        All tag, correspondent, document-type, storage-path, and custom-field
        parameters accept either integer IDs or string names — names are
        resolved to IDs transparently.

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

            ids: Return only documents whose ID is in this list.
            tags: Documents must have **all** of these tags (AND semantics).
                Accepts tag IDs or tag names.
            any_tags: Documents must have **at least one** of these tags
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
            storage_path: Filter to documents assigned to exactly this
                storage path.  Accepts a storage path ID or name.
            any_storage_paths: Filter to documents assigned to **any** of
                these storage paths (OR semantics).  Accepts IDs or names.
                Takes precedence over ``storage_path`` when both are given.
            exclude_storage_paths: Exclude documents assigned to any of
                these storage paths.  Accepts IDs or names.
            owner: Filter to documents owned by this user ID.
            exclude_owners: Exclude documents owned by any of these user IDs.
            custom_fields: Documents must have **all** of these custom fields
                set (AND semantics).  Accepts custom field IDs or names.
            any_custom_fields: Documents must have **at least one** of these
                custom fields set (OR semantics).  Accepts IDs or names.
            exclude_custom_fields: Documents must have **none** of these
                custom fields set.  Accepts IDs or names.
            custom_field_query: Filter documents by custom field values using
                a structured query.  Simple form:
                ``["Invoice Amount", "gt", 100]``.  Compound form:
                ``["AND", [["Amount", "gt", 100], ["Status", "exact", "paid"]]]``.
                Field references accept integer IDs or string names (resolved
                server-side, not by the client).
            archive_serial_number: Filter by exact archive serial number.
            archive_serial_number_from: Filter by archive serial number
                greater than or equal to this value.
            archive_serial_number_till: Filter by archive serial number
                less than or equal to this value.
            created_after: ISO-8601 date string or ``date`` object.  Only
                documents created **after** this date are returned.
            created_before: ISO-8601 date string or ``date`` object.  Only
                documents created **before** this date are returned.
            added_after: Date, datetime, or ISO-8601 string.  Only
                documents **added** (ingested) after this date/time.
            added_from: Date, datetime, or ISO-8601 string.  Only
                documents **added** on or after this date/time.
            added_before: Date, datetime, or ISO-8601 string.  Only
                documents **added** before this date/time.
            added_until: Date, datetime, or ISO-8601 string.  Only
                documents **added** on or before this date/time.
            modified_after: Date, datetime, or ISO-8601 string.  Only
                documents **modified** after this date/time.
            modified_from: Date, datetime, or ISO-8601 string.  Only
                documents **modified** on or after this date/time.
            modified_before: Date, datetime, or ISO-8601 string.  Only
                documents **modified** before this date/time.
            modified_until: Date, datetime, or ISO-8601 string.  Only
                documents **modified** on or before this date/time.
            checksum: MD5 checksum of the original file (exact match).
            page_size: Number of results per API page.  Default: ``25``.
            page: Return only this specific page of results (1-based). When
                set, auto-pagination is disabled. Default: ``None``.
            ordering: Field name to sort by. Default: ``None``.
            descending: When ``True``, reverses the sort direction.
                Default: ``False``.
            max_results: Stop after collecting this many documents.
                Default: ``None``.
            on_page: Callback invoked after each page fetch.  Receives
                ``(fetched_so_far, total)``.  Ignored when ``page`` is set.

        Returns:
            List of :class:`~easypaperless.models.documents.Document`
            objects.
        """
        params: dict[str, Any] = {"page_size": page_size}

        if search is not None:
            api_param = _SEARCH_MODE_MAP.get(search_mode, "search")
            params[api_param] = search

        if ids is not None:
            params["id__in"] = ",".join(str(i) for i in ids)

        if tags is not None:
            resolved = await self._resolver.resolve_list("tags", tags)
            params["tags__id__all"] = ",".join(str(t) for t in resolved)

        if any_tags is not None:
            resolved = await self._resolver.resolve_list("tags", any_tags)
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

        # Storage path filters
        if any_storage_paths is not None:
            resolved = await self._resolver.resolve_list("storage_paths", any_storage_paths)
            params["storage_path__id__in"] = ",".join(str(s) for s in resolved)
        elif storage_path is not None:
            resolved_id = await self._resolver.resolve("storage_paths", storage_path)
            params["storage_path__id__in"] = resolved_id

        if exclude_storage_paths is not None:
            resolved = await self._resolver.resolve_list("storage_paths", exclude_storage_paths)
            params["storage_path__id__none"] = ",".join(str(s) for s in resolved)

        # Owner filters
        if owner is not None:
            params["owner__id__in"] = owner

        if exclude_owners is not None:
            params["owner__id__none"] = ",".join(str(o) for o in exclude_owners)

        # Custom field existence filters
        if custom_fields is not None:
            resolved = await self._resolver.resolve_list("custom_fields", custom_fields)
            params["custom_fields__id__all"] = ",".join(str(f) for f in resolved)

        if any_custom_fields is not None:
            resolved = await self._resolver.resolve_list("custom_fields", any_custom_fields)
            params["custom_fields__id__in"] = ",".join(str(f) for f in resolved)

        if exclude_custom_fields is not None:
            resolved = await self._resolver.resolve_list("custom_fields", exclude_custom_fields)
            params["custom_fields__id__none"] = ",".join(str(f) for f in resolved)

        # Custom field value query
        if custom_field_query is not None:
            params["custom_field_query"] = json.dumps(custom_field_query)

        # Archive serial number filters
        if archive_serial_number is not None:
            params["archive_serial_number"] = archive_serial_number

        if archive_serial_number_from is not None:
            params["archive_serial_number__gte"] = archive_serial_number_from

        if archive_serial_number_till is not None:
            params["archive_serial_number__lte"] = archive_serial_number_till

        # Date filters — created (date only)
        if created_after is not None:
            params["created__date__gt"] = self._format_date_value(created_after)

        if created_before is not None:
            params["created__date__lt"] = self._format_date_value(created_before)

        # Date filters — added (date or datetime)
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

        # Date filters — modified (date or datetime)
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
            resp = await self._session.get("/documents/", params=params)
            items = resp.json().get("results", [])
            if max_results is not None:
                items = items[:max_results]
            return [Document.model_validate(item) for item in items]

        items = await self._session.get_all_pages(
            "/documents/", params, max_results=max_results, on_page=on_page
        )
        return [Document.model_validate(item) for item in items]

    async def update_document(
        self,
        id: int,
        *,
        title: str | None = None,
        content: str | None = None,
        date: str | None = None,
        correspondent: int | str | None = None,
        document_type: int | str | None = None,
        storage_path: int | str | None = None,
        tags: list[int | str] | None = None,
        asn: int | None = None,
        custom_fields: list[dict[str, Any]] | None = None,
        owner: int | None = None,
        set_permissions: SetPermissions | None = None,
    ) -> Document:
        """Partially update a document (PATCH semantics — only passed fields change).

        Args:
            id: Numeric ID of the document to update.
            title: New document title.
            content: OCR text content of the document.
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
            owner: Numeric user ID to assign as document owner.
            set_permissions: Explicit view/change permission sets.

        Returns:
            The updated :class:`~easypaperless.models.documents.Document`.
        """
        logger.debug("Updating document id=%d", id)
        payload: dict[str, Any] = {}

        if title is not None:
            payload["title"] = title
        if content is not None:
            payload["content"] = content
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
        if owner is not None:
            payload["owner"] = owner
        if set_permissions is not None:
            payload["set_permissions"] = set_permissions.model_dump()

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
