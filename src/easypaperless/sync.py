"""Synchronous wrapper around PaperlessClient.

Note: SyncPaperlessClient cannot be used inside an already-running event loop
(e.g., Jupyter notebooks). Use the async PaperlessClient directly there.
"""

from __future__ import annotations

import asyncio
import threading
from collections.abc import Coroutine
from typing import Any, TypeVar

from easypaperless._internal.sync_mixins import (
    SyncCorrespondentsMixin,
    SyncCustomFieldsMixin,
    SyncDocumentBulkMixin,
    SyncDocumentsMixin,
    SyncDocumentTypesMixin,
    SyncNonDocumentBulkMixin,
    SyncNotesMixin,
    SyncStoragePathsMixin,
    SyncTagsMixin,
    SyncUploadMixin,
)
from easypaperless.client import PaperlessClient

_T = TypeVar("_T")


class _SyncCore:
    """Background event loop, _run() helper, and context manager."""

    def __init__(self, url: str, api_key: str, **kwargs: Any) -> None:
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


class SyncPaperlessClient(
    SyncDocumentsMixin,
    SyncNotesMixin,
    SyncUploadMixin,
    SyncDocumentBulkMixin,
    SyncNonDocumentBulkMixin,
    SyncTagsMixin,
    SyncCorrespondentsMixin,
    SyncDocumentTypesMixin,
    SyncStoragePathsMixin,
    SyncCustomFieldsMixin,
    _SyncCore,
):
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
        super().__init__(url, api_key, **kwargs)

    def __enter__(self) -> SyncPaperlessClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
