# PROJ-12: Document Types CRUD

## Status: Implemented
**Created:** 2026-03-06
**Last Updated:** 2026-03-06

## Dependencies
- Requires: PROJ-1 (HTTP Client Core) — for authenticated HTTP requests and error mapping

## User Stories
- As a developer, I want to list all document types so that I can inspect the taxonomy defined in my paperless-ngx instance.
- As a developer, I want to filter document types by name substring so that I can find one without loading the full list.
- As a developer, I want to fetch a single document type by ID so that I can read its properties.
- As a developer, I want to create a new document type with name, auto-match settings, and permissions so that I can manage the taxonomy programmatically.
- As a developer, I want to update an existing document type so that I can rename it or adjust its auto-match rules.
- As a developer, I want to delete a document type so that I can remove unused types without using the web UI.

## Acceptance Criteria

### list_document_types
- [ ] `list_document_types(*, ids, name_contains, page, page_size, ordering, descending) -> list[DocumentType]` fetches `GET /document_types/` and returns validated `DocumentType` instances.
- [ ] `ids` filters to only document types whose ID is in the list (`id__in` query param).
- [ ] `name_contains` does a case-insensitive substring match on document type name (`name__icontains`).
- [ ] When `page` is omitted, all pages are fetched automatically (auto-pagination).
- [ ] When `page` is set, only that page is returned (disables auto-pagination).
- [ ] `ordering` + `descending` control sort order; `descending=True` prepends `-` to the field name.

### get_document_type
- [ ] `get_document_type(id: int) -> DocumentType` fetches `GET /document_types/{id}/` and returns a validated `DocumentType`.
- [ ] Raises `NotFoundError` on HTTP 404.

### create_document_type
- [ ] `create_document_type(*, name, match, matching_algorithm, is_insensitive, owner, set_permissions) -> DocumentType` sends `POST /document_types/` and returns the created `DocumentType`.
- [ ] `name` is required; all other fields are optional.
- [ ] `matching_algorithm` integer values: `0`=none, `1`=any word, `2`=all words, `3`=exact, `4`=regex, `5`=fuzzy, `6`=auto (ML).
- [ ] `owner` sets the owning user ID; `None` leaves the document type without an owner.
- [ ] `set_permissions` sets explicit view/change permissions via `SetPermissions` model.

### update_document_type
- [ ] `update_document_type(id: int, *, name, match, matching_algorithm, is_insensitive) -> DocumentType` sends `PATCH /document_types/{id}/` and returns the updated `DocumentType`.
- [ ] Only fields explicitly passed (not `None`) are included in the payload.
- [ ] Raises `NotFoundError` on HTTP 404.
- [ ] `owner` and `set_permissions` are **not yet supported** in `update_document_type` (planned — consistent with the same gap in `update_document`, `update_tag`, and `update_correspondent`).

### delete_document_type
- [ ] `delete_document_type(id: int) -> None` sends `DELETE /document_types/{id}/` and returns `None` on success.
- [ ] Raises `NotFoundError` on HTTP 404.

### General
- [ ] The `DocumentType` model exposes: `id`, `name`, `slug`, `match`, `matching_algorithm`, `is_insensitive`, `document_count`, `owner`, `user_can_change`.
- [ ] All methods are available on `SyncPaperlessClient` with the same signatures (blocking wrapper).

## Edge Cases
- Creating a document type with a name that already exists → server returns an error (likely HTTP 400); propagated as-is.
- Deleting a document type that is assigned to documents — paperless-ngx clears the `document_type` field on those documents; no error is raised.
- `update_document_type` called with no keyword arguments → empty PATCH payload; server returns the document type unchanged.

---
<!-- Sections below are added by subsequent skills -->

## Tech Design (Solution Architect)
_To be added by /architecture_

## QA Test Results
_To be added by /qa_

## Deployment
_To be added by /deploy_
