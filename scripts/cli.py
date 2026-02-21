"""cli.py — interactive CLI for easypaperless.

Exposes every PaperlessClient method with all parameters for testing and
demonstration purposes.

Setup:
    1. Copy .env.EXAMPLE to .env and fill in your credentials.
    2. Activate the venv:
           source venv/Scripts/activate
    3. Install script dependencies (once):
           pip install -e ".[scripts]"
    4. Install click (once — not added to pyproject.toml to keep the library
       dependency surface clean):
           pip install click
    5. Run:
           python scripts/cli.py --help

Examples:
    python scripts/cli.py documents list --max-results 3
    python scripts/cli.py tags list --name-contains inv
    python scripts/cli.py documents get 1 --include-metadata
    python scripts/cli.py documents download 42 --output invoice.pdf
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

import click
from dotenv import load_dotenv

from easypaperless import PaperlessClient
from easypaperless.exceptions import PaperlessError

# Load credentials from .env (git-ignored — never committed).
load_dotenv(Path(__file__).parent.parent / ".env")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _id_or_name(s: str) -> int | str:
    """Return an int if *s* looks like an integer, otherwise return the string."""
    try:
        return int(s)
    except ValueError:
        return s


def _out(obj, *, compact: bool) -> None:
    """Print a Pydantic model or plain dict/list as JSON to stdout."""
    if hasattr(obj, "model_dump"):
        data = obj.model_dump(mode="json")
    elif isinstance(obj, list) and obj and hasattr(obj[0], "model_dump"):
        data = [item.model_dump(mode="json") for item in obj]
    else:
        data = obj
    indent = None if compact else 2
    click.echo(json.dumps(data, indent=indent))


def _run(coro, *, compact: bool = False):
    """Execute *coro* synchronously; print result as JSON or exit on error."""
    try:
        result = asyncio.run(coro)
    except PaperlessError as exc:
        status = f" (HTTP {exc.status_code})" if exc.status_code else ""
        click.echo(f"Error{status}: {exc}", err=True)
        sys.exit(1)
    if result is not None:
        _out(result, compact=compact)
    return result


# ---------------------------------------------------------------------------
# Root group
# ---------------------------------------------------------------------------


@click.group()
@click.option(
    "--url",
    envvar="PAPERLESS_URL",
    required=True,
    help="Base URL of the paperless-ngx instance.",
)
@click.option(
    "--api-key",
    envvar="PAPERLESS_API_KEY",
    required=True,
    help="API token (Settings > API > Generate Token).",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    default=False,
    help="Enable DEBUG logging.",
)
@click.option(
    "--compact",
    "-c",
    is_flag=True,
    default=False,
    help="Print compact (single-line) JSON instead of pretty-printed.",
)
@click.pass_context
def cli(ctx: click.Context, url: str, api_key: str, verbose: bool, compact: bool) -> None:
    """easypaperless - interactive CLI for paperless-ngx."""
    if verbose:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s %(name)-40s %(levelname)-8s %(message)s",
            datefmt="%H:%M:%S",
        )
    ctx.ensure_object(dict)
    ctx.obj["url"] = url
    ctx.obj["api_key"] = api_key
    ctx.obj["compact"] = compact


def _client(ctx: click.Context) -> PaperlessClient:
    return PaperlessClient(url=ctx.obj["url"], api_key=ctx.obj["api_key"])


def _compact(ctx: click.Context) -> bool:
    return ctx.obj["compact"]


# ---------------------------------------------------------------------------
# documents group
# ---------------------------------------------------------------------------


@cli.group()
def documents() -> None:
    """Document operations."""


@documents.command("list")
@click.option("--search", default=None, help="Search string.")
@click.option(
    "--search-mode",
    default="title_or_text",
    show_default=True,
    type=click.Choice(["title", "title_or_text", "query"]),
    help="How the search string is applied.",
)
@click.option("--tags", multiple=True, metavar="TAG", help="Must have ALL of these tags (repeatable).")
@click.option("--any-tag", multiple=True, metavar="TAG", help="Must have ANY of these tags (repeatable).")
@click.option("--exclude-tags", multiple=True, metavar="TAG", help="Must have NONE of these tags (repeatable).")
@click.option("--correspondent", default=None, metavar="CORR", help="Exact correspondent (ID or name).")
@click.option("--any-correspondent", multiple=True, metavar="CORR", help="Any of these correspondents (repeatable).")
@click.option("--exclude-correspondents", multiple=True, metavar="CORR", help="Exclude these correspondents (repeatable).")
@click.option("--document-type", default=None, metavar="TYPE", help="Exact document type (ID or name).")
@click.option("--any-document-type", multiple=True, metavar="TYPE", help="Any of these document types (repeatable).")
@click.option("--exclude-document-types", multiple=True, metavar="TYPE", help="Exclude these document types (repeatable).")
@click.option("--asn", type=int, default=None, help="Archive serial number.")
@click.option("--created-after", default=None, metavar="DATE", help="ISO-8601 date (YYYY-MM-DD).")
@click.option("--created-before", default=None, metavar="DATE", help="ISO-8601 date (YYYY-MM-DD).")
@click.option("--added-after", default=None, metavar="DATE", help="ISO-8601 date (YYYY-MM-DD).")
@click.option("--added-before", default=None, metavar="DATE", help="ISO-8601 date (YYYY-MM-DD).")
@click.option("--modified-after", default=None, metavar="DATE", help="ISO-8601 date (YYYY-MM-DD).")
@click.option("--modified-before", default=None, metavar="DATE", help="ISO-8601 date (YYYY-MM-DD).")
@click.option("--page-size", type=int, default=25, show_default=True, help="Results per API page.")
@click.option("--max-results", type=int, default=None, help="Maximum total results to return.")
@click.pass_context
def documents_list(
    ctx,
    search,
    search_mode,
    tags,
    any_tag,
    exclude_tags,
    correspondent,
    any_correspondent,
    exclude_correspondents,
    document_type,
    any_document_type,
    exclude_document_types,
    asn,
    created_after,
    created_before,
    added_after,
    added_before,
    modified_after,
    modified_before,
    page_size,
    max_results,
):
    """List documents with optional filters."""

    async def _go():
        async with _client(ctx) as client:
            return await client.list_documents(
                search=search or None,
                search_mode=search_mode,
                tags=[_id_or_name(t) for t in tags] or None,
                any_tag=[_id_or_name(t) for t in any_tag] or None,
                exclude_tags=[_id_or_name(t) for t in exclude_tags] or None,
                correspondent=_id_or_name(correspondent) if correspondent else None,
                any_correspondent=[_id_or_name(c) for c in any_correspondent] or None,
                exclude_correspondents=[_id_or_name(c) for c in exclude_correspondents] or None,
                document_type=_id_or_name(document_type) if document_type else None,
                any_document_type=[_id_or_name(d) for d in any_document_type] or None,
                exclude_document_types=[_id_or_name(d) for d in exclude_document_types] or None,
                asn=asn,
                created_after=created_after,
                created_before=created_before,
                added_after=added_after,
                added_before=added_before,
                modified_after=modified_after,
                modified_before=modified_before,
                page_size=page_size,
                max_results=max_results,
            )

    _run(_go(), compact=_compact(ctx))


@documents.command("get")
@click.argument("id", type=int)
@click.option("--include-metadata", is_flag=True, default=False, help="Fetch and attach file-level metadata.")
@click.pass_context
def documents_get(ctx, id: int, include_metadata: bool):
    """Fetch a single document by ID."""

    async def _go():
        async with _client(ctx) as client:
            return await client.get_document(id, include_metadata=include_metadata)

    _run(_go(), compact=_compact(ctx))


@documents.command("metadata")
@click.argument("id", type=int)
@click.pass_context
def documents_metadata(ctx, id: int):
    """Fetch extended file-level metadata for a document."""

    async def _go():
        async with _client(ctx) as client:
            return await client.get_document_metadata(id)

    _run(_go(), compact=_compact(ctx))


@documents.command("update")
@click.argument("id", type=int)
@click.option("--title", default=None, help="New title.")
@click.option("--date", default=None, metavar="DATE", help="Creation date (YYYY-MM-DD).")
@click.option("--correspondent", default=None, metavar="CORR", help="Correspondent ID or name (0 to clear).")
@click.option("--document-type", default=None, metavar="TYPE", help="Document type ID or name (0 to clear).")
@click.option("--storage-path", default=None, metavar="PATH", help="Storage path ID or name (0 to clear).")
@click.option("--tags", multiple=True, metavar="TAG", help="Full tag replacement list (repeatable).")
@click.option("--asn", type=int, default=None, help="Archive serial number.")
@click.pass_context
def documents_update(ctx, id, title, date, correspondent, document_type, storage_path, tags, asn):
    """Partially update a document (PATCH - only passed fields change)."""

    async def _go():
        async with _client(ctx) as client:
            return await client.update_document(
                id,
                title=title,
                date=date,
                correspondent=_id_or_name(correspondent) if correspondent else None,
                document_type=_id_or_name(document_type) if document_type else None,
                storage_path=_id_or_name(storage_path) if storage_path else None,
                tags=[_id_or_name(t) for t in tags] or None,
                asn=asn,
            )

    _run(_go(), compact=_compact(ctx))


@documents.command("delete")
@click.argument("id", type=int)
@click.option("--yes", "-y", is_flag=True, default=False, help="Skip confirmation prompt.")
@click.pass_context
def documents_delete(ctx, id: int, yes: bool):
    """Permanently delete a document."""
    if not yes:
        click.confirm(f"Permanently delete document {id}?", abort=True)

    async def _go():
        async with _client(ctx) as client:
            await client.delete_document(id)

    _run(_go(), compact=_compact(ctx))
    click.echo(f"Deleted document {id}.")


@documents.command("download")
@click.argument("id", type=int)
@click.option("--original", is_flag=True, default=False, help="Download the original file instead of the archived PDF.")
@click.option("--output", "-o", default=None, metavar="FILE", help="Output file path (default: document_{id}[_original]).")
@click.pass_context
def documents_download(ctx, id: int, original: bool, output: str | None):
    """Download a document's binary content to a file."""
    if output is None:
        suffix = "_original" if original else ".pdf"
        output = f"document_{id}{suffix}"

    async def _go():
        async with _client(ctx) as client:
            return await client.download_document(id, original=original)

    try:
        data = asyncio.run(_go())
    except PaperlessError as exc:
        status = f" (HTTP {exc.status_code})" if exc.status_code else ""
        click.echo(f"Error{status}: {exc}", err=True)
        sys.exit(1)

    Path(output).write_bytes(data)
    click.echo(f"Saved {len(data):,} bytes -> {output}")


