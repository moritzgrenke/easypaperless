# [TASK] Add py.typed Marker File for PEP 561 Compliance

## Summary
The `easypaperless` package is missing a `py.typed` marker file as required by PEP 561. Without it, downstream tools like mypy treat the package as untyped and skip type analysis of its imports — even though the package ships full type annotations. This causes false negatives in projects that depend on `easypaperless`.

---

## Background / Context
A downstream project (an MCP server built on top of `easypaperless`) encountered mypy errors because the package was treated as untyped. PEP 561 specifies that a package signals its type-completeness by including an empty `py.typed` marker file in the package root. This file must also be included in the package distribution so it is present after installation.

References:
- https://peps.python.org/pep-0561/
- https://mypy.readthedocs.io/en/stable/running_mypy.html#missing-imports

---

## Objectives

- Add an empty `py.typed` file to `src/easypaperless/` (next to `__init__.py`).
- Ensure the file is included in the built distribution so it is present after `pip install`.

---

## Scope

### In Scope
- Creating `src/easypaperless/py.typed` (empty file).
- Updating `pyproject.toml` to include `py.typed` in the package data so it is distributed.

### Out of Scope
- Adding or modifying type annotations in the package source.
- Fixing type errors in downstream projects.

---

## Acceptance Criteria
- [ ] `src/easypaperless/py.typed` exists as an empty file.
- [ ] After `hatch build`, the built wheel contains `easypaperless/py.typed`.
- [ ] A project that depends on `easypaperless` and runs `mypy` no longer receives a "missing imports" or "untyped package" warning for `easypaperless`.

---

## Dependencies
None.

---

## Priority
`Medium`

---

## Additional Notes
- PEP 561 — https://peps.python.org/pep-0561/
- mypy docs on missing imports — https://mypy.readthedocs.io/en/stable/running_mypy.html#missing-imports

---

## QA

**Tested by:** QA Engineer
**Date:** 2026-03-15
**Commit:** 9db1cd1 (uncommitted working tree changes)

### Test Results

| # | Test Case | Expected | Actual | Status |
|---|-----------|----------|--------|--------|
| 1 | AC1: `src/easypaperless/py.typed` exists and is empty | File present, 0 bytes | File present, 0 bytes | ✅ Pass |
| 2 | AC2: Built wheel contains `easypaperless/py.typed` | `py.typed` found in wheel archive | `py.typed` present in `easypaperless-0.2.0-py3-none-any.whl` | ✅ Pass |
| 3 | AC3: mypy raises no "untyped package" warning when importing easypaperless | No mypy warning/error for missing types | `Success: no issues found in 1 source file` (tested with and without `--ignore-missing-imports`) | ✅ Pass |
| 4 | Regression: mypy passes on the package source itself | No mypy errors in `src/easypaperless/` | `Success: no issues found in 32 source files` | ✅ Pass |
| 5 | Regression: full test suite passes | 498 tests pass | 498 passed, 46 deselected (integration) | ✅ Pass |

### Bugs Found

None.

### Automated Tests
- Suite: pytest — 498 passed, 46 deselected (integration tests excluded by default)
- No failures.

### Summary
- ACs tested: 3/3
- ACs passing: 3/3
- Bugs found: 0
- Recommendation: ✅ Ready to merge
