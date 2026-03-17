# [BUG] `documents.notes.list()` Does Not Return `PagedResult`

## Summary

Issue #0029 changed all `list()` methods to return `PagedResult[T]` for API consistency, but `NotesResource.list()` (async) and `SyncNotesResource.list()` (sync) were omitted. Both still return `List[DocumentNote]`, breaking the uniform return-type contract established by #0029.

The paperless-ngx notes endpoint (`GET /documents/{id}/notes/`) returns the standard paginated envelope (`count`, `next`, `previous`, `all`, `results`) — the same format as all other list endpoints. The implementation should handle it identically to other resources, including full auto-pagination support.

---

## Environment

- **Version / Release:** 0.3.0
- **Python Version:** 3.11+
- **Other relevant context:** Discovered by a consumer of the library working on an MCP project. Note: issue #0017 incorrectly documented this endpoint as non-paginated — that claim was wrong and should be disregarded.

---

## Steps to Reproduce

1. Install easypaperless 0.3.0.
2. Call `await client.documents.notes.list(document_id=1)` (or the sync equivalent).
3. Inspect the return value.

---

## Expected Behavior

`documents.notes.list()` returns a `PagedResult[DocumentNote]`, populated directly from the paginated API envelope — exactly as other `list()` methods do:

- Auto-pagination (default): all pages fetched, `results` contains all notes, `next`/`previous` are `None`, `count` reflects the server total.
- Single-page (`page=<int>`): `next`/`previous` contain raw URLs from the API response.
- `all` field included when the API provides it.

---

## Actual Behavior

`documents.notes.list()` returns `List[DocumentNote]`. The paginated envelope (`count`, `next`, `previous`, `all`) is discarded, and the `PagedResult` wrapper is absent.

---

## Impact

- **Severity:** `Low`
- **Affected Users / Systems:** Any caller that expects a uniform `PagedResult` return type from all `list()` methods — e.g., code that accesses `.count`, `.next`, `.results`, etc. Callers relying on `list[DocumentNote]` are unaffected until they update their code.

---

## Acceptance Criteria

- [ ] `NotesResource.list()` (async) returns `PagedResult[DocumentNote]`, populated from the real paginated API envelope.
- [ ] `SyncNotesResource.list()` (sync) returns `PagedResult[DocumentNote]`.
- [ ] Auto-pagination behaviour matches other resources: all pages fetched by default, `next`/`previous` set to `None`, `count` from the first page's envelope.
- [ ] Single-page mode (`page=<int>`) returns `next`/`previous` verbatim from the API.
- [ ] `all` field is included when present in the API response, `None` otherwise.
- [ ] Return-type annotations and docstrings are updated to reflect `PagedResult[DocumentNote]`.
- [ ] Existing tests for `notes.list()` are updated to unpack `.results` and check `.count`.
- [ ] New/updated tests cover: auto-pagination shape, single-page shape, `all` field present vs absent.
- [ ] Mypy (strict) passes with no new errors.
- [ ] Ruff lint and format checks pass.
- [ ] Fix is released as part of version 0.3.1 (patch release).

---

## Additional Notes

- The incorrect claim in issue #0017 ("paperless-ngx does not paginate notes") led to the omission in #0029. The actual API response is the standard paginated envelope.
- Related: #0029 (PagedResult for all list methods), #0017 (Document Notes).

---

## QA

**Tested by:** QA Engineer
**Date:** 2026-03-17
**Commit:** 71c0c25 (working tree — unstaged changes tested)

### Test Results

