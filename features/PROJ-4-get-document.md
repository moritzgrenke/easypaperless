# PROJ-4: Get Document by ID

## Status: QA Passed
**Created:** 2026-03-06
**Last Updated:** 2026-03-06

## Dependencies
- Requires: PROJ-1 (HTTP Client Core) — for authenticated HTTP requests and error mapping
- Requires: PROJ-2 (Name-to-ID Resolver) — resolver infrastructure used by the client

## User Stories
- As a developer, I want to fetch a single document by its ID so that I can read its fields without retrieving a full list.
- As a developer, I want to optionally include extended file metadata (checksums, sizes, MIME type) in a single call so that I don't have to make a second request manually.
- As a developer, I want to fetch only the file metadata for a document so that I can perform a lightweight check (e.g. checksum comparison) without loading the full document.
- As a developer, I want a clear `NotFoundError` when a document ID does not exist so that I can handle missing documents gracefully.

## Acceptance Criteria
- [ ] `PaperlessClient.get_document(id: int) -> Document` fetches `GET /documents/{id}/` and returns a validated `Document` instance.
- [ ] `get_document` accepts an `include_metadata: bool = False` keyword argument.
- [ ] When `include_metadata=True`, the metadata endpoint (`GET /documents/{id}/metadata/`) is fetched **concurrently** (not serially) and the result is attached to `Document.metadata`.
- [ ] When `include_metadata=False` (default), `Document.metadata` is `None` and no metadata request is made.
- [ ] `PaperlessClient.get_document_metadata(id: int) -> DocumentMetadata` fetches only `GET /documents/{id}/metadata/` and returns a validated `DocumentMetadata` instance.
- [ ] Both methods raise `NotFoundError` when the server returns HTTP 404.
- [ ] The `Document` model exposes all standard paperless-ngx document fields: `id`, `title`, `content`, `tags`, `document_type`, `correspondent`, `storage_path`, `created`, `created_date`, `modified`, `added`, `archive_serial_number`, `original_file_name`, `archived_file_name`, `owner`, `user_can_change`, `is_shared_by_requester`, `notes`, `custom_fields`.
- [ ] The `DocumentMetadata` model exposes: `original_checksum`, `original_size`, `original_mime_type`, `media_filename`, `has_archive_version`, `original_metadata`, `archive_checksum`, `archive_size`, `archive_metadata`.
- [ ] Both methods are exposed on `SyncPaperlessClient` with the same signature (blocking wrapper).
- [ ] Both methods are part of the public API exported from `easypaperless/__init__.py` (via the client class).

## Edge Cases
- Document ID does not exist → raises `NotFoundError`.
- `include_metadata=True` and the metadata endpoint returns 404 (e.g. document deleted between requests) → `NotFoundError` is raised; partial data is not silently swallowed.
- `Document.metadata` is `None` by default (not fetched in list responses or plain `get_document` calls) — consumers must not assume it is always populated.
- `DocumentMetadata.archive_metadata` and `archive_checksum` are `None` when no archive version exists (`has_archive_version=False`).
- `Document.notes` defaults to an empty list when the API returns no notes field.
- Extra fields returned by the API are ignored (`extra="ignore"`) to stay forward-compatible with future paperless-ngx versions.

## Technical Requirements
- The concurrent fetch in `get_document(include_metadata=True)` must use `asyncio.gather` (or equivalent) — the two HTTP requests must be in-flight simultaneously.
- No name-to-ID resolution is needed for this feature (input is always an integer ID).
- Response validation uses Pydantic v2 `model_validate`.

---
<!-- Sections below are added by subsequent skills -->

## Tech Design (Solution Architect)
_To be added by /architecture_

## QA Test Results
**Tested:** 2026-03-07
**Tester:** QA Engineer (Claude)
**Result:** PRODUCTION-READY

### Acceptance Criteria

| # | Criterion | Result |
|---|-----------|--------|
| 1 | `get_document(id: int) -> Document` fetches `GET /documents/{id}/` and returns a validated `Document` | PASS |
| 2 | `get_document` accepts `include_metadata: bool = False` keyword argument | PASS |
| 3 | When `include_metadata=True`, metadata endpoint fetched **concurrently** via `asyncio.gather` | PASS |
| 4 | When `include_metadata=False` (default), `Document.metadata` is `None` and no metadata request is made | PASS |
| 5 | `get_document_metadata(id: int) -> DocumentMetadata` fetches only metadata endpoint | PASS |
| 6 | Both methods raise `NotFoundError` on HTTP 404 | PASS |
| 7 | `Document` model exposes all required fields (`id`, `title`, `content`, `tags`, `document_type`, `correspondent`, `storage_path`, `created`, `created_date`, `modified`, `added`, `archive_serial_number`, `original_file_name`, `archived_file_name`, `owner`, `user_can_change`, `is_shared_by_requester`, `notes`, `custom_fields`) | PASS |
| 8 | `DocumentMetadata` model exposes all required fields (`original_checksum`, `original_size`, `original_mime_type`, `media_filename`, `has_archive_version`, `original_metadata`, `archive_checksum`, `archive_size`, `archive_metadata`) | PASS |
| 9 | Both methods exposed on `SyncPaperlessClient` with same signature | PASS |
| 10 | Both methods part of public API exported from `easypaperless/__init__.py` | PASS |

### Edge Cases

| Edge Case | Result |
|-----------|--------|
| Document ID does not exist -> raises `NotFoundError` | PASS |
| `include_metadata=True` + metadata endpoint returns 404 -> `NotFoundError` raised (no partial data) | PASS |
| `Document.metadata` is `None` by default | PASS |
| `DocumentMetadata.archive_*` fields are `None` when `has_archive_version=False` | PASS |
| `Document.notes` defaults to empty list when API returns no notes field | PASS |
| Extra fields returned by API are ignored (`extra="ignore"`) | PASS |

### Technical Requirements

| Requirement | Result |
|-------------|--------|
| Concurrent fetch uses `asyncio.gather` | PASS — confirmed at line 55 of `mixins/documents.py` |
| No name-to-ID resolution needed (input is always integer ID) | PASS |
| Response validation uses Pydantic v2 `model_validate` | PASS |

### Static Analysis

| Check | Result |
|-------|--------|
| `mypy` (strict) | PASS — no issues in 3 source files |
| `ruff check` | PASS — all checks passed |
| Unit tests (85 in `test_client_documents.py`) | PASS — all 85 passed |
| Full test suite (328 tests) | PASS — all passed |
| Coverage for `models/documents.py` | 100% |
| Coverage for `sync_mixins/documents.py` | 100% |

### Test Gaps Noted (Low Priority)

The async client tests do not have dedicated `NotFoundError` tests for `get_document` and `get_document_metadata` (the sync client does). This is not a bug since 404 handling is implemented in the HTTP layer and verified by manual testing above, but adding explicit async tests would improve completeness.

### Bugs Found

None.

### Verdict

**PRODUCTION-READY** — All 10 acceptance criteria pass, all 6 edge cases pass, all technical requirements met, no bugs found. Static analysis clean.

## Deployment
_To be added by /deploy_
