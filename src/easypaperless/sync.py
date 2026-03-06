"""Synchronous wrapper around PaperlessClient.

Note: SyncPaperlessClient cannot be used inside an already-running event loop
(e.g., Jupyter notebooks). Use the async PaperlessClient directly there.
"""

from __future__ import annotations

import asyncio
import threading
from collections.abc import Coroutine
from pathlib import Path
from typing import Any, Callable, TypeVar

_T = TypeVar("_T")

from easypaperless.client import PaperlessClient
from easypaperless.models.correspondents import Correspondent
from easypaperless.models.custom_fields import CustomField
from easypaperless.models.document_types import DocumentType
from easypaperless.models.documents import Document, DocumentMetadata, DocumentNote
from easypaperless.models.permissions import SetPermissions
from easypaperless.models.storage_paths import StoragePath
from easypaperless.models.tags import Tag


class SyncPaperlessClient:
    """Synchronous interface to paperless-ngx.

    Exposes the same methods as
    :class:`~easypaperless.client.PaperlessClient` but runs them
    synchronously, making it suitable for scripts and REPL sessions that do
    not use ``asyncio``.

    All methods have identical signatures to their async counterparts on
    :class:`~easypaperless.client.PaperlessClient`.  Operations run on a
    dedicated background event loop thread so that the httpx connection pool
    is reused across calls and cleanup works correctly.

    Use as a context manager to ensure proper cleanup:

    Example:
        with SyncPaperlessClient(url="http://localhost:8000", api_key="abc") as client:
            tags = client.list_tags()
            docs = client.list_documents(search="invoice")

    Note:
        Cannot be used inside an already-running event loop (e.g. Jupyter
        notebooks).  Use :class:`~easypaperless.client.PaperlessClient`
        directly in those environments.
    """

    def __init__(self, url: str, api_key: str, **kwargs: Any) -> None:
        """Create a synchronous paperless-ngx client.

        Args:
            url: Base URL of the paperless-ngx instance
                (e.g. ``"http://localhost:8000"``).
            api_key: API token.  Generate one in paperless-ngx under
                *Settings → API → Generate Token*.
            **kwargs: Additional keyword arguments forwarded to
                :class:`~easypaperless.client.PaperlessClient` (e.g.
                ``poll_interval``, ``poll_timeout``).
        """
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._thread.start()
        self._async_client = PaperlessClient(url, api_key, **kwargs)

    def _run(self, coro: Coroutine[Any, Any, _T]) -> _T:
        """Submit a coroutine to the background event loop and block until done."""
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result()

    def close(self) -> None:
        """Close the underlying HTTP connection pool and stop the event loop.

        Called automatically when used as a context manager.
        """
        self._run(self._async_client.close())
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join()
        self._loop.close()

    def __enter__(self) -> SyncPaperlessClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Documents
    # ------------------------------------------------------------------

    def get_document(self, id: int, *, include_metadata: bool = False) -> Document:
        return self._run(self._async_client.get_document(id, include_metadata=include_metadata))

    def get_document_metadata(self, id: int) -> DocumentMetadata:
        return self._run(self._async_client.get_document_metadata(id))

    def list_documents(
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
        on_page: Callable[[int, int | None], None] | None = None,
    ) -> list[Document]:
        return self._run(self._async_client.list_documents(
            search=search,
            search_mode=search_mode,
            tags=tags,
            any_tag=any_tag,
            exclude_tags=exclude_tags,
            correspondent=correspondent,
            any_correspondent=any_correspondent,
            exclude_correspondents=exclude_correspondents,
            document_type=document_type,
            any_document_type=any_document_type,
            exclude_document_types=exclude_document_types,
            asn=asn,
            created_after=created_after,
            created_before=created_before,
            added_after=added_after,
            added_before=added_before,
            modified_after=modified_after,
            modified_before=modified_before,
            checksum=checksum,
            page_size=page_size,
            page=page,
            ordering=ordering,
            descending=descending,
            max_results=max_results,
            on_page=on_page,
        ))

    def update_document(
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
    ) -> Document:
        return self._run(self._async_client.update_document(
            id,
            title=title,
            content=content,
            date=date,
            correspondent=correspondent,
            document_type=document_type,
            storage_path=storage_path,
            tags=tags,
            asn=asn,
            custom_fields=custom_fields,
        ))

    def delete_document(self, id: int) -> None:
        return self._run(self._async_client.delete_document(id))

    def download_document(self, id: int, *, original: bool = False) -> bytes:
        return self._run(self._async_client.download_document(id, original=original))

    # ------------------------------------------------------------------
    # Notes
    # ------------------------------------------------------------------

    def get_notes(self, document_id: int) -> list[DocumentNote]:
        return self._run(self._async_client.get_notes(document_id))

    def create_note(self, document_id: int, *, note: str) -> DocumentNote:
        return self._run(self._async_client.create_note(document_id, note=note))

    def delete_note(self, document_id: int, note_id: int) -> None:
        return self._run(self._async_client.delete_note(document_id, note_id))

    # ------------------------------------------------------------------
    # Upload
    # ------------------------------------------------------------------

    def upload_document(
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
        return self._run(self._async_client.upload_document(
            file,
            title=title,
            created=created,
            correspondent=correspondent,
            document_type=document_type,
            storage_path=storage_path,
            tags=tags,
            asn=asn,
            wait=wait,
            poll_interval=poll_interval,
            poll_timeout=poll_timeout,
        ))

    # ------------------------------------------------------------------
    # Bulk operations
    # ------------------------------------------------------------------

    def bulk_edit(self, document_ids: list[int], method: str, **parameters: Any) -> None:
        return self._run(self._async_client.bulk_edit(document_ids, method, **parameters))

    def bulk_add_tag(self, document_ids: list[int], tag: int | str) -> None:
        return self._run(self._async_client.bulk_add_tag(document_ids, tag))

    def bulk_remove_tag(self, document_ids: list[int], tag: int | str) -> None:
        return self._run(self._async_client.bulk_remove_tag(document_ids, tag))

    def bulk_modify_tags(
        self,
        document_ids: list[int],
        *,
        add_tags: list[int | str] | None = None,
        remove_tags: list[int | str] | None = None,
    ) -> None:
        return self._run(self._async_client.bulk_modify_tags(
            document_ids, add_tags=add_tags, remove_tags=remove_tags
        ))

    def bulk_delete(self, document_ids: list[int]) -> None:
        return self._run(self._async_client.bulk_delete(document_ids))

    def bulk_edit_objects(
        self,
        object_type: str,
        object_ids: list[int],
        operation: str,
        **parameters: Any,
    ) -> None:
        return self._run(
            self._async_client.bulk_edit_objects(object_type, object_ids, operation, **parameters)
        )

    # ------------------------------------------------------------------
    # Tags
    # ------------------------------------------------------------------

    def list_tags(
        self,
        *,
        ids: list[int] | None = None,
        name_contains: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
        ordering: str | None = None,
        descending: bool = False,
    ) -> list[Tag]:
        return self._run(self._async_client.list_tags(
            ids=ids,
            name_contains=name_contains,
            page=page,
            page_size=page_size,
            ordering=ordering,
            descending=descending,
        ))

    def get_tag(self, id: int) -> Tag:
        return self._run(self._async_client.get_tag(id))

    def create_tag(
        self,
        *,
        name: str,
        color: str | None = None,
        is_inbox_tag: bool | None = None,
        match: str | None = None,
        matching_algorithm: int | None = None,
        is_insensitive: bool | None = None,
        parent: int | None = None,
        owner: int | None = None,
        set_permissions: SetPermissions | None = None,
    ) -> Tag:
        return self._run(self._async_client.create_tag(
            name=name,
            color=color,
            is_inbox_tag=is_inbox_tag,
            match=match,
            matching_algorithm=matching_algorithm,
            is_insensitive=is_insensitive,
            parent=parent,
            owner=owner,
            set_permissions=set_permissions,
        ))

    def update_tag(
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
        return self._run(self._async_client.update_tag(
            id,
            name=name,
            color=color,
            is_inbox_tag=is_inbox_tag,
            match=match,
            matching_algorithm=matching_algorithm,
            is_insensitive=is_insensitive,
            parent=parent,
        ))

    def delete_tag(self, id: int) -> None:
        return self._run(self._async_client.delete_tag(id))

    # ------------------------------------------------------------------
    # Correspondents
    # ------------------------------------------------------------------

    def list_correspondents(
        self,
        *,
        ids: list[int] | None = None,
        name_contains: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
        ordering: str | None = None,
        descending: bool = False,
    ) -> list[Correspondent]:
        return self._run(self._async_client.list_correspondents(
            ids=ids,
            name_contains=name_contains,
            page=page,
            page_size=page_size,
            ordering=ordering,
            descending=descending,
        ))

    def get_correspondent(self, id: int) -> Correspondent:
        return self._run(self._async_client.get_correspondent(id))

    def create_correspondent(
        self,
        *,
        name: str,
        match: str | None = None,
        matching_algorithm: int | None = None,
        is_insensitive: bool | None = None,
        owner: int | None = None,
        set_permissions: SetPermissions | None = None,
    ) -> Correspondent:
        return self._run(self._async_client.create_correspondent(
            name=name,
            match=match,
            matching_algorithm=matching_algorithm,
            is_insensitive=is_insensitive,
            owner=owner,
            set_permissions=set_permissions,
        ))

    def update_correspondent(
        self,
        id: int,
        *,
        name: str | None = None,
        match: str | None = None,
        matching_algorithm: int | None = None,
        is_insensitive: bool | None = None,
    ) -> Correspondent:
        return self._run(self._async_client.update_correspondent(
            id,
            name=name,
            match=match,
            matching_algorithm=matching_algorithm,
            is_insensitive=is_insensitive,
        ))

    def delete_correspondent(self, id: int) -> None:
        return self._run(self._async_client.delete_correspondent(id))

    # ------------------------------------------------------------------
    # Document Types
    # ------------------------------------------------------------------

    def list_document_types(
        self,
        *,
        ids: list[int] | None = None,
        name_contains: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
        ordering: str | None = None,
        descending: bool = False,
    ) -> list[DocumentType]:
        return self._run(self._async_client.list_document_types(
            ids=ids,
            name_contains=name_contains,
            page=page,
            page_size=page_size,
            ordering=ordering,
            descending=descending,
        ))

    def get_document_type(self, id: int) -> DocumentType:
        return self._run(self._async_client.get_document_type(id))

    def create_document_type(
        self,
        *,
        name: str,
        match: str | None = None,
        matching_algorithm: int | None = None,
        is_insensitive: bool | None = None,
        owner: int | None = None,
        set_permissions: SetPermissions | None = None,
    ) -> DocumentType:
        return self._run(self._async_client.create_document_type(
            name=name,
            match=match,
            matching_algorithm=matching_algorithm,
            is_insensitive=is_insensitive,
            owner=owner,
            set_permissions=set_permissions,
        ))

    def update_document_type(
        self,
        id: int,
        *,
        name: str | None = None,
        match: str | None = None,
        matching_algorithm: int | None = None,
        is_insensitive: bool | None = None,
    ) -> DocumentType:
        return self._run(self._async_client.update_document_type(
            id,
            name=name,
            match=match,
            matching_algorithm=matching_algorithm,
            is_insensitive=is_insensitive,
        ))

    def delete_document_type(self, id: int) -> None:
        return self._run(self._async_client.delete_document_type(id))

    # ------------------------------------------------------------------
    # Storage Paths
    # ------------------------------------------------------------------

    def list_storage_paths(
        self,
        *,
        ids: list[int] | None = None,
        name_contains: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
        ordering: str | None = None,
        descending: bool = False,
    ) -> list[StoragePath]:
        return self._run(self._async_client.list_storage_paths(
            ids=ids,
            name_contains=name_contains,
            page=page,
            page_size=page_size,
            ordering=ordering,
            descending=descending,
        ))

    def get_storage_path(self, id: int) -> StoragePath:
        return self._run(self._async_client.get_storage_path(id))

    def create_storage_path(
        self,
        *,
        name: str,
        path: str | None = None,
        match: str | None = None,
        matching_algorithm: int | None = None,
        is_insensitive: bool | None = None,
        owner: int | None = None,
        set_permissions: SetPermissions | None = None,
    ) -> StoragePath:
        return self._run(self._async_client.create_storage_path(
            name=name,
            path=path,
            match=match,
            matching_algorithm=matching_algorithm,
            is_insensitive=is_insensitive,
            owner=owner,
            set_permissions=set_permissions,
        ))

    def update_storage_path(
        self,
        id: int,
        *,
        name: str | None = None,
        path: str | None = None,
        match: str | None = None,
        matching_algorithm: int | None = None,
        is_insensitive: bool | None = None,
    ) -> StoragePath:
        return self._run(self._async_client.update_storage_path(
            id,
            name=name,
            path=path,
            match=match,
            matching_algorithm=matching_algorithm,
            is_insensitive=is_insensitive,
        ))

    def delete_storage_path(self, id: int) -> None:
        return self._run(self._async_client.delete_storage_path(id))

    # ------------------------------------------------------------------
    # Custom Fields
    # ------------------------------------------------------------------

    def list_custom_fields(
        self,
        *,
        page: int | None = None,
        page_size: int | None = None,
        ordering: str | None = None,
        descending: bool = False,
    ) -> list[CustomField]:
        return self._run(self._async_client.list_custom_fields(
            page=page,
            page_size=page_size,
            ordering=ordering,
            descending=descending,
        ))

    def get_custom_field(self, id: int) -> CustomField:
        return self._run(self._async_client.get_custom_field(id))

    def create_custom_field(
        self,
        *,
        name: str,
        data_type: str,
        extra_data: Any | None = None,
        owner: int | None = None,
        set_permissions: SetPermissions | None = None,
    ) -> CustomField:
        return self._run(self._async_client.create_custom_field(
            name=name,
            data_type=data_type,
            extra_data=extra_data,
            owner=owner,
            set_permissions=set_permissions,
        ))

    def update_custom_field(
        self,
        id: int,
        *,
        name: str | None = None,
        extra_data: Any | None = None,
    ) -> CustomField:
        return self._run(self._async_client.update_custom_field(
            id, name=name, extra_data=extra_data
        ))

    def delete_custom_field(self, id: int) -> None:
        return self._run(self._async_client.delete_custom_field(id))
