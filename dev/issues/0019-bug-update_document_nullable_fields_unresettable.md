# [BUG] None cannot express an explicit null value in update, create, upload, and list methods

## Summary
Across multiple client methods, `None` serves dual duty as both the default "not provided — skip this parameter" sentinel and as a semantically valid `null` value. This makes it impossible for callers to:
1. **Clear a nullable field** in update/create/upload methods (e.g. remove the owner from a document).
2. **Filter for records with no value set** in list methods (e.g. list documents that have no owner).

fields to consider: in all resources: owner, in documents: archive_serial_number, correspondent, document_type, storage_path


---

## Environment
- **Version / Release:** to be determined after issue 0018 is released
- **Python Version:** 3.11+
- **Paperless-ngx Version:** all supported versions
- **Other relevant context:** The pattern is present across all resource groups and is exacerbated by the resource-based API refactoring in issue 0018.

---

## Steps to Reproduce

### Scenario A — Cannot clear a nullable field
1. Assign an owner to a document in paperless-ngx.
2. Call `client.documents.update(document_id, owner=None)` intending to remove the owner.
3. Observe that the owner is unchanged — the `owner` field was silently omitted from the API request.

### Scenario B — Cannot filter for "no owner"
1. Have a mix of documents with and without an owner in paperless-ngx.
2. Call `client.documents.list(owner=None)` intending to retrieve only documents with no owner set.
3. Observe that the filter is ignored and all documents are returned.

---

## Expected Behavior
- When a parameter is **not passed** (or is passed as a dedicated sentinel such as `UNSET`), it is omitted from the API request / query string entirely, leaving the current value unchanged or not applying the filter.
- When a parameter is **explicitly set to `None`**, the value `null` (or its API equivalent, e.g. an empty filter) is sent to the API, clearing the field or filtering for records where the field is null.

---

## Actual Behavior
`None` is used as the default for all optional parameters, making it indistinguishable from an intentional `null`. Passing `owner=None` (or any other nullable parameter as `None`) silently skips the parameter, so:
- Nullable fields cannot be cleared via update/create/upload methods.
- List methods cannot filter for records where a nullable field is unset.

---

## Impact
- **Severity:** `High`
- **Affected Users / Systems:** Any caller of update, create, upload, or list methods that need to express an explicit `null` value for a nullable field. Affected resource groups include at minimum: documents, tags, correspondents, document types, storage paths, custom fields.

---

## Acceptance Criteria
- [ ] A dedicated sentinel value (e.g. `UNSET`) is introduced and used as the default for all nullable parameters across all affected methods. Only `UNSET` causes a parameter to be omitted from the API request.
- [ ] Passing `None` explicitly for a nullable parameter in an **update/create/upload** method results in `null` being sent in the API request body, clearing the field in paperless-ngx.
- [ ] Passing `None` explicitly for a nullable parameter in a **list** method results in the appropriate null filter being applied (e.g. `owner__isnull=true` or equivalent), returning only records where that field is unset.
- [ ] All affected methods in both the async client and the sync client are updated consistently.
- [ ] Existing tests are updated to reflect the new sentinel default.
- [ ] Regression tests verify that explicit `None` clears/filters correctly and that omitting a parameter leaves it unchanged/unfiltered.
- [ ] No unrelated functionality is broken.

---

## Out of Scope
- Changes to parameters that are non-nullable by nature (e.g. required IDs, boolean flags that cannot be null in the API).

---

## Additional Notes
- Pydantic's `PydanticUndefined` / `PydanticUndefinedType` or a custom module-level sentinel (`UNSET = object()`) are both valid implementation approaches; the choice is left to the implementer.
- A full audit of all method signatures across all resource groups should be performed to identify every affected parameter before implementing the fix.
- Related issues: [0005 – Update Document](0005-update-document.md), [0018 – Resource-Based Client API](018-refactoring-resource_based_client_api.md)
