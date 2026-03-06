# PROJ-14: Storage Paths CRUD

## Status: Implemented
**Created:** 2026-03-06
**Last Updated:** 2026-03-06

## Dependencies
- Requires: PROJ-1 (HTTP Client Core) — for authenticated HTTP requests and error mapping

## User Stories
- As a developer, I want to list all storage paths so that I can inspect how documents are organised on disk in my paperless-ngx instance.
- As a developer, I want to filter storage paths by name substring so that I can find one without loading the full list.
- As a developer, I want to fetch a single storage path by ID so that I can read its template string and properties.
- As a developer, I want to create a new storage path with a path template and auto-match settings so that incoming documents are automatically filed in a structured directory layout.
- As a developer, I want to update an existing storage path so that I can change its template or auto-match rules without recreating it.
- As a developer, I want to delete a storage path so that I can remove unused paths without using the web UI.

## Acceptance Criteria

### list_storage_paths
- [ ] `list_storage_paths(*, ids, name_contains, page, page_size, ordering, descending) -> list[StoragePath]` fetches `GET /storage_paths/` and returns validated `StoragePath` instances.
- [ ] `ids` filters to only storage paths whose ID is in the list (`id__in` query param).
- [ ] `name_contains` does a case-insensitive substring match on storage path name (`name__icontains`).
- [ ] When `page` is omitted, all pages are fetched automatically (auto-pagination).
- [ ] When `page` is set, only that page is returned (disables auto-pagination).
- [ ] `ordering` + `descending` control sort order; `descending=True` prepends `-` to the field name.

### get_storage_path
- [ ] `get_storage_path(id: int) -> StoragePath` fetches `GET /storage_paths/{id}/` and returns a validated `StoragePath`.
- [ ] Raises `NotFoundError` on HTTP 404.

### create_storage_path
- [ ] `create_storage_path(*, name, path, match, matching_algorithm, is_insensitive, owner, set_permissions) -> StoragePath` sends `POST /storage_paths/` and returns the created `StoragePath`.
- [ ] `name` is required; all other fields are optional.
- [ ] `path` is a template string controlling where archived files are stored. Supported placeholders: `{created_year}`, `{created_month}`, `{created_day}`, `{correspondent}`, `{document_type}`, `{title}`, `{asn}`. Example: `"{created_year}/{correspondent}/{title}"`. When omitted, the server default location is used.
- [ ] `matching_algorithm` integer values: `0`=none, `1`=any word, `2`=all words, `3`=exact, `4`=regex, `5`=fuzzy, `6`=auto (ML).
- [ ] `owner` sets the owning user ID; `None` leaves the storage path without an owner.
- [ ] `set_permissions` sets explicit view/change permissions via `SetPermissions` model.

### update_storage_path
- [ ] `update_storage_path(id: int, *, name, path, match, matching_algorithm, is_insensitive) -> StoragePath` sends `PATCH /storage_paths/{id}/` and returns the updated `StoragePath`.
- [ ] Only fields explicitly passed (not `None`) are included in the payload.
- [ ] Raises `NotFoundError` on HTTP 404.
- [ ] `owner` and `set_permissions` are **not yet supported** in `update_storage_path` (planned — consistent with the same gap in `update_document`, `update_tag`, `update_correspondent`, and `update_document_type`).

### delete_storage_path
- [ ] `delete_storage_path(id: int) -> None` sends `DELETE /storage_paths/{id}/` and returns `None` on success.
- [ ] Raises `NotFoundError` on HTTP 404.

### General
- [ ] The `StoragePath` model exposes: `id`, `name`, `slug`, `path`, `match`, `matching_algorithm`, `is_insensitive`, `document_count`, `owner`, `user_can_change`.
- [ ] All methods are available on `SyncPaperlessClient` with the same signatures (blocking wrapper).

## Edge Cases
- Creating a storage path with a name that already exists → server returns an error (likely HTTP 400); propagated as-is.
- Deleting a storage path that is assigned to documents — paperless-ngx clears the `storage_path` field on those documents; the physical files on disk are **not** moved; no error is raised.
- `path` template with unknown placeholders — the server may accept or reject them; the client does not validate placeholder names.
- `update_storage_path` called with no keyword arguments → empty PATCH payload; server returns the storage path unchanged.

---
<!-- Sections below are added by subsequent skills -->

## Tech Design (Solution Architect)
_To be added by /architecture_

## QA Test Results
_To be added by /qa_

## Deployment
_To be added by /deploy_
