# [FEATURE] Trash Resource — List and Manage Trashed Documents

## Summary

Expose the paperless-ngx `/api/trash/` endpoint as a `trash` resource on both async and sync clients. Users can list documents currently in the trash and perform targeted actions — restore or permanently empty — on them.

---

## Problem Statement

Documents deleted in paperless-ngx are moved to a trash bin rather than immediately removed. There is currently no way via easypaperless to inspect or manage this trash bin. Users who need to recover accidentally-deleted documents, or who want to permanently purge documents, have no wrapper support.

---

## Proposed Solution

Add a `trash` resource accessible as `client.trash` (async) and `sync_client.trash` (sync). The resource exposes three methods:

- **`list(page, page_size)`** — `GET /api/trash/` — returns a paginated `PagedResult[Document]` of all documents currently in the trash.
- **`restore(document_ids)`** — `POST /api/trash/` with `action="restore"` — recovers the given documents from the trash bin back to active status.
- **`empty(document_ids)`** — `POST /api/trash/` with `action="empty"` — permanently and irreversibly deletes the given documents. **This operation is non-undoable.**

The `empty()` method must carry a prominent docstring warning that the operation is permanent and cannot be undone.

The `document_ids` parameter name follows the convention used in the documents bulk-edit methods (e.g., `bulk_delete`, `bulk_add_tag`).

---

## User Stories

- As a Python developer, I want to list all documents in the trash so that I can inspect what has been deleted.
- As a Python developer, I want to restore trashed documents so that I can recover accidentally-deleted files.
- As a Python developer, I want to permanently delete trashed documents so that I can free storage space, knowing the operation is irreversible.

---

## Scope

