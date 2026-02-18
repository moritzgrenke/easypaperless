## Project
`easypaperless` — a Python API wrapper for paperless-ngx with an optional SQLite-backed DocumentStore for local caching and extended search.

```python
from easypaperless import PaperlessClient, DocumentStore
```

## Architecture

### HTTP Client
- HTTP client: `httpx` (async-first)
- Auth: API key via `Authorization: Token <key>` header, passed in constructor, never hardcoded
- Base URL comes from constructor, never hardcoded
- All responses mapped to Pydantic v2 models
- Error handling: custom exception hierarchy in `exceptions.py`
- No global state; client is always explicitly instantiated

### Sync vs Async
- Core implementation is **async** (`PaperlessClient`)
- A thin **`SyncPaperlessClient`** wrapper exposes the same interface synchronously via `asyncio.run()`
- Both are exported from the top-level package

### API Style — Flat Client Methods
All operations are flat methods on the client. No resource sub-objects.

```python
client = PaperlessClient(url="https://my.server", api_key="...")

doc   = await client.get_document(42)
docs  = await client.list_documents()
await client.update_document(42, title="New Title", tags=["invoice", "bank"])
await client.delete_document(42)

tags  = await client.list_tags()
tag   = await client.get_tag(7)
await client.create_tag(name="urgent")

task  = await client.upload_document("scan.pdf", title="April Invoice")
# optionally poll until processed:
doc   = await client.upload_document("scan.pdf", wait=True)
```

### Parameter Simplification — Name/ID Resolution
- All parameters that the raw API requires as integer IDs also accept **string names**
- The client resolves names to IDs internally (e.g. `tags=["invoice"]` → `tags=[3]`)
- Resolution happens lazily and is cached for the lifetime of the client instance
- Explicit integer IDs always work as-is

### Parameter Simplification — Naming
Simplified parameter names used throughout the client (raw API names in parentheses):

| Client parameter | Raw API parameter |
|---|---|
| `date` | `created` |
| `document_type` | `document_type` (accepts name or ID) |
| `asn` | `archive_serial_number` |
| `tags` | `tags__id__all` (has all of these, accepts names or IDs) |
| `any_tag` | `tags__id__in` |
| `exclude_tags` | `tags__id__none` |
| `correspondent` | `correspondent__id__in` (accepts name or ID) |
| `created_after` | `created__date__gt` |
| `created_before` | `created__date__lt` |

### Parameter Simplification — Search
`list_documents()` accepts `search=` and `search_mode=`:

| `search_mode` | Searches | Raw API param |
|---|---|---|
| `"title"` | title only (contains, case-insensitive) | `title__icontains` |
| `"title_or_text"` | title + OCR content | `search` (Whoosh FTS) |
| `"query"` | raw paperless query language | `query` |

Default `search_mode` is `"title_or_text"`.

```python
client.list_documents(search="invoice", search_mode="title_or_text")
client.list_documents(search="tag:invoice date:[2024 TO *]", search_mode="query")
```

### Covered Resources
All standard paperless-ngx API resources:
- Documents (get, list, update, delete, download, upload, bulk_edit)
- Bulk object edits (bulk_edit_objects)
- Tags (get, list, create, update, delete)
- Correspondents (get, list, create, update, delete)
- Document Types (get, list, create, update, delete)
- Storage Paths (get, list, create, update, delete)
- Custom Fields (get, list, create, update, delete)

### Upload with Processing Poll
- `upload_document(file, ...)` submits the file and returns a task ID immediately
- With `wait=True`, it polls the task status endpoint until processing completes and returns the resulting `Document`
- Polling interval and timeout are configurable

### DocumentStore (SQLite Cache)
- `DocumentStore` is a separate class, backed by SQLite
- It wraps a `PaperlessClient` and mirrors document metadata locally
- Sync is **manual/explicit**: call `store.sync()` to pull fresh data from the server
- Supports extended search not possible via the API (regex, date ranges, name-based filters)
- Search interface TBD — will be specified before implementation

### Error Handling
Custom exception hierarchy in `exceptions.py`:

```
PaperlessError               # base
├── AuthError                # 401, 403
├── NotFoundError            # 404
├── ValidationError          # 422 / bad input
├── ServerError              # 5xx
├── UploadError              # file submission failed
└── TaskTimeoutError         # upload poll exceeded timeout
```

## Structure

```
easypaperless/
├── __init__.py          # exports PaperlessClient, SyncPaperlessClient, DocumentStore
├── client.py            # async PaperlessClient
├── sync.py              # SyncPaperlessClient (asyncio.run wrapper)
├── store.py             # DocumentStore (SQLite)
├── models/
│   ├── __init__.py
│   ├── documents.py
│   ├── tags.py
│   ├── correspondents.py
│   ├── document_types.py
│   ├── storage_paths.py
│   └── custom_fields.py
├── exceptions.py
└── _internal/
    ├── http.py          # httpx session, auth header, request helpers
    └── resolvers.py     # name-to-ID resolution and caching
tests/
pyproject.toml
```

## Conventions
- All code, comments, and documentation strictly in **English** — even if prompts are written in German
- Async functions use `async def`; the sync wrapper in `sync.py` must never contain business logic
- Pydantic models are defined for all API responses; no raw dicts exposed to the user
- Name resolution must be transparent — callers should not need to know whether they passed a name or an ID
- Internal helpers and modules are prefixed with `_` (e.g. `_internal/`)
- `update_*` methods use `PATCH` (partial update); never `PUT`
- Tests go in `tests/`, mirroring the package structure

## Environment
- Always use the project's `venv` for installing packages and running tests
- Activate with `source venv/Scripts/activate` (Windows) before any `pip` or `pytest` calls

## Forbidden
- No `requests` library — use `httpx` exclusively
- Do not commit `.env` files
- Do not hardcode API base URL or API key anywhere
- Do not expose raw `httpx` exceptions to callers — always wrap in the custom hierarchy
- Do not add global/module-level state
