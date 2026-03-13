"""Sync document types resource."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, cast

from easypaperless.models._base import MatchingAlgorithm
from easypaperless.models.document_types import DocumentType
from easypaperless.models.permissions import SetPermissions

if TYPE_CHECKING:
    from easypaperless._internal.resources.document_types import DocumentTypesResource


class SyncDocumentTypesResource:
    """Sync accessor for document types: ``client.document_types``."""

    def __init__(self, async_document_types: DocumentTypesResource, run: Any) -> None:
        self._async_document_types = async_document_types
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
    ) -> List[DocumentType]:
        """Return document types defined in paperless-ngx."""
        return cast(
            List[DocumentType],
            self._run(
                self._async_document_types.list(
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

    def get(self, id: int) -> DocumentType:
        """Fetch a single document type by its ID."""
        return cast(DocumentType, self._run(self._async_document_types.get(id)))

    def create(
        self,
        *,
        name: str,
        match: str | None = None,
        matching_algorithm: MatchingAlgorithm | None = None,
        is_insensitive: bool | None = None,
        owner: int | None = None,
        set_permissions: SetPermissions | None = None,
    ) -> DocumentType:
        """Create a new document type."""
        return cast(
            DocumentType,
            self._run(
                self._async_document_types.create(
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
    ) -> DocumentType:
        """Partially update a document type."""
        return cast(
            DocumentType,
            self._run(
                self._async_document_types.update(
                    id,
                    name=name,
                    match=match,
                    matching_algorithm=matching_algorithm,
                    is_insensitive=is_insensitive,
                )
            ),
        )

    def delete(self, id: int) -> None:
        """Delete a document type."""
        self._run(self._async_document_types.delete(id))

    def bulk_delete(self, ids: List[int]) -> None:
        """Permanently delete multiple document types."""
        self._run(self._async_document_types.bulk_delete(ids))

    def bulk_set_permissions(
        self,
        ids: List[int],
        *,
        set_permissions: SetPermissions | None = None,
        owner: int | None = None,
        merge: bool = False,
    ) -> None:
        """Set permissions and/or owner on multiple document types."""
        self._run(
            self._async_document_types.bulk_set_permissions(
                ids, set_permissions=set_permissions, owner=owner, merge=merge
            )
        )
