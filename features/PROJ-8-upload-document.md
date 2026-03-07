# PROJ-8: Upload Document

## Status: QA Passed
**Created:** 2026-03-06
**Last Updated:** 2026-03-07

## Dependencies
- Requires: PROJ-1 (HTTP Client Core) — for authenticated multipart HTTP requests and error mapping
- Requires: PROJ-2 (Name-to-ID Resolver) — for transparent string-to-ID resolution of tags, correspondent, document type, storage path
- Requires: PROJ-4 (Get Document by ID) — used internally to fetch the resulting `Document` after task completion when `wait=True`

## User Stories
- As a developer, I want to upload a file to paperless-ngx by providing a file path so that I can ingest documents programmatically without using the web UI.
- As a developer, I want to pre-assign metadata (title, date, correspondent, document type, storage path, tags, ASN) at upload time so that newly ingested documents are organised without a follow-up update call.
- As a developer, I want to get back a task ID immediately (fire-and-forget) so that I can submit many uploads concurrently without blocking on processing.
- As a developer, I want to optionally wait for processing to complete and receive the resulting `Document` in a single call so that I don't have to implement polling logic myself.
- As a developer, I want a descriptive error when processing fails so that I can surface the paperless-ngx failure reason to my own application.
- As a developer, I want a timeout error when processing takes too long so that my application does not hang indefinitely.

## Acceptance Criteria
- [ ] `PaperlessClient.upload_document(file, **metadata) -> str | Document` sends a multipart POST to `POST /documents/post_document/` and returns a Celery task ID string by default.
- [ ] `file` accepts a `str` or `pathlib.Path` pointing to a local file. The file is read from disk and sent as the `document` form field along with its filename.
- [ ] The following optional keyword-only metadata fields are supported: `title`, `created` (ISO-8601 date string), `correspondent` (ID or name), `document_type` (ID or name), `storage_path` (ID or name), `tags` (list of IDs or names), `asn` (integer archive serial number).
- [ ] `correspondent`, `document_type`, `storage_path`, and `tags` accept string names which are resolved to IDs transparently before upload.
- [ ] Only metadata fields that are explicitly passed (not `None`) are included in the multipart payload.
- [ ] When `wait=False` (default), the method returns immediately with the task ID string (the raw UUID returned by paperless-ngx, stripped of surrounding quotes).
- [ ] When `wait=True`, the method polls `GET /api/tasks/?task_id=<id>` at `poll_interval` second intervals until the task reaches a terminal state or the timeout is exceeded.
- [ ] When `wait=True` and the task succeeds, the method returns the fully processed `Document` fetched via `get_document(document_id)`.
- [ ] When `wait=True` and the task fails, raises `UploadError` with the paperless-ngx failure message.
- [ ] When `wait=True` and processing does not complete within `poll_timeout` seconds, raises `TaskTimeoutError`.
- [ ] `poll_interval` and `poll_timeout` can be overridden per call (keyword arguments); they fall back to client-level defaults when omitted.
- [ ] The method is available on `SyncPaperlessClient` with the same signature (blocking wrapper).

## Edge Cases
- File path does not exist or is not readable → raises a standard Python `FileNotFoundError` before any HTTP request is made.
- Paperless-ngx rejects the upload (e.g. unsupported file type) → the task transitions to `FAILURE`; if `wait=True` this raises `UploadError`; if `wait=False` the caller receives the task ID and must poll manually to discover the failure.
- `wait=True` with a very short `poll_timeout` → raises `TaskTimeoutError`; the document may still be processed successfully on the server side.
- The task status endpoint returns an empty list before the task is registered → the poller continues sleeping and retrying until the task appears or the timeout is exceeded.
- Passing a tag name that does not exist in paperless-ngx raises a resolver error before any HTTP request is made.
- `created` is passed directly to the API as-is; no date validation is performed by the client — invalid strings will be rejected by the server.

## Technical Requirements
- Upload uses multipart form encoding (`files={"document": (filename, bytes)}`), not JSON.
- The task ID is returned as a plain string from the API response body (JSON-encoded string); outer quotes must be stripped.
- Polling state machine: `PENDING` / `STARTED` / `RETRY` → keep polling; `SUCCESS` → fetch document and return; `FAILURE` → raise `UploadError`; timeout → raise `TaskTimeoutError`.

---
<!-- Sections below are added by subsequent skills -->

## Tech Design (Solution Architect)
_To be added by /architecture_

## QA Test Results
**Date:** 2026-03-07
**Tester:** QA Engineer (Claude)
**Branch:** master (commit d8e4cc2)

### Test Environment
- Python 3.13.12, pytest 9.0.2, respx 0.22.0, mypy (strict), ruff
- All 341 tests pass (9 upload-specific); async upload mixin at 100% coverage

### Acceptance Criteria

