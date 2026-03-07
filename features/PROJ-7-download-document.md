# PROJ-7: Download Document

## Status: In Review
**Created:** 2026-03-06
**Last Updated:** 2026-03-06

## Dependencies
- Requires: PROJ-1 (HTTP Client Core) — for authenticated HTTP requests and error mapping

## User Stories
- As a developer, I want to download the archived (post-processed) PDF of a document so that I can work with the version paperless-ngx has optimised and OCR'd.
- As a developer, I want to download the original file that was uploaded so that I can retrieve the source file in its unmodified form.
- As a developer, I want the file returned as raw bytes so that I can save it to disk, pass it to another library, or stream it without additional processing.
- As a developer, I want a clear error when the server returns an HTML login page instead of the file so that auth misconfigurations are surfaced immediately rather than silently corrupting the download.
- As a developer, I want a `NotFoundError` when the document ID does not exist so that I can handle missing documents gracefully.

## Acceptance Criteria
- [ ] `PaperlessClient.download_document(id: int, *, original: bool = False) -> bytes` returns the raw binary content of the document file.
- [ ] When `original=False` (default), the archived/post-processed version is fetched from `GET /documents/{id}/archive/`.
- [ ] When `original=True`, the original uploaded file is fetched from `GET /documents/{id}/download/`.
- [ ] The return type is `bytes` — no decoding, no wrapping.
- [ ] Raises `NotFoundError` when the server returns HTTP 404.
- [ ] Raises `ServerError` when the response body is an HTML page (detected via `Content-Type: text/html` header or an `<!doctype` prefix in the body), indicating the server redirected to a login page instead of serving the file.
- [ ] The method is available on `SyncPaperlessClient` with the same signature (blocking wrapper).

## Edge Cases
- Document ID does not exist → raises `NotFoundError`.
- Auth token is invalid or expired: paperless-ngx may redirect to a login page rather than returning 401. This case is caught by the HTML-body detection and raises `ServerError` with a descriptive message.
- A document has no archive version (e.g. it was never processed): the API may return 404 or an error for `original=False`; this surfaces as `NotFoundError` or `ServerError` from the HTTP layer.
- The original file is not a PDF (e.g. an image or Word document): `download_document(original=True)` still returns the raw bytes regardless of format — callers are responsible for knowing the MIME type (retrievable via `get_document_metadata`).
- Large files: the entire response body is buffered into memory as `bytes`. There is no streaming API in this version.

## Technical Requirements
- The `original` flag maps to two different API endpoints: `original=True` → `/download/`, `original=False` → `/archive/`. This is an intentional paperless-ngx API design choice (not a naming error).
- HTML-response detection checks both the `Content-Type` response header and the first 9 bytes of the body (case-insensitive `<!doctype` prefix).

---
<!-- Sections below are added by subsequent skills -->

## Tech Design (Solution Architect)
_To be added by /architecture_

## QA Test Results
**Date:** 2026-03-07
**Tester:** QA Engineer (Claude)
**Branch:** master (commit b8575fc)

### Environment
- Python 3.13.12, pytest 9.0.2, respx 0.22.0
- mypy: strict, no errors (38 source files)
- ruff: no issues in library source (`src/`)
- Full test suite: 341 passed

### Acceptance Criteria

| # | Criterion | Result |
|---|-----------|--------|
| 1 | `download_document(id: int, *, original: bool = False) -> bytes` signature | **PASS** — matches spec exactly (mixins/documents.py L482) |
| 2 | `original=False` fetches from `GET /documents/{id}/archive/` | **PASS** — verified in code (L494: `endpoint = "download" if original else "archive"`) and test `test_download_document_archive` |
| 3 | `original=True` fetches from `GET /documents/{id}/download/` | **PASS** — verified in code and test `test_download_document_original` |
| 4 | Return type is `bytes` — no decoding, no wrapping | **PASS** — returns `resp.content` which is raw bytes; type annotation is `-> bytes` |
| 5 | Raises `NotFoundError` on HTTP 404 | **PASS** — `get_download` calls `_raise_for_status` which maps 404 to `NotFoundError`; tested in `test_download_document_not_found` |
| 6 | Raises `ServerError` on HTML response (Content-Type or `<!doctype` prefix) | **PASS** — both detection paths implemented (L497); tested in `test_download_document_html_content_type` and `test_download_document_html_body_prefix` |
| 7 | Available on `SyncPaperlessClient` with same signature | **PASS** — `SyncDocumentsMixin.download_document` delegates to async client; tested in `test_sync_download_document` |

### Edge Cases

| Edge Case | Result |
|-----------|--------|
| Document ID does not exist (404) | **PASS** — tested |
| Auth token invalid/expired (HTML login page redirect) | **PASS** — Content-Type check and body-prefix check both raise `ServerError` |
| No archive version (API returns 404) | **PASS** — `_raise_for_status` maps to `NotFoundError` |
| Non-PDF original file | **PASS** — returns raw bytes regardless of MIME type |
| Large files buffered into memory | **PASS** — no streaming; `resp.content` loads full body (documented limitation) |
| Redirect handling preserves auth | **PASS** — `get_download` follows redirects manually with fresh requests (http.py L103-135), re-attaching the default Authorization header each hop; max 5 hops |

### Additional Observations

1. **Redirect loop protection:** `get_download` limits to 5 redirect hops (http.py L122), preventing infinite loops. Good.
2. **HTML detection edge case — short body:** If the response body is fewer than 9 bytes and the Content-Type is not `text/html`, the `<!doctype` prefix check will not match (which is correct — a sub-9-byte body cannot be a valid HTML page). No bug.
3. **`ServerError.status_code` is `None` for HTML detection:** The `ServerError` raised on HTML detection passes `status_code=None` (L498-502). This is acceptable since the HTTP status was 200 — the error is semantic, not an HTTP error. Consistent with how `ServerError` is used for timeouts.

### Test Coverage
- 6 dedicated tests for `download_document` (5 async + 1 sync)
- All pass
- Covers: archive download, original download, 404, HTML content-type, HTML body prefix, sync wrapper

### Bugs Found
None.

### Production-Ready Decision
**READY** — All 7 acceptance criteria pass. All documented edge cases are covered. No bugs found. No Critical or High issues.

## Deployment
_To be added by /deploy_
