# PROJ-2: Name-to-ID Resolver

## Status: Implemented
**Created:** 2026-03-06
**Last Updated:** 2026-03-06

## Dependencies
- Requires: PROJ-1 (HTTP Client Core) — uses `HttpSession.get_all_pages()` to fetch resource listings

## Overview
An internal resolver that transparently converts human-readable string names (e.g. `"Invoice"`, `"ACME Corp"`) to the integer IDs that the paperless-ngx API requires. The resolver caches full resource listings in memory and is used by `PaperlessClient` so that all public methods accept either IDs or names interchangeably.

## User Stories
- As a developer, I want to pass a tag name like `"invoice"` instead of a numeric ID so that I don't need to look up IDs beforehand.
- As a developer, I want to pass a list of tag/correspondent/document-type names in one call so that I can resolve multiple values without writing a loop.
- As a developer, I want name lookups to be case-insensitive so that `"Invoice"` and `"invoice"` both resolve to the same ID.
- As a developer, I want an already-numeric ID to pass through unchanged so that I can mix IDs and names freely in the same list.
- As a developer, I want a clear error when a name doesn't exist so that I can detect typos or stale references immediately.
- As a developer, I want the resource listing to be fetched only once per session so that repeated lookups don't cause redundant API calls.
- As a developer, I want to invalidate the cache for a specific resource so that I can force a fresh fetch after creating or renaming items.

## Acceptance Criteria

### NameResolver class (`_internal/resolvers.py`)
- [ ] `NameResolver(session)` — accepts an `HttpSession` instance; stores it as a private attribute to avoid circular imports (typed as `object` internally).
- [ ] Maintains a per-resource in-memory cache: `dict[str, dict[str, int]]` mapping resource name → `{lowercase_item_name: id}`.

### `resolve(resource, value) -> int`
- [ ] When `value` is an `int`, returns it unchanged (pass-through).
- [ ] When `value` is a `str`, ensures the resource cache is loaded, then returns the matching integer ID.
- [ ] Name matching is case-insensitive (values are lowercased before lookup).
- [ ] Raises `NotFoundError` with a message identifying the resource and the missing name when the name is not in the cache.
- [ ] Logs a DEBUG message on successful resolution: resolved resource, original name, and resulting ID.

### `resolve_list(resource, values) -> list[int]`
- [ ] Resolves each element in `values` via `resolve()` and returns a list of ints in the same order.
- [ ] Accepts mixed lists of `int` and `str`.

### Cache loading (`_ensure_loaded`)
- [ ] On the first call to `resolve()` or `resolve_list()` for a given resource, fetches all pages via `session.get_all_pages(f"/{resource}/")`.
- [ ] Builds the cache as `{item["name"].lower(): item["id"]}` from the fetched items.
- [ ] Subsequent calls for the same resource use the in-memory cache without making API requests.
- [ ] Logs DEBUG messages on cache miss (before fetch) and after cache population (count of loaded names).
- [ ] Logs DEBUG message on cache hit.

### `invalidate(resource) -> None`
- [ ] Removes the cached listing for the given resource.
- [ ] Subsequent resolution calls for that resource trigger a fresh API fetch.
- [ ] Logs a DEBUG message when a cache entry is removed.
- [ ] No-ops silently when the resource is not cached.

### Integration with PaperlessClient
- [ ] `PaperlessClient.__init__` creates a single `NameResolver` instance shared across all operations.
- [ ] `NameResolver` is not part of the public API and not re-exported from `easypaperless.__init__`.
- [ ] The following resources are resolved transparently by `PaperlessClient` methods:
  - `tags` — used in `list_documents`, `update_document`, `create_*` methods
  - `correspondents` — used in `list_documents`, `update_document`, `create_*` methods
  - `document_types` — used in `list_documents`, `update_document`, `create_*` methods
  - `storage_paths` — used in `update_document`, `create_*` methods

## Edge Cases
- **Integer pass-through** — passing an `int` to `resolve()` returns it immediately without touching the cache.
- **Mixed int/str list** — `resolve_list()` handles lists containing both integers and strings correctly.
- **Name not found** — `NotFoundError` is raised with a message that identifies both the resource and the missing name.
- **int id as str** - When the user submits an id as a str. e.g. "42" and this name does not exist - the error raised should also give a hint: "you submitted an integer as a string. ..." or similar.
- **Case sensitivity** — `"Invoice"`, `"INVOICE"`, and `"invoice"` all resolve to the same ID.
- **Cache invalidation then re-lookup** — after `invalidate(resource)`, the next call to `resolve()` triggers a full re-fetch from the API.
- **Resource with zero items** — an empty resource listing populates the cache as an empty dict; any name lookup against it raises `NotFoundError`.

