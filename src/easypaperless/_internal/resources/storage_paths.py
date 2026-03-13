"""Storage paths resource for PaperlessClient."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, cast

from easypaperless._internal.sentinel import UNSET, _Unset
from easypaperless.models._base import MatchingAlgorithm
from easypaperless.models.permissions import SetPermissions
from easypaperless.models.storage_paths import StoragePath

if TYPE_CHECKING:
    from easypaperless.client import _ClientCore


class StoragePathsResource:
    """Accessor for storage paths: ``client.storage_paths``."""

    def __init__(self, core: _ClientCore) -> None:
        self._core = core

    async def list(
        self,
        *,
        ids: List[int] | None = None,
        name_contains: str | None = None,
        name_exact: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
        ordering: str | None = None,
        descending: bool = False,
    ) -> List[StoragePath]:
        """Return storage paths defined in paperless-ngx.

        Args:
            ids: Return only storage paths whose ID is in this list.
            name_contains: Case-insensitive substring filter on name.
            name_exact: Case-insensitive exact match on name.
            page: Return only this specific page (1-based).
            page_size: Number of results per page.
            ordering: Field to sort by.
            descending: When ``True``, reverses the sort direction.

        Returns:
            List of :class:`~easypaperless.models.storage_paths.StoragePath` objects.
        """
        params: dict[str, Any] = {}
        if ids is not None:
            params["id__in"] = ",".join(str(i) for i in ids)
        if name_contains is not None:
            params["name__icontains"] = name_contains
        if name_exact is not None:
            params["name__iexact"] = name_exact
        if page is not None:
            params["page"] = page
        if page_size is not None:
            params["page_size"] = page_size
        if ordering is not None:
            params["ordering"] = f"-{ordering}" if descending else ordering
        return cast(
            List[StoragePath],
            await self._core._list_resource("storage_paths", StoragePath, params or None),
        )

    async def get(self, id: int) -> StoragePath:
        """Fetch a single storage path by its ID.

        Args:
            id: Numeric storage-path ID.

        Returns:
            The :class:`~easypaperless.models.storage_paths.StoragePath` with the given ID.

        Raises:
            ~easypaperless.exceptions.NotFoundError: If no storage path exists with that ID.
        """
        return cast(StoragePath, await self._core._get_resource("storage_paths", id, StoragePath))

    async def create(
        self,
        *,
        name: str,
        path: str | None = None,
        match: str | None = None,
        matching_algorithm: MatchingAlgorithm | None = None,
        is_insensitive: bool | None = None,
        owner: int | None | _Unset = UNSET,
        set_permissions: SetPermissions | None = None,
    ) -> StoragePath:
        """Create a new storage path.

        Args:
            name: Storage-path name. Must be unique.
            path: Template string for the archive file path.
            match: Auto-matching pattern.
            matching_algorithm: Controls how ``match`` is applied.
            is_insensitive: When ``True``, ``match`` is case-insensitive.
            owner: Numeric user ID to assign as owner.
            set_permissions: Explicit view/change permission sets.

        Returns:
            The newly created :class:`~easypaperless.models.storage_paths.StoragePath`.
        """
        return cast(
            StoragePath,
            await self._core._create_resource(
                "storage_paths",
                StoragePath,
                owner=owner,
                set_permissions=set_permissions,
                name=name,
                path=path,
                match=match,
                matching_algorithm=matching_algorithm,
                is_insensitive=is_insensitive,
            ),
        )

    async def update(
        self,
        id: int,
        *,
        name: str | None | _Unset = UNSET,
        path: str | None | _Unset = UNSET,
        match: str | None | _Unset = UNSET,
        matching_algorithm: MatchingAlgorithm | None | _Unset = UNSET,
        is_insensitive: bool | None | _Unset = UNSET,
        owner: int | None | _Unset = UNSET,
    ) -> StoragePath:
        """Partially update a storage path (PATCH semantics).

        Args:
            id: Numeric ID of the storage path to update.
            name: Storage-path name.
            path: Template string for the archive file path.
            match: Auto-matching pattern.
            matching_algorithm: Controls how ``match`` is applied.
            is_insensitive: When ``True``, ``match`` is case-insensitive.
            owner: Numeric user ID to assign as owner.
                Pass ``None`` to clear the owner.
                Omit (or pass :data:`~easypaperless.UNSET`) to leave unchanged.

        Returns:
            The updated :class:`~easypaperless.models.storage_paths.StoragePath`.
        """
        return cast(
            StoragePath,
            await self._core._update_resource(
                "storage_paths",
                id,
                StoragePath,
                name=name,
                path=path,
                match=match,
                matching_algorithm=matching_algorithm,
                is_insensitive=is_insensitive,
                owner=owner,
            ),
        )

    async def delete(self, id: int) -> None:
        """Delete a storage path.

        Args:
            id: Numeric ID of the storage path to delete.

        Raises:
            ~easypaperless.exceptions.NotFoundError: If no storage path exists with that ID.
        """
        await self._core._delete_resource("storage_paths", id)

    async def bulk_delete(self, ids: List[int]) -> None:
        """Permanently delete multiple storage paths in a single request.

        Args:
            ids: List of storage path IDs to delete.
        """
        await self._core._bulk_edit_objects("storage_paths", ids, "delete")

    async def bulk_set_permissions(
        self,
        ids: List[int],
        *,
        set_permissions: SetPermissions | None = None,
        owner: int | None = None,
        merge: bool = False,
    ) -> None:
        """Set permissions and/or owner on multiple storage paths.

        Args:
            ids: List of storage path IDs to modify.
            set_permissions: Explicit view/change permission sets.
            owner: Numeric user ID to assign as owner.
            merge: When ``True``, new permissions are merged with existing ones.
        """
        params: dict[str, Any] = {"merge": merge}
        if set_permissions is not None:
            params["permissions"] = set_permissions.model_dump()
        if owner is not None:
            params["owner"] = owner
        await self._core._bulk_edit_objects("storage_paths", ids, "set_permissions", **params)
