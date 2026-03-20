# [FEATURE] Users Resource CRUD

## Summary

Add a `users` resource to both the async `PaperlessClient` and the sync `SyncPaperlessClient`, exposing full CRUD operations (`list`, `get`, `create`, `update`, `delete`) against the `/api/users/` and `/api/users/{id}/` endpoints. Also introduce a `PaperlessPermission` literal type enumerating all known Paperless permission strings to support type-safe, efficient permission checks on user objects.

---

## Problem Statement

There is currently no way for easypaperless users to manage Paperless system users programmatically. A common use case is querying a user's effective permissions (direct + inherited) to conditionally enable or disable application functionality. Without a typed permission vocabulary, callers must rely on raw strings that are easy to mistype and hard to discover.

---

## Proposed Solution

Expose a `users` resource on both clients, following the same resource-based pattern used by `tags`, `correspondents`, etc.

Introduce a `User` Pydantic model capturing all API response fields. Add a `PaperlessPermission` type alias (`Literal[...]`) that enumerates every known permission string, enabling type-safe permission comparisons and IDE autocompletion.

All mutable parameters in `update()` must default to `UNSET` so that only explicitly supplied fields are included in the PATCH request body — consistent with the existing UNSET/None semantics in the codebase.

---

## User Stories

- As a Python developer, I want to list, create, update, and delete Paperless users so that I can manage user accounts programmatically.
- As a Python developer, I want to retrieve a single user by ID so that I can inspect their profile and permission set.
- As a Python developer, I want to check whether a user has a specific permission (direct or inherited) so that I can gate application functionality based on their access rights.
- As a Python developer, I want IDE autocompletion and static type checking for permission strings so that I avoid typos and discover available permissions easily.

---

## Scope

### In Scope

- `User` Pydantic model with all fields from the API response schema (see below)
- `PaperlessPermission` — a `Literal[...]` type alias enumerating all known Paperless permission strings (full list provided in Additional Notes)
- `users.list()` — GET `/api/users/` with parameters: `username_contains`, `username_exact`, `ordering`, `page`, `page_size`; returns `PagedResult[User]`
- `users.get(id)` — GET `/api/users/{id}/`; returns `User`
- `users.create(...)` — POST `/api/users/`; accepts all writable fields; returns `User`
- `users.update(id, ...)` — PATCH `/api/users/{id}/`; all parameters default to `UNSET`; returns `User`
- `users.delete(id)` — DELETE `/api/users/{id}/`; returns `None`
- Async mixin (`_internal/mixins/users.py`) and sync mixin (`_internal/sync_mixins/users.py`)
- `User` model exported from `easypaperless.models` and via the top-level `__init__.py`
- `PaperlessPermission` exported from `easypaperless.models` and via the top-level `__init__.py`
- Integration of the `users` resource into `PaperlessClient` and `SyncPaperlessClient`
- Unit tests covering all five methods (mocked HTTP) for both async and sync variants

### Out of Scope

- Group management (`/api/groups/`)
- Permission assignment beyond what the PATCH endpoint supports
- Helper methods on `User` for permission checking (e.g., `.has_permission()`) — callers use `PaperlessPermission` with standard `in` checks against `user_permissions` / `inherited_permissions`
- MFA management

---

## Data Model

### `User` model fields

| Field | Type | Writable | Notes |
|---|---|---|---|
| `id` | `int` | No | Set by API |
| `username` | `str` | Yes | Required on create |
| `email` | `str` | Yes | |
| `password` | `str` | Yes | Write-only in practice; returned by API |
| `first_name` | `str` | Yes | |
| `last_name` | `str` | Yes | |
| `date_joined` | `datetime` | Yes | |
| `is_staff` | `bool` | Yes | |
| `is_active` | `bool` | Yes | |
| `is_superuser` | `bool` | Yes | |
| `groups` | `list[int]` | Yes | List of group IDs |
| `user_permissions` | `list[str]` | Yes | Direct permission strings |
| `inherited_permissions` | `list[str]` | No | Effective inherited permissions (read-only) |
| `is_mfa_enabled` | `bool` | No | Read-only |

### `users.list()` parameters

| Parameter | Type | API query param |
|---|---|---|
| `username_contains` | `str \| UnsetType` | `username__icontains` |
| `username_exact` | `str \| UnsetType` | `username__iexact` |
| `ordering` | `str \| UnsetType` | `ordering` |
| `page` | `int \| UnsetType` | `page` |
| `page_size` | `int \| UnsetType` | `page_size` |

