# Changelog

All notable changes to this project will be documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.3.0] - 2026-03-17

### Breaking Changes

- `PaperlessClient` and `SyncPaperlessClient` constructor parameter renamed from `api_key` to `api_token`. Update any call site passing `api_key=` as a keyword argument.
- All `list()` methods now return `PagedResult[T]` instead of `list[T]`. Update call sites to access items via `.results` and the total count via `.count`.

### Added

- `PagedResult[T]` generic Pydantic model exported from `easypaperless`. All `list()` methods across every resource (async and sync) now return this model, providing access to the total item count (`.count`), raw pagination URLs (`.next`, `.previous`), all matching IDs (`.all`), and the result items (`.results`).
- `Unset` type alias and `UNSET` sentinel constant are now exported from the top-level `easypaperless` namespace. Use `UNSET` to signal "not provided" in optional parameters, distinct from explicit `None` (which clears a nullable field). Previously only available as an internal symbol; now fully public and documented.
- Structured logging throughout the library. Every resource method emits an `INFO`-level log record when called; the HTTP layer emits `DEBUG`-level request and response details. All loggers are children of the `easypaperless` logger — attach any standard Python `logging` handler to capture them. Auth tokens are never logged.

### Fixed

- `SyncTagsResource.create()`: `color` and `is_inbox_tag` parameters now correctly default to `UNSET` (was `None`). Previously, omitting these arguments would send `"color": null` and `"is_inbox_tag": null` to the API, silently overriding server-side defaults.
- `None` / `UNSET` semantics corrected across all async resource `create()` and `update()` methods. Parameters that cannot be `None` (e.g. `name`, `match`, `is_insensitive`) now use `UNSET` as their default and exclude `None` from their type. Nullable parameters (e.g. `owner`, `correspondent`) preserve `None` as the "clear this field" value.
- `CustomFieldsResource.update()` now accepts `owner` and `set_permissions` parameters, matching the API capabilities.
- `set_permissions` now supports three-way semantics in all `create()` and `update()` methods: `UNSET` — omit from payload; `None` — overwrite with empty permissions; `SetPermissions(...)` — overwrite with the provided value.

### Changed

- All `Optional[X]` usages in resource method signatures replaced with `X | None` for consistency with the modern Python union syntax.
- Sync resource methods no longer declare an unused `logger` variable. Logging is emitted by the async delegate under the `easypaperless._internal.resources.*` logger hierarchy.

---

## [0.2.1] - 2026-03-15

### Added

- `py.typed` marker file added to the package, making `easypaperless` PEP 561 compliant. Downstream projects running mypy will now receive full type information without needing `--ignore-missing-imports`.

### Fixed

- `Document.created` is now typed as `date | None` instead of `datetime | None`, matching the paperless-ngx v9+ API contract. Parsing documents returned by paperless-ngx v9+ no longer raises a Pydantic `ValidationError` for this field.
  - **Note:** Non-midnight datetime strings (e.g. `"2024-03-15T10:00:00Z"`) passed as `created` will now raise a validation error. If you are on a pre-v9 instance that returns non-midnight datetimes for `created`, pin to `0.2.0`.
  - `Document.created_date` is deprecated by paperless-ngx as of v9 and will be removed in a future API version; use `Document.created` instead.

### Changed

- Sync resource method docstrings (all classes in `_internal/sync_resources/`) now contain full, self-contained `Args`, `Returns`, and `Raises` sections. The previous pattern of deferring to the async counterpart via a cross-reference has been removed.

---

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

