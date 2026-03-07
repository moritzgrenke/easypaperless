# PROJ-15: Non-Document Bulk Operations

## Status: Implemented
**Created:** 2026-03-06
**Last Updated:** 2026-03-06

## Dependencies
- Requires: PROJ-1 (HTTP Client Core) — for authenticated HTTP requests and error mapping

## User Stories
- As a developer, I want to permanently delete multiple tags, correspondents, document types, or storage paths in a single request so that I can clean up resources in bulk without looping.
- As a developer, I want to set permissions and owner on multiple non-document resources at once so that I can apply access control to an entire group of tags or correspondents in one call.
- As a developer, I want a low-level escape hatch to call any bulk object operation the paperless-ngx API supports so that new operations are accessible without waiting for a high-level helper.

## Acceptance Criteria

### Low-level primitive (implemented)
- [ ] `bulk_edit_objects(object_type: str, object_ids: list[int], operation: str, **parameters) -> None` sends `POST /bulk_edit_objects/` with payload `{"objects": object_ids, "object_type": object_type, "operation": operation, ...parameters}` and returns `None` on success.
- [ ] Valid `object_type` values: `"tags"`, `"correspondents"`, `"document_types"`, `"storage_paths"`. Custom fields are **not** supported by this endpoint.
- [ ] Supported `operation` values:
  - `"delete"` — no additional parameters required.
  - `"set_permissions"` — requires a `permissions` object (`{"view": {"users": [], "groups": []}, "change": {"users": [], "groups": []}}`), optional `owner` (user ID or `None`), and optional `merge` (boolean, default `False`; when `True`, new permissions are merged with existing ones rather than replacing them).
- [ ] Invalid `object_type` or `operation` strings are forwarded to the API as-is; the server returns an error which propagates to the caller.

### High-level helpers (implemented)
- [ ] `bulk_delete_tags(ids: list[int]) -> None`
- [ ] `bulk_delete_correspondents(ids: list[int]) -> None`
- [ ] `bulk_delete_document_types(ids: list[int]) -> None`
- [ ] `bulk_delete_storage_paths(ids: list[int]) -> None`
- [ ] `bulk_set_permissions_tags(ids, *, permissions, owner, merge) -> None`
- [ ] `bulk_set_permissions_correspondents(ids, *, permissions, owner, merge) -> None`
- [ ] `bulk_set_permissions_document_types(ids, *, permissions, owner, merge) -> None`
- [ ] `bulk_set_permissions_storage_paths(ids, *, permissions, owner, merge) -> None`
- [ ] All high-level helpers are implemented on top of `bulk_edit_objects`.

### General
- [ ] `bulk_edit_objects` is available on `SyncPaperlessClient` with the same signature (blocking wrapper).

## Edge Cases
- Empty `object_ids` list — the request is sent as-is; the API treats it as a no-op.
- `object_type="custom_fields"` is not supported by the `bulk_edit_objects` endpoint — the server will return an error.
- `bulk_edit_objects` with `operation="delete"` on resources assigned to documents — paperless-ngx clears the relevant field on those documents; physical files are not moved.
- `set_permissions` with `merge=False` (default) replaces all existing permissions; use `merge=True` to additive-update instead of overwrite.

## Out of Scope
- Bulk operations on documents — covered by PROJ-9 (Document Bulk Operations).

---
<!-- Sections below are added by subsequent skills -->

## Tech Design (Solution Architect)
_To be added by /architecture_

## QA Test Results
_To be added by /qa_

## Deployment
_To be added by /deploy_