### `users.create()` required / optional parameters

`username` is required. All other writable fields are optional and default to `UNSET`.

### `users.update()` parameters

All parameters (except `id`) default to `UNSET`. Only fields with a non-UNSET value are included in the PATCH request body.

---

## Acceptance Criteria

- [ ] `User` Pydantic model exists in `src/easypaperless/models/` with all fields typed correctly, including `inherited_permissions: list[str]` and `is_mfa_enabled: bool` as read-only (not writable via `create`/`update`).
- [ ] `PaperlessPermission` is a `Literal[...]` type alias covering every permission string listed in Additional Notes, exported from `easypaperless.models` and `easypaperless`.
- [ ] `users.list()` sends GET `/api/users/` with correct query parameters and returns `PagedResult[User]`.
- [ ] `users.list()` omits any parameter that is `UNSET` from the request.
- [ ] `users.get(id)` sends GET `/api/users/{id}/` and returns a `User`.
- [ ] `users.create(...)` sends POST `/api/users/` with all provided (non-UNSET) fields and returns a `User`.
- [ ] `users.update(id, ...)` sends PATCH `/api/users/{id}/` containing only non-UNSET fields and returns a `User`.
- [ ] `users.update(id, ...)` with all parameters left as `UNSET` sends an empty body `{}`.
- [ ] `users.delete(id)` sends DELETE `/api/users/{id}/` and returns `None`.
- [ ] All five methods exist on both `PaperlessClient.users` (async) and `SyncPaperlessClient.users` (sync).
- [ ] `User`, `PaperlessPermission` are importable directly from `easypaperless`.
- [ ] Unit tests cover `list`, `get`, `create`, `update`, `delete` for both async and sync clients using mocked HTTP responses.
- [ ] `mypy --strict` passes with no new errors.
- [ ] `ruff check` passes with no new errors.

---

## Dependencies & Constraints

- Follows the UNSET/None pattern established in issue #0028.
- Must return `PagedResult[User]` from `list()`, consistent with issue #0029.
- The `password` field appears in API responses but is effectively write-only in real Paperless deployments. The model must include it as an optional `str` field since the API does return it.
- `PaperlessPermission` is a documentation and type-safety aid; the actual permission strings come from the API at runtime. The `Literal` type does not need to be exhaustive for the code to work, but should include the full known list.

---

## Priority

`Medium`

---

## Additional Notes

### Known Paperless Permission Strings

