# [REFACTORING] Expand Sync Method Docstrings with Full Parameter Documentation

## Summary

Sync mixin methods currently contain docstrings that reference their async counterparts for parameter documentation (e.g. "See `<async_method>` for parameter details."). This approach is unreliable for AI coding agents and makes the public API harder to use without IDE cross-referencing. The fix is to replace those cross-references with the full, self-contained parameter documentation copied (and kept in sync) from the corresponding async methods.

---

## Current State

Every sync mixin in `src/easypaperless/_internal/sync_mixins/` contains docstrings that delegate parameter descriptions to the async counterpart. For example, a sync method may only document its return type and then say "See `AsyncDocumentsResource.list` for parameter descriptions." This means:

- Callers reading the sync API in isolation get no parameter information.
- AI coding agents that do not follow cross-references cannot infer what arguments a sync method accepts.
- The async and sync docstrings are not structurally parallel, making audits and updates error-prone.

---

## Desired State

Every public method in every sync mixin has a complete, self-contained docstring:

- The summary line and `Args:` block are identical in content to the corresponding async method's docstring.
- The `Returns:` and `Raises:` sections are present and accurate for the sync variant.
- No docstring in a sync mixin contains a cross-reference to an async method in place of parameter documentation.
- Async docstrings are reviewed and updated where they are found to be incomplete or inconsistent, so that both sides remain parallel.

---

## Motivation

- [x] Improve readability
- [x] Eliminate duplication of effort (the current approach shifts work onto the reader)
- [x] Align with current standards / conventions
- [ ] Improve maintainability
- [ ] Reduce complexity

---

## Scope

### In Scope

- All sync mixin files under `src/easypaperless/_internal/sync_mixins/`
- All public methods in those files that currently reference an async counterpart instead of documenting parameters directly
- Corresponding async mixin files under `src/easypaperless/_internal/mixins/` — reviewed and updated where their docstrings are incomplete or inconsistent with their sync counterparts

### Out of Scope

- Any functional or behavioral change to sync or async methods
- Docstrings of non-public (underscore-prefixed) methods
- Model classes, exceptions, or any code outside the mixin directories

---

## Risks & Considerations

- The only risk is a copy-paste error where a parameter description from the async side is transferred incorrectly or becomes stale after future async changes. A clear convention (keep both sides structurally identical) mitigates this.

---

## Acceptance Criteria

- [ ] Existing behavior is fully preserved (no functional changes).
- [ ] No sync mixin method docstring contains a cross-reference to an async method as a substitute for parameter documentation.
- [ ] Every public sync mixin method has an `Args:` block that lists and describes all parameters (excluding `self`).
- [ ] The `Args:` block of each sync method is content-equivalent to the `Args:` block of its async counterpart.
- [ ] All async mixin docstrings that were found incomplete are updated to be complete and consistent.
- [ ] `mypy`, `ruff`, and all existing tests pass without modification.

---

## Priority

`Medium`

---

## Additional Notes

- Related to the initial sync client implementation: issue #0016.