@documents.command("upload")
@click.argument("file", type=click.Path(exists=True, dir_okay=False))
@click.option("--title", default=None, help="Document title.")
@click.option("--created", default=None, metavar="DATE", help="Creation date (YYYY-MM-DD).")
@click.option("--correspondent", default=None, metavar="CORR", help="Correspondent ID or name.")
@click.option("--document-type", default=None, metavar="TYPE", help="Document type ID or name.")
@click.option("--storage-path", default=None, metavar="PATH", help="Storage path ID or name.")
@click.option("--tags", multiple=True, metavar="TAG", help="Tags to assign (repeatable).")
@click.option("--asn", type=int, default=None, help="Archive serial number.")
@click.option("--wait", is_flag=True, default=False, help="Wait for processing to complete and print the resulting document.")
@click.option("--poll-interval", type=float, default=None, help="Seconds between status checks (default: client default).")
@click.option("--poll-timeout", type=float, default=None, help="Max seconds to wait for processing (default: client default).")
@click.pass_context
def documents_upload(
    ctx,
    file,
    title,
    created,
    correspondent,
    document_type,
    storage_path,
    tags,
    asn,
    wait,
    poll_interval,
    poll_timeout,
):
    """Upload a document to paperless-ngx."""

    async def _go():
        async with _client(ctx) as client:
            return await client.upload_document(
                file,
                title=title,
                created=created,
                correspondent=_id_or_name(correspondent) if correspondent else None,
                document_type=_id_or_name(document_type) if document_type else None,
                storage_path=_id_or_name(storage_path) if storage_path else None,
                tags=[_id_or_name(t) for t in tags] or None,
                asn=asn,
                wait=wait,
                poll_interval=poll_interval,
                poll_timeout=poll_timeout,
            )

    result = _run(_go(), compact=_compact(ctx))
    if not wait and isinstance(result, str):
        # task_id was already printed by _run as a JSON string; add a hint
        click.echo("(pass --wait to block until processing completes)", err=True)