| # | Criterion | Result | Notes |
|---|-----------|--------|-------|
| 1 | `upload_document(file, **metadata) -> str \| Document` sends multipart POST to `/documents/post_document/` and returns task ID | **PASS** | `test_upload_returns_task_id` confirms |
| 2 | `file` accepts `str` or `pathlib.Path`; file read from disk and sent as `document` form field with filename | **PASS** | `Path(file)` handles both; `files={"document": (file_path.name, file_bytes)}` correct |
| 3 | Optional keyword-only metadata: `title`, `created`, `correspondent`, `document_type`, `storage_path`, `tags`, `asn` | **PASS** | `test_upload_sends_metadata_fields` confirms all fields |
| 4 | `correspondent`, `document_type`, `storage_path`, `tags` accept string names resolved to IDs | **PASS** | `test_upload_resolves_names` confirms via resolver |
| 5 | Only non-`None` metadata fields included in multipart payload | **PASS** | `test_upload_omits_none_metadata` confirms |
| 6 | `wait=False` (default) returns task ID string, quotes stripped | **PASS** | `resp.text.strip('"')` strips quotes; test confirms |
| 7 | `wait=True` polls `GET /api/tasks/?task_id=<id>` at `poll_interval` intervals | **PASS** | `test_upload_wait_true_polls_and_returns_document` confirms |
| 8 | `wait=True` + task SUCCESS returns `Document` via `get_document(document_id)` | **PASS** | Test confirms `isinstance(result, Document)` |
| 9 | `wait=True` + task FAILURE raises `UploadError` with failure message | **PASS** | `test_upload_wait_true_failure_raises_upload_error` confirms |
| 10 | `wait=True` + timeout raises `TaskTimeoutError` | **PASS** | `test_upload_wait_timeout_raises_task_timeout_error` confirms |
| 11 | `poll_interval` and `poll_timeout` overridable per-call, fall back to client defaults | **PASS** | Code uses `if poll_interval is not None else self._poll_interval`; client defaults set in `_ClientCore.__init__` |
| 12 | Method available on `SyncPaperlessClient` with same signature | **PASS** | `SyncUploadMixin.upload_document` mirrors async signature exactly |

**Acceptance criteria: 12/12 passed, 0 failed**

### Edge Cases (from spec)

| # | Edge Case | Result | Notes |
|---|-----------|--------|-------|
| 1 | File path does not exist → `FileNotFoundError` before HTTP | **PASS** | `Path.read_bytes()` raises naturally; `test_upload_file_not_found_raises` confirms |
| 2 | Task transitions to FAILURE; `wait=True` raises `UploadError` | **PASS** | Tested |
| 3 | `wait=True` with very short `poll_timeout` → `TaskTimeoutError` | **PASS** | Tested with `poll_timeout=0.05` |
| 4 | Task status endpoint returns empty list → poller continues | **PASS** | `test_upload_empty_task_response_keeps_polling` confirms |
| 5 | Non-existent tag name → resolver error before HTTP | **PASS** | Resolver raises `NotFoundError`; covered by resolver tests (PROJ-2) |
| 6 | `created` passed as-is, no client-side validation | **PASS** | Code does `data["created"] = created` with no parsing |

**Edge cases: 6/6 passed**

### Additional Edge Cases Identified by QA

| # | Edge Case | Severity | Resolution |
|---|-----------|----------|------------|
| 1 | `STARTED` and `RETRY` task statuses not explicitly tested | **Low** | **FIXED** — `test_upload_wait_started_then_success` and `test_upload_wait_retry_then_success` added; both pass. |
| 2 | `REVOKED` task status causes polling until timeout | **Low** | **FIXED** — `_poll_task` now treats `REVOKED` as a terminal state and raises `UploadError`; confirmed by `test_upload_wait_revoked_raises_upload_error`. |
| 3 | `related_document=None` on SUCCESS task would raise `TypeError` | **Low** | **FIXED** — Guard clause added before `int(task.related_document)`; raises `UploadError` with descriptive message; confirmed by `test_upload_wait_success_no_related_document_raises`. |
| 4 | No sync `upload_document` test in `test_sync.py` | **Low** | **FIXED** — `test_sync_upload_document` added to `test_sync.py`; passes. |

### Static Analysis
- **mypy (strict):** 0 errors on upload-related files
- **ruff:** All checks passed
- **Coverage:** async upload mixin 100%, sync upload mixin 100%

### Regression Testing
- Full test suite: **346 passed**, 39 deselected (integration markers)
- No regressions in PROJ-1 through PROJ-7 features

### Security Audit
- No secrets or credentials in code
- File read uses `Path.read_bytes()` -- no path traversal risk (caller controls the path)
- No user-supplied data injected into URLs unsafely (task ID comes from server response)
- Multipart encoding via httpx -- no injection vectors

### Summary
- **Acceptance criteria:** 12/12 passed
- **Documented edge cases:** 6/6 passed
- **Bugs found:** 0 Critical, 0 High, 0 Medium, 4 Low (all fixed)
- **Production-ready:** YES

All 4 low-severity observations have been resolved: STARTED/RETRY/REVOKED status tests added, REVOKED treated as terminal, None-guard for `related_document`, and sync test added.

## Deployment
_To be added by /deploy_
