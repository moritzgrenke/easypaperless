"""DocumentStore — SQLite-backed local cache of paperless-ngx documents."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import re
import sqlite3
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

from easypaperless.client import PaperlessClient
from easypaperless.models.documents import Document, DocumentMetadata

if TYPE_CHECKING:
    from easypaperless._embedding import EmbeddingProvider

logger = logging.getLogger(__name__)


_DDL = """
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    correspondent_id INTEGER,
    document_type_id INTEGER,
    created_date TEXT,
    added_date TEXT,
    modified_date TEXT,
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

CREATE TABLE IF NOT EXISTS document_metadata (
    document_id INTEGER PRIMARY KEY,
    original_checksum TEXT,
    archive_checksum  TEXT,
    original_size     INTEGER,
    archive_size      INTEGER,
    original_mime_type TEXT,
    media_filename    TEXT,
    has_archive_version INTEGER,
    raw_json          TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS embeddings (
    document_id  INTEGER NOT NULL,
    chunk_index  INTEGER NOT NULL,
    chunk_text   TEXT    NOT NULL,
    embedding    BLOB    NOT NULL,
    PRIMARY KEY (document_id, chunk_index)
);
"""


def _chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Split text into overlapping fixed-character windows.

    Args:
        text: Input text to chunk.
        chunk_size: Maximum characters per chunk.
        overlap: Number of characters shared between consecutive chunks.

    Returns:
        List of text chunks.  Returns a single-element list when ``text`` is
        shorter than ``chunk_size``.  Returns an empty list for empty input.
    """
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]
    step = max(1, chunk_size - overlap)
    chunks: list[str] = []
    start = 0
    while start < len(text):
        chunks.append(text[start : start + chunk_size])
        start += step
    return chunks


def _cosine_similarity(a: Any, b: Any) -> float:
    """Compute cosine similarity between two numpy vectors.

    Args:
        a: First vector (numpy array).
        b: Second vector (numpy array).

    Returns:
        Cosine similarity in the range ``[-1.0, 1.0]``.  Returns ``0.0`` if
        either vector has zero norm.
    """
    import numpy as np  # noqa: PLC0415 — intentionally lazy

    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


