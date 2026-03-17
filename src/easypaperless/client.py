"""Async PaperlessClient — the primary public interface."""

from __future__ import annotations

import logging
from typing import Any

from easypaperless._internal.http import HttpSession
from easypaperless._internal.resolvers import NameResolver
from easypaperless._internal.resources.correspondents import CorrespondentsResource
from easypaperless._internal.resources.custom_fields import CustomFieldsResource
from easypaperless._internal.resources.document_types import DocumentTypesResource
from easypaperless._internal.resources.documents import DocumentsResource
from easypaperless._internal.resources.storage_paths import StoragePathsResource
from easypaperless._internal.resources.tags import TagsResource
from easypaperless._internal.sentinel import UNSET, Unset
from easypaperless.models.paged_result import PagedResult
from easypaperless.models.permissions import SetPermissions

logger = logging.getLogger(__name__)


class _ClientCore:
    """Base class: constructor, context manager, and internal CRUD helpers."""

    documents: DocumentsResource
    tags: TagsResource
    correspondents: CorrespondentsResource
    document_types: DocumentTypesResource
    storage_paths: StoragePathsResource
    custom_fields: CustomFieldsResource

    def __init__(
        self,
        url: str,
        api_token: str,
        *,
        timeout: float = 30.0,
        poll_interval: float = 2.0,
        poll_timeout: float = 60.0,
    ) -> None:
        self._session = HttpSession(base_url=url, api_token=api_token, timeout=timeout)
        self._resolver = NameResolver(self._session)
        self._poll_interval = poll_interval
        self._poll_timeout = poll_timeout

        self.documents = DocumentsResource(self)
        self.tags = TagsResource(self)
        self.correspondents = CorrespondentsResource(self)
        self.document_types = DocumentTypesResource(self)
        self.storage_paths = StoragePathsResource(self)
        self.custom_fields = CustomFieldsResource(self)

    async def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        await self._session.close()

    async def __aenter__(self) -> PaperlessClient:
        return self  # type: ignore[return-value]

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def _list_resource(
        self,
        resource: str,
        model_class: type[Any],
        params: dict[str, Any] | None = None,
    ) -> PagedResult[Any]:
        if params and "page" in params:
            raw = await self._session.get_page(f"/{resource}/", params=params)
        else:
            raw = await self._session.get_all_pages_paged(f"/{resource}/", params)
        return PagedResult(
            count=raw.count,
            next=raw.next,
            previous=raw.previous,
            all=raw.all_ids,
            results=[model_class.model_validate(item) for item in raw.items],
        )

    async def _get_resource(self, resource: str, id: int, model_class: type[Any]) -> Any:
        resp = await self._session.get(f"/{resource}/{id}/")
        return model_class.model_validate(resp.json())

    async def _create_resource(
        self,
        resource: str,
        model_class: type[Any],
        *,
        owner: int | None | Unset = UNSET,
        set_permissions: SetPermissions | None | Unset = UNSET,
        **kwargs: Any,
    ) -> Any:
        logger.debug("Creating %s resource", resource)
        payload = {k: v for k, v in kwargs.items() if not isinstance(v, Unset)}
        if not isinstance(owner, Unset):
            payload["owner"] = owner
        if not isinstance(set_permissions, Unset):
            payload["set_permissions"] = (
                SetPermissions().model_dump()
                if set_permissions is None
                else set_permissions.model_dump()
            )
        resp = await self._session.post(f"/{resource}/", json=payload)
        self._resolver.invalidate(resource)
        return model_class.model_validate(resp.json())

    async def _update_resource(
        self,
        resource: str,
        id: int,
        model_class: type[Any],
        *,
        set_permissions: SetPermissions | None | Unset = UNSET,
        **kwargs: Any,
    ) -> Any:
        logger.debug("Updating %s resource id=%d", resource, id)
        payload = {k: v for k, v in kwargs.items() if not isinstance(v, Unset)}
        if not isinstance(set_permissions, Unset):
            payload["set_permissions"] = (
                SetPermissions().model_dump()
                if set_permissions is None
                else set_permissions.model_dump()
            )
        resp = await self._session.patch(f"/{resource}/{id}/", json=payload)
        self._resolver.invalidate(resource)
        return model_class.model_validate(resp.json())

    async def _delete_resource(self, resource: str, id: int) -> None:
        logger.debug("Deleting %s resource id=%d", resource, id)
        await self._session.delete(f"/{resource}/{id}/")
        self._resolver.invalidate(resource)

    async def _bulk_edit_objects(
        self,
        object_type: str,
        object_ids: list[int],
        operation: str,
        **parameters: Any,
    ) -> None:
        payload = {
            "objects": object_ids,
            "object_type": object_type,
            "operation": operation,
            **parameters,
        }
        await self._session.post("/bulk_edit_objects/", json=payload)


class PaperlessClient(_ClientCore):
    """Async client for the paperless-ngx API.

    Resources are accessible as attributes:

    * ``client.correspondents`` — correspondent CRUD + bulk ops -
      see `easypaperless.resources.CorrespondentsResource`
    * ``client.custom_fields`` — custom field CRUD -
      see `easypaperless.resources.CustomFieldsResource`
    * ``client.document_types`` — document type CRUD + bulk ops -
      see `easypaperless.resources.DocumentTypesResource`
    * ``client.documents`` — document CRUD, bulk ops, upload, download -
      see `easypaperless.resources.DocumentsResource`
    * ``client.documents.notes`` — document notes -
      see `easypaperless.resources.NotesResource`
    * ``client.storage_paths`` — storage path CRUD + bulk ops -
      see `easypaperless.resources.StoragePathsResource`
    * ``client.tags`` — tag CRUD + bulk ops -
      see `easypaperless.resources.TagsResource`

    Use as an async context manager to ensure the underlying HTTP connection
    pool is closed when you are done:

    Example:
        async with PaperlessClient(url="http://localhost:8000", api_token="abc") as client:
            docs = await client.documents.list(max_results=10)
    """

    def __init__(
        self,
        url: str,
        api_token: str,
        *,
        timeout: float = 30.0,
        poll_interval: float = 2.0,
        poll_timeout: float = 60.0,
    ) -> None:
        """Create an async paperless-ngx client.

        Args:
            url: Base URL of the paperless-ngx instance
                (e.g. ``"http://localhost:8000"``).
            api_token: API token.  Generate one in paperless-ngx under
                *Settings → API → Generate Token*.
            timeout: Default request timeout in seconds.  Default: ``30.0``.
            poll_interval: Seconds between status checks when ``wait=True``
                is passed to :meth:`documents.upload`.  Default: ``2.0``.
            poll_timeout: Maximum seconds to wait for a document to finish
                processing before raising
                :exc:`~easypaperless.exceptions.TaskTimeoutError`.
                Default: ``60.0``.
        """
        super().__init__(
            url, api_token, timeout=timeout, poll_interval=poll_interval, poll_timeout=poll_timeout
        )

    async def __aenter__(self) -> PaperlessClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