## Technical Notes
- `NameResolver` is an internal class; import path is `easypaperless._internal.resolvers`.
- `HttpSession` is passed as a generic `object` to the constructor to avoid a circular import; only async methods (`get_all_pages`) are called on it at runtime.
- The cache is session-scoped (lives for the lifetime of the `PaperlessClient` instance) with no TTL or automatic expiry.

---

## Tech Design (Solution Architect)
_To be added by /architecture_

## QA Test Results
**Date:** 2026-03-07
**Tester:** QA Engineer (Claude)
**Test suite:** `tests/test_resolvers.py` — 10 tests, all passing
**Code coverage:** 100% line coverage on `src/easypaperless/_internal/resolvers.py`

### Acceptance Criteria Results

| # | Criterion | Result |
|---|-----------|--------|
| 1 | `NameResolver(session)` accepts session, stores as private attr | PASS |
| 2 | Per-resource in-memory cache `dict[str, dict[str, int]]` | PASS |
| 3 | `resolve()` int pass-through returns unchanged | PASS |
| 4 | `resolve()` string loads cache and returns matching ID | PASS |
| 5 | Case-insensitive name matching | PASS |
| 6 | `NotFoundError` with resource and missing name in message | PASS |
| 7 | DEBUG log on successful resolution | PASS (code-verified) |
| 8 | `resolve_list()` resolves each element, preserves order | PASS |
| 9 | `resolve_list()` accepts mixed int/str lists | PASS |
| 10 | `_ensure_loaded` fetches via `get_all_pages` on first call | PASS |
| 11 | Cache built as `{name.lower(): id}` | PASS |
| 12 | Subsequent calls use cache without API requests | PASS |
| 13 | DEBUG log on cache miss, population, and hit | PASS (code-verified) |
| 14 | `invalidate()` removes cached listing | PASS |
| 15 | After invalidate, next resolve triggers fresh fetch | PASS |
| 16 | DEBUG log on cache invalidation | PASS (code-verified) |
| 17 | `invalidate()` no-ops silently when resource not cached | PASS |
| 18 | `PaperlessClient.__init__` creates single shared `NameResolver` | PASS |
| 19 | `NameResolver` not in public API / `__all__` | PASS |
| 20 | Tags, correspondents, document_types, storage_paths resolved transparently | PASS |

### Edge Cases Tested

| Edge Case | Result | Notes |
|-----------|--------|-------|
| Integer pass-through | PASS | No cache touched |
| Mixed int/str list | PASS | |
| Name not found | PASS | `NotFoundError` raised with resource + name |
| Int ID as string (e.g. `"42"`) | **BUG** | Hint message contains literal `{value}` — see Bug #1 |
| Case sensitivity (`"Invoice"` / `"INVOICE"` / `"invoice"`) | PASS | |
| Cache invalidation then re-lookup | PASS | |
| Resource with zero items | PASS | Empty dict cached; any lookup raises `NotFoundError` |
| Different resources cached separately | PASS | |

### Lint / Type-Check

| Tool | Result | Notes |
|------|--------|-------|
| mypy (strict) | PASS | No issues |
| ruff | **BUG** | Line 57 exceeds 100 chars (101) — see Bug #2 |

### Bugs Found

**Bug #1 — Medium: Hint message for int-as-string has uninterpolated `{value}`**
- **File:** `src/easypaperless/_internal/resolvers.py`, line 37
- **Severity:** Medium
- **Description:** The second string in the hint concatenation is a plain string, not an f-string, so `{value}` is rendered literally instead of being interpolated.
- **Actual output:** `"... use int({value}) instead of a string ..."`
- **Expected output:** `"... use int(42) instead of a string ..."`
- **Steps to reproduce:** Call `await resolver.resolve("tags", "42")` when no tag named `"42"` exists.
- **Fix:** Add the `f` prefix to the second string on line 37: `f" integer ID — use int({value}) instead..."`.

**Bug #2 — Low: Ruff E501 line length violation**
- **File:** `src/easypaperless/_internal/resolvers.py`, line 57
- **Severity:** Low
- **Description:** Line 57 is 101 characters, exceeding the project's 100-character limit.
- **Steps to reproduce:** Run `ruff check src/easypaperless/_internal/resolvers.py`.

### Regression Testing
- Full test suite (290 tests, excluding integration): ALL PASSED
- No regressions detected in related features

### Summary
- **Acceptance criteria:** 20/20 passed
- **Edge cases:** 7/8 passed, 1 bug (medium)
- **Bugs found:** 2 total — 1 Medium, 1 Low
- **Production-ready:** YES (no Critical or High bugs)

## Deployment
_To be added by /deploy_
