# [FEATURE] Document Bulk Download

## Summary
Add a `bulk_download()` method to the documents resource that calls `POST /api/documents/bulk_download/` and returns the raw ZIP archive bytes. This lets users download multiple documents in one request, controlling which file variant (archived PDF, original, or both) is included and which compression algorithm is used.

---

## Problem Statement
The paperless-ngx API exposes a dedicated bulk-download endpoint that produces a ZIP archive containing multiple documents in a single request. easypaperless has no wrapper for this endpoint, forcing users to download documents one by one or call the raw HTTP layer themselves.

---

## Proposed Solution
Expose a `bulk_download()` method on the `documents` resource (both async and sync clients). The method accepts a list of document IDs plus the three optional parameters defined by the API schema (`content`, `compression`, `follow_formatting`) and returns the raw binary content of the resulting ZIP archive.

---

## User Stories

- As a developer, I want to download multiple documents as a single ZIP archive so that I can save them locally or pass them to a downstream process without looping over individual download calls.
- As a developer, I want to choose whether the ZIP contains archived PDFs, original files, or both so that I can get exactly the file variants I need.
- As a developer, I want to select the compression algorithm for the ZIP so that I can trade off file size against CPU time on the server.
- As a developer, I want to control whether document filename formatting is applied so that files in the ZIP reflect the configured naming scheme.

---

## Scope

### In Scope
- `documents.bulk_download(document_ids, *, content, compression, follow_formatting) -> bytes` on the async client
- Equivalent sync method on `SyncPaperlessClient`
- `content` parameter: literal `"archive"` | `"originals"` | `"both"`, default `"archive"`
- `compression` parameter: literal `"none"` | `"deflated"` | `"bzip2"` | `"lzma"`, default `"none"`
- `follow_formatting` parameter: `bool`, default `False`
- Method returns raw `bytes` (the ZIP file body)

### Out of Scope
- Saving the ZIP to disk (caller's responsibility)
- Streaming / chunked download
- Any other bulk endpoint (covered by issue 0009)

---

## Acceptance Criteria
- [ ] `client.documents.bulk_download(document_ids)` sends `POST /api/documents/bulk_download/` with body `{"documents": document_ids, "content": "archive", "compression": "none", "follow_formatting": false}` when called with defaults.
- [ ] Passing explicit `content`, `compression`, and `follow_formatting` values sends the correct values in the request body.
- [ ] The method returns the raw response bytes (the ZIP archive).
- [ ] `content` accepts only the three valid string literals; `compression` accepts only the four valid string literals (enforced via type annotations / Literal types).
- [ ] The sync client exposes an equivalent `bulk_download()` method with the same signature and behaviour.
- [ ] Unit tests cover: default parameters, all non-default `content` values, at least one non-default `compression` value, `follow_formatting=True`, and the sync client.

---

## Dependencies & Constraints
- Depends on the existing `HttpSession` for authenticated POST requests.
- The response body must be read as raw bytes (not parsed as JSON).

---

## Priority
`Medium`

---

## Additional Notes
- API reference: `POST /api/documents/bulk_download/`
- Request schema: `BulkDownloadRequest` — `documents` (required, list of int), `content` (string enum, default `"archive"`), `compression` (string enum, default `"none"`), `follow_formatting` (bool, default `false`)
- The response is a binary ZIP stream, not JSON.

---

## QA

**Tested by:** QA Engineer
**Date:** 2026-03-31
**Commit:** e131063 (re-run after BUG-001 fix)

### Test Results

| # | Test Case | Expected | Actual | Status |
|---|-----------|----------|--------|--------|
| 1 | AC1: `bulk_download(ids)` sends POST to `/api/documents/bulk_download/` with default body `{"documents": ids, "content": "archive", "compression": "none", "follow_formatting": false}` | Correct endpoint and payload | `test_bulk_download_defaults` verifies all fields | ✅ Pass |
| 2 | AC2: Explicit `content="originals"` is sent in body | `content == "originals"` in payload | `test_bulk_download_content_originals` confirms | ✅ Pass |
| 2b | AC2: Explicit `content="both"` is sent in body | `content == "both"` in payload | `test_bulk_download_content_both` confirms | ✅ Pass |
| 2c | AC2: Explicit `compression="lzma"` is sent in body | `compression == "lzma"` in payload | `test_bulk_download_compression_lzma` confirms | ✅ Pass |
| 2d | AC2: `follow_formatting=True` is sent in body | `follow_formatting == True` in payload | `test_bulk_download_follow_formatting` confirms | ✅ Pass |
| 3 | AC3: Method returns raw response bytes | `bytes` object returned | `resp.content` returned directly; all tests assert `result == ZIP_BYTES` | ✅ Pass |
| 4 | AC4: `content` and `compression` enforced via `Literal` type annotations | Mypy catches invalid values at type-check time | `Literal["archive","originals","both"]` and `Literal["none","deflated","bzip2","lzma"]`; mypy reports no issues | ✅ Pass |
| 5 | AC5: Sync client exposes `bulk_download()` with same signature | Method exists on `SyncDocumentsResource`, delegates to async | `test_sync_bulk_download` passes with `content="originals"`, `compression="lzma"` | ✅ Pass |
| 6 | AC6: Unit tests cover defaults, all non-default `content` values, ≥1 non-default `compression`, `follow_formatting=True`, sync | All required test cases present | 7 unit tests in `test_client_bulk.py` + 1 in `test_sync.py` | ✅ Pass |
| 7 | Edge: Empty document list is forwarded as-is | `documents == []` in body | `test_bulk_download_empty_document_list` confirms | ✅ Pass |
| 8 | Ruff linting — `tests/integration/test_bulk_download.py` | No lint errors | BUG-001 fixed: `io` now appears before `zipfile`; `ruff check .` passes clean | ✅ Pass |

### Bugs Found

None.

### Automated Tests
- Suite: `pytest tests/` — **638 passed, 0 failed**
- Ruff: No errors
- Mypy: No issues (38 source files)

### Summary
- ACs tested: 6/6
- ACs passing: 6/6
- Bugs found: 0
- Recommendation: ✅ Ready to merge
