"""Synchronous wrapper around PaperlessClient.

Note: SyncPaperlessClient cannot be used inside an already-running event loop
(e.g., Jupyter notebooks). Use the async PaperlessClient directly there.
"""

from __future__ import annotations

import asyncio
import inspect
from typing import Any

from easypaperless.client import PaperlessClient


class SyncPaperlessClient:
    """Synchronous interface to paperless-ngx.

    All async methods of PaperlessClient are available here with the same
    signatures, executed via asyncio.run(). No business logic lives here.
    """

    def __init__(self, url: str, api_key: str, **kwargs: Any) -> None:
        self._async_client = PaperlessClient(url, api_key, **kwargs)

    def __getattr__(self, name: str) -> Any:
        attr = getattr(self._async_client, name)
        if inspect.iscoroutinefunction(attr):
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                return asyncio.run(attr(*args, **kwargs))
            wrapper.__name__ = name
            return wrapper
        return attr

    def close(self) -> None:
        asyncio.run(self._async_client.close())

    def __enter__(self) -> SyncPaperlessClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
