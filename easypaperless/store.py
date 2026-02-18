"""DocumentStore — SQLite-backed local cache of paperless-ngx documents."""

from __future__ import annotations

import asyncio
import json
import re
import sqlite3
from datetime import date
from pathlib import Path
from typing import Any

from easypaperless.client import PaperlessClient
from easypaperless.models.documents import Document


_DDL = """
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    correspondent_id INTEGER,
    document_type_id INTEGER,
    created_date TEXT,
    raw_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    raw_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS correspondents (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    raw_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS document_types (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    raw_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS storage_paths (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    raw_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS document_tags (
    document_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    PRIMARY KEY (document_id, tag_id)
);

CREATE TABLE IF NOT EXISTS sync_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


class DocumentStore:
    """SQLite-backed local mirror of paperless-ngx document metadata.

    Sync is manual and explicit: call store.sync() to pull fresh data from the
    server. search_documents() is a pure SQLite query — no network involved.
    """

    def __init__(self, client: PaperlessClient, db_path: str | Path) -> None:
        self._client = client
        self._db_path = Path(db_path)
        self._conn: sqlite3.Connection | None = None

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self._db_path)
            self._conn.row_factory = sqlite3.Row
            self._conn.executescript(_DDL)
            self._conn.commit()
        return self._conn

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    # ------------------------------------------------------------------
    # Sync
    # ------------------------------------------------------------------

    async def sync(self) -> int:
        """Pull all documents and supporting metadata from the server and upsert locally.

        Returns the number of documents synced.
        """
        docs, tags, correspondents, doc_types, storage_paths = await asyncio.gather(
            self._client.list_documents(),
            self._client.list_tags(),
            self._client.list_correspondents(),
            self._client.list_document_types(),
            self._client.list_storage_paths(),
        )

        conn = self._get_conn()

        # Upsert tags
        conn.executemany(
            "INSERT OR REPLACE INTO tags (id, name, raw_json) VALUES (?, ?, ?)",
            [(t.id, t.name, t.model_dump_json()) for t in tags],
        )

        # Upsert correspondents
        conn.executemany(
            "INSERT OR REPLACE INTO correspondents (id, name, raw_json) VALUES (?, ?, ?)",
            [(c.id, c.name, c.model_dump_json()) for c in correspondents],
        )

        # Upsert document types
        conn.executemany(
            "INSERT OR REPLACE INTO document_types (id, name, raw_json) VALUES (?, ?, ?)",
            [(dt.id, dt.name, dt.model_dump_json()) for dt in doc_types],
        )

        # Upsert storage paths
        conn.executemany(
            "INSERT OR REPLACE INTO storage_paths (id, name, raw_json) VALUES (?, ?, ?)",
            [(sp.id, sp.name, sp.model_dump_json()) for sp in storage_paths],
        )

        # Upsert documents
        for doc in docs:
            created_date_str = doc.created_date.isoformat() if doc.created_date else None
            conn.execute(
                """INSERT OR REPLACE INTO documents
                   (id, title, correspondent_id, document_type_id, created_date, raw_json)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    doc.id,
                    doc.title,
                    doc.correspondent,
                    doc.document_type,
                    created_date_str,
                    doc.model_dump_json(),
                ),
            )
            # Rebuild document_tags
            conn.execute("DELETE FROM document_tags WHERE document_id = ?", (doc.id,))
            conn.executemany(
                "INSERT OR IGNORE INTO document_tags (document_id, tag_id) VALUES (?, ?)",
                [(doc.id, tag_id) for tag_id in doc.tags],
            )

        from datetime import datetime, timezone
        conn.execute(
            "INSERT OR REPLACE INTO sync_metadata (key, value) VALUES ('last_sync', ?)",
            (datetime.now(timezone.utc).isoformat(),),
        )
        conn.commit()

        return len(docs)

    # ------------------------------------------------------------------
    # Search (pure SQLite, no network)
    # ------------------------------------------------------------------

    def search_documents(
        self,
        *,
        title_contains: str | None = None,
        title_regex: str | None = None,
        content_regex: str | None = None,
        tags: list[int | str] | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        correspondent: int | str | None = None,
    ) -> list[Document]:
        conn = self._get_conn()

        conditions: list[str] = []
        bind: list[Any] = []

        if title_contains is not None:
            conditions.append("d.title LIKE ?")
            bind.append(f"%{title_contains}%")

        if created_after is not None:
            conditions.append("d.created_date > ?")
            bind.append(created_after)

        if created_before is not None:
            conditions.append("d.created_date < ?")
            bind.append(created_before)

        if correspondent is not None:
            corr_id = self._resolve_local("correspondents", correspondent)
            conditions.append("d.correspondent_id = ?")
            bind.append(corr_id)

        if tags:
            tag_ids = [self._resolve_local("tags", t) for t in tags]
            for tag_id in tag_ids:
                conditions.append(
                    "EXISTS (SELECT 1 FROM document_tags dt WHERE dt.document_id = d.id AND dt.tag_id = ?)"
                )
                bind.append(tag_id)

        where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        sql = f"SELECT d.raw_json FROM documents d {where_clause}"
        rows = conn.execute(sql, bind).fetchall()

        results: list[Document] = []
        title_re = re.compile(title_regex, re.IGNORECASE) if title_regex else None
        content_re = re.compile(content_regex, re.IGNORECASE) if content_regex else None

        for row in rows:
            data = json.loads(row["raw_json"])
            if title_re and not title_re.search(data.get("title", "")):
                continue
            if content_re and not content_re.search(data.get("content", "") or ""):
                continue
            results.append(Document.model_validate(data))

        return results

    def _resolve_local(self, table: str, value: int | str) -> int:
        if isinstance(value, int):
            return value
        conn = self._get_conn()
        row = conn.execute(
            f"SELECT id FROM {table} WHERE LOWER(name) = ?", (value.lower(),)
        ).fetchone()
        if row is None:
            from easypaperless.exceptions import NotFoundError
            raise NotFoundError(f"{table!r} item with name {value!r} not found in local cache")
        return row["id"]
