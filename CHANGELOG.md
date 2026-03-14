# Changelog

All notable changes to this project will be documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.2.0] - 2026-03-14

### Breaking Changes

- `DocumentsResource.update()`: parameter `date` renamed to `created`; parameter `asn` renamed to `archive_serial_number`.
- `DocumentsResource.upload()`: parameter `asn` renamed to `archive_serial_number`.
- `DocumentsResource.list()`: default `search_mode` changed from `"title_or_text"` to `"title_or_content"`; map key `"title_or_text"` removed in favour of `"title_or_content"`.
- `client.bulk_edit_objects()` is now private (`_bulk_edit_objects`). It was an internal helper and was not intended for direct use.
- `client.documents.bulk_edit()` is now private (`_bulk_edit`). It was an internal helper and was not intended for direct use.
- `create()` methods on `TagsResource`, `CorrespondentsResource`, `DocumentTypesResource`, `StoragePathsResource`, and `CustomFieldsResource`: `is_insensitive` now defaults to `True` (was `False`), matching the paperless-ngx API default.
- The client API has been refactored from flat methods to a resource-based API.
  All resource operations are now accessed through resource objects on the client:

| Before (0.1) | After (0.2) |
|---|---|
| `client.list_documents(...)` | `client.documents.list(...)` |
| `client.get_document(id)` | `client.documents.get(id)` |
| `client.get_document_metadata(id)` | `client.documents.get_metadata(id)` |
| `client.update_document(id, ...)` | `client.documents.update(id, ...)` |
| `client.delete_document(id)` | `client.documents.delete(id)` |
| `client.download_document(id)` | `client.documents.download(id)` |
| `client.upload_document(...)` | `client.documents.upload(...)` |
| `client.get_notes(doc_id)` | `client.documents.notes.list(doc_id)` |
| `client.create_note(...)` | `client.documents.notes.create(...)` |
| `client.delete_note(...)` | `client.documents.notes.delete(...)` |
| `client.bulk_edit(...)` | `client.documents.bulk_edit(...)` |
| `client.bulk_add_tag(...)` | `client.documents.bulk_add_tag(...)` |
| `client.bulk_remove_tag(...)` | `client.documents.bulk_remove_tag(...)` |
| `client.bulk_modify_tags(...)` | `client.documents.bulk_modify_tags(...)` |
| `client.bulk_delete_documents(ids)` | `client.documents.bulk_delete(ids)` |
| `client.bulk_set_correspondent(...)` | `client.documents.bulk_set_correspondent(...)` |
| `client.bulk_set_document_type(...)` | `client.documents.bulk_set_document_type(...)` |
| `client.bulk_set_storage_path(...)` | `client.documents.bulk_set_storage_path(...)` |
| `client.bulk_modify_custom_fields(...)` | `client.documents.bulk_modify_custom_fields(...)` |
| `client.bulk_set_permissions(...)` | `client.documents.bulk_set_permissions(...)` |
| `client.list_tags(...)` | `client.tags.list(...)` |
| `client.get_tag(id)` | `client.tags.get(id)` |
| `client.create_tag(...)` | `client.tags.create(...)` |
| `client.update_tag(id, ...)` | `client.tags.update(id, ...)` |
| `client.delete_tag(id)` | `client.tags.delete(id)` |
| `client.bulk_delete_tags(ids)` | `client.tags.bulk_delete(ids)` |
| `client.bulk_set_permissions_tags(...)` | `client.tags.bulk_set_permissions(...)` |
| `client.list_correspondents(...)` | `client.correspondents.list(...)` |
| `client.get_correspondent(id)` | `client.correspondents.get(id)` |
| `client.create_correspondent(...)` | `client.correspondents.create(...)` |
| `client.update_correspondent(id, ...)` | `client.correspondents.update(id, ...)` |
| `client.delete_correspondent(id)` | `client.correspondents.delete(id)` |
| `client.list_document_types(...)` | `client.document_types.list(...)` |
| `client.get_document_type(id)` | `client.document_types.get(id)` |
| `client.create_document_type(...)` | `client.document_types.create(...)` |
| `client.update_document_type(id, ...)` | `client.document_types.update(id, ...)` |
| `client.delete_document_type(id)` | `client.document_types.delete(id)` |
| `client.list_storage_paths(...)` | `client.storage_paths.list(...)` |
| `client.get_storage_path(id)` | `client.storage_paths.get(id)` |
| `client.create_storage_path(...)` | `client.storage_paths.create(...)` |
| `client.update_storage_path(id, ...)` | `client.storage_paths.update(id, ...)` |
| `client.delete_storage_path(id)` | `client.storage_paths.delete(id)` |
| `client.list_custom_fields(...)` | `client.custom_fields.list(...)` |
| `client.get_custom_field(id)` | `client.custom_fields.get(id)` |
| `client.create_custom_field(...)` | `client.custom_fields.create(...)` |
| `client.update_custom_field(id, ...)` | `client.custom_fields.update(id, ...)` |
| `client.delete_custom_field(id)` | `client.custom_fields.delete(id)` |

The same changes apply to `SyncPaperlessClient`.

### Fixed

- `DocumentsResource.upload()` `created` parameter now also accepts a `date` object (previously only `str`).
- `SyncPaperlessClient` `create()` method signatures now consistently include `UNSET` as the default for optional nullable parameters, matching the async client.

### Removed

- All flat mixin-based methods on `PaperlessClient` and `SyncPaperlessClient`.
- Internal `_internal/mixins/` and `_internal/sync_mixins/` directories.

### Added

- Resource classes in `_internal/resources/` and `_internal/sync_resources/`.
- `client.documents`, `client.tags`, `client.correspondents`, `client.document_types`,
  `client.storage_paths`, `client.custom_fields` resource accessors.
- `client.documents.notes` sub-resource for document notes.

