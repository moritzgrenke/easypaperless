# [REFACTORING] Hide Low-Level Bulk Edit Methods from Public API

## Summary

`client.bulk_edit_objects()` and `client.documents.bulk_edit()` are currently exposed as public methods. They are internal implementation details that power the high-level bulk operation resource methods. They should be made private so users are guided to use the higher-level API only.

---

## Current State

- `client.bulk_edit_objects()` is a public method on `PaperlessClient` (and `SyncPaperlessClient`).
- `client.documents.bulk_edit()` is a public method on the documents resource.
- Both are used internally by the high-level bulk operation methods (e.g. `client.documents.bulk_delete()`, `client.tags.bulk_delete()`, etc.).
- Exposing these low-level methods invites misuse, increases the maintenance surface, and adds API noise for users who should only interact with the high-level methods.

---

## Desired State

- `bulk_edit_objects` and `documents.bulk_edit` are private (prefixed with `_`) and no longer part of the documented public API.
- The high-level bulk operation resource methods continue to work exactly as before, using the now-private helpers internally.
- No sync wrappers exist for these methods (they were only needed because the methods were public; the private internal helpers do not require sync equivalents).
- Users cannot accidentally discover or call these methods through normal IDE autocompletion or documentation.

---

## Motivation

- [x] Reduce complexity
- [x] Improve readability
- [x] Align with current standards / conventions

---

## Scope

### In Scope

- Rename `bulk_edit_objects` to `_bulk_edit_objects` on the async client.
- Rename `documents.bulk_edit` to `documents._bulk_edit` on the documents resource (async mixin).
- Update all internal call sites to use the renamed private methods.
- Remove any public sync wrappers for these two methods from `SyncPaperlessClient` and the sync documents mixin.
- Remove these methods from `__init__.py` exports if currently listed there.

### Out of Scope

- Changes to the behavior or signatures of the high-level bulk operation methods.
- Refactoring of any other methods beyond the two identified.
- Changes to tests that exercise only the high-level methods (they should pass without modification).

---

## Risks & Considerations

- Any user code directly calling `client.bulk_edit_objects()` or `client.documents.bulk_edit()` will break. These are considered low-level internals not intended for direct use, so this is an acceptable breaking change.
- Unit and integration tests that directly call these methods must be updated to call the private equivalents or be removed if they only tested the internal mechanics.

---

## Acceptance Criteria

- [ ] `client.bulk_edit_objects` is no longer accessible as a public attribute (renamed to `_bulk_edit_objects`).
- [ ] `client.documents.bulk_edit` is no longer accessible as a public attribute (renamed to `_bulk_edit`).
- [ ] All high-level bulk operation methods (e.g. `bulk_delete`, `bulk_add_tag`, etc.) continue to function correctly via the renamed private helpers.
- [ ] No public sync wrappers exist for `_bulk_edit_objects` or `_bulk_edit`.
- [ ] The methods do not appear in public documentation or `__init__.py` exports.
- [ ] All existing tests for high-level bulk operations pass without modification.

---

## Priority

`Medium`

---

## Additional Notes

Related to issue #0018 (Resource-Based Client API refactoring) which introduced the high-level bulk operation resource methods that make these low-level methods redundant as public API surface.

## QA

**Tested by:** QA Engineer
**Date:** 2026-03-14
**Commit:** d474c3d

### Test Results

| # | Test Case | Expected | Actual | Status |
|---|-----------|----------|--------|--------|
| 1 | AC1: `client.bulk_edit_objects` removed as public method | Not accessible on `PaperlessClient` | Public wrapper removed from `client.py`; only `_bulk_edit_objects` on `_ClientCore` remains | ✅ Pass |
| 2 | AC2: `client.documents.bulk_edit` removed as public method | Not accessible on `DocumentsResource` | Renamed to `_bulk_edit` in `resources/documents.py` | ✅ Pass |
| 3 | AC3: All high-level bulk methods work via renamed private helpers | All internal call sites use `_bulk_edit` / `_bulk_edit_objects` | All 9 call sites in `documents.py` updated; resource files (tags, correspondents, etc.) already used `_bulk_edit_objects` | ✅ Pass |
| 4 | AC4: No public sync wrappers for `_bulk_edit_objects` or `_bulk_edit` | Both removed from `sync.py` and `sync_resources/documents.py` | `SyncPaperlessClient.bulk_edit_objects` and `SyncDocumentsResource.bulk_edit` both removed | ✅ Pass |
| 5 | AC5: Methods absent from `__init__.py` exports | Neither name exported | `grep` found no references to `bulk_edit` in `__init__.py` | ✅ Pass |
| 6 | AC6: All existing high-level bulk operation tests pass without modification | Tests for `bulk_delete`, `bulk_add_tag`, etc. unchanged and green | 498 tests pass; high-level bulk tests untouched | ✅ Pass |
| 7 | Edge: Tests that directly tested low-level methods updated appropriately | `test_bulk_edit_raw` and `test_bulk_edit_objects` updated to private names; `test_sync_bulk_edit_objects` removed | Confirmed in diff — consistent with Risks & Considerations | ✅ Pass |
| 8 | Edge: Non-document resource bulk ops (`tags`, `correspondents`, `document_types`, `storage_paths`) unaffected | Internal `_bulk_edit_objects` calls in resource files unchanged | Already used private `_bulk_edit_objects` — no changes needed | ✅ Pass |

### Bugs Found

None.

### Automated Tests

- Suite: `pytest tests/` — 498 passed, 0 failed (46 deselected — integration tests requiring live instance)

### Summary

- ACs tested: 6/6
- ACs passing: 6/6
- Bugs found: 0
- Recommendation: ✅ Ready to merge
