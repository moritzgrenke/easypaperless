# [BUG] `SyncTagsResource.create()` Uses `None` Instead of `UNSET` for `color` and `is_inbox_tag`

## Summary

`SyncTagsResource.create()` declares `color` and `is_inbox_tag` with a default of `None`, while the async counterpart `TagsResource.create()` correctly defaults both to `UNSET`. This means calling `sync_client.tags.create(name="foo")` without providing those arguments will pass explicit `null` values to the API, instead of omitting the fields entirely — silently overwriting API-side defaults.

---

## Environment
- **Version / Release:** 0.2.1
- **Other relevant context:** Affects `SyncPaperlessClient` only; `PaperlessClient` (async) is correct.

---

## Steps to Reproduce
1. Instantiate `SyncPaperlessClient`.
2. Call `client.tags.create(name="my-tag")` without specifying `color` or `is_inbox_tag`.
3. Observe that the API request includes `"color": null` and `"is_inbox_tag": null` in the payload.

## Expected Behavior

The fields `color` and `is_inbox_tag` are omitted from the request payload when not explicitly provided, matching the behavior of the async `PaperlessClient.tags.create()`.

---

## Actual Behavior

`color` and `is_inbox_tag` are sent as `null` in the request body because the sync wrapper defaults them to `None` instead of `UNSET`. The async method receives `None` (an explicit value) rather than `UNSET` (sentinel for "omit"), so the fields are included in the API payload.

---

## Root Cause

In `src/easypaperless/_internal/sync_resources/tags.py`, `SyncTagsResource.create()` declares:

```python
color: str | None = None,
is_inbox_tag: bool | None = None,
```

The correct signatures (matching the async resource) are:

```python
color: str | None | _Unset = UNSET,
is_inbox_tag: bool | None | _Unset = UNSET,
```

---

## Impact
- **Severity:** Medium
- **Affected Users / Systems:** All users of `SyncPaperlessClient.tags.create()` who rely on API-side defaults for `color` or `is_inbox_tag`.

---

## Acceptance Criteria
- [ ] `SyncTagsResource.create()` parameter `color` defaults to `UNSET` with type `str | None | _Unset`.
- [ ] `SyncTagsResource.create()` parameter `is_inbox_tag` defaults to `UNSET` with type `bool | None | _Unset`.
- [ ] A regression test verifies that omitting `color` and `is_inbox_tag` in `SyncTagsResource.create()` does not include those fields in the API payload.
- [ ] No other sync resource methods are affected (confirmed by audit: only `tags.create` has this issue).

---

## Additional Notes

A full audit of all sync resource files (documents, correspondents, document_types, storage_paths, custom_fields) confirmed that `tags.create` is the **only** location with this mismatch.

---

## QA

**Tested by:** QA Engineer
**Date:** 2026-03-15
**Commit:** uncommitted (working tree changes on top of 9d7febd)

### Test Results

| # | Test Case | Expected | Actual | Status |
|---|-----------|----------|--------|--------|
| 1 | AC1: `color` type is `str \| None \| _Unset` with default `UNSET` | Signature matches async counterpart | `color: str \| None \| _Unset = UNSET` confirmed in source | ✅ Pass |
| 2 | AC2: `is_inbox_tag` type is `bool \| None \| _Unset` with default `UNSET` | Signature matches async counterpart | `is_inbox_tag: bool \| None \| _Unset = UNSET` confirmed in source | ✅ Pass |
| 3 | AC3: Regression test — omitting both fields excludes them from API payload | `color` and `is_inbox_tag` absent from POST body | Test `test_sync_create_tag_omits_color_and_is_inbox_tag_when_not_provided` passes | ✅ Pass |
| 4 | AC4: No other sync resource methods are affected | All other sync resources have correct defaults | Full audit confirmed; only `tags.create` was changed | ✅ Pass |
| 5 | Type check: mypy strict on changed file | No type errors | `Success: no issues found in 1 source file` | ✅ Pass |
| 6 | Lint: ruff on changed files | No lint violations | `All checks passed!` | ✅ Pass |
| 7 | Full test suite regression | All existing tests pass | 500 passed, 0 failed | ✅ Pass |

### Bugs Found

None.

### Automated Tests

- Suite: `pytest tests/` — **500 passed, 0 failed** (46 deselected due to markers)
- New regression test: `test_sync_create_tag_omits_color_and_is_inbox_tag_when_not_provided` — ✅ Pass

### Summary

- ACs tested: 4/4
- ACs passing: 4/4
- Bugs found: 0
- Recommendation: ✅ Ready to merge