| # | Test Case | Expected | Actual | Status |
|---|-----------|----------|--------|--------|
| 1 | AC1: `NotesResource.list()` returns `PagedResult[DocumentNote]` | `PagedResult[DocumentNote]` returned, populated from paginated envelope | Return type changed, `cast(PagedResult[DocumentNote], ...)` used, `test_get_notes` verifies `isinstance(result, PagedResult)` | ✅ Pass |
| 2 | AC2: `SyncNotesResource.list()` returns `PagedResult[DocumentNote]` | Sync wrapper returns `PagedResult[DocumentNote]` | Return type annotation and cast updated, `test_sync_get_notes` verifies `result.count` and `result.results` | ✅ Pass |
| 3 | AC3: Auto-pagination — all pages fetched, `next`/`previous` are `None` | Multi-page responses merged, `next`/`previous` set to `None` | `test_get_notes_auto_pagination` confirms 2-page merge, `result.next is None`, `result.previous is None` | ✅ Pass |
| 4 | AC4: Single-page mode (`page=<int>`) preserves raw `next`/`previous` | `next` URL returned verbatim from API | `test_get_notes_single_page` confirms `result.next == "http://localhost/api/documents/42/notes/?page=2"` | ✅ Pass |
| 5 | AC5: `all` field included when present, `None` otherwise | `result.all == [1]` when present; `result.all is None` when absent | `test_get_notes_all_field` and `test_get_notes_all_field_absent` both pass | ✅ Pass |
| 6 | AC6: Return-type annotations and docstrings updated | `-> PagedResult[DocumentNote]` in both async and sync; docstring updated | Both `NotesResource.list()` and `SyncNotesResource.list()` have correct type annotations and updated docstrings with `page`/`page_size` Args sections | ✅ Pass |
| 7 | AC7: Existing tests updated to unpack `.results` and check `.count` | `test_get_notes` and `test_get_notes_empty` use `.results` and `.count` | Both tests updated; `test_get_notes` asserts `result.count == 1`; `test_get_notes_empty` asserts `result.count == 0` | ✅ Pass |
| 8 | AC8: Tests cover auto-pagination, single-page, `all` field present/absent | All three shapes tested | Async: 4 tests cover all shapes. Sync: only basic case tested — no sync test for single-page mode or `all` field. | ⚠️ Partial |
| 9 | AC9: Mypy (strict) passes with no new errors | `Success: no issues found in 33 source files` | `mypy src/easypaperless/` reports no errors | ✅ Pass |
| 10 | AC10: Ruff lint and format checks pass | All checks pass for changed files | `ruff check` passes for all changed files. `ruff format --check` fails for 7 files **not modified by this issue** (pre-existing) | ✅ Pass |
| 11 | AC11: Fix released as part of v0.3.1 | Version bumped and released | Issue still in "Implemented" state — not yet deployed | ⏳ Not yet |
| 12 | Edge: Empty notes list | `PagedResult` with `count=0`, `results=[]` | `test_get_notes_empty` confirms this | ✅ Pass |
| 13 | Edge: NotFoundError propagation from `list()` | `NotFoundError` raised on 404 | `test_get_notes_not_found` confirms | ✅ Pass |
| 14 | Edge: Nested user object in response | `user` field normalised to int | `test_get_notes_nested_user` confirms `result.results[0].user == 1` | ✅ Pass |

### Bugs Found

#### BUG-001 — Sync `notes.list()` missing tests for single-page mode and `all` field [Severity: Low]

**Steps to reproduce:**
1. Open `tests/test_sync.py` and inspect the notes section.
2. Note that only `test_sync_get_notes` covers `notes.list()`, with a single-page response.

**Expected:** AC8 states tests cover "auto-pagination shape, single-page shape, `all` field present vs absent". The sync resource accepts `page` and `page_size` parameters but has no test for `page=1` (single-page mode) or for the `all` field.
**Actual:** Only the basic auto-pagination (single-page server response) case is tested for sync. The `page` parameter path and `all` field are untested in sync.
**Severity:** Low
**Notes:** The async tests cover all shapes exhaustively and the sync wrapper is a thin `self._run(...)` delegate. No functional gap exists in practice, but AC8 coverage is incomplete for sync.
**Fix:** Added `test_sync_get_notes_single_page`, `test_sync_get_notes_auto_pagination`, `test_sync_get_notes_all_field`, and `test_sync_get_notes_all_field_absent` to `tests/test_sync.py`. All 4 tests pass.

### Automated Tests

- Suite: `tests/test_client_notes.py` — 13 passed, 0 failed
- Suite: `tests/test_sync.py` (notes section) — 5 passed, 0 failed (4 added post-QA to fix BUG-001)
- Full suite: `pytest tests/` — 577 passed, 46 deselected, 0 failed

### Summary

- ACs tested: 10/11 (AC11 requires a release — not yet applicable)
- ACs passing: 10/10 tested (AC8 fully met after BUG-001 fix)
- Bugs found: 1 (Critical: 0, High: 0, Medium: 0, Low: 1) — ✅ fixed
- Recommendation: ✅ Ready to merge