# ---------------------------------------------------------------------------
# tags group
# ---------------------------------------------------------------------------


@cli.group()
def tags() -> None:
    """Tag operations."""


@tags.command("list")
@click.option("--ids", type=int, multiple=True, metavar="INT", help="Return only these tag IDs (repeatable).")
@click.option("--name-contains", default=None, metavar="TEXT", help="Case-insensitive substring filter on name.")
@click.pass_context
def tags_list(ctx, ids, name_contains):
    """List tags."""

    async def _go():
        async with _client(ctx) as client:
            return await client.list_tags(
                ids=list(ids) or None,
                name_contains=name_contains,
            )

    _run(_go(), compact=_compact(ctx))


@tags.command("get")
@click.argument("id", type=int)
@click.pass_context
def tags_get(ctx, id: int):
    """Fetch a single tag by ID."""

    async def _go():
        async with _client(ctx) as client:
            return await client.get_tag(id)

    _run(_go(), compact=_compact(ctx))


@tags.command("create")
@click.option("--name", required=True, help="Tag name (must be unique).")
@click.pass_context
def tags_create(ctx, name: str):
    """Create a new tag."""

    async def _go():
        async with _client(ctx) as client:
            return await client.create_tag(name=name)

    _run(_go(), compact=_compact(ctx))


