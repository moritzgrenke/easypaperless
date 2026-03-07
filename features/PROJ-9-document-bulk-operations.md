# PROJ-9: Document Bulk Operations

## Status: QA Passed
**Created:** 2026-03-06
**Last Updated:** 2026-03-07

## Dependencies
- Requires: PROJ-1 (HTTP Client Core) — for authenticated HTTP requests and error mapping
- Requires: PROJ-2 (Name-to-ID Resolver) — for transparent string-to-ID resolution of tag, correspondent, document type, and storage path names

## User Stories
- As a developer, I want to add a tag to many documents in a single request so that I don't have to loop over individual `update_document` calls.
- As a developer, I want to remove a tag from many documents in a single request so that I can efficiently untag a batch.
- As a developer, I want to atomically add and remove multiple tags on a set of documents in one request so that the batch update is consistent and requires only one round trip.
- As a developer, I want to permanently delete many documents in a single request so that bulk cleanup is fast.
- As a developer, I want to assign a correspondent, document type, or storage path to many documents at once so that I can re-organise a batch without looping.
- As a developer, I want to add and/or remove custom field values on many documents at once so that I can update structured metadata in bulk.
- As a developer, I want to set permissions and owner on many documents at once so that I can apply access control to an entire batch.
- As a developer, I want a low-level escape hatch to call any bulk-edit method the paperless-ngx API supports, so that operations not yet covered by high-level helpers are still accessible.

## Acceptance Criteria

### High-level helpers
- [ ] `bulk_add_tag(document_ids: list[int], tag: int | str) -> None` adds a single tag to all listed documents. `tag` accepts an ID or name.
- [ ] `bulk_remove_tag(document_ids: list[int], tag: int | str) -> None` removes a single tag from all listed documents. `tag` accepts an ID or name.
- [ ] `bulk_modify_tags(document_ids: list[int], *, add_tags: list[int | str] | None, remove_tags: list[int | str] | None) -> None` atomically adds and/or removes multiple tags on all listed documents. Both parameters accept IDs or names and are optional (passing neither is a no-op).
- [ ] `bulk_delete(document_ids: list[int]) -> None` permanently deletes all listed documents.
- [ ] All high-level helpers accept string tag names and resolve them to IDs transparently before sending the request.
- [ ] All methods return `None` on success.

### Metadata assignment helpers (planned)
- [ ] `bulk_set_correspondent(document_ids: list[int], correspondent: int | str | None) -> None` assigns a correspondent to all listed documents. Accepts an ID or name; `None` clears the assignment.
- [ ] `bulk_set_document_type(document_ids: list[int], document_type: int | str | None) -> None` assigns a document type to all listed documents. Accepts an ID or name; `None` clears the assignment.
- [ ] `bulk_set_storage_path(document_ids: list[int], storage_path: int | str | None) -> None` assigns a storage path to all listed documents. Accepts an ID or name; `None` clears the assignment.
- [ ] `bulk_modify_custom_fields(document_ids: list[int], *, add_fields: list[dict] | None, remove_fields: list[int] | None) -> None` atomically adds and/or removes custom field values on all listed documents.
- [ ] `bulk_set_permissions(document_ids: list[int], *, set_permissions: SetPermissions | None, owner: int | None, merge: bool = False) -> None` applies permissions and/or owner to all listed documents. When `merge=True`, the new permissions are merged with existing ones rather than replacing them.
- [ ] `bulk_set_correspondent`, `bulk_set_document_type`, and `bulk_set_storage_path` accept string names and resolve them to IDs transparently.

### Low-level primitive
- [ ] `bulk_edit(document_ids: list[int], method: str, **parameters) -> None` sends `POST /documents/bulk_edit/` with payload `{"documents": document_ids, "method": method, "parameters": parameters}`.
- [ ] `bulk_edit` uses an extended request timeout of 120 seconds (large batches can take considerably longer than the default).
- [ ] All high-level helpers are implemented on top of `bulk_edit`.

### General
- [ ] All methods are available on `SyncPaperlessClient` with the same signatures (blocking wrapper).

## Edge Cases
- Empty `document_ids` list — the request is sent as-is; the API treats it as a no-op.
- `bulk_modify_tags` called with both `add_tags=None` and `remove_tags=None` — resolves to empty lists and sends `modify_tags` with empty arrays (no-op on the server).
- A tag name passed to any helper does not exist in paperless-ngx → resolver raises an error before the HTTP request is made.
- Large batches may approach the 120-second timeout; the extended timeout is applied per-request. If the server still times out, the underlying HTTP error propagates to the caller.
- `bulk_delete` is permanent and irreversible — no confirmation or undo mechanism is provided by this API.
- `bulk_edit` is a low-level method; passing an unknown `method` string will be forwarded to the API which may return an error — the caller is responsible for using valid method names.

## Out of Scope
- Bulk operations on non-document resources (tags, correspondents, etc.) — covered by a separate feature (`bulk_edit_objects`).

---
<!-- Sections below are added by subsequent skills -->

## Tech Design (Solution Architect)
_To be added by /architecture_

## QA Test Results
**QA Date:** 2026-03-07
**Tested by:** QA Engineer
**Branch:** master (commit a3bdb13)

### Environment
- Python 3.13.12, pytest 9.0.2, mypy strict, ruff
- All tests pass (71 bulk+sync tests verified), 95%+ coverage overall
- mypy: 0 errors across 38 source files

### Acceptance Criteria Results

