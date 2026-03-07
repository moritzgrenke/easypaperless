# PROJ-1: HTTP Client Core

## Status: Implemented
**Created:** 2026-03-06
**Last Updated:** 2026-03-06

## Dependencies
- None

## Overview
Internal HTTP session with token authentication, error mapping, pagination, and a structured exception hierarchy. This is the foundation all other features build on.

## User Stories
- As a developer, I want to instantiate a client with a base URL and API key so that I don't have to manage authentication headers manually.
- As a developer, I want HTTP errors mapped to typed Python exceptions so that I can handle auth failures, not-found cases, and server errors distinctly in my code.
- As a developer, I want paginated list endpoints to be automatically traversed so that I don't have to implement pagination logic myself.
- As a developer, I want to configure a default request timeout at construction time so that I can tune the client for slow or fast server environments.
- As a developer, I want binary downloads to work correctly even when the server issues cross-host redirects so that file downloads don't silently fail or return wrong content.

## Acceptance Criteria

### HttpSession
- [ ] `HttpSession(base_url, api_key, timeout=30.0)` — `timeout` is configurable at construction; defaults to 30 seconds.
- [ ] Base URL is normalized: trailing slashes stripped, `/api` appended.
- [ ] All requests include `Authorization: Token {api_key}` header.
- [ ] `close()` closes the underlying HTTP connection pool.
- [ ] `request(method, path, *, params, json, data, files, timeout)` — generic request; per-call `timeout` overrides the session default.
- [ ] Convenience methods: `get()`, `post()`, `patch()`, `delete()`.
- [ ] `post()` exposes a `timeout` parameter (for long-running operations like uploads).
- [ ] `get_download()` follows redirects manually, re-attaching the `Authorization` header on each hop (up to 5 hops).
- [ ] `get_all_pages(path, params, *, max_results, on_page)` — fetches all pages of a paginated list endpoint, optionally capped at `max_results`; calls `on_page(fetched_so_far, total_count)` after each page.

### Exception Hierarchy
- [ ] `PaperlessError(message, status_code=None)` — base exception; all easypaperless exceptions inherit from it.
- [ ] `AuthError` — raised on 401 or 403 responses.
- [ ] `NotFoundError` — raised on 404 responses.
- [ ] `ValidationError` — raised on 422 responses.
- [ ] `ServerError` — raised on 5xx responses and on transport-level errors (timeouts, connection failures).
- [ ] `UploadError` — raised when a document processing task reports a `FAILURE` status.
- [ ] `TaskTimeoutError` — raised when upload polling exceeds the configured timeout; `status_code` is always `None`.
- [ ] All exceptions carry the originating HTTP status code where applicable.

## Edge Cases
- **Trailing slash in base URL** — must be stripped before `/api` is appended to avoid double-slash paths.
- **Non-JSON error responses** — `_raise_for_status` falls back to raw response text if the body is not valid JSON.
- **Redirect strips auth header** — `get_download()` handles cross-host redirects by manually re-issuing each hop rather than relying on httpx's built-in redirect follower.
- **Redirect loop** — `get_download()` aborts after 5 hops to prevent infinite loops.
- **Transport errors** — `httpx.TimeoutException` and `httpx.HTTPError` are caught and re-raised as `ServerError` with a descriptive message.
- **max_results across pages** — `get_all_pages()` truncates results to exactly `max_results` even when the last fetched page contains extra items.
- **per-call timeout on post** — individual calls (e.g. upload) can override the session-level timeout via the `timeout` parameter on `post()`.

## Technical Notes
- HTTP client: `httpx` (async-first; `httpx.AsyncClient` used internally).
- `HttpSession` is an internal class (`_internal/http.py`); not part of the public API.
- Exceptions (`exceptions.py`) are public and re-exported from `easypaperless.__init__`.

---

## Tech Design (Solution Architect)
_To be added by /architecture_

## QA Test Results
**QA Date:** 2026-03-07
**Tester:** QA Engineer (automated + manual)
**Overall Verdict:** READY (with 1 Low bug)

### Acceptance Criteria Results

#### HttpSession
| # | Criterion | Result | Notes |
|---|-----------|--------|-------|
| 1 | `HttpSession(base_url, api_key, timeout=30.0)` — timeout configurable, defaults to 30s | PASS | Verified via manual test: default is 30.0, custom value accepted |
| 2 | Base URL normalized: trailing slashes stripped, `/api` appended | PASS | Verified `http://x.com/` -> `http://x.com/api`, `http://x.com///` -> `http://x.com/api` |
| 3 | All requests include `Authorization: Token {api_key}` header | PASS | Verified via `_get_client().headers` inspection |
| 4 | `close()` closes the underlying HTTP connection pool | PASS | Verified: sets `_client` to `None`, idempotent (double-close safe) |
| 5 | `request(method, path, *, params, json, data, files, timeout)` — generic request with per-call timeout | PASS | Signature verified; per-call timeout forwarded to httpx |
| 6 | Convenience methods: `get()`, `post()`, `patch()`, `delete()` | PASS | All four present, delegate to `request()` |
| 7 | `post()` exposes a `timeout` parameter | PASS | Signature: `post(self, path, *, json, data, files, timeout)` |
| 8 | `get_download()` follows redirects manually, re-attaching auth header (up to 5 hops) | PASS | Code review: uses `follow_redirects=False`, loops with `hops < 5`, re-issues via `client.request` which includes default auth headers |
| 9 | `get_all_pages(path, params, *, max_results, on_page)` — paginated fetch with cap and callback | PASS | Signature verified; behavior tested in 6 unit tests |

