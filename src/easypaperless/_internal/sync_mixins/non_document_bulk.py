"""Sync non-document bulk operations mixin."""

from __future__ import annotations

from collections.abc import Coroutine
from typing import TYPE_CHECKING, Any, TypeVar

from easypaperless.models.permissions import SetPermissions

if TYPE_CHECKING:
    from easypaperless.client import PaperlessClient

_T = TypeVar("_T")


class SyncNonDocumentBulkMixin:
    if TYPE_CHECKING:
        _async_client: PaperlessClient

        def _run(self, coro: Coroutine[Any, Any, _T]) -> _T: ...

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

    # -- Bulk delete helpers --------------------------------------------------

    def bulk_delete_tags(self, ids: list[int]) -> None:
        return self._run(self._async_client.bulk_delete_tags(ids))

    def bulk_delete_correspondents(self, ids: list[int]) -> None:
        return self._run(self._async_client.bulk_delete_correspondents(ids))

    def bulk_delete_document_types(self, ids: list[int]) -> None:
        return self._run(self._async_client.bulk_delete_document_types(ids))

    def bulk_delete_storage_paths(self, ids: list[int]) -> None:
        return self._run(self._async_client.bulk_delete_storage_paths(ids))

    # -- Bulk set-permissions helpers -----------------------------------------

    def bulk_set_permissions_tags(
        self,
        ids: list[int],
        *,
        set_permissions: SetPermissions | None = None,
        owner: int | None = None,
        merge: bool = False,
    ) -> None:
        return self._run(
            self._async_client.bulk_set_permissions_tags(
                ids, set_permissions=set_permissions, owner=owner, merge=merge
            )
        )

    def bulk_set_permissions_correspondents(
        self,
        ids: list[int],
        *,
        set_permissions: SetPermissions | None = None,
        owner: int | None = None,
        merge: bool = False,
    ) -> None:
        return self._run(
            self._async_client.bulk_set_permissions_correspondents(
                ids, set_permissions=set_permissions, owner=owner, merge=merge
            )
        )

    def bulk_set_permissions_document_types(
        self,
        ids: list[int],
        *,
        set_permissions: SetPermissions | None = None,
        owner: int | None = None,
        merge: bool = False,
    ) -> None:
        return self._run(
            self._async_client.bulk_set_permissions_document_types(
                ids, set_permissions=set_permissions, owner=owner, merge=merge
            )
        )

    def bulk_set_permissions_storage_paths(
        self,
        ids: list[int],
        *,
        set_permissions: SetPermissions | None = None,
        owner: int | None = None,
        merge: bool = False,
    ) -> None:
        return self._run(
            self._async_client.bulk_set_permissions_storage_paths(
                ids, set_permissions=set_permissions, owner=owner, merge=merge
            )
        )