```python
"documents.change_uisettings", "paperless_mail.delete_mailrule",
"guardian.delete_groupobjectpermission", "authtoken.change_token",
"account.delete_emailconfirmation", "admin.delete_logentry",
"socialaccount.delete_socialtoken", "contenttypes.add_contenttype",
"paperless.change_applicationconfiguration",
"django_celery_results.delete_taskresult", "documents.add_workflowrun",
"documents.change_sharelink", "authtoken.view_token",
"documents.view_document", "django_celery_results.add_groupresult",
"documents.change_correspondent", "paperless_mail.add_mailrule",
"socialaccount.change_socialtoken", "paperless_mail.change_processedmail",
"auth.change_user", "documents.change_document",
"contenttypes.delete_contenttype", "documents.delete_uisettings",
"documents.change_savedviewfilterrule", "documents.add_customfieldinstance",
"documents.view_documenttype", "mfa.add_authenticator",
"account.view_emailconfirmation", "documents.add_storagepath",
"documents.change_storagepath", "socialaccount.add_socialapp",
"django_celery_results.view_taskresult", "documents.add_workflowactionwebhook",
"documents.delete_workflowrun", "documents.delete_workflowactionwebhook",
"documents.change_workflowactionwebhook", "documents.add_sharelink",
"documents.delete_customfieldinstance", "mfa.delete_authenticator",
"authtoken.delete_tokenproxy", "paperless_mail.change_mailrule",
"documents.change_workflow", "socialaccount.delete_socialapp",
"documents.delete_tag", "socialaccount.change_socialaccount",
"documents.add_savedview", "documents.view_paperlesstask",
"documents.view_workflowactionwebhook", "paperless_mail.add_mailaccount",
"socialaccount.view_socialaccount", "guardian.add_groupobjectpermission",
"contenttypes.view_contenttype", "documents.add_workflowtrigger",
"documents.change_log", "django_celery_results.add_chordcounter",
"documents.view_savedviewfilterrule", "auth.view_permission",
"authtoken.view_tokenproxy", "guardian.view_groupobjectpermission",
"documents.change_workflowaction", "documents.view_savedview",
"django_celery_results.change_groupresult",
"django_celery_results.change_chordcounter",
"documents.delete_savedviewfilterrule",
"paperless.add_applicationconfiguration",
"django_celery_results.view_chordcounter",
"guardian.view_userobjectpermission", "documents.view_workflowactionemail",
"paperless.view_applicationconfiguration", "documents.add_savedviewfilterrule",
"documents.view_uisettings", "django_celery_results.delete_chordcounter",
"documents.view_correspondent", "documents.delete_sharelink",
"documents.delete_customfield", "authtoken.delete_token",
"documents.view_tag", "django_celery_results.view_groupresult",
"documents.view_storagepath", "guardian.change_userobjectpermission",
"mfa.view_authenticator", "documents.change_workflowrun",
"socialaccount.delete_socialaccount", "auth.change_group",
"documents.add_workflowaction", "documents.delete_workflowaction",
"admin.view_logentry", "paperless_mail.view_processedmail",
"documents.view_workflowrun", "authtoken.change_tokenproxy",
"documents.change_documenttype", "paperless_mail.delete_processedmail",
"guardian.change_groupobjectpermission", "socialaccount.view_socialapp",
"documents.view_workflow", "documents.change_note",
"paperless.delete_applicationconfiguration", "paperless_mail.view_mailrule",
"account.add_emailaddress", "documents.add_correspondent",
"documents.add_tag", "authtoken.add_tokenproxy", "auditlog.add_logentry",
"documents.delete_documenttype", "account.change_emailconfirmation",
"documents.delete_correspondent", "django_celery_results.add_taskresult",
"sessions.change_session", "sessions.delete_session",
"documents.delete_workflowactionemail", "documents.view_note",
"auth.add_user", "auth.add_group", "documents.delete_paperlesstask",
"documents.add_note", "documents.delete_note", "documents.change_customfield",
"paperless_mail.delete_mailaccount", "documents.add_customfield",
"contenttypes.change_contenttype", "admin.change_logentry",
"paperless_mail.view_mailaccount", "sessions.view_session",
"auditlog.view_logentry", "socialaccount.add_socialtoken",
"documents.delete_workflow", "django_celery_results.delete_groupresult",
"auth.delete_permission", "auth.delete_user", "mfa.change_authenticator",
"documents.view_customfield", "account.view_emailaddress", "auth.view_group",
"documents.view_log", "documents.delete_workflowtrigger",
"documents.view_workflowaction", "socialaccount.change_socialapp",
"documents.delete_document", "documents.view_workflowtrigger",
"documents.change_tag", "auth.view_user", "documents.add_log",
"documents.delete_log", "auth.add_permission", "documents.add_document",
"documents.view_customfieldinstance", "account.delete_emailaddress",
"paperless_mail.add_processedmail", "sessions.add_session",
"account.change_emailaddress", "admin.add_logentry",
"guardian.add_userobjectpermission", "django_celery_results.change_taskresult",
"socialaccount.view_socialtoken", "documents.add_workflow",
"documents.change_customfieldinstance", "auth.change_permission",
"documents.change_workflowactionemail", "documents.delete_storagepath",
"documents.change_workflowtrigger", "documents.change_paperlesstask",
"documents.add_workflowactionemail", "documents.add_paperlesstask",
"authtoken.add_token", "socialaccount.add_socialaccount",
"documents.delete_savedview", "paperless_mail.change_mailaccount",
"auth.delete_group", "documents.change_savedview",
"documents.add_documenttype", "documents.add_uisettings",
"documents.view_sharelink", "auditlog.change_logentry",
"account.add_emailconfirmation", "auditlog.delete_logentry",
"guardian.delete_userobjectpermission"
```

### Permission Check Usage Example

```python
from easypaperless import PaperlessPermission

user = await client.users.get(1)
all_perms = set(user.user_permissions) | set(user.inherited_permissions)
can_view_docs = "documents.view_document" in all_perms  # type-safe via PaperlessPermission
```

---

## QA

**Tested by:** QA Engineer
**Date:** 2026-03-20
**Commit:** adf7579

### Test Results

