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

---

## QA

**Tested by:** QA Engineer
**Date:** 2026-04-07
**Commit:** dc83702 (implementation uncommitted at QA time — working tree changes)

### Test Results

| # | Test Case | Expected | Actual | Status |
|---|-----------|----------|--------|--------|
| 1 | AC1: `client.documents.history(document_id)` callable on async client | Method exists, callable, returns result | `DocumentsResource.history` present with correct signature | ✅ Pass |
| 2 | AC1: `client.documents.history(document_id)` callable on sync client | Method exists on `SyncDocumentsResource` | `SyncDocumentsResource.history` present with correct signature | ✅ Pass |
| 3 | AC2: `page` and `page_size` forwarded as query params | `?page=2&page_size=5` appears in request URL | Query string `b'page=2&page_size=5'` confirmed in request | ✅ Pass |
| 4 | AC2: No params → no query string appended | Request URL has no page params | Confirmed — `params or None` guard prevents empty dict | ✅ Pass |
| 5 | AC3: Return type is `PagedResult[AuditLogEntry]` | `isinstance(result, PagedResult)` and items are `AuditLogEntry` | Confirmed via test and manual verification | ✅ Pass |
| 6 | AC4: Plain array → synthetic `PagedResult` with `count=len`, `next=None`, `previous=None` | count=2, next=None, previous=None | count=2, next=None, previous=None — confirmed | ✅ Pass |
| 7 | AC4: `all` set to list of entry IDs | `all=[5, 3]` for two entries | `all=[5, 3]` — confirmed | ✅ Pass |
| 8 | AC4: `all=None` when empty array | `all=None` | `all=None` — confirmed | ✅ Pass |
| 9 | AC5: `actor=None` entry does not raise | Returns `AuditLogEntry` with `actor=None` | `result.results[0].actor is None` — confirmed | ✅ Pass |
| 10 | AC5: Entry with actor parses `AuditLogActor` correctly | `actor.id=4`, `actor.username="claude-ki"` | Confirmed via test | ✅ Pass |
| 11 | AC6: `AuditLogActor` exported from top-level `easypaperless` | `import easypaperless; easypaperless.AuditLogActor` works | `<class 'easypaperless.models.documents.AuditLogActor'>` | ✅ Pass |
| 12 | AC6: `AuditLogEntry` exported from top-level `easypaperless` | `easypaperless.AuditLogEntry` works | `<class 'easypaperless.models.documents.AuditLogEntry'>` | ✅ Pass |
| 13 | AC7: Tests cover non-empty plain-array response | Test exists and passes | `test_history_returns_paged_result` ✅ | ✅ Pass |
| 14 | AC7: Tests cover empty plain-array response | Test exists and passes | `test_history_empty` ✅ | ✅ Pass |
| 15 | AC7: Tests cover `actor=None` entry | Test exists and passes | `test_history_entry_no_actor` ✅ | ✅ Pass |
| 16 | AC8: mypy strict passes | No errors on `src/easypaperless/` | `Success: no issues found in 38 source files` | ✅ Pass |
| 17 | AC9: Ruff lint passes | No lint errors | `All checks passed!` | ✅ Pass |
| 18 | AC9: Ruff format passes (changed files) | No format issues on src/ and new test file | `39 files already formatted` | ✅ Pass |
| 19 | Edge: `NotFoundError` raised for unknown document ID | `NotFoundError` raised on 404 | `test_history_not_found` ✅ | ✅ Pass |
| 20 | Edge: Docstrings present on async and sync methods | Non-empty `__doc__` on both | Both confirmed True | ✅ Pass |
| 21 | Regression: Full test suite unaffected | 652 passed, 0 failed | 652 passed in 117s | ✅ Pass |

### Bugs Found

None.

### Automated Tests
- Suite: `pytest tests/` (excluding integration) — **652 passed, 0 failed**
- Suite: `pytest tests/test_client_history.py` — **10 passed, 0 failed**
- Mypy strict: ✅ Clean
- Ruff lint: ✅ Clean
- Ruff format (changed files): ✅ Clean

### Summary
- ACs tested: 9/9
- ACs passing: 9/9
- Bugs found: 0
- Recommendation: ✅ Ready to merge
