"""Sync tags resource."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, cast

from easypaperless.models._base import MatchingAlgorithm
from easypaperless.models.permissions import SetPermissions
from easypaperless.models.tags import Tag

if TYPE_CHECKING:
    from easypaperless._internal.resources.tags import TagsResource


class SyncTagsResource:
    """Sync accessor for tags: ``client.tags``."""

    def __init__(self, async_tags: TagsResource, run: Any) -> None:
        self._async_tags = async_tags
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
    ) -> List[Tag]:
        """Return tags defined in paperless-ngx."""
        return cast(
            List[Tag],
            self._run(
                self._async_tags.list(
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

    def get(self, id: int) -> Tag:
        """Fetch a single tag by its ID."""
        return cast(Tag, self._run(self._async_tags.get(id)))

    def create(
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
        """Create a new tag."""
        return cast(
            Tag,
            self._run(
                self._async_tags.create(
                    name=name,
                    color=color,
                    is_inbox_tag=is_inbox_tag,
                    match=match,
                    matching_algorithm=matching_algorithm,
                    is_insensitive=is_insensitive,
                    parent=parent,
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
        color: str | None = None,
        is_inbox_tag: bool | None = None,
        match: str | None = None,
        matching_algorithm: MatchingAlgorithm | None = None,
        is_insensitive: bool | None = None,
        parent: int | None = None,
    ) -> Tag:
        """Partially update a tag."""
        return cast(
            Tag,
            self._run(
                self._async_tags.update(
                    id,
                    name=name,
                    color=color,
                    is_inbox_tag=is_inbox_tag,
                    match=match,
                    matching_algorithm=matching_algorithm,
                    is_insensitive=is_insensitive,
                    parent=parent,
                )
            ),
        )

    def delete(self, id: int) -> None:
        """Delete a tag."""
        self._run(self._async_tags.delete(id))

    def bulk_delete(self, ids: List[int]) -> None:
        """Permanently delete multiple tags."""
        self._run(self._async_tags.bulk_delete(ids))

    def bulk_set_permissions(
        self,
        ids: List[int],
        *,
        set_permissions: SetPermissions | None = None,
        owner: int | None = None,
        merge: bool = False,
    ) -> None:
        """Set permissions and/or owner on multiple tags."""
        self._run(
            self._async_tags.bulk_set_permissions(
                ids, set_permissions=set_permissions, owner=owner, merge=merge
            )
        )
