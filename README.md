# easypaperless

A Python API wrapper for [paperless-ngx](https://docs.paperless-ngx.com/) with an optional SQLite-backed document store for local caching and extended search.

## Installation

```bash
pip install easypaperless
```

From source:

```bash
git clone https://github.com/your-org/easypaperless
cd easypaperless
python -m venv venv
source venv/Scripts/activate   # Windows
# source venv/bin/activate     # Linux / macOS
pip install -e .
```

## Quick start — async

```python
import asyncio
from easypaperless import PaperlessClient

async def main():
    async with PaperlessClient(url="http://localhost:8000", api_key="YOUR_TOKEN") as client:
        # List documents — full-text search across title and OCR content
        docs = await client.list_documents(search="invoice")

        # Fetch a single document
        doc = await client.get_document(42)
        print(doc.title, doc.created_date)

        # Update metadata — string names are resolved to IDs automatically
        await client.update_document(42, tags=["paid"], correspondent="ACME Corp")

        # Upload and wait for processing to complete
        doc = await client.upload_document("scan.pdf", title="April Invoice", wait=True)
        print("Processed:", doc.id)

asyncio.run(main())
```

## Quick start — sync

```python
from easypaperless import SyncPaperlessClient

with SyncPaperlessClient(url="http://localhost:8000", api_key="YOUR_TOKEN") as client:
    tags = client.list_tags()
    docs = client.list_documents(search="receipt", tags=["inbox"])
    client.update_document(docs[0].id, tags=["processed"])
```

> **Note:** `SyncPaperlessClient` cannot be used inside an already-running
> event loop (e.g. Jupyter notebooks). Use `PaperlessClient` directly there.

## DocumentStore — local cache

```python
from easypaperless import PaperlessClient, DocumentStore

async with PaperlessClient(url="http://localhost:8000", api_key="YOUR_TOKEN") as client:
    store = DocumentStore(client, db_path="paperless.db")

    # Pull all data from the server into SQLite
    count = await store.sync()
    print(f"Synced {count} documents")

    # Search locally — no network request
    results = store.search_documents(
        tags=["invoice"],
        created_after="2024-01-01",
        title_regex=r"Q[1-4]\s+\d{4}",  # Python regex on title
    )
    store.close()
```

## Filtering documents

`list_documents()` accepts a rich set of filter parameters.  All parameters
that accept IDs also accept string names — resolution happens transparently.

### Search

| Parameter | Type | Description |
|---|---|---|
| `search` | `str` | Search string; behaviour controlled by `search_mode`. |
| `search_mode` | `str` | `"title_or_text"` *(default)* — FTS across title + OCR content; `"title"` — title substring; `"query"` — raw paperless query language; `"original_filename"` — original file-name substring. |

### Tag filters

| Parameter | Type | Semantics |
|---|---|---|
| `tags` | `list[int \| str]` | Document must have **all** of these tags (AND). |
| `any_tag` | `list[int \| str]` | Document must have **at least one** of these tags (OR). |
| `exclude_tags` | `list[int \| str]` | Document must have **none** of these tags. |

### Correspondent filters

| Parameter | Type | Semantics |
|---|---|---|
| `correspondent` | `int \| str` | Document is assigned to this correspondent (single value). |
| `any_correspondent` | `list[int \| str]` | Document is assigned to **any** of these (OR).  Takes precedence over `correspondent`. |
| `exclude_correspondents` | `list[int \| str]` | Document is **not** assigned to any of these. |

### Document-type filters

| Parameter | Type | Semantics |
|---|---|---|
| `document_type` | `int \| str` | Document has this type (single value). |
| `any_document_type` | `list[int \| str]` | Document type is **any** of these (OR).  Takes precedence over `document_type`. |
| `exclude_document_types` | `list[int \| str]` | Document type is **none** of these. |

### Date filters

All date strings are ISO-8601 (`"YYYY-MM-DD"`).

| Parameter | Filters on | Raw API param |
|---|---|---|
| `created_after` | Document date | `created__date__gt` |
| `created_before` | Document date | `created__date__lt` |
| `added_after` | Ingestion date | `added__date__gt` |
| `added_before` | Ingestion date | `added__date__lt` |
| `modified_after` | Last-modified date | `modified__date__gt` |
| `modified_before` | Last-modified date | `modified__date__lt` |

### Other filters

| Parameter | Type | Description |
|---|---|---|
| `asn` | `int` | Archive serial number (exact match). |
| `checksum` | `str` | MD5 checksum of the original file (exact match). |

### Pagination and ordering

| Parameter | Default | Description |
|---|---|---|
| `page_size` | `25` | Results per API page.  Increase (e.g. `500`) to reduce round-trips on large archives. |
| `page` | `None` | Return exactly this page (1-based).  Disables auto-pagination — only that single page is fetched. |
| `ordering` | `None` | Field to sort by, e.g. `"created"`, `"title"`, `"added"`. |
| `descending` | `False` | When `True`, reverses the `ordering` direction. |
| `max_results` | `None` | Stop fetching once this many documents have been collected.  Avoids pulling the entire archive when you only need the first N results.  Ignored when `page` is set (use `page_size` instead). |

### Example

```python
docs = await client.list_documents(
    any_correspondent=["ACME Corp", "Bank"],
    exclude_document_types=["Spam"],
    added_after="2024-01-01",
    tags=["inbox"],
    ordering="created",
    descending=True,
    page_size=100,
    max_results=50,
)
```

## Listing tags, correspondents, document types, storage paths, custom fields

All `list_*` resource methods support the same set of pagination and ordering
parameters in addition to their own filters (`ids`, `name_contains`):

| Parameter | Default | Description |
|---|---|---|
| `page` | `None` | Return exactly this page (1-based).  Disables auto-pagination. |
| `page_size` | server default | Results per page when `page` is set. |
| `ordering` | `None` | Field to sort by, e.g. `"name"`, `"id"`. |
| `descending` | `False` | When `True`, reverses the `ordering` direction. |

```python
# First 10 tags sorted by name descending
tags = await client.list_tags(page=1, page_size=10, ordering="name", descending=True)

# All correspondents whose name contains "bank", sorted by name
corrs = await client.list_correspondents(name_contains="bank", ordering="name")
```

## Logging

`easypaperless` uses the standard `logging` module under the `easypaperless` logger hierarchy.

```python
import logging

logging.basicConfig(level=logging.WARNING)          # default — warnings only
logging.getLogger("easypaperless").setLevel(logging.INFO)   # upload/sync progress
logging.getLogger("easypaperless").setLevel(logging.DEBUG)  # full request detail
```

| Level | What you see |
|-------|--------------|
| `WARNING` | Task failures, timeouts |
| `INFO` | Upload/sync progress, document counts |
| `DEBUG` | Every HTTP request, task polling, SQL queries |

## API reference

Generate the full HTML reference locally:

```bash
pip install -e ".[docs]"
pdoc easypaperless -o docs/
# open docs/easypaperless.html
```

Or browse interactively while writing code:

```bash
pdoc easypaperless
# serves at http://localhost:8080
```
