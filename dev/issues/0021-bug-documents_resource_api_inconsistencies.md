# [BUG] Documents Resource API Inconsistencies

## Summary

Four API inconsistencies exist in `DocumentsResource` that make the interface confusing or incorrect: a wrong parameter name in `update()`, an inconsistent abbreviation for archive serial number across methods, a wrong default value in `search_mode`, and a missing type in `upload()`.

---

## Bugs

### 1. `update()`: parameter `date` should be named `created`

`DocumentsResource.update()` exposes the creation date field as `date`, but the paperless-ngx API field is `created`, and `upload()` already uses `created` for the same concept. This inconsistency forces users to learn two names for the same field.

**Actual:** `documents.update(id, date="2024-01-01")`
**Expected:** `documents.update(id, created="2024-01-01")`

---

### 2. `update()` and `upload()`: `asn` should be named `archive_serial_number`

`DocumentsResource.update()` and `upload()` expose the archive serial number field as `asn`. However, `DocumentsResource.list()` already uses the full name `archive_serial_number` for the same concept. The abbreviation is inconsistent with the rest of the API surface.

**Actual:** `documents.update(id, asn=42)` / `documents.upload(..., asn=42)`
**Expected:** `documents.update(id, archive_serial_number=42)` / `documents.upload(..., archive_serial_number=42)`

---

### 3. `list()`: `search_mode` default and map key `"title_or_text"` should be `"title_or_content"`

`DocumentsResource.list()` uses `"title_or_text"` as the name for the combined title/content search mode. The paperless-ngx field is called `content`, not `text`. The internal `_SEARCH_MODE_MAP` key and the default value of `search_mode` must both be updated to `"title_or_content"` for consistency with the field name.

**Actual:** `search_mode="title_or_text"` (default), map key `"title_or_text"`
**Expected:** `search_mode="title_or_content"` (default), map key `"title_or_content"`

---

### 4. `upload()`: `created` parameter accepts only `str`, should also accept `date`

`DocumentsResource.upload()` declares `created: str | None = None`. Other date parameters throughout the resource accept `date | str`. The `created` parameter in `upload()` should accept a Python `date` object in addition to an ISO-8601 string, consistent with the rest of the API.

**Actual:** `created: str | None = None`
**Expected:** `created: date | str | None = None`

---

## Impact

- **Severity:** `Medium`
- **Affected:** All callers of `DocumentsResource.update()`, `upload()`, and `list()`.

---

## Acceptance Criteria

- [ ] `DocumentsResource.update()` parameter `date` is renamed to `created`. The payload key sent to the API remains `"created"`.
- [ ] `DocumentsResource.update()` parameter `asn` is renamed to `archive_serial_number`. The payload key sent to the API remains `"archive_serial_number"`.
- [ ] `DocumentsResource.upload()` parameter `asn` is renamed to `archive_serial_number`. The multipart field sent to the API remains `"archive_serial_number"`.
- [ ] `_SEARCH_MODE_MAP` key `"title_or_text"` is renamed to `"title_or_content"`. The mapped API value (`"search"`) remains unchanged.
- [ ] `DocumentsResource.list()` default for `search_mode` is updated from `"title_or_text"` to `"title_or_content"`.
- [ ] `DocumentsResource.upload()` `created` parameter type is widened to `date | str | None`. A `date` value is formatted to an ISO-8601 string before being sent to the API.
- [ ] All sync counterparts (`SyncDocumentsResource`) are updated in lockstep.
- [ ] Docstrings are updated to reflect the new parameter names and types.
- [ ] Ruff linting and Mypy type checking pass without errors.
- [ ] Existing tests are updated to use the new parameter names; all tests pass.

---

## Additional Notes

- These are breaking renames — callers using keyword arguments will need to update. Because the package has not yet reached a stable 1.x release, this is acceptable without a major version bump, but the changes must be documented in the CHANGELOG.
- No changes to model fields or API query keys are required; only Python parameter names and types change.

---

## QA

**Tested by:** QA Engineer
**Date:** 2026-03-14
**Commit:** 45fe47f

### Test Results