class DocumentStore:
    """SQLite-backed local mirror of paperless-ngx document metadata.

    Wraps a :class:`~easypaperless.client.PaperlessClient` and mirrors
    document metadata (plus tags, correspondents, document types, and storage
    paths) into a local SQLite database for fast, offline-capable search.

    Sync is **manual and explicit**: call :meth:`sync` to pull fresh data from
    the server.  :meth:`search_documents` is a pure SQLite query — no network
    is involved.

    Example:
        async with PaperlessClient(url="...", api_key="...") as client:
            store = DocumentStore(client, "paperless.db")
            await store.sync()
            results = store.search_documents(tags=["invoice"], created_after="2024-01-01")
            store.close()
    """

    def __init__(self, client: PaperlessClient, db_path: str | Path) -> None:
        """Create a DocumentStore backed by a local SQLite file.

        Args:
            client: An initialised
                :class:`~easypaperless.client.PaperlessClient` used for
                fetching data during :meth:`sync`.
            db_path: Path to the SQLite database file.  The file is created
                if it does not exist.
        """
        self._client = client
        self._db_path = Path(db_path)
        self._conn: sqlite3.Connection | None = None

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            logger.debug("Opening SQLite database at %s", self._db_path)
            self._conn = sqlite3.connect(self._db_path)
            self._conn.row_factory = sqlite3.Row
            self._conn.executescript(_DDL)
            self._conn.commit()
        return self._conn

    def close(self) -> None:
        """Close the SQLite database connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    # ------------------------------------------------------------------
    # Sync
    # ------------------------------------------------------------------

    async def sync(
        self,
        *,
        force_full: bool = False,
        on_doc_fetched: Callable[[int, int | None], None] | None = None,
    ) -> int:
        """Pull documents and supporting metadata from the server and upsert locally.

        On the first call (no ``last_sync`` recorded) a full fetch is performed.
        On subsequent calls only documents modified after the previous sync date
        are fetched (incremental sync), which is much faster for large archives.

        Fetches documents, tags, correspondents, document types, and storage
        paths in parallel, then upserts everything into SQLite.  Existing
        local records are replaced; documents no longer present on the server
        are *not* removed by incremental syncs.

        Args:
            force_full: If ``True``, ignore ``last_sync`` and fetch all
                documents regardless.  Use this to pick up deleted documents
                or to rebuild the store from scratch.
            on_doc_fetched: Optional callback invoked after each API page of
                documents is fetched.  Receives ``(fetched_so_far, total)``
                where ``total`` is the server-reported document count (may be
                ``None`` if the server does not report it).  Use this for
                progress reporting during the slow initial fetch.

        Returns:
            Number of documents synced.
        """
        from datetime import datetime, timedelta

        modified_after: str | None = None
        if not force_full:
            conn = self._get_conn()
            row = conn.execute(
                "SELECT value FROM sync_metadata WHERE key = 'last_sync'"
            ).fetchone()
            if row is not None:
                last_sync_dt = datetime.fromisoformat(row["value"])
                # Subtract 1 day: modified__date__gt is date-only (strictly >),
                # so subtracting 1 day ensures docs modified on the sync day are included.
                cutoff = (last_sync_dt.date() - timedelta(days=1)).isoformat()
                modified_after = cutoff
                logger.info("Incremental sync: fetching documents modified after %s", cutoff)
            else:
                logger.info("No previous sync found — performing full sync")
        else:
            logger.info("Force full sync requested")

        logger.info("Starting sync from server")
        docs, tags, correspondents, doc_types, storage_paths = await asyncio.gather(
            self._client.list_documents(
                page_size=500,
                modified_after=modified_after,
                on_page=on_doc_fetched,
            ),
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
            created_date_str  = doc.created_date.isoformat()        if doc.created_date else None
            added_date_str    = doc.added.date().isoformat()         if doc.added         else None
            modified_date_str = doc.modified.date().isoformat()      if doc.modified      else None
            conn.execute(
                """INSERT OR REPLACE INTO documents
                   (id, title, correspondent_id, document_type_id, created_date,
                    added_date, modified_date, raw_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    doc.id,
                    doc.title,
                    doc.correspondent,
                    doc.document_type,
                    created_date_str,
                    added_date_str,
                    modified_date_str,
                    doc.model_dump_json(),
                ),
            )
            # Rebuild document_tags
            conn.execute("DELETE FROM document_tags WHERE document_id = ?", (doc.id,))
            conn.executemany(
                "INSERT OR IGNORE INTO document_tags (document_id, tag_id) VALUES (?, ?)",
                [(doc.id, tag_id) for tag_id in doc.tags],
            )

        from datetime import timezone
        conn.execute(
            "INSERT OR REPLACE INTO sync_metadata (key, value) VALUES ('last_sync', ?)",
            (datetime.now(timezone.utc).isoformat(),),
        )
        conn.commit()
        logger.info(
            "Sync complete: %d documents, %d tags, %d correspondents, %d document_types, %d storage_paths",
            len(docs), len(tags), len(correspondents), len(doc_types), len(storage_paths),
        )

        return len(docs)

    async def sync_metadata(self, concurrency: int = 20) -> int:
        """Fetch and cache file-level metadata (checksums, sizes) for all local documents.

        Queries ``GET /api/documents/{id}/metadata/`` for every document
        currently in the local cache, using a semaphore to bound concurrent
        requests.  Results are upserted into the ``document_metadata`` table.

        Call this after :meth:`sync` to populate checksums needed by
        :meth:`find_unsynced_files`.

        Args:
            concurrency: Maximum number of parallel metadata requests.

        Returns:
            Number of documents for which metadata was requested (including
            failures, which are logged as warnings and skipped).
        """
        conn = self._get_conn()
        rows = conn.execute("SELECT id FROM documents").fetchall()
        doc_ids = [row["id"] for row in rows]

        sem = asyncio.Semaphore(concurrency)

        async def _fetch_one(doc_id: int) -> tuple[int, DocumentMetadata | None]:
            async with sem:
                try:
                    meta = await self._client.get_document_metadata(doc_id)
                    return doc_id, meta
                except Exception as exc:  # noqa: BLE001
                    logger.warning(
                        "Failed to fetch metadata for document %d: %s", doc_id, exc
                    )
                    return doc_id, None

        pairs = await asyncio.gather(*[_fetch_one(doc_id) for doc_id in doc_ids])

        for doc_id, meta in pairs:
            if meta is None:
                continue
            conn.execute(
                """INSERT OR REPLACE INTO document_metadata
                   (document_id, original_checksum, archive_checksum, original_size,
                    archive_size, original_mime_type, media_filename,
                    has_archive_version, raw_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    doc_id,
                    meta.original_checksum,
                    meta.archive_checksum,
                    meta.original_size,
                    meta.archive_size,
                    meta.original_mime_type,
                    meta.media_filename,
                    int(meta.has_archive_version) if meta.has_archive_version is not None else None,
                    meta.model_dump_json(),
                ),
            )

        conn.commit()
        logger.info("sync_metadata complete: %d documents processed", len(doc_ids))
        return len(doc_ids)

    # ------------------------------------------------------------------
    # Checksum-based file comparison
    # ------------------------------------------------------------------

    def get_document_by_checksum(self, checksum: str) -> Document | None:
        """Look up a document by its file checksum.

        Queries the local ``document_metadata`` table for a matching
        ``original_checksum`` or ``archive_checksum``.  Requires
        :meth:`sync_metadata` to have been called first.

        Args:
            checksum: Hex digest string (e.g. MD5) to search for.

        Returns:
            The matching :class:`~easypaperless.models.documents.Document`,
            or ``None`` if no match is found.
        """
        conn = self._get_conn()
        row = conn.execute(
            """SELECT d.raw_json
               FROM document_metadata dm
               JOIN documents d ON d.id = dm.document_id
               WHERE dm.original_checksum = ? OR dm.archive_checksum = ?""",
            (checksum, checksum),
        ).fetchone()
        if row is None:
            return None
        return Document.model_validate(json.loads(row["raw_json"]))

    def find_unsynced_files(
        self,
        path: str | Path,
        pattern: str = "**/*",
        hash_algo: str = "md5",
    ) -> list[Path]:
        """Find files on disk that are not yet present in paperless.

        Computes a hash for each file matched by ``pattern`` under ``path``
        and checks it against the local ``document_metadata`` cache.  Files
        whose hash is not found are considered unsynced.

        .. note::
            :meth:`sync_metadata` must be called before this method for
            checksums to be present in the local database.

        Args:
            path: Root directory to search.
            pattern: Glob pattern relative to ``path``.
            hash_algo: Hash algorithm name accepted by :func:`hashlib.new`
                (default ``"md5"``).

        Returns:
            List of :class:`~pathlib.Path` objects for files not found in
            paperless.
        """
        root = Path(path)
        unsynced: list[Path] = []

        for file_path in root.glob(pattern):
            if not file_path.is_file():
                continue
            h = hashlib.new(hash_algo)
            with file_path.open("rb") as fh:
                while chunk := fh.read(65536):
                    h.update(chunk)
            if self.get_document_by_checksum(h.hexdigest()) is None:
                unsynced.append(file_path)

        return unsynced

    # ------------------------------------------------------------------
    # Semantic search (embeddings)
    # ------------------------------------------------------------------

    async def embed_documents(
        self,
        provider: EmbeddingProvider,
        *,
        chunk_size: int = 512,
        chunk_overlap: int = 64,
        batch_size: int = 32,
        force: bool = False,
        on_chunk_embedded: Callable[[int, int], None] | None = None,
    ) -> int:
        """Embed all locally cached documents and store vectors in SQLite.

        For each document, builds a text string from the title and OCR content,
        splits it into overlapping chunks, and embeds each chunk via
        ``provider``.  Embeddings are stored as ``numpy.float32`` byte blobs.

        Documents that already have embeddings are skipped unless
        ``force=True``.

        Args:
            provider: An :class:`~easypaperless._embedding.EmbeddingProvider`
                instance (e.g.
                :class:`~easypaperless._embedding.SentenceTransformerProvider`
                or :class:`~easypaperless._embedding.OllamaProvider`).
            chunk_size: Maximum characters per text chunk.
            chunk_overlap: Character overlap between consecutive chunks.
            batch_size: Number of chunks sent to ``provider.embed()`` per call.
            force: If ``True``, re-embed documents that already have stored
                embeddings.
            on_chunk_embedded: Optional callback invoked after each batch of
                chunks is embedded and stored.  Receives
                ``(embedded_so_far, total)`` as positional arguments.  Use
                this for progress reporting.

        Returns:
            Total number of chunks embedded and stored.

        Raises:
            ImportError: If ``numpy`` is not installed.
        """
        try:
            import numpy as np  # noqa: PLC0415
        except ImportError as exc:
            raise ImportError(
                "numpy is required for embed_documents. "
                "Install it with: pip install easypaperless[embeddings]"
            ) from exc

        conn = self._get_conn()
        rows = conn.execute("SELECT raw_json FROM documents").fetchall()
        docs = [Document.model_validate(json.loads(r["raw_json"])) for r in rows]

        # Collect (doc_id, chunks) pairs for documents that need embedding
        doc_chunks: list[tuple[int, list[str]]] = []
        for doc in docs:
            if not force:
                existing = conn.execute(
                    "SELECT 1 FROM embeddings WHERE document_id = ? LIMIT 1", (doc.id,)
                ).fetchone()
                if existing:
                    continue
            else:
                conn.execute("DELETE FROM embeddings WHERE document_id = ?", (doc.id,))

            text = f"{doc.title}\n\n{doc.content or ''}"
            chunks = _chunk_text(text, chunk_size, chunk_overlap)
            if chunks:
                doc_chunks.append((doc.id, chunks))

        # Flatten to (doc_id, chunk_index, text) triples
        all_items: list[tuple[int, int, str]] = [
            (doc_id, i, chunk)
            for doc_id, chunks in doc_chunks
            for i, chunk in enumerate(chunks)
        ]

        total = 0
        total_chunks = len(all_items)
        for batch_start in range(0, total_chunks, batch_size):
            batch = all_items[batch_start : batch_start + batch_size]
            texts = [item[2] for item in batch]
            embeddings = await provider.embed(texts)
            for (doc_id, chunk_index, chunk_text_str), embedding in zip(batch, embeddings):
                blob = np.array(embedding, dtype=np.float32).tobytes()
                conn.execute(
                    """INSERT OR REPLACE INTO embeddings
                       (document_id, chunk_index, chunk_text, embedding)
                       VALUES (?, ?, ?, ?)""",
                    (doc_id, chunk_index, chunk_text_str, blob),
                )
            total += len(batch)
            if on_chunk_embedded is not None:
                on_chunk_embedded(total, total_chunks)

        conn.commit()
        logger.info("embed_documents complete: %d chunks stored", total)
        return total

    async def semantic_search(
        self,
        query: str,
        provider: EmbeddingProvider,
        *,
        max_results: int = 10,
        tags: list[int | str] | None = None,
        any_tag: list[int | str] | None = None,
        exclude_tags: list[int | str] | None = None,
        correspondent: int | str | None = None,
        any_correspondent: list[int | str] | None = None,
        exclude_correspondents: list[int | str] | None = None,
        document_type: int | str | None = None,
        any_document_type: list[int | str] | None = None,
        exclude_document_types: list[int | str] | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        added_after: str | None = None,
        added_before: str | None = None,
        modified_after: str | None = None,
        modified_before: str | None = None,
    ) -> list[tuple[Document, float]]:
        """Find documents semantically similar to a query string.

        Embeds the query and computes cosine similarity against every stored
        chunk embedding.  For each document the **maximum** similarity across
        all its chunks is used (best-chunk-wins strategy).

        SQL filters are applied before loading embeddings to avoid unnecessary
        work.

        Args:
            query: Natural-language query string.
            provider: The same
                :class:`~easypaperless._embedding.EmbeddingProvider` used
                during :meth:`embed_documents`.
            max_results: Maximum number of results to return.
            tags: Documents must have **all** of these tags.
            any_tag: Documents must have **at least one** of these tags.
            exclude_tags: Documents must have **none** of these tags.
            correspondent: Filter to a single correspondent (name or ID).
            any_correspondent: Filter to any of these correspondents.
            exclude_correspondents: Exclude these correspondents.
            document_type: Filter to a single document type (name or ID).
            any_document_type: Filter to any of these document types.
            exclude_document_types: Exclude these document types.
            created_after: ISO-8601 date — only docs created after this date.
            created_before: ISO-8601 date — only docs created before this date.
            added_after: ISO-8601 date — only docs added after this date.
            added_before: ISO-8601 date — only docs added before this date.
            modified_after: ISO-8601 date — only docs modified after this date.
            modified_before: ISO-8601 date — only docs modified before this date.

        Returns:
            List of ``(Document, similarity_score)`` tuples, sorted by
            similarity descending.

        Raises:
            ImportError: If ``numpy`` is not installed.
        """
        try:
            import numpy as np  # noqa: PLC0415
        except ImportError as exc:
            raise ImportError(
                "numpy is required for semantic_search. "
                "Install it with: pip install easypaperless[embeddings]"
            ) from exc

        query_vecs = await provider.embed([query])
        query_vec = np.array(query_vecs[0], dtype=np.float32)

        conn = self._get_conn()

        conditions, bind = self._build_filter_sql(
            tags=tags,
            any_tag=any_tag,
            exclude_tags=exclude_tags,
            correspondent=correspondent,
            any_correspondent=any_correspondent,
            exclude_correspondents=exclude_correspondents,
            document_type=document_type,
            any_document_type=any_document_type,
            exclude_document_types=exclude_document_types,
            created_after=created_after,
            created_before=created_before,
            added_after=added_after,
            added_before=added_before,
            modified_after=modified_after,
            modified_before=modified_before,
        )

        if conditions:
            where = "WHERE " + " AND ".join(conditions)
            rows = conn.execute(
                f"SELECT e.document_id, e.embedding FROM embeddings e "
                f"JOIN documents d ON d.id = e.document_id {where}",
                bind,
            ).fetchall()
        else:
            rows = conn.execute("SELECT document_id, embedding FROM embeddings").fetchall()

        if not rows:
            return []

        doc_max_sim: dict[int, float] = {}
        for row in rows:
            doc_id = row["document_id"]
            vec = np.frombuffer(row["embedding"], dtype=np.float32)
            sim = _cosine_similarity(query_vec, vec)
            if doc_id not in doc_max_sim or sim > doc_max_sim[doc_id]:
                doc_max_sim[doc_id] = sim

        top_ids = sorted(doc_max_sim, key=doc_max_sim.__getitem__, reverse=True)[:max_results]

        results: list[tuple[Document, float]] = []
        for doc_id in top_ids:
            row = conn.execute(
                "SELECT raw_json FROM documents WHERE id = ?", (doc_id,)
            ).fetchone()
            if row:
                doc = Document.model_validate(json.loads(row["raw_json"]))
                results.append((doc, doc_max_sim[doc_id]))

        return results

    # ------------------------------------------------------------------
    # Search (pure SQLite, no network)
    # ------------------------------------------------------------------

    def _build_filter_sql(
        self,
        *,
        tags: list[int | str] | None = None,
        any_tag: list[int | str] | None = None,
        exclude_tags: list[int | str] | None = None,
        correspondent: int | str | None = None,
        any_correspondent: list[int | str] | None = None,
        exclude_correspondents: list[int | str] | None = None,
        document_type: int | str | None = None,
        any_document_type: list[int | str] | None = None,
        exclude_document_types: list[int | str] | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        added_after: str | None = None,
        added_before: str | None = None,
        modified_after: str | None = None,
        modified_before: str | None = None,
    ) -> tuple[list[str], list[Any]]:
        """Build WHERE conditions against the ``documents d`` table alias.

        Returns ``(conditions, bind)`` to be joined into a WHERE clause.
        """
        conditions: list[str] = []
        bind: list[Any] = []

        # tags: document must have ALL of these
        if tags:
            tag_ids = [self._resolve_local("tags", t) for t in tags]
            for tag_id in tag_ids:
                conditions.append(
                    "EXISTS (SELECT 1 FROM document_tags dt"
                    " WHERE dt.document_id = d.id AND dt.tag_id = ?)"
                )
                bind.append(tag_id)

        # any_tag: document must have AT LEAST ONE of these
        if any_tag:
            tag_ids = [self._resolve_local("tags", t) for t in any_tag]
            placeholders = ",".join("?" * len(tag_ids))
            conditions.append(
                f"EXISTS (SELECT 1 FROM document_tags dt"
                f" WHERE dt.document_id = d.id AND dt.tag_id IN ({placeholders}))"
            )
            bind.extend(tag_ids)

        # exclude_tags: document must have NONE of these
        if exclude_tags:
            tag_ids = [self._resolve_local("tags", t) for t in exclude_tags]
            placeholders = ",".join("?" * len(tag_ids))
            conditions.append(
                f"NOT EXISTS (SELECT 1 FROM document_tags dt"
                f" WHERE dt.document_id = d.id AND dt.tag_id IN ({placeholders}))"
            )
            bind.extend(tag_ids)

        # correspondent / any_correspondent — any_correspondent takes precedence
        if any_correspondent:
            corr_ids = [self._resolve_local("correspondents", c) for c in any_correspondent]
            placeholders = ",".join("?" * len(corr_ids))
            conditions.append(f"d.correspondent_id IN ({placeholders})")
            bind.extend(corr_ids)
        elif correspondent is not None:
            corr_id = self._resolve_local("correspondents", correspondent)
            conditions.append("d.correspondent_id = ?")
            bind.append(corr_id)

        if exclude_correspondents:
            corr_ids = [self._resolve_local("correspondents", c) for c in exclude_correspondents]
            placeholders = ",".join("?" * len(corr_ids))
            conditions.append(f"(d.correspondent_id IS NULL OR d.correspondent_id NOT IN ({placeholders}))")
            bind.extend(corr_ids)

        # document_type / any_document_type — any_document_type takes precedence
        if any_document_type:
            dt_ids = [self._resolve_local("document_types", dt) for dt in any_document_type]
            placeholders = ",".join("?" * len(dt_ids))
            conditions.append(f"d.document_type_id IN ({placeholders})")
            bind.extend(dt_ids)
        elif document_type is not None:
            dt_id = self._resolve_local("document_types", document_type)
            conditions.append("d.document_type_id = ?")
            bind.append(dt_id)

        if exclude_document_types:
            dt_ids = [self._resolve_local("document_types", dt) for dt in exclude_document_types]
            placeholders = ",".join("?" * len(dt_ids))
            conditions.append(f"(d.document_type_id IS NULL OR d.document_type_id NOT IN ({placeholders}))")
            bind.extend(dt_ids)

        # Date range filters
        if created_after is not None:
            conditions.append("d.created_date > ?")
            bind.append(created_after)
        if created_before is not None:
            conditions.append("d.created_date < ?")
            bind.append(created_before)
        if added_after is not None:
            conditions.append("d.added_date > ?")
            bind.append(added_after)
        if added_before is not None:
            conditions.append("d.added_date < ?")
            bind.append(added_before)
        if modified_after is not None:
            conditions.append("d.modified_date > ?")
            bind.append(modified_after)
        if modified_before is not None:
            conditions.append("d.modified_date < ?")
            bind.append(modified_before)

        return conditions, bind

    def search_documents(
        self,
        *,
        title_contains: str | None = None,
        title_regex: str | None = None,
        content_regex: str | None = None,
        tags: list[int | str] | None = None,
        any_tag: list[int | str] | None = None,
        exclude_tags: list[int | str] | None = None,
        correspondent: int | str | None = None,
        any_correspondent: list[int | str] | None = None,
        exclude_correspondents: list[int | str] | None = None,
        document_type: int | str | None = None,
        any_document_type: list[int | str] | None = None,
        exclude_document_types: list[int | str] | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        added_after: str | None = None,
        added_before: str | None = None,
        modified_after: str | None = None,
        modified_before: str | None = None,
        max_results: int | None = None,
    ) -> list[Document]:
        """Search the local SQLite cache — no network request is made.

        SQL filters are applied first; ``title_regex`` and ``content_regex``
        are applied in Python on the resulting rows.

        Args:
            title_contains: Case-insensitive substring match on the title.
            title_regex: Python ``re`` pattern on the title (case-insensitive).
            content_regex: Python ``re`` pattern on OCR content (case-insensitive).
            tags: Documents must have **all** of these tags (name or ID).
            any_tag: Documents must have **at least one** of these tags.
            exclude_tags: Documents must have **none** of these tags.
            correspondent: Filter to a single correspondent (name or ID).
            any_correspondent: Filter to any of these correspondents.
            exclude_correspondents: Exclude these correspondents.
            document_type: Filter to a single document type (name or ID).
            any_document_type: Filter to any of these document types.
            exclude_document_types: Exclude these document types.
            created_after: ISO-8601 date — only docs created after this date.
            created_before: ISO-8601 date — only docs created before this date.
            added_after: ISO-8601 date — only docs added after this date.
            added_before: ISO-8601 date — only docs added before this date.
            modified_after: ISO-8601 date — only docs modified after this date.
            modified_before: ISO-8601 date — only docs modified before this date.
            max_results: If given, truncate the final result list to this length.

        Returns:
            List of :class:`~easypaperless.models.documents.Document`
            objects matching all supplied filters.
        """
        logger.debug("search_documents()")

        conn = self._get_conn()

        conditions: list[str] = []
        bind: list[Any] = []

        if title_contains is not None:
            conditions.append("d.title LIKE ?")
            bind.append(f"%{title_contains}%")

        filter_conditions, filter_bind = self._build_filter_sql(
            tags=tags,
            any_tag=any_tag,
            exclude_tags=exclude_tags,
            correspondent=correspondent,
            any_correspondent=any_correspondent,
            exclude_correspondents=exclude_correspondents,
            document_type=document_type,
            any_document_type=any_document_type,
            exclude_document_types=exclude_document_types,
            created_after=created_after,
            created_before=created_before,
            added_after=added_after,
            added_before=added_before,
            modified_after=modified_after,
            modified_before=modified_before,
        )
        conditions.extend(filter_conditions)
        bind.extend(filter_bind)

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

        if max_results is not None:
            results = results[:max_results]

        logger.debug("search_documents returned %d result(s)", len(results))
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
