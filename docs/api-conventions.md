# API Naming Conventions

Conventions for `PaperlessClient` method names and parameter names. Apply to all new and future resource features.

---

## Method Names

| Operation | Pattern | Example |
|-----------|---------|---------|
| List all | `list_{resource_plural}` | `list_tags`, `list_document_types` |
| Fetch one | `get_{resource_singular}` | `get_tag`, `get_document_type` |
| Create | `create_{resource_singular}` | `create_tag`, `create_document_type` |
| Update (PATCH) | `update_{resource_singular}` | `update_tag`, `update_document_type` |
| Delete | `delete_{resource_singular}` | `delete_tag`, `delete_document_type` |
| Bulk ops | `bulk_{action}` | `bulk_add_tag`, `bulk_delete` |

Resource names in method names follow the Python attribute form: `document_type` (not `documenttype` or `documentType`).

---

## Parameter Names

### Primary key
Always `id` — never `tag_id`, `document_id`, etc.

```python
async def get_tag(self, id: int) -> Tag: ...
async def update_tag(self, id: int, *, name: str | None = None) -> Tag: ...
```

### Sub-resource keys
When a method belongs to a nested resource, the parent key uses `{parent_singular}_id`. The sub-resource's own key uses `{resource_singular}_id`.

```python
async def get_notes(self, document_id: int) -> list[DocumentNote]: ...
async def delete_note(self, document_id: int, note_id: int) -> None: ...
```

### Standard list filter parameters
Every `list_*` method uses the same parameter names in the same order:

| Parameter | Type | Meaning |
|-----------|------|---------|
| `ids` | `list[int] \| None` | Filter to specific IDs |
| `name_contains` | `str \| None` | Case-insensitive substring match on `name` |
| `page` | `int \| None` | Fetch a single page (disables auto-pagination) |
| `page_size` | `int \| None` | Results per page |
| `ordering` | `str \| None` | Field name to sort by |
| `descending` | `bool` | Reverse sort direction (default `False`) |

Not all resources support all filters — only include the ones the API supports. Keep the order consistent when multiple are present.

### Document FK filter parameters
When filtering documents by a related resource:

| Semantic | Pattern | Type | Example |
|---------|---------|------|---------|
| Must match exactly one | `{resource_singular}` | `int \| str \| None` | `correspondent` |
| Must match any of | `any_{resource_plural}` | `list[int \| str] \| None` | `any_correspondents` |
| Must match none of | `exclude_{resource_plural}` | `list[int \| str] \| None` | `exclude_correspondents` |

All FK parameters accept either integer IDs or string names (resolved transparently).

> All FK filter parameters use the plural form (e.g. `any_tags`, not `any_tag`).

### Common field names

| Concept | Parameter name | Notes |
|---------|---------------|-------|
| Resource name | `name` | Always `name`, never `title` for resource labels |
| Document title | `title` | Documents have `title`, not `name` |
| Document creation date | `date` | ISO-8601 string `"YYYY-MM-DD"`, not `created` |
| Archive serial number | `archive_serial_number` | not some abbreviation |
| Auto-match pattern | `match` | |
| Match algorithm | `matching_algorithm` | Integer enum |
| Case-insensitive match | `is_insensitive` | |
| Owner user ID | `owner` | |
| Permission set | `set_permissions` | `SetPermissions` model |