@tags.command("update")
@click.argument("id", type=int)
@click.option("--name", default=None, help="New tag name.")
@click.pass_context
def tags_update(ctx, id: int, name: str | None):
    """Partially update a tag."""

    async def _go():
        async with _client(ctx) as client:
            kwargs = {}
            if name is not None:
                kwargs["name"] = name
            return await client.update_tag(id, **kwargs)

    _run(_go(), compact=_compact(ctx))


@tags.command("delete")
@click.argument("id", type=int)
@click.option("--yes", "-y", is_flag=True, default=False, help="Skip confirmation prompt.")
@click.pass_context
def tags_delete(ctx, id: int, yes: bool):
    """Delete a tag."""
    if not yes:
        click.confirm(f"Delete tag {id}?", abort=True)

    async def _go():
        async with _client(ctx) as client:
            await client.delete_tag(id)

    _run(_go(), compact=_compact(ctx))
    click.echo(f"Deleted tag {id}.")


# ---------------------------------------------------------------------------
# correspondents group
# ---------------------------------------------------------------------------


@cli.group()
def correspondents() -> None:
    """Correspondent operations."""


@correspondents.command("list")
@click.option("--ids", type=int, multiple=True, metavar="INT", help="Return only these correspondent IDs (repeatable).")
@click.option("--name-contains", default=None, metavar="TEXT", help="Case-insensitive substring filter on name.")
@click.pass_context
def correspondents_list(ctx, ids, name_contains):
    """List correspondents."""

    async def _go():
        async with _client(ctx) as client:
            return await client.list_correspondents(
                ids=list(ids) or None,
                name_contains=name_contains,
            )

    _run(_go(), compact=_compact(ctx))


@correspondents.command("get")
@click.argument("id", type=int)
@click.pass_context
def correspondents_get(ctx, id: int):
    """Fetch a single correspondent by ID."""

    async def _go():
        async with _client(ctx) as client:
            return await client.get_correspondent(id)

    _run(_go(), compact=_compact(ctx))


@correspondents.command("create")
@click.option("--name", required=True, help="Correspondent name (must be unique).")
@click.pass_context
def correspondents_create(ctx, name: str):
    """Create a new correspondent."""

    async def _go():
        async with _client(ctx) as client:
            return await client.create_correspondent(name=name)

    _run(_go(), compact=_compact(ctx))


