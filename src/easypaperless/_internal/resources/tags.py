"""Tags resource for PaperlessClient."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, cast

from easypaperless.models._base import MatchingAlgorithm
from easypaperless.models.permissions import SetPermissions
from easypaperless.models.tags import Tag

if TYPE_CHECKING:
    from easypaperless.client import _ClientCore


class TagsResource:
    """Accessor for tags: ``client.tags``."""

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
    ) -> List[Tag]:
        """Return tags defined in paperless-ngx.

        Args:
            ids: Return only tags whose ID is in this list.
            name_contains: Case-insensitive substring filter on tag name.
            name_exact: Case-insensitive exact match on tag name.
            page: Return only this specific page (1-based).
            page_size: Number of results per page.
            ordering: Field to sort by.
            descending: When ``True``, reverses the sort direction.

        Returns:
            List of :class:`~easypaperless.models.tags.Tag` objects.
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
            List[Tag],
            await self._core._list_resource("tags", Tag, params or None),
        )

    async def get(self, id: int) -> Tag:
        """Fetch a single tag by its ID.

        Args:
            id: Numeric tag ID.

        Returns:
            The :class:`~easypaperless.models.tags.Tag` with the given ID.

        Raises:
            ~easypaperless.exceptions.NotFoundError: If no tag exists with
                that ID.
        """
        return cast(Tag, await self._core._get_resource("tags", id, Tag))

    async def create(
        self,
        *,
        name: str,
        color: str | None = None,
        is_inbox_tag: bool | None = None,
        match: str | None = None,
        matching_algorithm: MatchingAlgorithm | None = None,
        is_insensitive: bool | None = None,
        parent: int | None = None,
        owner: int | None = None,
        set_permissions: SetPermissions | None = None,
    ) -> Tag:
        """Create a new tag.

        Args:
            name: Tag name. Must be unique.
            color: Background colour as a CSS hex string.
            is_inbox_tag: When ``True``, newly ingested documents get this tag.
            match: Auto-matching pattern.
            matching_algorithm: Controls how ``match`` is applied.
            is_insensitive: When ``True``, ``match`` is case-insensitive.
            parent: ID of parent tag for hierarchical trees.
            owner: Numeric user ID to assign as owner.
            set_permissions: Explicit view/change permission sets.

        Returns:
            The newly created :class:`~easypaperless.models.tags.Tag`.
        """
        return cast(
            Tag,
            await self._core._create_resource(
                "tags",
                Tag,
                owner=owner,
                set_permissions=set_permissions,
                name=name,
                color=color,
                is_inbox_tag=is_inbox_tag,
                match=match,
                matching_algorithm=matching_algorithm,
                is_insensitive=is_insensitive,
                parent=parent,
            ),
        )

    async def update(
        self,
        id: int,
        *,
        name: str | None = None,
        color: str | None = None,
        is_inbox_tag: bool | None = None,
        match: str | None = None,
        matching_algorithm: MatchingAlgorithm | None = None,
        is_insensitive: bool | None = None,
        parent: int | None = None,
    ) -> Tag:
        """Partially update a tag (PATCH semantics).

        Args:
            id: Numeric ID of the tag to update.
            name: Tag name.
            color: Background colour as a CSS hex string.
            is_inbox_tag: When ``True``, newly ingested documents get this tag.
            match: Auto-matching pattern.
            matching_algorithm: Controls how ``match`` is applied.
            is_insensitive: When ``True``, ``match`` is case-insensitive.
            parent: ID of parent tag.

        Returns:
            The updated :class:`~easypaperless.models.tags.Tag`.
        """
        return cast(
            Tag,
            await self._core._update_resource(
                "tags",
                id,
                Tag,
                name=name,
                color=color,
                is_inbox_tag=is_inbox_tag,
                match=match,
                matching_algorithm=matching_algorithm,
                is_insensitive=is_insensitive,
                parent=parent,
            ),
        )

    async def delete(self, id: int) -> None:
        """Delete a tag.

        Args:
            id: Numeric ID of the tag to delete.

        Raises:
            ~easypaperless.exceptions.NotFoundError: If no tag exists with
                that ID.
        """
        await self._core._delete_resource("tags", id)

    async def bulk_delete(self, ids: List[int]) -> None:
        """Permanently delete multiple tags in a single request.

        Args:
            ids: List of tag IDs to delete.
        """
        await self._core._bulk_edit_objects("tags", ids, "delete")

    async def bulk_set_permissions(
        self,
        ids: List[int],
        *,
        set_permissions: SetPermissions | None = None,
        owner: int | None = None,
        merge: bool = False,
    ) -> None:
        """Set permissions and/or owner on multiple tags.

        Args:
            ids: List of tag IDs to modify.
            set_permissions: Explicit view/change permission sets.
            owner: Numeric user ID to assign as owner.
            merge: When ``True``, new permissions are merged with existing ones.
        """
        params: dict[str, Any] = {"merge": merge}
        if set_permissions is not None:
            params["permissions"] = set_permissions.model_dump()
        if owner is not None:
            params["owner"] = owner
        await self._core._bulk_edit_objects("tags", ids, "set_permissions", **params)
