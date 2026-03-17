# [REFACTORING] Rename `api_key` Parameter to `api_token` in Clients and Scripts

## Summary
The constructor parameter used to supply a Paperless-ngx API token is currently named `api_key` across `PaperlessClient`, `SyncPaperlessClient`, the internal `HttpSession`, and usage examples. The paperless-ngx API uses token-based authentication; the correct and more descriptive name is `api_token`. This rename makes the public API self-documenting and consistent with paperless-ngx terminology.

---

## Current State
- `PaperlessClient.__init__` accepts `api_key: str`
- `SyncPaperlessClient.__init__` accepts `api_key: str`
- `HttpSession.__init__` accepts `api_key: str` and stores it as `self._api_key`
- All usage examples in `scripts/` (excluding `cli.py`) and docstring examples use `api_key=`

---

## Desired State
- All three `__init__` signatures use `api_token: str` instead of `api_key`
- Internal storage in `HttpSession` is renamed accordingly
- All docstring examples, inline comments, and usage scripts (excluding `cli.py`) are updated to use `api_token=`
- Public behaviour is completely unchanged — only the parameter name differs

---

## Motivation
- [x] Improve readability
- [x] Align with current standards / conventions

---

## Scope

### In Scope
- `src/easypaperless/client.py` — `PaperlessClient.__init__` parameter and docstring example
- `src/easypaperless/sync.py` — `SyncPaperlessClient.__init__` parameter and docstring example
- `src/easypaperless/_internal/http.py` — `HttpSession.__init__` parameter and internal attribute
- `src/easypaperless/resources.py` — docstring usage example
- `scripts/` — all example scripts except `cli.py`

### Out of Scope
- `scripts/cli.py` — must not be touched
- Any HTTP header values or runtime behaviour
- Test files (unless they directly test the parameter name)

---

## Risks & Considerations
- **Breaking change for existing users:** Any caller passing `api_key=` as a keyword argument will break. This should be noted prominently in the changelog as a breaking change for the next release.
- The rename must be applied consistently across all three layers (`client.py`, `sync.py`, `http.py`) to avoid internal mismatches.

---

## Acceptance Criteria
- [ ] Existing behavior is fully preserved (no functional changes).
- [ ] `PaperlessClient(url=..., api_token=...)` works; `api_key=` is no longer accepted.
- [ ] `SyncPaperlessClient(url=..., api_token=...)` works; `api_key=` is no longer accepted.
- [ ] `HttpSession` internally uses `api_token` / `_api_token` consistently.
- [ ] All docstring examples across `client.py`, `sync.py`, `http.py`, and `resources.py` use `api_token=`.
- [ ] All scripts in `scripts/` (except `cli.py`) use `api_token=`.
- [ ] `cli.py` is untouched.
- [ ] `ruff check` and `mypy` pass with no new errors.

---

## Priority
`Medium`

---

## Additional Notes
- Breaking change — must be mentioned in CHANGELOG under the next release version.

---

## QA

**Tested by:** QA Engineer
**Date:** 2026-03-17
**Commit:** working tree (post-implementation, pre-commit)

### Test Results

| # | Test Case | Expected | Actual | Status |
|---|-----------|----------|--------|--------|
| 1 | AC1: Existing behavior preserved (no functional changes) | All 573 tests pass | 573 passed, 46 deselected | ✅ Pass |
| 2 | AC2: `PaperlessClient(url=..., api_token=...)` works; `api_key=` rejected | `api_token=` accepted, `api_key=` raises `TypeError` | `api_token` in signature; `api_key=` raises `TypeError: unexpected keyword argument 'api_key'. Did you mean 'api_token'?` | ✅ Pass |
| 3 | AC3: `SyncPaperlessClient(url=..., api_token=...)` works; `api_key=` rejected | `api_token=` accepted, `api_key=` raises `TypeError` | `api_token` in signature; `api_key=` raises `TypeError` | ✅ Pass |
| 4 | AC4: `HttpSession` uses `api_token` / `_api_token` internally | Parameter named `api_token`, stored as `self._api_token`, used in auth header | Confirmed via diff and introspection | ✅ Pass |
| 5 | AC5: Docstring examples in `client.py`, `sync.py`, `http.py`, `resources.py` use `api_token=` | All docstring examples updated | Updated in `client.py`, `sync.py`, `resources.py` — `http.py` has no public docstring example (internal class) | ✅ Pass |
| 6 | AC6: All scripts in `scripts/` (except `cli.py`) use `api_token=` | `api_token=` in all non-cli scripts | `mg_quickstart_test.py` and `mg_quickstart_test_sync.py` both updated to `api_token=` | ✅ Pass |
| 7 | AC7: `cli.py` is untouched | No diff for `cli.py` | `git diff HEAD -- scripts/cli.py` produces empty output | ✅ Pass |
| 8 | AC8: `ruff check` and `mypy` pass | No new errors | Both pass cleanly | ✅ Pass |
| 9 | Edge: No remaining `api_key` references in src/, scripts/, tests/ (excluding cli.py) | Zero matches | `grep -rn "api_key"` returns no results | ✅ Pass |
| 10 | Edge: `mg_quickstart_test_sync.py` still contains hardcoded real URL and token value | Placeholders like async version | URL and token value are real/hardcoded (`d69b3da4...`), unlike async version which uses `"your url"` / `"your token"` | ❌ Fail |

### Bugs Found

#### BUG-001 — `mg_quickstart_test_sync.py` retains hardcoded credentials [Severity: Low] ✅ Fixed
**Steps to reproduce:**
1. Open `scripts/mg_quickstart_test_sync.py`
2. Compare with `scripts/mg_quickstart_test.py`

**Expected:** Both scripts use placeholder values for URL and token (as the async version does: `"your url"`, `"your token"`)
**Actual:** The sync script still contains a hardcoded real IP address (`http://192.168.178.86:8100`) and a real-looking API token string (`d69b3da4dfd61dec7c60110bdae16637ced2b013`) — the rename changed only the variable name from `api_key` to `api_token` but did not redact the value
**Severity:** Low
**Notes:** Fixed — `mg_quickstart_test_sync.py` now uses `"your url"` and `"your token"` placeholders, consistent with the async script.

### Automated Tests
- Suite: `pytest tests/` — 573 passed, 46 deselected (integration tests skipped)
- Failed: None

### Summary
- ACs tested: 8/8
- ACs passing: 8/8
- Bugs found: 1 (Critical: 0, High: 0, Medium: 0, Low: 1)
- Recommendation: ✅ Ready to merge (BUG-001 fixed)
