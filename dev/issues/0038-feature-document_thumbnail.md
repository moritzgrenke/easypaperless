# [FEATURE] Fetch Document Thumbnail Image

## Summary
Add a `thumbnail()` method to the documents resource that retrieves the thumbnail image for a given document from the Paperless-ngx API and returns it as raw bytes.

---

## Problem Statement
The Paperless-ngx API exposes a `GET /api/documents/{id}/thumb/` endpoint that returns a binary thumbnail image for a document. This endpoint is not yet wrapped by easypaperless, leaving users without a convenient way to retrieve document thumbnails via the client.

---

## Proposed Solution
Expose a `thumbnail(id: int) -> bytes` method on the documents resource (both async and sync clients). The method sends an authenticated GET request to `/api/documents/{id}/thumb/` and returns the raw binary content of the thumbnail image.

---

## User Stories

- As a developer, I want to retrieve the thumbnail image of a document by its ID so that I can display or process the preview image in my application.
- As a developer, I want the thumbnail returned as raw bytes so that I can save it to disk, pass it to an image library, or serve it over HTTP without additional processing.
- As a developer, I want a `NotFoundError` when the document ID does not exist so that I can handle missing documents gracefully.

---

## Scope

### In Scope
- `documents.thumbnail(id: int) -> bytes` method on the async `DocumentsResource`
- Equivalent method on the sync `SyncDocumentsResource`
- Returns raw binary content (`bytes`) of the thumbnail image
- Raises `NotFoundError` on HTTP 404
- Raises `ServerError` on unexpected HTML responses (auth redirect detection, same pattern as `download()`)

### Out of Scope
- Decoding or parsing the image (callers handle image format themselves)
- Streaming / partial content support
- Any method to set or replace the thumbnail

---

## Acceptance Criteria
- [ ] `documents.thumbnail(id: int) -> bytes` exists on the async documents resource
- [ ] The method sends a `GET` request to `/api/documents/{id}/thumb/`
- [ ] The return value is the raw binary content of the thumbnail (`bytes`)
- [ ] Raises `NotFoundError` when the server returns HTTP 404
- [ ] Raises `ServerError` when the response body is an HTML page (Content-Type `text/html` or `<!doctype` prefix), indicating an auth redirect
- [ ] The method is available on `SyncDocumentsResource` with the same signature (blocking wrapper)

---

## Dependencies & Constraints
- Follows the same implementation pattern as `download()` in `_internal/mixins/documents.py`
- Relies on the existing HTTP client auth and error-mapping infrastructure

---

## Priority
`Medium`

---

## Additional Notes
- Paperless-ngx API reference: `GET /api/documents/{id}/thumb/` — returns `string($binary)`
- The response MIME type is typically `image/webp` or `image/png`, but callers are responsible for determining the format

---

## QA

**Tested by:** QA Engineer
**Date:** 2026-03-31
**Commit:** 5c3cd87 (unstaged changes reviewed)

### Test Results

| # | Test Case | Expected | Actual | Status |
|---|-----------|----------|--------|--------|
| 1 | AC1: `thumbnail(id)` exists on async `DocumentsResource` | Method present with correct signature | `async def thumbnail(self, id: int) -> bytes` found at resources/documents.py:682 | ✅ Pass |
| 2 | AC2: Sends GET to `/api/documents/{id}/thumb/` | Correct URL path used | Path `f"/documents/{id}/thumb/"` passed to `get_download()` | ✅ Pass |
| 3 | AC3: Returns raw `bytes` of thumbnail image | `bytes` returned | Method returns `resp.content` (bytes); all unit tests confirm correct bytes returned | ✅ Pass |
| 4 | AC4: Raises `NotFoundError` on HTTP 404 | `NotFoundError` raised | `get_download` calls `_raise_for_status` which raises `NotFoundError` on 404; confirmed by unit tests | ✅ Pass |
| 5 | AC5: Raises `ServerError` on HTML response (content-type `text/html` or `<!doctype` prefix) | `ServerError` raised | Both checks present in implementation; 3 unit tests confirm (HTML content-type, uppercase `<!DOCTYPE`, lowercase `<!doctype`) | ✅ Pass |
| 6 | AC6: `thumbnail(id)` available on `SyncDocumentsResource` with same signature | Sync wrapper present | `def thumbnail(self, id: int) -> bytes` at sync_resources/documents.py:408; delegates via `self._run()` | ✅ Pass |
| 7 | Edge: `image/webp` MIME type returned as bytes unchanged | Raw bytes returned | `test_thumbnail_document_webp` confirms WebP magic bytes pass through unmodified | ✅ Pass |
| 8 | Edge: Auth-preserving redirect followed on thumb endpoint | Redirects followed with auth header | Uses existing `get_download()` which re-attaches auth on each redirect hop (same as `download()`) | ✅ Pass |
| 9 | Regression: No existing tests broken | Full suite passes | 631 unit tests passed, 0 failures | ✅ Pass |
| 10 | Type check: mypy strict passes | No type errors | `mypy src/easypaperless/` → "Success: no issues found in 38 source files" | ✅ Pass |
| 11 | Lint: ruff check passes | No lint errors | `ruff check .` → all clean | ✅ Pass |
| 12 | Integration test: real Paperless instance returns image bytes | Non-empty bytes starting with known image magic | Untested — requires live Paperless instance; integration test file `tests/integration/test_thumbnail.py` is present and correct | ⚠️ Untested |

### Bugs Found

None.

### Automated Tests

- `tests/test_client_documents.py` (thumbnail subset) — 6 passed, 0 failed
- `tests/test_sync.py` (thumbnail subset) — 2 passed, 0 failed
- Full unit suite — 631 passed, 0 failed
- Integration: `tests/integration/test_thumbnail.py` — not run (requires live instance)

### Summary

- ACs tested: 6/6
- ACs passing: 6/6
- Bugs found: 0
- Recommendation: ✅ Ready to merge
