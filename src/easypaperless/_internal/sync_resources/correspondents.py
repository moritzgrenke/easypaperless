"""Sync correspondents resource."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, cast

from easypaperless._internal.sentinel import UNSET, _Unset
from easypaperless.models._base import MatchingAlgorithm
from easypaperless.models.correspondents import Correspondent
from easypaperless.models.permissions import SetPermissions

if TYPE_CHECKING:
    from easypaperless._internal.resources.correspondents import CorrespondentsResource


class SyncCorrespondentsResource:
    """Sync accessor for correspondents: ``client.correspondents``."""

    def __init__(self, async_correspondents: CorrespondentsResource, run: Any) -> None:
        self._async_correspondents = async_correspondents
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
    ) -> List[Correspondent]:
        """Return correspondents defined in paperless-ngx.
        
        This is a sync wrapper for the async method with exactly the same parameters.
        See: `easypaperless.CorrespondentsResource.list` 
        """
        return cast(
            List[Correspondent],
            self._run(
                self._async_correspondents.list(
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

    def get(self, id: int) -> Correspondent:
        """Fetch a single correspondent by its ID.
        
        This is a sync wrapper for the async method with exactly the same parameters.
        See: `easypaperless.CorrespondentsResource.get` 
        """
        return cast(Correspondent, self._run(self._async_correspondents.get(id)))

    def create(
        self,
        *,
        name: str,
        match: str | None = None,
        matching_algorithm: MatchingAlgorithm | None = None,
        is_insensitive: bool | None = None,
        owner: int | None | _Unset = UNSET,
        set_permissions: SetPermissions | None = None,
    ) -> Correspondent:
        """Create a new correspondent.
        
        This is a sync wrapper for the async method with exactly the same parameters.
        See: `easypaperless.CorrespondentsResource.create` 
        """
        return cast(
            Correspondent,
            self._run(
                self._async_correspondents.create(
                    name=name,
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
        name: str | None | _Unset = UNSET,
        match: str | None | _Unset = UNSET,
        matching_algorithm: MatchingAlgorithm | None | _Unset = UNSET,
        is_insensitive: bool | None | _Unset = UNSET,
        owner: int | None | _Unset = UNSET,
    ) -> Correspondent:
        """Partially update a correspondent.
        
        This is a sync wrapper for the async method with exactly the same parameters.
        See: `easypaperless.CorrespondentsResource.update` 
        """
        return cast(
            Correspondent,
            self._run(
                self._async_correspondents.update(
                    id,
                    name=name,
                    match=match,
                    matching_algorithm=matching_algorithm,
                    is_insensitive=is_insensitive,
                    owner=owner,
                )
            ),
        )

    def delete(self, id: int) -> None:
        """Delete a correspondent.
        
        This is a sync wrapper for the async method with exactly the same parameters.
        See: `easypaperless.CorrespondentsResource.delete` 
        """
        self._run(self._async_correspondents.delete(id))

    def bulk_delete(self, ids: List[int]) -> None:
        """Permanently delete multiple correspondents.
        
        This is a sync wrapper for the async method with exactly the same parameters.
        See: `easypaperless.CorrespondentsResource.bulk_delete` 
        """
        self._run(self._async_correspondents.bulk_delete(ids))

    def bulk_set_permissions(
        self,
        ids: List[int],
        *,
        set_permissions: SetPermissions | None = None,
        owner: int | None = None,
        merge: bool = False,
    ) -> None:
        """Set permissions and/or owner on multiple correspondents.
        
        This is a sync wrapper for the async method with exactly the same parameters.
        See: `easypaperless.CorrespondentsResource.bulk_set_permissions` 
        """
        self._run(
            self._async_correspondents.bulk_set_permissions(
                ids, set_permissions=set_permissions, owner=owner, merge=merge
            )
        )
