"""Sync storage paths resource."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, cast

from easypaperless.models._base import MatchingAlgorithm
from easypaperless.models.permissions import SetPermissions
from easypaperless.models.storage_paths import StoragePath

if TYPE_CHECKING:
    from easypaperless._internal.resources.storage_paths import StoragePathsResource


class SyncStoragePathsResource:
    """Sync accessor for storage paths: ``client.storage_paths``."""

    def __init__(self, async_storage_paths: StoragePathsResource, run: Any) -> None:
        self._async_storage_paths = async_storage_paths
        self._run = run

    def list(
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
        
        This is a sync wrapper for the async method with exactly the same parameters.
        See: `easypaperless.StoragePathsResource.list` 
        """
        return cast(
            List[StoragePath],
            self._run(
                self._async_storage_paths.list(
                    ids=ids,
                    name_contains=name_contains,
                    name_exact=name_exact,
                    page=page,
                    page_size=page_size,
                    ordering=ordering,
                    descending=descending,
                )
            ),
        )

    def get(self, id: int) -> StoragePath:
        """Fetch a single storage path by its ID.
        
        This is a sync wrapper for the async method with exactly the same parameters.
        See: `easypaperless.StoragePathsResource.get` 
        """
        return cast(StoragePath, self._run(self._async_storage_paths.get(id)))

    def create(
        self,
        *,
        name: str,
        path: str | None = None,
        match: str | None = None,
        matching_algorithm: MatchingAlgorithm | None = None,
        is_insensitive: bool | None = None,
        owner: int | None = None,
        set_permissions: SetPermissions | None = None,
    ) -> StoragePath:
        """Create a new storage path.
        
        This is a sync wrapper for the async method with exactly the same parameters.
        See: `easypaperless.StoragePathsResource.create` 
        """
        return cast(
            StoragePath,
            self._run(
                self._async_storage_paths.create(
                    name=name,
                    path=path,
                    match=match,
                    matching_algorithm=matching_algorithm,
                    is_insensitive=is_insensitive,
                    owner=owner,
                    set_permissions=set_permissions,
                )
            ),
        )

    def update(
        self,
        id: int,
        *,
        name: str | None = None,
        path: str | None = None,
        match: str | None = None,
        matching_algorithm: MatchingAlgorithm | None = None,
        is_insensitive: bool | None = None,
    ) -> StoragePath:
        """Partially update a storage path.
        
        This is a sync wrapper for the async method with exactly the same parameters.
        See: `easypaperless.StoragePathsResource.update` 
        """
        return cast(
            StoragePath,
            self._run(
                self._async_storage_paths.update(
                    id,
                    name=name,
                    path=path,
                    match=match,
                    matching_algorithm=matching_algorithm,
                    is_insensitive=is_insensitive,
                )
            ),
        )

    def delete(self, id: int) -> None:
        """Delete a storage path.
        
        This is a sync wrapper for the async method with exactly the same parameters.
        See: `easypaperless.StoragePathsResource.delete` 
        """
        self._run(self._async_storage_paths.delete(id))

    def bulk_delete(self, ids: List[int]) -> None:
        """Permanently delete multiple storage paths.
        
        This is a sync wrapper for the async method with exactly the same parameters.
        See: `easypaperless.StoragePathsResource.bulk_delete` 
        """
        self._run(self._async_storage_paths.bulk_delete(ids))

    def bulk_set_permissions(
        self,
        ids: List[int],
        *,
        set_permissions: SetPermissions | None = None,
        owner: int | None = None,
        merge: bool = False,
    ) -> None:
        """Set permissions and/or owner on multiple storage paths.
        
        This is a sync wrapper for the async method with exactly the same parameters.
        See: `easypaperless.StoragePathsResource.bulk_set_permissions` 
        """
        self._run(
            self._async_storage_paths.bulk_set_permissions(
                ids, set_permissions=set_permissions, owner=owner, merge=merge
            )
        )
