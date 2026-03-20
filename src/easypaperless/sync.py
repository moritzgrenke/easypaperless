"""Synchronous wrapper around PaperlessClient.

Note: SyncPaperlessClient cannot be used inside an already-running event loop
(e.g., Jupyter notebooks). Use the async PaperlessClient directly there.
"""

from __future__ import annotations

import asyncio
import threading
from collections.abc import Coroutine
from typing import Any, TypeVar

from easypaperless._internal.sync_resources.correspondents import SyncCorrespondentsResource
from easypaperless._internal.sync_resources.custom_fields import SyncCustomFieldsResource
from easypaperless._internal.sync_resources.document_types import SyncDocumentTypesResource
from easypaperless._internal.sync_resources.documents import SyncDocumentsResource
from easypaperless._internal.sync_resources.storage_paths import SyncStoragePathsResource
from easypaperless._internal.sync_resources.tags import SyncTagsResource
from easypaperless._internal.sync_resources.trash import SyncTrashResource
from easypaperless._internal.sync_resources.users import SyncUsersResource
from easypaperless.client import PaperlessClient

_T = TypeVar("_T")


class _SyncCore:
    """Background event loop, _run() helper, and context manager."""

    documents: SyncDocumentsResource
    tags: SyncTagsResource
    correspondents: SyncCorrespondentsResource
    document_types: SyncDocumentTypesResource
    storage_paths: SyncStoragePathsResource
    custom_fields: SyncCustomFieldsResource
    users: SyncUsersResource
    trash: SyncTrashResource

    def __init__(self, url: str, api_token: str, **kwargs: Any) -> None:
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._thread.start()
        self._async_client = PaperlessClient(url, api_token, **kwargs)

        self.documents = SyncDocumentsResource(self._async_client.documents, self._run)
        self.tags = SyncTagsResource(self._async_client.tags, self._run)
        self.correspondents = SyncCorrespondentsResource(
            self._async_client.correspondents, self._run
        )
        self.document_types = SyncDocumentTypesResource(
            self._async_client.document_types, self._run
        )
        self.storage_paths = SyncStoragePathsResource(self._async_client.storage_paths, self._run)
        self.custom_fields = SyncCustomFieldsResource(self._async_client.custom_fields, self._run)
        self.users = SyncUsersResource(self._async_client.users, self._run)
        self.trash = SyncTrashResource(self._async_client.trash, self._run)

    def _run(self, coro: Coroutine[Any, Any, _T]) -> _T:
        """Submit a coroutine to the background event loop and block until done."""
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result()

    def close(self) -> None:
        """Close the underlying HTTP connection pool and stop the event loop.

        Safe to call multiple times — subsequent calls are no-ops.
        """
        if self._loop.is_closed():
            return
        self._run(self._async_client.close())
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join()
        self._loop.close()

    def __enter__(self) -> SyncPaperlessClient:
        return self  # type: ignore[return-value]

    def __exit__(self, *args: Any) -> None:
        self.close()


class SyncPaperlessClient(_SyncCore):
    """Synchronous interface to paperless-ngx.

    Resources are accessible as attributes:

    * ``client.correspondents`` — correspondent CRUD + bulk ops -
      see `easypaperless.resources.SyncCorrespondentsResource`
    * ``client.custom_fields`` — custom field CRUD -
      see `easypaperless.resources.SyncCustomFieldsResource`
    * ``client.document_types`` — document type CRUD + bulk ops -
      see `easypaperless.resources.SyncDocumentTypesResource`
    * ``client.documents`` — document CRUD, bulk ops, upload, download -
      see `easypaperless.resources.SyncDocumentsResource`
    * ``client.documents.notes`` — document notes -
      see `easypaperless.resources.SyncNotesResource`
    * ``client.storage_paths`` — storage path CRUD + bulk ops -
      see `easypaperless.resources.SyncStoragePathsResource`
    * ``client.tags`` — tag CRUD + bulk ops -
      see `easypaperless.resources.SyncTagsResource`
    * ``client.users`` — user CRUD -
      see `easypaperless.resources.SyncUsersResource`
    * ``client.trash`` — list, restore, and permanently delete trashed documents -
      see `easypaperless.resources.SyncTrashResource`

    All methods are synchronous wrappers around the async
    :class:`~easypaperless.client.PaperlessClient`.  Operations run on a
    dedicated background event loop thread so that the httpx connection pool
    is reused across calls and cleanup works correctly.

    Use as a context manager to ensure proper cleanup:

    Example:
        with SyncPaperlessClient(url="http://localhost:8000", api_token="abc") as client:
            tags = client.tags.list()
            docs = client.documents.list(search="invoice")

    Note:
        Cannot be used inside an already-running event loop (e.g. Jupyter
        notebooks).  Use :class:`~easypaperless.client.PaperlessClient`
        directly in those environments.
    """

    def __init__(self, url: str, api_token: str, **kwargs: Any) -> None:
        """Create a synchronous paperless-ngx client.

        Args:
            url: Base URL of the paperless-ngx instance
                (e.g. ``"http://localhost:8000"``).
            api_token: API token.  Generate one in paperless-ngx under
                *Settings → API → Generate Token*.
            **kwargs: Additional keyword arguments forwarded to
                :class:`~easypaperless.client.PaperlessClient` (e.g.
                ``poll_interval``, ``poll_timeout``).
        """
        super().__init__(url, api_token, **kwargs)

    def __enter__(self) -> SyncPaperlessClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
