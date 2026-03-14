"""Sync documents resource."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, List, cast

from easypaperless._internal.sentinel import UNSET, _Unset
from easypaperless.models.documents import Document, DocumentMetadata, DocumentNote
from easypaperless.models.permissions import SetPermissions

if TYPE_CHECKING:
    from easypaperless._internal.resources.documents import DocumentsResource, NotesResource


class SyncNotesResource:
    """Sync accessor for document notes: ``client.documents.notes``."""

    def __init__(self, async_notes: NotesResource, run: Any) -> None:
        self._async_notes = async_notes
        self._run = run

    def list(self, document_id: int) -> List[DocumentNote]:
        """Fetch all notes attached to a document.
        
        This is a sync wrapper for the async method with exactly the same parameters.
        See: `easypaperless.NotesResource.list` 
        """
        return cast(List[DocumentNote], self._run(self._async_notes.list(document_id)))

    def create(self, document_id: int, *, note: str) -> DocumentNote:
        """Create a new note on a document.
        
        This is a sync wrapper for the async method with exactly the same parameters.
        See: `easypaperless.NotesResource.create` 
        """
        return cast(DocumentNote, self._run(self._async_notes.create(document_id, note=note)))

    def delete(self, document_id: int, note_id: int) -> None:
        """Delete a note from a document.
        
        This is a sync wrapper for the async method with exactly the same parameters.
        See: `easypaperless.NotesResource.delete` 
        """
        self._run(self._async_notes.delete(document_id, note_id))


class SyncDocumentsResource:
    """Sync accessor for documents: ``client.documents``."""

    def __init__(self, async_documents: DocumentsResource, run: Any) -> None:
        self._async_documents = async_documents
        self._run = run
        self.notes = SyncNotesResource(async_documents.notes, run)

    def get(self, id: int, *, include_metadata: bool = False) -> Document:
        """Fetch a single document by its ID.
        
        This is a sync wrapper for the async method with exactly the same parameters.
        See: `easypaperless.DocumentsResource.get` 
        """
        return cast(
            Document, self._run(self._async_documents.get(id, include_metadata=include_metadata))
        )

    def get_metadata(self, id: int) -> DocumentMetadata:
        """Fetch the extended file-level metadata for a document.
        
        This is a sync wrapper for the async method with exactly the same parameters.
        See: `easypaperless.DocumentsResource.get_metadata` 
        """
        return cast(DocumentMetadata, self._run(self._async_documents.get_metadata(id)))

    def list(
        self,
        *,
        search: str | None = None,
        search_mode: str = "title_or_content",
        ids: List[int] | None = None,
        tags: List[int | str] | None = None,
        any_tags: List[int | str] | None = None,
        exclude_tags: List[int | str] | None = None,
        correspondent: int | str | None | _Unset = UNSET,
        any_correspondent: List[int | str] | None = None,
        exclude_correspondents: List[int | str] | None = None,
        document_type: int | str | None | _Unset = UNSET,
        document_type_name_contains: str | None = None,
        document_type_name_exact: str | None = None,
        any_document_type: List[int | str] | None = None,
        exclude_document_types: List[int | str] | None = None,
        storage_path: int | str | None | _Unset = UNSET,
        any_storage_paths: List[int | str] | None = None,
        exclude_storage_paths: List[int | str] | None = None,
        owner: int | None | _Unset = UNSET,
        exclude_owners: List[int] | None = None,
        custom_fields: List[int | str] | None = None,
        any_custom_fields: List[int | str] | None = None,
        exclude_custom_fields: List[int | str] | None = None,
        custom_field_query: List[Any] | None = None,
        archive_serial_number: int | None | _Unset = UNSET,
        archive_serial_number_from: int | None = None,
        archive_serial_number_till: int | None = None,
        created_after: date | str | None = None,
        created_before: date | str | None = None,
        added_after: date | datetime | str | None = None,
        added_from: date | datetime | str | None = None,
        added_before: date | datetime | str | None = None,
        added_until: date | datetime | str | None = None,
        modified_after: date | datetime | str | None = None,
        modified_from: date | datetime | str | None = None,
        modified_before: date | datetime | str | None = None,
        modified_until: date | datetime | str | None = None,
        checksum: str | None = None,
        page_size: int = 25,
        page: int | None = None,
        ordering: str | None = None,
        descending: bool = False,
        max_results: int | None = None,
        on_page: Callable[[int, int | None], None] | None = None,
    ) -> List[Document]:
        """Return a filtered list of documents.
        
        This is a sync wrapper for the async method with exactly the same parameters.
        See: `easypaperless.DocumentsResource.list` 
        """
        return cast(
            List[Document],
            self._run(
                self._async_documents.list(
                    search=search,
                    search_mode=search_mode,
                    ids=ids,
                    tags=tags,
                    any_tags=any_tags,
                    exclude_tags=exclude_tags,
                    correspondent=correspondent,
                    any_correspondent=any_correspondent,
                    exclude_correspondents=exclude_correspondents,
                    document_type=document_type,
                    document_type_name_contains=document_type_name_contains,
                    document_type_name_exact=document_type_name_exact,
                    any_document_type=any_document_type,
                    exclude_document_types=exclude_document_types,
                    storage_path=storage_path,
                    any_storage_paths=any_storage_paths,
                    exclude_storage_paths=exclude_storage_paths,
                    owner=owner,
                    exclude_owners=exclude_owners,
                    custom_fields=custom_fields,
                    any_custom_fields=any_custom_fields,
                    exclude_custom_fields=exclude_custom_fields,
                    custom_field_query=custom_field_query,
                    archive_serial_number=archive_serial_number,
                    archive_serial_number_from=archive_serial_number_from,
                    archive_serial_number_till=archive_serial_number_till,
                    created_after=created_after,
                    created_before=created_before,
                    added_after=added_after,
                    added_from=added_from,
                    added_before=added_before,
                    added_until=added_until,
                    modified_after=modified_after,
                    modified_from=modified_from,
                    modified_before=modified_before,
                    modified_until=modified_until,
                    checksum=checksum,
                    page_size=page_size,
                    page=page,
                    ordering=ordering,
                    descending=descending,
                    max_results=max_results,
                    on_page=on_page,
                )
            ),
        )

    def update(
        self,
        id: int,
        *,
        title: str | None | _Unset = UNSET,
        content: str | None | _Unset = UNSET,
        created: date | str | None | _Unset = UNSET,
        correspondent: int | str | None | _Unset = UNSET,
        document_type: int | str | None | _Unset = UNSET,
        storage_path: int | str | None | _Unset = UNSET,
        tags: List[int | str] | None | _Unset = UNSET,
        archive_serial_number: int | None | _Unset = UNSET,
        custom_fields: List[dict[str, Any]] | None | _Unset = UNSET,
        owner: int | None | _Unset = UNSET,
        set_permissions: SetPermissions | None | _Unset = UNSET,
        remove_inbox_tags: bool | None | _Unset = UNSET,
    ) -> Document:
        """Partially update a document.

        This is a sync wrapper for the async method with exactly the same parameters.
        See: `easypaperless.DocumentsResource.update`
        """
        return cast(
            Document,
            self._run(
                self._async_documents.update(
                    id,
                    title=title,
                    content=content,
                    created=created,
                    correspondent=correspondent,
                    document_type=document_type,
                    storage_path=storage_path,
                    tags=tags,
                    archive_serial_number=archive_serial_number,
                    custom_fields=custom_fields,
                    owner=owner,
                    set_permissions=set_permissions,
                    remove_inbox_tags=remove_inbox_tags,
                )
            ),
        )

    def delete(self, id: int) -> None:
        """Permanently delete a document.
        
        This is a sync wrapper for the async method with exactly the same parameters.
        See: `easypaperless.DocumentsResource.delete` 
        """
        self._run(self._async_documents.delete(id))

    def download(self, id: int, *, original: bool = False) -> bytes:
        """Download the binary content of a document.
        
        This is a sync wrapper for the async method with exactly the same parameters.
        See: `easypaperless.DocumentsResource.download` 
        """
        return cast(bytes, self._run(self._async_documents.download(id, original=original)))

    def upload(
        self,
        file: str | Path,
        *,
        title: str | None = None,
        created: date | str | None = None,
        correspondent: int | str | None | _Unset = UNSET,
        document_type: int | str | None | _Unset = UNSET,
        storage_path: int | str | None | _Unset = UNSET,
        tags: List[int | str] | None = None,
        archive_serial_number: int | None | _Unset = UNSET,
        custom_fields: List[dict[str, Any]] | None = None,
        wait: bool = False,
        poll_interval: float | None = None,
        poll_timeout: float | None = None,
    ) -> str | Document:
        """Upload a document to paperless-ngx.

        This is a sync wrapper for the async method with exactly the same parameters.
        See: `easypaperless.DocumentsResource.upload`
        """
        return cast(
            str | Document,
            self._run(
                self._async_documents.upload(
                    file,
                    title=title,
                    created=created,
                    correspondent=correspondent,
                    document_type=document_type,
                    storage_path=storage_path,
                    tags=tags,
                    archive_serial_number=archive_serial_number,
                    custom_fields=custom_fields,
                    wait=wait,
                    poll_interval=poll_interval,
                    poll_timeout=poll_timeout,
                )
            ),
        )

    def bulk_add_tag(self, document_ids: List[int], tag: int | str) -> None:
        """Add a tag to multiple documents.
        
        This is a sync wrapper for the async method with exactly the same parameters.
        See: `easypaperless.DocumentsResource.bulk_add_tag` 
        """
        self._run(self._async_documents.bulk_add_tag(document_ids, tag))

    def bulk_remove_tag(self, document_ids: List[int], tag: int | str) -> None:
        """Remove a tag from multiple documents.
        
        This is a sync wrapper for the async method with exactly the same parameters.
        See: `easypaperless.DocumentsResource.bulk_remove_tag` 
        """
        self._run(self._async_documents.bulk_remove_tag(document_ids, tag))

    def bulk_modify_tags(
        self,
        document_ids: List[int],
        *,
        add_tags: List[int | str] | None = None,
        remove_tags: List[int | str] | None = None,
    ) -> None:
        """Add and/or remove tags on multiple documents atomically.
        
        This is a sync wrapper for the async method with exactly the same parameters.
        See: `easypaperless.DocumentsResource.bulk_modify_tags` 
        """
        self._run(
            self._async_documents.bulk_modify_tags(
                document_ids, add_tags=add_tags, remove_tags=remove_tags
            )
        )

    def bulk_delete(self, document_ids: List[int]) -> None:
        """Permanently delete multiple documents.
        
        This is a sync wrapper for the async method with exactly the same parameters.
        See: `easypaperless.DocumentsResource.bulk_delete` 
        """
        self._run(self._async_documents.bulk_delete(document_ids))

    def bulk_set_correspondent(
        self, document_ids: List[int], correspondent: int | str | None
    ) -> None:
        """Assign a correspondent to multiple documents.
        
        This is a sync wrapper for the async method with exactly the same parameters.
        See: `easypaperless.DocumentsResource.bulk_set_correspondent` 
        """
        self._run(self._async_documents.bulk_set_correspondent(document_ids, correspondent))

    def bulk_set_document_type(
        self, document_ids: List[int], document_type: int | str | None
    ) -> None:
        """Assign a document type to multiple documents.
        
        This is a sync wrapper for the async method with exactly the same parameters.
        See: `easypaperless.DocumentsResource.bulk_set_document_type` 
        """
        self._run(self._async_documents.bulk_set_document_type(document_ids, document_type))

    def bulk_set_storage_path(
        self, document_ids: List[int], storage_path: int | str | None
    ) -> None:
        """Assign a storage path to multiple documents.
        
        This is a sync wrapper for the async method with exactly the same parameters.
        See: `easypaperless.DocumentsResource.bulk_set_storage_path` 
        """
        self._run(self._async_documents.bulk_set_storage_path(document_ids, storage_path))

    def bulk_modify_custom_fields(
        self,
        document_ids: List[int],
        *,
        add_fields: List[dict[str, Any]] | None = None,
        remove_fields: List[int] | None = None,
    ) -> None:
        """Add and/or remove custom field values on multiple documents.
        
        This is a sync wrapper for the async method with exactly the same parameters.
        See: `easypaperless.DocumentsResource.bulk_modify_custom_fields` 
        """
        self._run(
            self._async_documents.bulk_modify_custom_fields(
                document_ids, add_fields=add_fields, remove_fields=remove_fields
            )
        )

    def bulk_set_permissions(
        self,
        document_ids: List[int],
        *,
        set_permissions: SetPermissions | None = None,
        owner: int | None = None,
        merge: bool = False,
    ) -> None:
        """Set permissions and/or owner on multiple documents.
        
        This is a sync wrapper for the async method with exactly the same parameters.
        See: `easypaperless.DocumentsResource.bulk_set_permissions` 
        """
        self._run(
            self._async_documents.bulk_set_permissions(
                document_ids,
                set_permissions=set_permissions,
                owner=owner,
                merge=merge,
            )
        )
