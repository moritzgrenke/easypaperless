"""Async PaperlessClient — the primary public interface."""

from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import Any

from easypaperless._internal.http import HttpSession
from easypaperless._internal.resolvers import NameResolver
from easypaperless.exceptions import TaskTimeoutError, UploadError
from easypaperless.models.correspondents import Correspondent
from easypaperless.models.custom_fields import CustomField
from easypaperless.models.document_types import DocumentType
from easypaperless.models.documents import Document, Task, TaskStatus
from easypaperless.models.storage_paths import StoragePath
from easypaperless.models.tags import Tag

_SEARCH_MODE_MAP = {
    "title": "title__icontains",
    "title_or_text": "search",
    "query": "query",
}

_RESOURCE_MODELS = {
    "tags": Tag,
    "correspondents": Correspondent,
    "document_types": DocumentType,
    "storage_paths": StoragePath,
    "custom_fields": CustomField,
}


class PaperlessClient:
    """Async client for the paperless-ngx API."""

    def __init__(
        self,
        url: str,
        api_key: str,
        *,
        poll_interval: float = 2.0,
        poll_timeout: float = 60.0,
    ) -> None:
        self._session = HttpSession(base_url=url, api_key=api_key)
        self._resolver = NameResolver(self._session)
        self._poll_interval = poll_interval
        self._poll_timeout = poll_timeout

    async def close(self) -> None:
        await self._session.close()

    async def __aenter__(self) -> PaperlessClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    # ------------------------------------------------------------------
    # Documents
    # ------------------------------------------------------------------

    async def get_document(self, id: int) -> Document:
        resp = await self._session.get(f"/documents/{id}/")
        return Document.model_validate(resp.json())

    async def list_documents(
        self,
        *,
        search: str | None = None,
        search_mode: str = "title_or_text",
        tags: list[int | str] | None = None,
        any_tag: list[int | str] | None = None,
        exclude_tags: list[int | str] | None = None,
        correspondent: int | str | None = None,
        document_type: int | str | None = None,
        asn: int | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
    ) -> list[Document]:
        params: dict[str, Any] = {}

        if search is not None:
            api_param = _SEARCH_MODE_MAP.get(search_mode, "search")
            params[api_param] = search

        if tags is not None:
            resolved = await self._resolver.resolve_list("tags", tags)
            params["tags__id__all"] = ",".join(str(t) for t in resolved)

        if any_tag is not None:
            resolved = await self._resolver.resolve_list("tags", any_tag)
            params["tags__id__in"] = ",".join(str(t) for t in resolved)

        if exclude_tags is not None:
            resolved = await self._resolver.resolve_list("tags", exclude_tags)
            params["tags__id__none"] = ",".join(str(t) for t in resolved)

        if correspondent is not None:
            resolved_id = await self._resolver.resolve("correspondents", correspondent)
            params["correspondent__id__in"] = resolved_id

        if document_type is not None:
            resolved_id = await self._resolver.resolve("document_types", document_type)
            params["document_type"] = resolved_id

        if asn is not None:
            params["archive_serial_number"] = asn

        if created_after is not None:
            params["created__date__gt"] = created_after

        if created_before is not None:
            params["created__date__lt"] = created_before

        items = await self._session.get_all_pages("/documents/", params)
        return [Document.model_validate(item) for item in items]

    async def update_document(
        self,
        id: int,
        *,
        title: str | None = None,
        date: str | None = None,
        correspondent: int | str | None = None,
        document_type: int | str | None = None,
        storage_path: int | str | None = None,
        tags: list[int | str] | None = None,
        asn: int | None = None,
        custom_fields: list[dict] | None = None,
    ) -> Document:
        payload: dict[str, Any] = {}

        if title is not None:
            payload["title"] = title
        if date is not None:
            payload["created"] = date
        if correspondent is not None:
            payload["correspondent"] = await self._resolver.resolve("correspondents", correspondent)
        if document_type is not None:
            payload["document_type"] = await self._resolver.resolve("document_types", document_type)
        if storage_path is not None:
            payload["storage_path"] = await self._resolver.resolve("storage_paths", storage_path)
        if tags is not None:
            payload["tags"] = await self._resolver.resolve_list("tags", tags)
        if asn is not None:
            payload["archive_serial_number"] = asn
        if custom_fields is not None:
            payload["custom_fields"] = custom_fields

        resp = await self._session.patch(f"/documents/{id}/", json=payload)
        return Document.model_validate(resp.json())

    async def delete_document(self, id: int) -> None:
        await self._session.delete(f"/documents/{id}/")

    async def download_document(self, id: int, *, original: bool = False) -> bytes:
        endpoint = "download" if original else "archive"
        resp = await self._session.get(f"/documents/{id}/{endpoint}/")
        return resp.content

    # ------------------------------------------------------------------
    # Upload
    # ------------------------------------------------------------------

    async def upload_document(
        self,
        file: str | Path,
        *,
        title: str | None = None,
        created: str | None = None,
        correspondent: int | str | None = None,
        document_type: int | str | None = None,
        storage_path: int | str | None = None,
        tags: list[int | str] | None = None,
        asn: int | None = None,
        wait: bool = False,
        poll_interval: float | None = None,
        poll_timeout: float | None = None,
    ) -> str | Document:
        file_path = Path(file)
        file_bytes = file_path.read_bytes()

        data: dict[str, Any] = {}
        if title is not None:
            data["title"] = title
        if created is not None:
            data["created"] = created
        if correspondent is not None:
            data["correspondent"] = await self._resolver.resolve("correspondents", correspondent)
        if document_type is not None:
            data["document_type"] = await self._resolver.resolve("document_types", document_type)
        if storage_path is not None:
            data["storage_path"] = await self._resolver.resolve("storage_paths", storage_path)
        if tags is not None:
            resolved = await self._resolver.resolve_list("tags", tags)
            data["tags"] = resolved
        if asn is not None:
            data["archive_serial_number"] = asn

        files = {"document": (file_path.name, file_bytes)}
        resp = await self._session.post("/documents/post_document/", data=data, files=files)
        task_id: str = resp.text.strip('"')

        if not wait:
            return task_id

        interval = poll_interval if poll_interval is not None else self._poll_interval
        timeout = poll_timeout if poll_timeout is not None else self._poll_timeout
        return await self._poll_task(task_id, poll_interval=interval, poll_timeout=timeout)

    async def _poll_task(
        self, task_id: str, *, poll_interval: float, poll_timeout: float
    ) -> Document:
        deadline = time.monotonic() + poll_timeout
        while time.monotonic() < deadline:
            resp = await self._session.get("/tasks/", params={"task_id": task_id})
            tasks = resp.json()
            if not tasks:
                await asyncio.sleep(poll_interval)
                continue

            task = Task.model_validate(tasks[0])
            if task.status == TaskStatus.SUCCESS:
                doc_id = int(task.related_document)  # type: ignore[arg-type]
                return await self.get_document(doc_id)
            elif task.status == TaskStatus.FAILURE:
                raise UploadError(f"Document processing failed: {task.result}")
            await asyncio.sleep(poll_interval)

        raise TaskTimeoutError(f"Task {task_id!r} did not complete within {poll_timeout}s")

    # ------------------------------------------------------------------
    # Bulk operations
    # ------------------------------------------------------------------

    async def bulk_edit(
        self, document_ids: list[int], method: str, **parameters: Any
    ) -> None:
        payload = {"documents": document_ids, "method": method, "parameters": parameters}
        await self._session.post("/documents/bulk_edit/", json=payload)

    async def bulk_add_tag(self, document_ids: list[int], tag: int | str) -> None:
        tag_id = await self._resolver.resolve("tags", tag)
        await self.bulk_edit(document_ids, "add_tag", tag=tag_id)

    async def bulk_remove_tag(self, document_ids: list[int], tag: int | str) -> None:
        tag_id = await self._resolver.resolve("tags", tag)
        await self.bulk_edit(document_ids, "remove_tag", tag=tag_id)

    async def bulk_modify_tags(
        self,
        document_ids: list[int],
        *,
        add_tags: list[int | str] | None = None,
        remove_tags: list[int | str] | None = None,
    ) -> None:
        add_ids = await self._resolver.resolve_list("tags", add_tags or [])
        remove_ids = await self._resolver.resolve_list("tags", remove_tags or [])
        await self.bulk_edit(document_ids, "modify_tags", add_tags=add_ids, remove_tags=remove_ids)

    async def bulk_delete(self, document_ids: list[int]) -> None:
        await self.bulk_edit(document_ids, "delete")

    async def bulk_edit_objects(
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

    # ------------------------------------------------------------------
    # Internal resource helpers
    # ------------------------------------------------------------------

    async def _list_resource(self, resource: str, model_class: type) -> list:
        items = await self._session.get_all_pages(f"/{resource}/")
        return [model_class.model_validate(item) for item in items]

    async def _get_resource(self, resource: str, id: int, model_class: type):
        resp = await self._session.get(f"/{resource}/{id}/")
        return model_class.model_validate(resp.json())

    async def _create_resource(self, resource: str, model_class: type, **kwargs: Any):
        payload = {k: v for k, v in kwargs.items() if v is not None}
        resp = await self._session.post(f"/{resource}/", json=payload)
        self._resolver.invalidate(resource)
        return model_class.model_validate(resp.json())

    async def _update_resource(self, resource: str, id: int, model_class: type, **kwargs: Any):
        payload = {k: v for k, v in kwargs.items() if v is not None}
        resp = await self._session.patch(f"/{resource}/{id}/", json=payload)
        self._resolver.invalidate(resource)
        return model_class.model_validate(resp.json())

    async def _delete_resource(self, resource: str, id: int) -> None:
        await self._session.delete(f"/{resource}/{id}/")
        self._resolver.invalidate(resource)

    # ------------------------------------------------------------------
    # Tags
    # ------------------------------------------------------------------

    async def list_tags(self) -> list[Tag]:
        return await self._list_resource("tags", Tag)

    async def get_tag(self, id: int) -> Tag:
        return await self._get_resource("tags", id, Tag)

    async def create_tag(self, *, name: str, **kwargs: Any) -> Tag:
        return await self._create_resource("tags", Tag, name=name, **kwargs)

    async def update_tag(self, id: int, **kwargs: Any) -> Tag:
        return await self._update_resource("tags", id, Tag, **kwargs)

    async def delete_tag(self, id: int) -> None:
        await self._delete_resource("tags", id)

    # ------------------------------------------------------------------
    # Correspondents
    # ------------------------------------------------------------------

    async def list_correspondents(self) -> list[Correspondent]:
        return await self._list_resource("correspondents", Correspondent)

    async def get_correspondent(self, id: int) -> Correspondent:
        return await self._get_resource("correspondents", id, Correspondent)

    async def create_correspondent(self, *, name: str, **kwargs: Any) -> Correspondent:
        return await self._create_resource("correspondents", Correspondent, name=name, **kwargs)

    async def update_correspondent(self, id: int, **kwargs: Any) -> Correspondent:
        return await self._update_resource("correspondents", id, Correspondent, **kwargs)

    async def delete_correspondent(self, id: int) -> None:
        await self._delete_resource("correspondents", id)

    # ------------------------------------------------------------------
    # Document Types
    # ------------------------------------------------------------------

    async def list_document_types(self) -> list[DocumentType]:
        return await self._list_resource("document_types", DocumentType)

    async def get_document_type(self, id: int) -> DocumentType:
        return await self._get_resource("document_types", id, DocumentType)

    async def create_document_type(self, *, name: str, **kwargs: Any) -> DocumentType:
        return await self._create_resource("document_types", DocumentType, name=name, **kwargs)

    async def update_document_type(self, id: int, **kwargs: Any) -> DocumentType:
        return await self._update_resource("document_types", id, DocumentType, **kwargs)

    async def delete_document_type(self, id: int) -> None:
        await self._delete_resource("document_types", id)

    # ------------------------------------------------------------------
    # Storage Paths
    # ------------------------------------------------------------------

    async def list_storage_paths(self) -> list[StoragePath]:
        return await self._list_resource("storage_paths", StoragePath)

    async def get_storage_path(self, id: int) -> StoragePath:
        return await self._get_resource("storage_paths", id, StoragePath)

    async def create_storage_path(self, *, name: str, **kwargs: Any) -> StoragePath:
        return await self._create_resource("storage_paths", StoragePath, name=name, **kwargs)

    async def update_storage_path(self, id: int, **kwargs: Any) -> StoragePath:
        return await self._update_resource("storage_paths", id, StoragePath, **kwargs)

    async def delete_storage_path(self, id: int) -> None:
        await self._delete_resource("storage_paths", id)

    # ------------------------------------------------------------------
    # Custom Fields
    # ------------------------------------------------------------------

    async def list_custom_fields(self) -> list[CustomField]:
        return await self._list_resource("custom_fields", CustomField)

    async def get_custom_field(self, id: int) -> CustomField:
        return await self._get_resource("custom_fields", id, CustomField)

    async def create_custom_field(self, *, name: str, data_type: str, **kwargs: Any) -> CustomField:
        return await self._create_resource(
            "custom_fields", CustomField, name=name, data_type=data_type, **kwargs
        )

    async def update_custom_field(self, id: int, **kwargs: Any) -> CustomField:
        return await self._update_resource("custom_fields", id, CustomField, **kwargs)

    async def delete_custom_field(self, id: int) -> None:
        await self._delete_resource("custom_fields", id)
