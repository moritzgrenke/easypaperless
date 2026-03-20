"""Sync trash resource."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, cast

from easypaperless._internal.sentinel import UNSET, Unset
from easypaperless.models.documents import Document
from easypaperless.models.paged_result import PagedResult

if TYPE_CHECKING:
    from easypaperless._internal.resources.trash import TrashResource


class SyncTrashResource:
    """Sync accessor for the trash bin: ``client.trash``."""

    def __init__(self, async_trash: TrashResource, run: Any) -> None:
        self._async_trash = async_trash
        self._run = run

    def list(
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
        return cast(
            PagedResult[Document],
            self._run(self._async_trash.list(page=page, page_size=page_size)),
        )

    def restore(self, document_ids: List[int]) -> None:
        """Restore trashed documents back to active status.

        Args:
            document_ids: List of numeric document IDs to restore.
        """
        self._run(self._async_trash.restore(document_ids))

    def empty(self, document_ids: List[int]) -> None:
        """Permanently delete trashed documents.

        .. warning::
            **This operation is irreversible and cannot be undone.**
            The documents will be permanently removed and cannot be recovered.

        Args:
            document_ids: List of numeric document IDs to permanently delete.
        """
        self._run(self._async_trash.empty(document_ids))