| # | Test Case | Expected | Actual | Status |
|---|-----------|----------|--------|--------|
| 1 | AC: `DocumentsResource.update()` parameter `date` renamed to `created` | `created: date | str | None | _Unset = UNSET` in update() | Confirmed: `resources/documents.py` update() line 447 uses `created` | ✅ Pass |
| 2 | AC: Payload key for created date remains `"created"` in update() | `payload["created"] = ...` | Code: `payload["created"] = self._format_date_value(created) if created is not None else None` | ✅ Pass |
| 3 | AC: `DocumentsResource.update()` parameter `asn` renamed to `archive_serial_number` | `archive_serial_number` in update() | Confirmed: `resources/documents.py` update() line 452 uses `archive_serial_number` | ✅ Pass |
| 4 | AC: Payload key for ASN remains `"archive_serial_number"` in update() | `payload["archive_serial_number"] = ...` | Code: `payload["archive_serial_number"] = archive_serial_number` | ✅ Pass |
| 5 | AC: `DocumentsResource.upload()` parameter `asn` renamed to `archive_serial_number` | `archive_serial_number` in upload() | Confirmed: `resources/documents.py` upload() line 573 uses `archive_serial_number` | ✅ Pass |
| 6 | AC: Multipart field for ASN remains `"archive_serial_number"` in upload() | `data["archive_serial_number"] = ...` | Code: `data["archive_serial_number"] = archive_serial_number` | ✅ Pass |
| 7 | AC: `_SEARCH_MODE_MAP` key renamed from `"title_or_text"` to `"title_or_content"` | `"title_or_content": "search"` in map | Confirmed: `_SEARCH_MODE_MAP` in `resources/documents.py` line 35 | ✅ Pass |
| 8 | AC: `DocumentsResource.list()` default for `search_mode` updated to `"title_or_content"` | `search_mode: str = "title_or_content"` | Confirmed: line 176 | ✅ Pass |
| 9 | AC: `DocumentsResource.upload()` `created` type widened to `date | str | None` | Type annotation `date | str | None = None` | Confirmed: `upload()` line 568 `created: date | str | None = None` | ✅ Pass |
| 10 | AC: `date` object formatted to ISO-8601 before sending | `_format_date_value(created)` called | Code: `data["created"] = self._format_date_value(created)` | ✅ Pass |
| 11 | AC: Sync counterparts (`SyncDocumentsResource`) updated in lockstep | Same parameter names and types in sync | Confirmed: `sync_resources/documents.py` uses `created`, `archive_serial_number`, `search_mode="title_or_content"` | ✅ Pass |
| 12 | AC: Docstrings updated | New names documented | Confirmed: docstrings use `created`, `archive_serial_number`, `title_or_content` | ✅ Pass |
| 13 | AC: Ruff linting passes | No ruff errors | Ruff passes on src/ | ✅ Pass |
| 14 | AC: Mypy type checking passes | No mypy errors | Mypy passes on src/ | ✅ Pass |
| 15 | AC: Existing tests updated and pass | Tests use new param names | 498 passed — except 1 failure (see BUG-001) | ❌ Fail |

### Bugs Found

#### BUG-001 — `test_sentinel.py` test still uses old `asn` parameter name [Severity: High]

**File:** `tests/test_sentinel.py`, line 437
**Test:** `test_update_document_none_clears_multiple_nullable_fields`

**Description:** The test calls `await client.documents.update(1, ..., asn=None, ...)`. The parameter was renamed from `asn` to `archive_serial_number` as part of this issue. This test was not updated, causing it to fail with:

```
TypeError: DocumentsResource.update() got an unexpected keyword argument 'asn'
```

This is a direct regression from the rename: the test was supposed to be updated but was missed.

**Impact:** The test suite has 1 failing test that is directly attributable to this issue's changes. The AC "Existing tests are updated to use the new parameter names; all tests pass" is not met.

### Automated Tests

- Suite: `tests/test_sentinel.py` — 1 test fails: `test_update_document_none_clears_multiple_nullable_fields`
- Suite: `tests/` (full) — 498 passed, 1 failed

### Summary

- ACs tested: 9/9 (plus code and docstring reviews)
- ACs passing: 8/9 (AC "Existing tests are updated to use the new parameter names; all tests pass" fails)
- Bugs found: 1 (Critical: 0, High: 1, Medium: 0, Low: 0)
- Recommendation: ❌ Needs fix before merge — test `test_update_document_none_clears_multiple_nullable_fields` must be updated to use `archive_serial_number=None` instead of `asn=None`

---

## QA Re-check

**Tested by:** QA Engineer
**Date:** 2026-03-14
**Commit:** 81b13e1

### BUG-001 Re-verification

| # | Check | Expected | Actual | Status |
|---|-------|----------|--------|--------|
| 1 | `test_update_document_none_clears_multiple_nullable_fields` uses `archive_serial_number=None` | `archive_serial_number=None` at line 437 | Confirmed: `tests/test_sentinel.py` line 437 | ✅ Fixed |
| 2 | Full test suite | 499 passed, 0 failed | 499 passed, 0 failed | ✅ Pass |

### Summary

- BUG-001 resolved: stale `asn=None` argument updated to `archive_serial_number=None`
- All ACs: 9/9 passing
- Recommendation: ✅ Ready to merge
