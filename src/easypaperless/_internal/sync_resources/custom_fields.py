"""Sync custom fields resource."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from easypaperless._internal.sentinel import UNSET, Unset
from easypaperless.models.custom_fields import CustomField
from easypaperless.models.paged_result import PagedResult
from easypaperless.models.permissions import SetPermissions

if TYPE_CHECKING:
    from easypaperless._internal.resources.custom_fields import CustomFieldsResource


class SyncCustomFieldsResource:
    """Sync accessor for custom fields: ``client.custom_fields``."""

    def __init__(self, async_custom_fields: CustomFieldsResource, run: Any) -> None:
        self._async_custom_fields = async_custom_fields
        self._run = run

    def list(
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
        return cast(
            PagedResult[CustomField],
            self._run(
                self._async_custom_fields.list(
                    name_contains=name_contains,
                    name_exact=name_exact,
                    page=page,
                    page_size=page_size,
                    ordering=ordering,
                    descending=descending,
                )
            ),
        )

    def get(self, id: int) -> CustomField:
        """Fetch a single custom field by its ID.

        Args:
            id: Numeric custom-field ID.

        Returns:
            The :class:`~easypaperless.models.custom_fields.CustomField` with the given ID.

        Raises:
            ~easypaperless.exceptions.NotFoundError: If no custom field exists with that ID.
        """
        return cast(CustomField, self._run(self._async_custom_fields.get(id)))

    def create(
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
            self._run(
                self._async_custom_fields.create(
                    name=name,
                    data_type=data_type,
                    extra_data=extra_data,
                    owner=owner,
                    set_permissions=set_permissions,
                )
            ),
        )

    def update(
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
            self._run(
                self._async_custom_fields.update(
                    id,
                    name=name,
                    data_type=data_type,
                    extra_data=extra_data,
                    owner=owner,
                    set_permissions=set_permissions,
                )
            ),
        )

    def delete(self, id: int) -> None:
        """Delete a custom field.

        Args:
            id: Numeric ID of the custom field to delete.

        Raises:
            ~easypaperless.exceptions.NotFoundError: If no custom field exists with that ID.
        """
        self._run(self._async_custom_fields.delete(id))