@correspondents.command("update")
@click.argument("id", type=int)
@click.option("--name", default=None, help="New correspondent name.")
@click.pass_context
def correspondents_update(ctx, id: int, name: str | None):
    """Partially update a correspondent."""

    async def _go():
        async with _client(ctx) as client:
            kwargs = {}
            if name is not None:
                kwargs["name"] = name
            return await client.update_correspondent(id, **kwargs)

    _run(_go(), compact=_compact(ctx))


@correspondents.command("delete")
@click.argument("id", type=int)
@click.option("--yes", "-y", is_flag=True, default=False, help="Skip confirmation prompt.")
@click.pass_context
def correspondents_delete(ctx, id: int, yes: bool):
    """Delete a correspondent."""
    if not yes:
        click.confirm(f"Delete correspondent {id}?", abort=True)

    async def _go():
        async with _client(ctx) as client:
            await client.delete_correspondent(id)

    _run(_go(), compact=_compact(ctx))
    click.echo(f"Deleted correspondent {id}.")


# ---------------------------------------------------------------------------
# document-types group
# ---------------------------------------------------------------------------


@cli.group("document-types")
def document_types() -> None:
    """Document type operations."""


@document_types.command("list")
@click.option("--ids", type=int, multiple=True, metavar="INT", help="Return only these document-type IDs (repeatable).")
@click.option("--name-contains", default=None, metavar="TEXT", help="Case-insensitive substring filter on name.")
@click.pass_context
def document_types_list(ctx, ids, name_contains):
    """List document types."""

    async def _go():
        async with _client(ctx) as client:
            return await client.list_document_types(
                ids=list(ids) or None,
                name_contains=name_contains,
            )

    _run(_go(), compact=_compact(ctx))


@document_types.command("get")
@click.argument("id", type=int)
@click.pass_context
def document_types_get(ctx, id: int):
    """Fetch a single document type by ID."""

    async def _go():
        async with _client(ctx) as client:
            return await client.get_document_type(id)

    _run(_go(), compact=_compact(ctx))


@document_types.command("create")
@click.option("--name", required=True, help="Document type name (must be unique).")
@click.pass_context
def document_types_create(ctx, name: str):
    """Create a new document type."""

    async def _go():
        async with _client(ctx) as client:
            return await client.create_document_type(name=name)

    _run(_go(), compact=_compact(ctx))


@document_types.command("update")
@click.argument("id", type=int)
@click.option("--name", default=None, help="New document type name.")
@click.pass_context
def document_types_update(ctx, id: int, name: str | None):
    """Partially update a document type."""

    async def _go():
        async with _client(ctx) as client:
            kwargs = {}
            if name is not None:
                kwargs["name"] = name
            return await client.update_document_type(id, **kwargs)

    _run(_go(), compact=_compact(ctx))


@document_types.command("delete")
@click.argument("id", type=int)
@click.option("--yes", "-y", is_flag=True, default=False, help="Skip confirmation prompt.")
@click.pass_context
def document_types_delete(ctx, id: int, yes: bool):
    """Delete a document type."""
    if not yes:
        click.confirm(f"Delete document type {id}?", abort=True)

    async def _go():
        async with _client(ctx) as client:
            await client.delete_document_type(id)

    _run(_go(), compact=_compact(ctx))
    click.echo(f"Deleted document type {id}.")


# ---------------------------------------------------------------------------
# storage-paths group
# ---------------------------------------------------------------------------


@cli.group("storage-paths")
def storage_paths() -> None:
    """Storage path operations."""


@storage_paths.command("list")
@click.option("--ids", type=int, multiple=True, metavar="INT", help="Return only these storage-path IDs (repeatable).")
@click.option("--name-contains", default=None, metavar="TEXT", help="Case-insensitive substring filter on name.")
@click.pass_context
def storage_paths_list(ctx, ids, name_contains):
    """List storage paths."""

    async def _go():
        async with _client(ctx) as client:
            return await client.list_storage_paths(
                ids=list(ids) or None,
                name_contains=name_contains,
            )

    _run(_go(), compact=_compact(ctx))