| # | Test Case | Expected | Actual | Status |
|---|-----------|----------|--------|--------|
| 1 | AC: `User` model exists with all typed fields | All fields typed correctly; `inherited_permissions` and `is_mfa_enabled` present as read-only | Model exists in `models/users.py` with correct types; `extra="ignore"` config present | ✅ Pass |
| 2 | AC: `PaperlessPermission` Literal covers all 176 known strings | All spec permission strings present in type alias | Implementation has exactly 176 entries, zero discrepancies vs. spec | ✅ Pass |
| 3 | AC: `PaperlessPermission` exported from `easypaperless.models` and `easypaperless` | Importable at both paths | `from easypaperless import PaperlessPermission` ✅; `from easypaperless.models import PaperlessPermission` ✅ | ✅ Pass |
| 4 | AC: `users.list()` sends GET `/api/users/` with correct query params | Correct parameter names (`username__icontains`, `username__iexact`, `ordering`, `page`, `page_size`) | Verified in `test_users_list_with_filters` | ✅ Pass |
| 5 | AC: `users.list()` omits UNSET params | No query params sent when all args are UNSET | `test_users_list_unset_params_omitted` verifies empty params dict | ✅ Pass |
| 6 | AC: `users.list()` returns `PagedResult[User]` | Returns `PagedResult[User]` | `test_users_list` confirms `result.count` and `result.results[0]` is `User` | ✅ Pass |
| 7 | AC: `users.get(id)` sends GET `/api/users/{id}/` and returns `User` | Correct URL, returns `User` | `test_users_get` passes; URL `/users/1/` correctly routed | ✅ Pass |
| 8 | AC: `users.create()` sends POST with non-UNSET fields only | Only provided fields in payload; `username` always present | `test_users_create` and `test_users_create_only_username` verify | ✅ Pass |
| 9 | AC: `users.update()` sends PATCH with non-UNSET fields only | Partial payload with only provided fields | `test_users_update` verifies partial body | ✅ Pass |
| 10 | AC: `users.update()` with all UNSET sends empty body `{}` | Body is `{}` | `test_users_update_empty_body` passes | ✅ Pass |
| 11 | AC: `users.delete(id)` sends DELETE and returns `None` | DELETE `/api/users/{id}/`, returns `None` | `test_users_delete` passes | ✅ Pass |
| 12 | AC: All five methods on both `PaperlessClient.users` (async) and `SyncPaperlessClient.users` (sync) | Both clients expose `list`, `get`, `create`, `update`, `delete` | All sync/async tests pass; resource types confirmed | ✅ Pass |
| 13 | AC: `User` importable from `easypaperless` | `from easypaperless import User` works | `test_user_importable_from_easypaperless` passes | ✅ Pass |
| 14 | AC: Unit tests cover all 5 methods for both async and sync | 10 method-specific tests + model and export tests | 21 tests total, all passing | ✅ Pass |
| 15 | AC: `mypy --strict` passes with no new errors | No mypy errors | `mypy src/easypaperless/` → "Success: no issues found in 36 source files" | ✅ Pass |
| 16 | AC: `ruff check` passes | No ruff errors | "All checks passed!" | ✅ Pass |
| 17 | Edge: `username_exact` filter parameter sent correctly | `username__iexact` appears in query params | Not covered by a dedicated test — `test_users_list_with_filters` only exercises `username_contains`; the mapping in source code is correct though | ⚠️ Low |
| 18 | Regression: Full test suite (611 tests) passes | No regressions | 611 passed, 47 deselected (integration tests) | ✅ Pass |

### Bugs Found

#### BUG-001 — `username_exact` filter not covered by tests [Severity: Low] ✅ Fixed

**Steps to reproduce:**
1. Open `tests/test_client_users.py`
2. Inspect `test_users_list_with_filters` — it calls `client.users.list(username_contains="ali", ordering="username", page=1, page_size=10)`.
3. Notice `username_exact` is never passed in any test.

**Expected:** A test verifying that `username_exact="alice"` results in `username__iexact=alice` in the request query params.
**Actual:** The `username__iexact` mapping exists in source code and is correct, but there is no test exercising it.
**Severity:** Low
**Notes:** Implementation is correct; this is a test coverage gap only.
**Fix:** `test_users_list_username_exact_filter` added to `tests/test_client_users.py`.

### Automated Tests
- Suite: `tests/test_client_users.py` — 21 passed, 0 failed
- Suite: Full test suite — 611 passed, 0 failed, 47 deselected (integration markers)

### Summary
- ACs tested: 13/13
- ACs passing: 13/13
- Bugs found: 1 (Critical: 0, High: 0, Medium: 0, Low: 1)
- Recommendation: ✅ Ready to merge
