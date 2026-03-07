"""Non-document bulk operations mixin for PaperlessClient."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from easypaperless.models.permissions import SetPermissions

if TYPE_CHECKING:
    from easypaperless._internal.http import HttpSession


class NonDocumentBulkMixin:
    if TYPE_CHECKING:
        _session: HttpSession

    async def bulk_edit_objects(
        self,
        object_type: str,
        object_ids: list[int],
        operation: str,
        **parameters: Any,
    ) -> None:
        """Execute a bulk operation on non-document objects (tags, etc.).

        This is a low-level method; prefer the higher-level helpers such as
        :meth:`bulk_delete_tags` or :meth:`bulk_set_permissions_tags`.

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

    # -- Bulk delete helpers --------------------------------------------------

    async def bulk_delete_tags(self, ids: list[int]) -> None:
        """Permanently delete multiple tags in a single request.

        Args:
            ids: List of tag IDs to delete.
        """
        await self.bulk_edit_objects("tags", ids, "delete")

    async def bulk_delete_correspondents(self, ids: list[int]) -> None:
        """Permanently delete multiple correspondents in a single request.

        Args:
            ids: List of correspondent IDs to delete.
        """
        await self.bulk_edit_objects("correspondents", ids, "delete")

    async def bulk_delete_document_types(self, ids: list[int]) -> None:
        """Permanently delete multiple document types in a single request.

        Args:
            ids: List of document type IDs to delete.
        """
        await self.bulk_edit_objects("document_types", ids, "delete")

    async def bulk_delete_storage_paths(self, ids: list[int]) -> None:
        """Permanently delete multiple storage paths in a single request.

        Args:
            ids: List of storage path IDs to delete.
        """
        await self.bulk_edit_objects("storage_paths", ids, "delete")

    # -- Bulk set-permissions helpers -----------------------------------------

    async def bulk_set_permissions_tags(
        self,
        ids: list[int],
        *,
        set_permissions: SetPermissions | None = None,
        owner: int | None = None,
        merge: bool = False,
    ) -> None:
        """Set permissions and/or owner on multiple tags.

        Args:
            ids: List of tag IDs to modify.
            set_permissions: Explicit view/change permission sets to apply.
            owner: Numeric user ID to assign as owner.
            merge: When ``True``, new permissions are merged with existing
                ones rather than replacing them.
        """
        params: dict[str, Any] = {"merge": merge}
        if set_permissions is not None:
            params["permissions"] = set_permissions.model_dump()
        if owner is not None:
            params["owner"] = owner
        await self.bulk_edit_objects("tags", ids, "set_permissions", **params)

    async def bulk_set_permissions_correspondents(
        self,
        ids: list[int],
        *,
        set_permissions: SetPermissions | None = None,
        owner: int | None = None,
        merge: bool = False,
    ) -> None:
        """Set permissions and/or owner on multiple correspondents.

        Args:
            ids: List of correspondent IDs to modify.
            set_permissions: Explicit view/change permission sets to apply.
            owner: Numeric user ID to assign as owner.
            merge: When ``True``, new permissions are merged with existing
                ones rather than replacing them.
        """
        params: dict[str, Any] = {"merge": merge}
        if set_permissions is not None:
            params["permissions"] = set_permissions.model_dump()
        if owner is not None:
            params["owner"] = owner
        await self.bulk_edit_objects("correspondents", ids, "set_permissions", **params)

    async def bulk_set_permissions_document_types(
        self,
        ids: list[int],
        *,
        set_permissions: SetPermissions | None = None,
        owner: int | None = None,
        merge: bool = False,
    ) -> None:
        """Set permissions and/or owner on multiple document types.

        Args:
            ids: List of document type IDs to modify.
            set_permissions: Explicit view/change permission sets to apply.
            owner: Numeric user ID to assign as owner.
            merge: When ``True``, new permissions are merged with existing
                ones rather than replacing them.
        """
        params: dict[str, Any] = {"merge": merge}
        if set_permissions is not None:
            params["permissions"] = set_permissions.model_dump()
        if owner is not None:
            params["owner"] = owner
        await self.bulk_edit_objects("document_types", ids, "set_permissions", **params)

    async def bulk_set_permissions_storage_paths(
        self,
        ids: list[int],
        *,
        set_permissions: SetPermissions | None = None,
        owner: int | None = None,
        merge: bool = False,
    ) -> None:
        """Set permissions and/or owner on multiple storage paths.

        Args:
            ids: List of storage path IDs to modify.
            set_permissions: Explicit view/change permission sets to apply.
            owner: Numeric user ID to assign as owner.
            merge: When ``True``, new permissions are merged with existing
                ones rather than replacing them.
        """
        params: dict[str, Any] = {"merge": merge}
        if set_permissions is not None:
            params["permissions"] = set_permissions.model_dump()
        if owner is not None:
            params["owner"] = owner
        await self.bulk_edit_objects("storage_paths", ids, "set_permissions", **params)
