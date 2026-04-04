# [BUG] Wrong Query Parameter Keys for Single-Value Filters in `documents.list()`

## Summary

`documents.list()` builds incorrect query parameter keys for several single-value FK filters, causing them to be silently ignored by the Paperless-ngx API. The confirmed case is `document_type=<id>`, which sends the key `document_type` instead of `document_type__id` — the API does not recognise this and returns all documents unfiltered. Three additional filters use `__id__in` for a single resolved ID, which is semantically wrong (an "in"-list operator applied to a scalar) and inconsistent with the intended single-value lookup params.

No similar bugs were found in any other resource (`tags`, `correspondents`, `document_types`, `storage_paths`, `custom_fields`, `users`, `trash`), as those resources do not perform FK-based filtering. The sync `SyncDocumentsResource.list()` delegates directly to the async implementation, so it is affected by exactly the same bugs.

---

## Environment
- **Version / Release:** current main
- **Python Version:** 3.11+
- **Paperless-ngx Version:** any
- **Platform / OS:** any

---

## Steps to Reproduce

1. Instantiate a `PaperlessClient` connected to a Paperless-ngx instance with documents of multiple types.
2. Call `await client.documents.list(document_type=<valid_id>)`.
3. Observe that all documents are returned, not just those of the given type.

---

## Expected Behavior

Each single-value filter sends the correct query parameter key to the API and returns only documents that match the filter value.

---

## Actual Behavior

The following wrong query parameter keys are used in `src/easypaperless/_internal/resources/documents.py`:

| Parameter | Current (wrong) key | Correct key | Line | Effect |
|---|---|---|---|---|
| `document_type` | `document_type` | `document_type__id` | 424 | **Confirmed broken** — API ignores the param entirely, all documents returned |
| `correspondent` | `correspondent__id__in` (with a single scalar) | `correspondent__id` | 405 | Semantically wrong; may work by accident in some Django DRF versions |
| `storage_path` | `storage_path__id__in` (with a single scalar) | `storage_path__id` | 438 | Same as above |
| `owner` | `owner__id__in` (with a single scalar) | `owner__id` | 448 | Same as above |

---

## Impact
- **Severity:** High
- **Affected Users / Systems:** Any user filtering `documents.list()` by `document_type`, `correspondent`, `storage_path`, or `owner` with a single value. Filters silently produce wrong results with no error raised.

---

## Acceptance Criteria
- [ ] `documents.list(document_type=<id>)` sends `document_type__id=<id>` to the API and returns only matching documents.
- [ ] `documents.list(correspondent=<id>)` sends `correspondent__id=<id>` and returns only matching documents.
- [ ] `documents.list(storage_path=<id>)` sends `storage_path__id=<id>` and returns only matching documents.
- [ ] `documents.list(owner=<id>)` sends `owner__id=<id>` and returns only matching documents.
- [ ] `documents.list(document_type=None)` still sends `document_type__isnull=true` (null-filter path is unchanged).
- [ ] `documents.list(correspondent=None)` still sends `correspondent__isnull=true`.
- [ ] `documents.list(storage_path=None)` still sends `storage_path__isnull=true`.
- [ ] `documents.list(owner=None)` still sends `owner__isnull=true`.
- [ ] Multi-value variants (`any_document_type`, `any_correspondent`, `any_storage_paths`, `exclude_*`) are unaffected.
- [ ] Name-based document type filters (`document_type_name_contains`, `document_type_name_exact`) are unaffected.
- [ ] Unit tests assert the exact query parameter key sent for each corrected filter.
- [ ] No regression in any other `documents.list()` filter.

---

## Additional Notes

The sync resource (`src/easypaperless/_internal/sync_resources/documents.py`) is a thin wrapper that calls the async implementation, so fixing the async resource fixes both clients simultaneously — no separate change is needed in the sync resource.

Related original feature spec: [0003-list-documents.md](0003-list-documents.md)

---

## QA

**Tested by:** QA Engineer  
**Date:** 2026-04-04  
**Commit:** e04123f (fixes applied as unstaged working-tree changes)

### Test Results

| # | Test Case | Expected | Actual | Status |
|---|-----------|----------|--------|--------|
| 1 | AC1: `document_type=<id>` sends `document_type__id=<id>` | `params["document_type__id"] == "<id>"` | Correct key sent | ✅ Pass |
| 2 | AC2: `correspondent=<id>` sends `correspondent__id=<id>` | `params["correspondent__id"] == "<id>"` | Correct key sent | ✅ Pass |
| 3 | AC3: `storage_path=<id>` sends `storage_path__id=<id>` | `params["storage_path__id"] == "<id>"` | Correct key sent | ✅ Pass |
| 4 | AC4: `owner=<id>` sends `owner__id=<id>` | `params["owner__id"] == "<id>"` | Correct key sent | ✅ Pass |
| 5 | AC5: `document_type=None` sends `document_type__isnull=true` | null-filter key unchanged | Correct | ✅ Pass |
| 6 | AC6: `correspondent=None` sends `correspondent__isnull=true` | null-filter key unchanged | Correct | ✅ Pass |
| 7 | AC7: `storage_path=None` sends `storage_path__isnull=true` | null-filter key unchanged | Correct | ✅ Pass |
| 8 | AC8: `owner=None` sends `owner__isnull=true` | null-filter key unchanged | Correct | ✅ Pass |
| 9 | AC9: `any_document_type`, `any_correspondent`, `any_storage_paths`, `exclude_*` unaffected | Multi-value params unchanged | `__id__in` / `__none` keys intact | ✅ Pass |
| 10 | AC10: `document_type_name_contains`, `document_type_name_exact` unaffected | Name-based params unchanged | Correct keys in place | ✅ Pass |
| 11 | AC11: Unit tests assert exact param key for each corrected filter | Tests cover all 4 filters by ID and by name | 8 new/updated tests added | ✅ Pass |
| 12 | AC12: No regression in other `documents.list()` filters | Full suite passes | 642 tests passed, 0 failed | ✅ Pass |
| 13 | Edge: `document_type` by name resolves correctly to `document_type__id` | ID resolved then sent as `document_type__id` | Correct | ✅ Pass |
| 14 | Edge: `correspondent` by name resolves correctly to `correspondent__id` | ID resolved then sent as `correspondent__id` | Correct | ✅ Pass |
| 15 | Edge: `any_document_type` overrides single `document_type` param | Only `document_type__id__in` present | Neither `document_type__id` nor old `document_type` key present | ✅ Pass |
| 16 | Regression: Sync client inherits fix without changes | `SyncDocumentsResource` delegates to async | Verified by test_sync_* suite (642 passed) | ✅ Pass |

### Bugs Found

None.

### Automated Tests

- Suite: `tests/test_client_documents.py` + `tests/test_sentinel.py` — 165 passed, 0 failed
- Suite: Full project (`pytest tests/`) — 642 passed, 0 failed
- Lint: `ruff check .` — All checks passed
- Type check: `mypy src/easypaperless/` — Success: no issues found in 38 source files

### Summary

- ACs tested: 12/12
- ACs passing: 12/12
- Bugs found: 0
- Recommendation: ✅ Ready to merge