@storage_paths.command("get")
@click.argument("id", type=int)
@click.pass_context
def storage_paths_get(ctx, id: int):
    """Fetch a single storage path by ID."""

    async def _go():
        async with _client(ctx) as client:
            return await client.get_storage_path(id)

    _run(_go(), compact=_compact(ctx))


@storage_paths.command("create")
@click.option("--name", required=True, help="Storage path name (must be unique).")
@click.option("--path", default=None, metavar="TEMPLATE", help="Paperless path template, e.g. '{correspondent}/{title}'.")
@click.pass_context
def storage_paths_create(ctx, name: str, path: str | None):
    """Create a new storage path."""

    async def _go():
        async with _client(ctx) as client:
            kwargs = {}
            if path is not None:
                kwargs["path"] = path
            return await client.create_storage_path(name=name, **kwargs)

    _run(_go(), compact=_compact(ctx))


@storage_paths.command("update")
@click.argument("id", type=int)
@click.option("--name", default=None, help="New storage path name.")
@click.option("--path", default=None, metavar="TEMPLATE", help="New path template.")
@click.pass_context
def storage_paths_update(ctx, id: int, name: str | None, path: str | None):
    """Partially update a storage path."""

    async def _go():
        async with _client(ctx) as client:
            kwargs = {}
            if name is not None:
                kwargs["name"] = name
            if path is not None:
                kwargs["path"] = path
            return await client.update_storage_path(id, **kwargs)

    _run(_go(), compact=_compact(ctx))


@storage_paths.command("delete")
@click.argument("id", type=int)
@click.option("--yes", "-y", is_flag=True, default=False, help="Skip confirmation prompt.")
@click.pass_context
def storage_paths_delete(ctx, id: int, yes: bool):
    """Delete a storage path."""
    if not yes:
        click.confirm(f"Delete storage path {id}?", abort=True)

    async def _go():
        async with _client(ctx) as client:
            await client.delete_storage_path(id)

    _run(_go(), compact=_compact(ctx))
    click.echo(f"Deleted storage path {id}.")


# ---------------------------------------------------------------------------
# custom-fields group
# ---------------------------------------------------------------------------


@cli.group("custom-fields")
def custom_fields() -> None:
    """Custom field operations."""


@custom_fields.command("list")
@click.pass_context
def custom_fields_list(ctx):
    """List all custom fields."""

    async def _go():
        async with _client(ctx) as client:
            return await client.list_custom_fields()

    _run(_go(), compact=_compact(ctx))


@custom_fields.command("get")
@click.argument("id", type=int)
@click.pass_context
def custom_fields_get(ctx, id: int):
    """Fetch a single custom field by ID."""

    async def _go():
        async with _client(ctx) as client:
            return await client.get_custom_field(id)

    _run(_go(), compact=_compact(ctx))


@custom_fields.command("create")
@click.option("--name", required=True, help="Field name (must be unique).")
@click.option(
    "--data-type",
    required=True,
    type=click.Choice(
        ["string", "boolean", "integer", "float", "monetary", "date", "url", "documentlink", "select"],
        case_sensitive=False,
    ),
    help="Value type for this field.",
)
@click.pass_context
def custom_fields_create(ctx, name: str, data_type: str):
    """Create a new custom field."""

    async def _go():
        async with _client(ctx) as client:
            return await client.create_custom_field(name=name, data_type=data_type)

    _run(_go(), compact=_compact(ctx))


@custom_fields.command("update")
@click.argument("id", type=int)
@click.option("--name", default=None, help="New field name.")
@click.pass_context
def custom_fields_update(ctx, id: int, name: str | None):
    """Partially update a custom field."""

    async def _go():
        async with _client(ctx) as client:
            kwargs = {}
            if name is not None:
                kwargs["name"] = name
            return await client.update_custom_field(id, **kwargs)

    _run(_go(), compact=_compact(ctx))


