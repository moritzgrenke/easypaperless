# [FEATURE] Optional Retry-with-Backoff Support for Transient Network/Proxy Errors

## Summary

Add configurable retry-with-exponential-backoff to `HttpSession` so the client can
automatically recover from transient infrastructure errors (proxy resets, connection
drops, timeouts) without requiring callers to implement their own retry wrappers.

---

## Problem Statement

When Paperless-ngx is deployed behind a reverse proxy (e.g. Synology DSM), bulk
operations issued in rapid succession can cause the proxy to close or reset the
connection. The proxy returns an HTML error page instead of a valid API response.
This manifests as two concrete problems:

1. **Misleading exception type.** `_raise_for_status` maps every HTTP 404 to
   `NotFoundError`. A proxy-generated 404 page is indistinguishable from a genuine
   "document not found" 404. Callers cannot determine whether retrying is safe.

2. **No built-in retry.** The library makes exactly one attempt per request. A single
   transient failure aborts the entire operation, even though reissuing the same
   request seconds later would succeed. Users currently must wrap every call in a
   manual retry helper.

---

## Proposed Solution

Expose optional retry parameters on both `PaperlessClient` and `SyncPaperlessClient`.
When configured, `HttpSession` automatically retries failed requests with exponential
backoff before propagating the exception. Retry behaviour must be opt-in; the default
is zero retries to preserve the current behaviour exactly.

The parameters available at client construction time:

- `retry_attempts` (int, default `0`) — maximum number of retry attempts after the
  first failure. `0` means no retry.
- `retry_backoff` (float, default `1.0`) — initial sleep in seconds between attempts;
  doubles on each subsequent attempt.
- `retry_on` (tuple of exception types, default covers `ServerError`,
  `httpx.TimeoutException`, `httpx.ConnectError`) — exception types that trigger a
  retry. `NotFoundError` (real API 404) must **not** be in the default set.

As an alternative to the above parameters, the client may also accept a pre-configured
`tenacity.Retrying` / `tenacity.AsyncRetrying` instance directly, keeping the library
itself dependency-free for users who do not need tenacity.

---

## User Stories

- As a developer running bulk operations against a Paperless-ngx instance behind a
  reverse proxy, I want the client to automatically retry on transient connection
  errors so that my scripts do not abort due to occasional proxy hiccups.
- As a developer, I want retry to be disabled by default so that existing code is not
  silently affected.
- As a developer, I want to configure which exception types trigger a retry so that
  genuine errors (e.g. `NotFoundError`) are never silently retried.
- As a developer, I want a clear and actionable exception message when all retries are
  exhausted so that I can diagnose the root cause without having to parse raw HTML
  output.

---

## Scope

### In Scope
- `retry_attempts`, `retry_backoff`, `retry_on` parameters on `PaperlessClient` and
  `SyncPaperlessClient`.
- Retry loop implemented inside `HttpSession.request` (async) and its sync counterpart.
- Optional acceptance of a `tenacity.Retrying` / `tenacity.AsyncRetrying` instance as
  an alternative to the individual parameters.
- A dedicated `RetryExhaustedError` exception (subclass of the existing exception
  hierarchy) raised when all retry attempts are spent, carrying: attempt count, the
  URL that was requested, and the last underlying exception as `__cause__`.
- Suppression of raw response bodies (e.g. HTML error pages) from exception messages;
  the response body may be included only as a truncated hint (≤ 200 chars) with a note
  that it may be a proxy-generated page.
- Documentation of the new parameters in client docstrings.

### Out of Scope
- Changing which HTTP status codes map to which exception types (existing behaviour
  preserved).
- Per-method retry overrides (client-level configuration only).
- Automatic detection or classification of proxy-generated error pages.
- Adding `tenacity` as a mandatory dependency.

---

## Acceptance Criteria
- [ ] `PaperlessClient(retry_attempts=0)` behaves identically to the current client
      (no retry, no sleep).
- [ ] When `retry_attempts=N` and a configured exception is raised, the client retries
      up to N times with exponential backoff before propagating the exception.
- [ ] `NotFoundError` is not retried when using the default `retry_on` set.
- [ ] The retry attempt count and backoff delay are logged at DEBUG level on each
      retry.
- [ ] Both async (`PaperlessClient`) and sync (`SyncPaperlessClient`) clients support
      the retry parameters.
- [ ] Passing a `tenacity.Retrying` instance instead of individual parameters works
      correctly for the sync client, and a `tenacity.AsyncRetrying` instance works for
      the async client.
- [ ] When all retry attempts are exhausted, a `RetryExhaustedError` is raised. Its
      message clearly states the number of attempts made and the target URL, and the
      last underlying exception is attached as `__cause__`.
- [ ] Exception messages never contain raw HTML. If the response body appears to be
      HTML, it is replaced with a short human-readable note (e.g. "response body
      appears to be an HTML page — this may indicate a proxy or gateway error") plus at
      most a 200-character truncated excerpt.
- [ ] All existing tests pass without modification.
- [ ] New unit tests verify: zero retries (default), successful retry after one
      failure, exhaustion of retries raising `RetryExhaustedError`, non-retriable
      exception types, and HTML body suppression in the raised exception.

---

## Dependencies & Constraints

- `tenacity` support is optional and must not be a mandatory dependency.
- Must remain compatible with the existing `httpx`-based `HttpSession`.
- The async retry loop must not block the event loop (use `asyncio.sleep`).

---

## Priority
`Medium`

---

## Additional Notes

- Related issue: #0033 (proxy HTTPS scheme bug) — same environment class, different
  root cause.
- Prior art: `urllib3.util.Retry`, `tenacity`, `httpx.HTTPTransport(retries=...)`.
- User-side workaround until resolved: wrap bulk calls in a manual retry loop.