**HttpSession total: 9/9 PASS**

#### Exception Hierarchy
| # | Criterion | Result | Notes |
|---|-----------|--------|-------|
| 1 | `PaperlessError(message, status_code=None)` — base exception | PASS | Tested in `test_exceptions.py` |
| 2 | `AuthError` — raised on 401 or 403 | PASS | Tested via parametrized error mapping |
| 3 | `NotFoundError` — raised on 404 | PASS | Tested |
| 4 | `ValidationError` — raised on 422 | PASS | Tested |
| 5 | `ServerError` — raised on 5xx and transport errors | PASS | 500/503 tested; transport error mapping in code (TimeoutException, HTTPError -> ServerError) |
| 6 | `UploadError` — raised on task FAILURE | PASS | Class exists, tested in `test_exceptions.py` and `test_client_upload.py` |
| 7 | `TaskTimeoutError` — status_code always None | PASS | `__init__` hardcodes `status_code=None`; tested |
| 8 | All exceptions carry originating HTTP status code | PASS | Verified for all subclasses |

**Exception Hierarchy total: 8/8 PASS**

### Edge Cases

| # | Edge Case | Result | Notes |
|---|-----------|--------|-------|
| 1 | Trailing slash in base URL stripped before `/api` append | PASS | Multiple trailing slashes handled correctly |
| 2 | Non-JSON error responses — fallback to raw text | PASS | Code: `except Exception: detail = response.text` (line 49-50). Not unit-tested but code-reviewed as correct |
| 3 | Redirect strips auth header — `get_download()` re-issues requests | PASS | Uses `follow_redirects=False` + manual loop through `client.request()` which carries default headers |
| 4 | Redirect loop — aborts after 5 hops | PASS | `while resp.is_redirect and hops < 5` |
| 5 | Transport errors — TimeoutException and HTTPError caught as ServerError | PASS | Present in `request()`, `get_download()`, and `get_all_pages()` next-page fetcher |
| 6 | `max_results` across pages — truncates to exact count | PASS | 4 dedicated tests covering single-page trim, exact-page-size, cross-page, and no-limit |
| 7 | Per-call timeout on `post()` | PASS | Forwarded via `request(..., timeout=timeout)` |

**Edge Cases total: 7/7 PASS**

### Additional Findings (identified by QA)

| # | Finding | Notes |
|---|---------|-------|
| 1 | `get_download()` has zero unit test coverage | Lines 112-135 are entirely uncovered. Redirect logic, transport error handling within download, and the 5-hop limit are tested only by code review. |
| 2 | `post()`, `patch()`, `delete()` convenience methods have zero direct unit test coverage | Lines 146, 149, 152 uncovered. They are trivial delegations to `request()` and are exercised indirectly by higher-level tests. |
| 3 | Transport error paths in `request()` have zero unit test coverage | Lines 88-95 (TimeoutException, HTTPError catch blocks) are uncovered. |
| 4 | Non-JSON error body fallback has zero unit test coverage | Lines 49-50. |
| 5 | `on_page` callback in `get_all_pages()` is never tested | No test verifies the callback is invoked with correct `(fetched_count, total_count)` values. |

### Bugs Found

| # | Severity | Description | Location | Steps to Reproduce |
|---|----------|-------------|----------|-------------------|
| 1 | **Low** | Mypy strict-mode errors: `list[dict]` should be `list[dict[str, Any]]` | `src/easypaperless/_internal/http.py` lines 161, 162 | Run `mypy src/easypaperless/_internal/http.py` — reports 2 `[type-arg]` errors |

### Test Coverage Summary
- `exceptions.py`: **100%** coverage
- `_internal/http.py`: **67%** coverage (39 statements missed)
- Key untested areas: `get_download()`, transport error handling, non-JSON error fallback, `on_page` callback, convenience methods

### Regression Testing
- Full test suite (272 tests): **ALL PASSED**
- Ruff lint: **PASSED** (no issues)
- Mypy: **FAILED** (2 low-severity type-arg errors on http.py)

### Security Audit
- Auth header correctly attached to all requests via httpx default headers
- `get_download()` correctly re-attaches auth on cross-host redirects (security-positive design)
- Redirect loop protection in place (5-hop limit)
- No secrets logged (only status codes and paths in log messages)
- No hardcoded credentials found

### Production-Ready Decision
**READY** — No Critical or High severity bugs. The single Low bug (mypy type annotation) does not affect runtime behavior. Test coverage gaps exist but the untested code paths are straightforward delegations or have been verified by code review.

## Deployment
_To be added by /deploy_
