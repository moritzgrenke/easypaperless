"""Sync custom fields resource."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, cast

from easypaperless.models.custom_fields import CustomField
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
        page: int | None = None,
        page_size: int | None = None,
        ordering: str | None = None,
        descending: bool = False,
    ) -> List[CustomField]:
        """Return all custom fields defined in paperless-ngx."""
        return cast(
            List[CustomField],
            self._run(
                self._async_custom_fields.list(
                    page=page,
                    page_size=page_size,
                    ordering=ordering,
                    descending=descending,
                )
            ),
        )

    def get(self, id: int) -> CustomField:
        """Fetch a single custom field by its ID."""
        return cast(CustomField, self._run(self._async_custom_fields.get(id)))

    def create(
        self,
        *,
        name: str,
        data_type: str,
        extra_data: Any | None = None,
        owner: int | None = None,
        set_permissions: SetPermissions | None = None,
    ) -> CustomField:
        """Create a new custom field."""
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
        name: str | None = None,
        extra_data: Any | None = None,
    ) -> CustomField:
        """Partially update a custom field."""
        return cast(
            CustomField,
            self._run(
                self._async_custom_fields.update(
                    id,
                    name=name,
                    extra_data=extra_data,
                )
            ),
        )

    def delete(self, id: int) -> None:
        """Delete a custom field."""
        self._run(self._async_custom_fields.delete(id))
