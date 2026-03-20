"""Trash resource for PaperlessClient."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, List, cast

from easypaperless._internal.sentinel import UNSET, Unset
from easypaperless.models.documents import Document
from easypaperless.models.paged_result import PagedResult

if TYPE_CHECKING:
    from easypaperless.client import _ClientCore

logger = logging.getLogger(__name__)


class TrashResource:
    """Accessor for the trash bin: ``client.trash``."""

    def __init__(self, core: _ClientCore) -> None:
        self._core = core

    async def list(
        self,
        *,
        page: int | Unset = UNSET,
        page_size: int | Unset = UNSET,
    ) -> PagedResult[Document]:
        """Return all documents currently in the trash.

        When ``page`` is ``UNSET`` (the default), all pages are fetched
        automatically and ``next`` / ``previous`` in the result are always
        ``None``.  When ``page`` is set, only that page is fetched and
        ``next`` / ``previous`` reflect the raw API values.

        Args:
            page: Return only this specific page (1-based).
            page_size: Number of results per page.

        Returns:
            :class:`~easypaperless.models.paged_result.PagedResult` of
            :class:`~easypaperless.models.documents.Document` objects currently
            in the trash.
        """
        logger.info("Listing trashed documents")
        params: dict[str, Any] = {}
        if not isinstance(page, Unset):
            params["page"] = page
        if not isinstance(page_size, Unset):
            params["page_size"] = page_size
        return cast(
            PagedResult[Document],
            await self._core._list_resource("trash", Document, params or None),
        )

    async def restore(self, document_ids: List[int]) -> None:
        """Restore trashed documents back to active status.

        Args:
            document_ids: List of numeric document IDs to restore.
        """
        logger.info("Restoring %d trashed document(s)", len(document_ids))
        await self._core._session.post(
            "/trash/",
            json={"documents": document_ids, "action": "restore"},
        )

    async def empty(self, document_ids: List[int]) -> None:
        """Permanently delete trashed documents.

        .. warning::
            **This operation is irreversible and cannot be undone.**
            The documents will be permanently removed and cannot be recovered.

        Args:
            document_ids: List of numeric document IDs to permanently delete.
        """
        logger.info("Permanently deleting %d trashed document(s)", len(document_ids))
        await self._core._session.post(
            "/trash/",
            json={"documents": document_ids, "action": "empty"},
        )
