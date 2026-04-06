# [FEATURE] Document History (Audit Log) Endpoint

## Summary

Expose `/api/documents/{id}/history/` as `client.documents.history(document_id)` in both the async and sync clients. The endpoint returns the audit log for a single document — a list of timestamped change entries with actor information.

---

## Problem Statement

The paperless-ngx API provides an audit log per document via `GET /api/documents/{id}/history/`, but easypaperless has no method to access it. Users who want to inspect what changes were made to a document, and by whom, have no way to do so through the library.

---

## Proposed Solution

Add a `history()` method to the documents resource (both async and sync) that calls `/api/documents/{id}/history/` and returns a `PagedResult[AuditLogEntry]`.

**Actual API response shape (verified against a live instance):**

The endpoint returns a plain JSON array — not a paginated envelope — regardless of what the OpenAPI schema documents. This is the same behavior as the `/documents/{id}/notes/` endpoint (see #0034). The implementation must handle this defensively: if the response is a plain list, wrap it into a synthetic `PagedResult` with `count=len(results)`, `next=None`, `previous=None`, and `all` set to the list of entry IDs.

Optional `page` and `page_size` query parameters should be forwarded to the API if provided, but their effect on the real API is unconfirmed — they may be silently ignored.

**New models required:**

- `AuditLogActor` — `id: int`, `username: str`
- `AuditLogEntry` — `id: int`, `timestamp: datetime`, `action: str`, `changes: dict[str, Any]`, `actor: AuditLogActor | None`

---

## User Stories

- As a Python developer, I want to call `client.documents.history(document_id)` so that I can retrieve the full audit log for a document.
- As a Python developer, I want the actor field to be `None`-safe so that system-generated log entries (no actor) don't cause errors.

---

## Scope

### In Scope

- `AsyncDocumentsResource.history(document_id, page=None, page_size=None)` method
- `SyncDocumentsResource.history(document_id, page=None, page_size=None)` method
- `AuditLogActor` and `AuditLogEntry` Pydantic models
- Defensive plain-array handling (same pattern as notes/#0034)
- Both models exported via `__init__.py` as part of the public API
- Unit tests (async and sync) mocking the plain-array response shape
- Docstrings on both async and sync methods

### Out of Scope

- Filtering or searching within history entries
- Pagination across multiple pages (forwarding params is sufficient; full auto-pagination is not required)
- Modifying or deleting history entries (API does not support this)

---

## Acceptance Criteria

- [ ] `client.documents.history(document_id)` is callable on both the async and sync clients.
- [ ] The method accepts optional `page: int | None` and `page_size: int | None` parameters, forwarded as query params when provided.
- [ ] The return type is `PagedResult[AuditLogEntry]`.
- [ ] When the API returns a plain JSON array, it is wrapped into a synthetic `PagedResult` with `count=len(results)`, `next=None`, `previous=None`, and `all` set to the list of entry IDs (or `None` if empty).
- [ ] `AuditLogEntry.actor` is typed as `AuditLogActor | None` and does not raise an error when `actor` is absent or `null` in the response.
- [ ] `AuditLogActor` and `AuditLogEntry` are exported from the top-level `easypaperless` package.
- [ ] Unit tests cover: non-empty plain-array response, empty plain-array response, and `actor=None` entries.
- [ ] Mypy (strict) passes with no new errors.
- [ ] Ruff lint and format checks pass.

---

## Dependencies & Constraints

- Follows the same plain-array defensive wrapping pattern established by #0034 for notes.
- `PagedResult` model is already implemented (#0029).
- Both async mixin and sync mixin must be updated (mirrors the notes pattern from #0017/#0034).

---

## Priority

`Medium`

---

## Additional Notes

- Verified via `curl` against a live paperless-ngx instance: the response is a plain JSON array of `AuditLogEntry` objects (no `count`, `next`, `previous` envelope).
- The `changes` field is a free-form dict — keys and value shapes vary by change type (e.g. tag additions, content updates, field changes). Typing it as `dict[str, Any]` is intentional.
- Related: #0034 (plain-array pattern for notes), #0029 (PagedResult model).
