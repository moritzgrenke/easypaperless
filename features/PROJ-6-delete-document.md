# PROJ-6: Delete Document

## Status: Implemented
**Created:** 2026-03-06
**Last Updated:** 2026-03-06

## Dependencies
- Requires: PROJ-1 (HTTP Client Core) — for authenticated HTTP requests and error mapping

## User Stories
- As a developer, I want to permanently delete a document by its ID so that I can remove unwanted or duplicate documents from paperless-ngx.
- As a developer, I want a clear `NotFoundError` when the document ID does not exist so that I can distinguish a successful delete from a missing document.
- As a developer, I want the delete to return nothing on success so that I don't have to handle an unused return value.

## Acceptance Criteria
- [ ] `PaperlessClient.delete_document(id: int) -> None` sends `DELETE /documents/{id}/` and returns `None` on success (HTTP 204).
- [ ] Raises `NotFoundError` when the server returns HTTP 404.
- [ ] The method is available on `SyncPaperlessClient` with the same signature (blocking wrapper).

## Edge Cases
- Document ID does not exist → raises `NotFoundError`.
- Deleting a document is permanent and irreversible — there is no soft-delete or trash mechanism in paperless-ngx; the spec intentionally does not add one.
- Calling `delete_document` on an ID that was already deleted raises `NotFoundError` (idempotency is not guaranteed).

---
<!-- Sections below are added by subsequent skills -->

## Tech Design (Solution Architect)
_To be added by /architecture_

## QA Test Results
**Date:** 2026-03-07
**Tester:** QA Engineer (AI)
**Branch:** master

### Acceptance Criteria

| # | Criterion | Result |
|---|-----------|--------|
| 1 | `PaperlessClient.delete_document(id: int) -> None` sends `DELETE /documents/{id}/` and returns `None` on success (HTTP 204) | PASS |
| 2 | Raises `NotFoundError` when the server returns HTTP 404 | PASS (via HTTP layer; see test gap below) |
| 3 | The method is available on `SyncPaperlessClient` with the same signature (blocking wrapper) | PASS |

### Edge Cases

| Edge Case | Result |
|-----------|--------|
| Document ID does not exist → raises `NotFoundError` | PASS — HTTP layer maps 404 to `NotFoundError` automatically |
| Already-deleted ID raises `NotFoundError` (no idempotency) | PASS — same 404 mapping applies |

### Test Coverage

| Area | Detail |
|------|--------|
| Async happy path (`test_delete_document`) | Covered — mocks DELETE returning 204 |
| Sync happy path (`test_sync_delete_document`) | Covered — sync wrapper delegates correctly |
| Async 404 / `NotFoundError` | **GAP** — no dedicated `test_delete_document_not_found` test (other methods like `get_document`, `update_document`, `download_document` all have explicit 404 tests) |

### Code Quality

| Check | Result |
|-------|--------|
| `mypy src/easypaperless/` (strict) | PASS — 0 errors |
| `ruff check` (library source) | PASS — no issues in `src/` |
| Full test suite (340 tests) | PASS — 0 failures |
| Coverage of `documents.py` async mixin | 94% |
| Coverage of `sync_mixins/documents.py` | 100% |

### Regression

No regressions detected. All 340 existing tests pass. Features PROJ-1 through PROJ-5 (QA Passed) remain stable.

### Bugs Found

| # | Severity | Description |
|---|----------|-------------|
| 1 | **Low** | Missing explicit `test_delete_document_not_found` test. The 404 → `NotFoundError` mapping works (verified via HTTP layer tests and consistent with all other methods), but every other document method (`get_document`, `update_document`, `download_document`) has its own dedicated 404 test. Adding one for `delete_document` would be consistent and guard against future regressions if the delete path ever diverges. |

### Production-Ready Decision

**READY** — No Critical or High bugs. The single Low-severity finding is a minor test coverage gap that does not affect correctness (the underlying 404 mapping is thoroughly tested in the HTTP layer). Recommend adding the missing test before or during deployment for consistency.

## Deployment
_To be added by /deploy_