#### High-level helpers
| # | Criterion | Result | Notes |
|---|-----------|--------|-------|
| 1 | `bulk_add_tag(document_ids, tag)` adds a tag; accepts ID or name | PASS | Tested with int ID and string name resolution |
| 2 | `bulk_remove_tag(document_ids, tag)` removes a tag; accepts ID or name | PASS | Tested with int ID |
| 3 | `bulk_modify_tags(document_ids, *, add_tags, remove_tags)` atomically adds/removes multiple tags | PASS | Both params optional, defaults to empty lists |
| 4 | `bulk_delete(document_ids)` permanently deletes listed documents | PASS | Delegates to `bulk_edit` with method `"delete"` |
| 5 | All helpers accept string tag names and resolve via `NameResolver` | PASS | `resolve()` and `resolve_list()` used correctly |
| 6 | All methods return `None` on success | PASS | No return value from any helper |

#### Metadata assignment helpers
| # | Criterion | Result | Notes |
|---|-----------|--------|-------|
| 7 | `bulk_set_correspondent(document_ids, correspondent)` — accepts ID, name, or None | PASS | Tested by ID, by name, and with None |
| 8 | `bulk_set_document_type(document_ids, document_type)` — accepts ID, name, or None | PASS | Tested by ID, by name, and with None |
| 9 | `bulk_set_storage_path(document_ids, storage_path)` — accepts ID, name, or None | PASS | Tested by ID, by name, and with None |
| 10 | `bulk_modify_custom_fields(document_ids, *, add_fields, remove_fields)` | PASS | Tested with values and with defaults (empty) |
| 11 | `bulk_set_permissions(document_ids, *, set_permissions, owner, merge)` | PASS | Tested with full perms+owner and with merge=True |
| 12 | `bulk_set_correspondent/document_type/storage_path` resolve string names | PASS | Name resolution tested for all three |

#### Low-level primitive
| # | Criterion | Result | Notes |
|---|-----------|--------|-------|
| 13 | `bulk_edit(document_ids, method, **parameters)` sends POST to `/documents/bulk_edit/` | PASS | Payload structure: `{"documents": ..., "method": ..., "parameters": ...}` |
| 14 | `bulk_edit` uses extended timeout of 120 seconds | PASS | `timeout=120.0` passed to `self._session.post()` |
| 15 | All high-level helpers are implemented on top of `bulk_edit` | PASS | Every helper calls `self.bulk_edit(...)` internally |

#### General
| # | Criterion | Result | Notes |
|---|-----------|--------|-------|
| 16 | All methods available on `SyncPaperlessClient` with same signatures | PASS | Full method parity confirmed (10 methods each) |

**Acceptance Criteria: 16/16 PASSED**

### Edge Cases Tested

| Edge Case | Result | Notes |
|-----------|--------|-------|
| Empty `document_ids` list | PASS | No guard; sent as-is (API treats as no-op per spec) |
| `bulk_modify_tags` with both params None | PASS | Defaults to empty lists, sends `modify_tags` with `[]` |
| String name not found in resolver | PASS | `NameResolver.resolve()` raises `NotFoundError` before HTTP call |
| 120s timeout on `bulk_edit` | PASS | Verified in source; `HttpSession.post` accepts and forwards `timeout` kwarg |
| `bulk_delete` irreversibility | N/A | By design — no confirmation mechanism, documented in spec |
| Unknown `method` to `bulk_edit` | PASS | Forwarded to API as-is; caller responsible |

### Observations (Low Severity)

| # | Severity | Description | Status |
|---|----------|-------------|--------|
| O1 | Low | **No payload assertion in tests.** All 20 async bulk tests mock the POST endpoint and assert success, but none verify the JSON body sent to the API. A `side_effect` or `request.content` assertion would catch payload-structure regressions (e.g., wrong parameter names like `add_custom_fields` vs `add_fields`). | **Fixed & Verified** — All async bulk tests now assert the full JSON payload structure via a `_payload()` helper (20 assertions across all test functions). |
| O2 | Low | **Sync test coverage gap.** `test_sync.py` covers `bulk_add_tag` and `bulk_delete` for the sync client, but does not cover `bulk_remove_tag`, `bulk_modify_tags`, `bulk_set_correspondent`, `bulk_set_document_type`, `bulk_set_storage_path`, `bulk_modify_custom_fields`, or `bulk_set_permissions`. The sync wrappers are thin delegation, so risk is minimal, but coverage is incomplete. | **Fixed & Verified** — 7 new sync tests added; all 9 sync bulk tests pass. |
| O3 | Low | **`sync_mixins/document_bulk.py` coverage at 69%.** The uncovered sync methods correspond to the missing sync tests in O2 above. | **Fixed & Verified** — Coverage confirmed at 96% (only uncovered line is `bulk_edit` which delegates directly). |

### Regression Testing
- Full test suite: **346 passed**, 39 deselected (integration)
- mypy strict: **0 errors** in 38 source files
- Ruff lint on `src/`: clean (lint issues are only in `scripts/` and `tests/integration/`, unrelated to PROJ-9)
- No regressions detected in PROJ-1 through PROJ-8 functionality

### Security Audit
- `bulk_delete` is permanent and irreversible — this is documented and by design
- `bulk_edit` accepts arbitrary `method` strings — low risk since it is documented as a low-level escape hatch
- No injection vectors: all parameters are serialized as JSON via httpx
- Authentication enforced via `HttpSession` headers on all requests

### Production-Ready Recommendation
**YES** — Production-ready.

All 16 acceptance criteria pass. No Critical or High severity bugs found. The three Low-severity observations (O1-O3) are test coverage improvements that do not affect runtime correctness. The implementation is clean, well-structured, and follows project conventions.

## Deployment
_To be added by /deploy_