@custom_fields.command("delete")
@click.argument("id", type=int)
@click.option("--yes", "-y", is_flag=True, default=False, help="Skip confirmation prompt.")
@click.pass_context
def custom_fields_delete(ctx, id: int, yes: bool):
    """Delete a custom field."""
    if not yes:
        click.confirm(f"Delete custom field {id}?", abort=True)

    async def _go():
        async with _client(ctx) as client:
            await client.delete_custom_field(id)

    _run(_go(), compact=_compact(ctx))
    click.echo(f"Deleted custom field {id}.")


# ---------------------------------------------------------------------------
# bulk group
# ---------------------------------------------------------------------------


@cli.group()
def bulk() -> None:
    """Bulk document operations."""


@bulk.command("add-tag")
@click.argument("doc_ids", type=int, nargs=-1, required=True, metavar="DOC_IDS...")
@click.option("--tag", required=True, metavar="TAG", help="Tag to add (ID or name).")
@click.pass_context
def bulk_add_tag(ctx, doc_ids, tag):
    """Add a tag to multiple documents."""

    async def _go():
        async with _client(ctx) as client:
            await client.bulk_add_tag(list(doc_ids), _id_or_name(tag))

    _run(_go(), compact=_compact(ctx))
    click.echo(f"Added tag {tag!r} to documents {list(doc_ids)}.")


@bulk.command("remove-tag")
@click.argument("doc_ids", type=int, nargs=-1, required=True, metavar="DOC_IDS...")
@click.option("--tag", required=True, metavar="TAG", help="Tag to remove (ID or name).")
@click.pass_context
def bulk_remove_tag(ctx, doc_ids, tag):
    """Remove a tag from multiple documents."""

    async def _go():
        async with _client(ctx) as client:
            await client.bulk_remove_tag(list(doc_ids), _id_or_name(tag))

    _run(_go(), compact=_compact(ctx))
    click.echo(f"Removed tag {tag!r} from documents {list(doc_ids)}.")


@bulk.command("modify-tags")
@click.argument("doc_ids", type=int, nargs=-1, required=True, metavar="DOC_IDS...")
@click.option("--add-tags", multiple=True, metavar="TAG", help="Tags to add (repeatable).")
@click.option("--remove-tags", multiple=True, metavar="TAG", help="Tags to remove (repeatable).")
@click.pass_context
def bulk_modify_tags(ctx, doc_ids, add_tags, remove_tags):
    """Add and/or remove tags on multiple documents atomically."""

    async def _go():
        async with _client(ctx) as client:
            await client.bulk_modify_tags(
                list(doc_ids),
                add_tags=[_id_or_name(t) for t in add_tags] or None,
                remove_tags=[_id_or_name(t) for t in remove_tags] or None,
            )

    _run(_go(), compact=_compact(ctx))
    click.echo(f"Modified tags on documents {list(doc_ids)}.")


@bulk.command("delete")
@click.argument("doc_ids", type=int, nargs=-1, required=True, metavar="DOC_IDS...")
@click.option("--yes", "-y", is_flag=True, default=False, help="Skip confirmation prompt.")
@click.pass_context
def bulk_delete(ctx, doc_ids, yes):
    """Permanently delete multiple documents."""
    if not yes:
        click.confirm(f"Permanently delete documents {list(doc_ids)}?", abort=True)

    async def _go():
        async with _client(ctx) as client:
            await client.bulk_delete(list(doc_ids))

    _run(_go(), compact=_compact(ctx))
    click.echo(f"Deleted documents {list(doc_ids)}.")


@bulk.command("edit-objects")
@click.option(
    "--object-type",
    required=True,
    metavar="TYPE",
    help="Object type (e.g. 'tags', 'correspondents').",
)
@click.option("--ids", type=int, multiple=True, required=True, metavar="INT", help="Object IDs to operate on (repeatable).")
@click.option("--operation", required=True, metavar="OP", help="Operation name (e.g. 'delete').")
@click.pass_context
def bulk_edit_objects(ctx, object_type, ids, operation):
    """Execute a bulk operation on non-document objects."""

    async def _go():
        async with _client(ctx) as client:
            await client.bulk_edit_objects(object_type, list(ids), operation)

    _run(_go(), compact=_compact(ctx))
    click.echo(f"Bulk {operation!r} on {object_type} {list(ids)} completed.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    cli()