### In Scope
- `GET /api/trash/` — `list()` method returning `PagedResult[Document]`, supporting `page` and `page_size` pagination parameters.
- `POST /api/trash/` — `restore(document_ids)` method, sends `{"documents": <ids>, "action": "restore"}`.
- `POST /api/trash/` — `empty(document_ids)` method, sends `{"documents": <ids>, "action": "empty"}`, documented as non-undoable.
- Async resource (`TrashResource`) and sync resource (`SyncTrashResource`).
- Exposed on `PaperlessClient` as `client.trash` and on `SyncPaperlessClient` as `sync_client.trash`.
- Logging calls consistent with other resource methods (issue #0030 pattern).

### Out of Scope
- A combined `action(document_ids, action)` method — the two actions are intentionally separate methods for clarity and safety.
- Individual per-document restore or delete (both methods accept a list and always send a bulk POST).
- Any filtering beyond `page` and `page_size` on the list endpoint.
- Soft-delete or moving documents to trash (that is handled by the existing delete method on documents).

---

## Acceptance Criteria

- [ ] `client.trash.list()` sends `GET /api/trash/` and returns a `PagedResult[Document]`.
- [ ] `client.trash.list(page=2, page_size=10)` passes `page` and `page_size` as query parameters.
- [ ] `client.trash.restore(document_ids=[1, 2])` sends `POST /api/trash/` with body `{"documents": [1, 2], "action": "restore"}`.
- [ ] `client.trash.empty(document_ids=[3])` sends `POST /api/trash/` with body `{"documents": [3], "action": "empty"}`.
- [ ] The `empty()` method docstring contains a clear **irreversible / non-undoable** warning.
- [ ] Both async (`TrashResource`) and sync (`SyncTrashResource`) variants are implemented.
- [ ] `client.trash` and `sync_client.trash` are accessible as public attributes.
- [ ] Unit tests cover: list with default params, list with explicit pagination, `restore()`, `empty()`.
- [ ] Mypy strict and Ruff checks pass.

---

## Dependencies & Constraints

- Follows the resource-based API pattern established in issue #0018.
- `list()` must return `PagedResult[Document]` consistent with issue #0029.
- Logging must follow the pattern introduced in issue #0030.
- Sync resource mirrors the async resource as per issue #0016.
- `document_ids` parameter name is consistent with documents bulk-edit methods (`bulk_delete`, `bulk_add_tag`, etc.).

---

## Priority
`Medium`

---

## Additional Notes

The paperless-ngx API reference for this endpoint:
- `GET /api/trash/` — paginated list, query params: `page` (int), `page_size` (int).
- `POST /api/trash/` — body: `{ "documents": [<id>, ...], "action": "empty" | "restore" }`. No response body on success (HTTP 200 with empty or minimal response expected).

Naming rationale: non-document resource bulk methods use plain `ids` (e.g., `tags.bulk_delete(ids=...)`), but the trash resource operates specifically on documents, so `document_ids` is the consistent choice — matching the pattern in `DocumentsResource._bulk_edit(document_ids, ...)`.

---

## QA

**Tested by:** QA Engineer
**Date:** 2026-03-20
**Commit:** 5911a00

### Test Results

| # | Test Case | Expected | Actual | Status |
|---|-----------|----------|--------|--------|
| 1 | AC1: `client.trash.list()` sends `GET /api/trash/` and returns `PagedResult[Document]` | `PagedResult[Document]` with count=1 and result id=42 | Matches expected | ✅ Pass |
| 2 | AC2: `client.trash.list(page=2, page_size=10)` passes pagination as query params | Query params `page=2`, `page_size=10` sent | Params correctly forwarded | ✅ Pass |
| 3 | AC3: `client.trash.restore(document_ids=[1, 2])` sends correct POST body | Body `{"documents": [1, 2], "action": "restore"}`, returns None | Exact match, None returned | ✅ Pass |
| 4 | AC4: `client.trash.empty(document_ids=[3])` sends correct POST body | Body `{"documents": [3], "action": "empty"}`, returns None | Exact match, None returned | ✅ Pass |
| 5 | AC5: `empty()` docstring contains irreversible/non-undoable warning | Warning present in docstring | `.. warning:: **This operation is irreversible and cannot be undone.**` present in both async and sync | ✅ Pass |
| 6 | AC6: Both `TrashResource` (async) and `SyncTrashResource` (sync) are implemented | Both classes exist with `list`, `restore`, `empty` | Confirmed in `_internal/resources/trash.py` and `_internal/sync_resources/trash.py` | ✅ Pass |
| 7 | AC7: `client.trash` and `sync_client.trash` are public attributes | Accessible and typed correctly | Confirmed via `test_trash_resource_on_async_client` and `test_trash_resource_on_sync_client` | ✅ Pass |
| 8 | AC8: Unit tests cover list default, list with pagination, restore, empty | All 4 async + 3 sync variants covered | 10 tests pass in `test_client_trash.py` | ✅ Pass |
| 9 | AC9: Mypy strict and Ruff checks pass | No errors | Mypy: 0 issues; Ruff check: all passed; Ruff format: trash files already formatted | ✅ Pass |
| 10 | Edge: Default `list()` sends no query params | Empty params dict | `test_trash_list_no_params_sent_by_default` confirms `params == {}` | ✅ Pass |
| 11 | Edge: Logging calls consistent with other resources | `logger.info(...)` called in all three methods | All three methods (`list`, `restore`, `empty`) log at INFO level | ✅ Pass |
| 12 | Regression: Full test suite (622 tests) unaffected | All pass | 622 passed, 0 failed | ✅ Pass |
| 13 | `TrashResource` and `SyncTrashResource` exported from `resources.py` `__all__` | Both in `__all__` | Confirmed in `resources.py` lines 30, 41, 61–62 | ✅ Pass |

### Bugs Found

None.

### Automated Tests

- Suite: `tests/test_client_trash.py` — 10 passed, 0 failed
- Suite: Full test suite — 622 passed, 0 failed
- Note: `ruff format --check` reports 6 pre-existing files needing reformatting (all unrelated to this issue — `test_client_documents.py`, `test_issue_0020_new_params.py`, `test_issue_0030_logging.py`, `test_sentinel.py`, integration tests). Trash-specific files are already correctly formatted.

### Summary

- ACs tested: 9/9
- ACs passing: 9/9
- Bugs found: 0
- Recommendation: ✅ Ready to merge
