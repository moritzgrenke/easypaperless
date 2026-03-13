"""Correspondents resource for PaperlessClient."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, cast

from easypaperless.models._base import MatchingAlgorithm
from easypaperless.models.correspondents import Correspondent
from easypaperless.models.permissions import SetPermissions

if TYPE_CHECKING:
    from easypaperless.client import _ClientCore


class CorrespondentsResource:
    """Accessor for correspondents: ``client.correspondents``."""

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
    ) -> List[Correspondent]:
        """Return correspondents defined in paperless-ngx.

        Args:
            ids: Return only correspondents whose ID is in this list.
            name_contains: Case-insensitive substring filter on name.
            name_exact: Case-insensitive exact match on name.
            page: Return only this specific page (1-based).
            page_size: Number of results per page.
            ordering: Field to sort by.
            descending: When ``True``, reverses the sort direction.

        Returns:
            List of :class:`~easypaperless.models.correspondents.Correspondent` objects.
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
            List[Correspondent],
            await self._core._list_resource("correspondents", Correspondent, params or None),
        )

    async def get(self, id: int) -> Correspondent:
        """Fetch a single correspondent by its ID.

        Args:
            id: Numeric correspondent ID.

        Returns:
            The :class:`~easypaperless.models.correspondents.Correspondent` with the given ID.

        Raises:
            ~easypaperless.exceptions.NotFoundError: If no correspondent exists with that ID.
        """
        return cast(
            Correspondent, await self._core._get_resource("correspondents", id, Correspondent)
        )

    async def create(
        self,
        *,
        name: str,
        match: str | None = None,
        matching_algorithm: MatchingAlgorithm | None = None,
        is_insensitive: bool | None = None,
        owner: int | None = None,
        set_permissions: SetPermissions | None = None,
    ) -> Correspondent:
        """Create a new correspondent.

        Args:
            name: Correspondent name. Must be unique.
            match: Auto-matching pattern.
            matching_algorithm: Controls how ``match`` is applied.
            is_insensitive: When ``True``, ``match`` is case-insensitive.
            owner: Numeric user ID to assign as owner.
            set_permissions: Explicit view/change permission sets.

        Returns:
            The newly created :class:`~easypaperless.models.correspondents.Correspondent`.
        """
        return cast(
            Correspondent,
            await self._core._create_resource(
                "correspondents",
                Correspondent,
                owner=owner,
                set_permissions=set_permissions,
                name=name,
                match=match,
                matching_algorithm=matching_algorithm,
                is_insensitive=is_insensitive,
            ),
        )

    async def update(
        self,
        id: int,
        *,
        name: str | None = None,
        match: str | None = None,
        matching_algorithm: MatchingAlgorithm | None = None,
        is_insensitive: bool | None = None,
    ) -> Correspondent:
        """Partially update a correspondent (PATCH semantics).

        Args:
            id: Numeric ID of the correspondent to update.
            name: Correspondent name.
            match: Auto-matching pattern.
            matching_algorithm: Controls how ``match`` is applied.
            is_insensitive: When ``True``, ``match`` is case-insensitive.

        Returns:
            The updated :class:`~easypaperless.models.correspondents.Correspondent`.
        """
        return cast(
            Correspondent,
            await self._core._update_resource(
                "correspondents",
                id,
                Correspondent,
                name=name,
                match=match,
                matching_algorithm=matching_algorithm,
                is_insensitive=is_insensitive,
            ),
        )

    async def delete(self, id: int) -> None:
        """Delete a correspondent.

        Args:
            id: Numeric ID of the correspondent to delete.

        Raises:
            ~easypaperless.exceptions.NotFoundError: If no correspondent exists with that ID.
        """
        await self._core._delete_resource("correspondents", id)

    async def bulk_delete(self, ids: List[int]) -> None:
        """Permanently delete multiple correspondents in a single request.

        Args:
            ids: List of correspondent IDs to delete.
        """
        await self._core._bulk_edit_objects("correspondents", ids, "delete")

    async def bulk_set_permissions(
        self,
        ids: List[int],
        *,
        set_permissions: SetPermissions | None = None,
        owner: int | None = None,
        merge: bool = False,
    ) -> None:
        """Set permissions and/or owner on multiple correspondents.

        Args:
            ids: List of correspondent IDs to modify.
            set_permissions: Explicit view/change permission sets.
            owner: Numeric user ID to assign as owner.
            merge: When ``True``, new permissions are merged with existing ones.
        """
        params: dict[str, Any] = {"merge": merge}
        if set_permissions is not None:
            params["permissions"] = set_permissions.model_dump()
        if owner is not None:
            params["owner"] = owner
        await self._core._bulk_edit_objects("correspondents", ids, "set_permissions", **params)
