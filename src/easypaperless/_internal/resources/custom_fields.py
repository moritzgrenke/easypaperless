"""Custom fields resource for PaperlessClient."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, cast

from easypaperless._internal.sentinel import UNSET, _Unset
from easypaperless.models.custom_fields import CustomField
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
        page: int | None = None,
        page_size: int | None = None,
        ordering: str | None = None,
        descending: bool = False,
    ) -> List[CustomField]:
        """Return all custom fields defined in paperless-ngx.

        Args:
            page: Return only this specific page (1-based).
            page_size: Number of results per page.
            ordering: Field to sort by.
            descending: When ``True``, reverses the sort direction.

        Returns:
            List of :class:`~easypaperless.models.custom_fields.CustomField` objects.
        """
        params: dict[str, Any] = {}
        if page is not None:
            params["page"] = page
        if page_size is not None:
            params["page_size"] = page_size
        if ordering is not None:
            params["ordering"] = f"-{ordering}" if descending else ordering
        return cast(
            List[CustomField],
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
        owner: int | None | _Unset = UNSET,
        set_permissions: SetPermissions | None = None,
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
        name: str | None | _Unset = UNSET,
        extra_data: Any | None | _Unset = UNSET,
    ) -> CustomField:
        """Partially update a custom field (PATCH semantics).

        Args:
            id: Numeric ID of the custom field to update.
            name: Field name shown in the UI.
            extra_data: Additional configuration for the field type.

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
                extra_data=extra_data,
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
