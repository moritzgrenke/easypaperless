"""Sync correspondents resource."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, cast

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
        """Return correspondents defined in paperless-ngx."""
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
        """Fetch a single correspondent by its ID."""
        return cast(Correspondent, self._run(self._async_correspondents.get(id)))

    def create(
        self,
        *,
        name: str,
        match: str | None = None,
        matching_algorithm: MatchingAlgorithm | None = None,
        is_insensitive: bool | None = None,
        owner: int | None = None,
        set_permissions: SetPermissions | None = None,
    ) -> Correspondent:
        """Create a new correspondent."""
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
        name: str | None = None,
        match: str | None = None,
        matching_algorithm: MatchingAlgorithm | None = None,
        is_insensitive: bool | None = None,
    ) -> Correspondent:
        """Partially update a correspondent."""
        return cast(
            Correspondent,
            self._run(
                self._async_correspondents.update(
                    id,
                    name=name,
                    match=match,
                    matching_algorithm=matching_algorithm,
                    is_insensitive=is_insensitive,
                )
            ),
        )

    def delete(self, id: int) -> None:
        """Delete a correspondent."""
        self._run(self._async_correspondents.delete(id))

    def bulk_delete(self, ids: List[int]) -> None:
        """Permanently delete multiple correspondents."""
        self._run(self._async_correspondents.bulk_delete(ids))

    def bulk_set_permissions(
        self,
        ids: List[int],
        *,
        set_permissions: SetPermissions | None = None,
        owner: int | None = None,
        merge: bool = False,
    ) -> None:
        """Set permissions and/or owner on multiple correspondents."""
        self._run(
            self._async_correspondents.bulk_set_permissions(
                ids, set_permissions=set_permissions, owner=owner, merge=merge
            )
        )
