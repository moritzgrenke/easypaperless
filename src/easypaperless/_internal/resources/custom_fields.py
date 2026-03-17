"""Custom fields resource for PaperlessClient."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from easypaperless._internal.sentinel import UNSET, Unset
from easypaperless.models.custom_fields import CustomField
from easypaperless.models.paged_result import PagedResult
from easypaperless.models.permissions import SetPermissions

if TYPE_CHECKING:
    from easypaperless.client import _ClientCore


class CustomFieldsResource:
    """Accessor for custom fields: ``client.custom_fields``."""

    def __init__(self, core: _ClientCore) -> None:
        self._core = core

    async def list(
        self,
        *,
        name_contains: str | None = None,
        name_exact: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
        ordering: str | None = None,
        descending: bool = False,
    ) -> PagedResult[CustomField]:
        """Return all custom fields defined in paperless-ngx.

        When ``page`` is ``None`` (the default), all pages are fetched
        automatically and ``next`` / ``previous`` in the result are always
        ``None``.  When ``page`` is set, only that page is fetched and
        ``next`` / ``previous`` reflect the raw API values.

        Args:
            name_contains: Case-insensitive substring filter on name.
            name_exact: Case-insensitive exact match on name.
            page: Return only this specific page (1-based).
            page_size: Number of results per page.
            ordering: Field to sort by.
            descending: When ``True``, reverses the sort direction.

        Returns:
            :class:`~easypaperless.models.paged_result.PagedResult` of
            :class:`~easypaperless.models.custom_fields.CustomField` objects.
        """
        params: dict[str, Any] = {}
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
            PagedResult[CustomField],
            await self._core._list_resource("custom_fields", CustomField, params or None),
        )

    async def get(self, id: int) -> CustomField:
        """Fetch a single custom field by its ID.

        Args:
            id: Numeric custom-field ID.

        Returns:
            The :class:`~easypaperless.models.custom_fields.CustomField` with the given ID.

        Raises:
            ~easypaperless.exceptions.NotFoundError: If no custom field exists with that ID.
        """
        return cast(CustomField, await self._core._get_resource("custom_fields", id, CustomField))

    async def create(
        self,
        *,
        name: str,
        data_type: str,
        extra_data: Any | None = None,
        owner: int | None | Unset = UNSET,
        set_permissions: SetPermissions | None | Unset = UNSET,
    ) -> CustomField:
        """Create a new custom field.

        Args:
            name: Field name shown in the UI. Must be unique.
            data_type: Value type. One of ``"string"``, ``"boolean"``,
                ``"integer"``, ``"float"``, ``"monetary"``, ``"date"``,
                ``"url"``, ``"documentlink"``, ``"select"``.
            extra_data: Additional configuration for the field type.
            owner: Numeric user ID to assign as owner.
            set_permissions: Explicit view/change permission sets.
                Pass ``None`` to create with empty permissions.

        Returns:
            The newly created :class:`~easypaperless.models.custom_fields.CustomField`.
        """
        return cast(
            CustomField,
            await self._core._create_resource(
                "custom_fields",
                CustomField,
                owner=owner,
                set_permissions=set_permissions,
                name=name,
                data_type=data_type,
                extra_data=extra_data,
            ),
        )

    async def update(
        self,
        id: int,
        *,
        name: str | Unset = UNSET,
        data_type: str | Unset = UNSET,
        extra_data: Any | None | Unset = UNSET,
        owner: int | None | Unset = UNSET,
        set_permissions: SetPermissions | None | Unset = UNSET,
    ) -> CustomField:
        """Partially update a custom field (PATCH semantics).

        Args:
            id: Numeric ID of the custom field to update.
            name: Field name shown in the UI.
            data_type: Value type (e.g. ``"string"``, ``"boolean"``, ``"integer"``).
                Omit (or pass :data:`~easypaperless.UNSET`) to leave unchanged.
            extra_data: Additional configuration for the field type.
            owner: Numeric user ID to assign as owner.
                Pass ``None`` to clear the owner.
                Omit (or pass :data:`~easypaperless.UNSET`) to leave unchanged.
            set_permissions: Explicit view/change permission sets.
                Pass ``None`` to clear all permissions (overwrite with empty).
                Omit (or pass :data:`~easypaperless.UNSET`) to leave unchanged.

        Returns:
            The updated :class:`~easypaperless.models.custom_fields.CustomField`.
        """
        return cast(
            CustomField,
            await self._core._update_resource(
                "custom_fields",
                id,
                CustomField,
                name=name,
                data_type=data_type,
                extra_data=extra_data,
                owner=owner,
                set_permissions=set_permissions,
            ),
        )

    async def delete(self, id: int) -> None:
        """Delete a custom field.

        Args:
            id: Numeric ID of the custom field to delete.

        Raises:
            ~easypaperless.exceptions.NotFoundError: If no custom field exists with that ID.
        """
        await self._core._delete_resource("custom_fields", id)
