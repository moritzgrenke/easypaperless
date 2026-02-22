"""Document-related Pydantic models."""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TaskStatus(StrEnum):
    """Status values for a paperless-ngx background processing task."""

    PENDING = "PENDING"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    RETRY = "RETRY"
    REVOKED = "REVOKED"


class Task(BaseModel):
    """A paperless-ngx background processing task (e.g. document ingestion).

    Attributes:
        task_id: Unique Celery task identifier.
        task_file_name: Original file name submitted for processing.
        status: Current task status as a :class:`TaskStatus` enum value.
        result: Human-readable result or error message, set on completion.
        related_document: String representation of the resulting document ID
            on success, ``None`` otherwise.
    """

    model_config = ConfigDict(extra="ignore")

    task_id: str
    task_file_name: str | None = None
    date_created: datetime | None = None
    date_done: datetime | None = None
    type: str | None = None
    status: TaskStatus | None = None
    result: str | None = None
    acknowledged: bool | None = None
    related_document: str | None = None


class SearchHit(BaseModel):
    """Full-text search relevance metadata returned alongside a document.

    Attributes:
        score: Relevance score assigned by the Whoosh FTS engine.
        highlights: HTML snippet with matching terms highlighted.
        rank: Position in the result set by relevance.
    """

    model_config = ConfigDict(extra="ignore")

    score: float | None = None
    highlights: str | None = None
    note_highlights: str | None = None
    rank: int | None = None


class CustomFieldValue(BaseModel):
    """A custom field value attached to a document.

    Attributes:
        field: ID of the :class:`~easypaperless.models.custom_fields.CustomField`
            definition.
        value: The stored value; its Python type depends on the field's
            ``data_type``.
    """

    model_config = ConfigDict(extra="ignore")

    field: int
    value: Any = None


class DocumentNote(BaseModel):
    """A user note attached to a document.

    Attributes:
        id: Unique note ID.
        note: Text content of the note.
        created: Timestamp when the note was created.
        document: ID of the parent document.
        user: ID of the user who created the note.
    """

    model_config = ConfigDict(extra="ignore")

    id: int | None = None
    note: str
    created: datetime | None = None
    document: int | None = None
    user: int | None = None

    @field_validator("user", mode="before")
    @classmethod
    def _coerce_user(cls, v: object) -> int | None:
        if isinstance(v, dict):
            return v.get("id")
        return v  # type: ignore[return-value]


class FileMetadataEntry(BaseModel):
    """A single embedded metadata key-value pair from a document file.

    Paperless-ngx reads file-level metadata (e.g. PDF XMP/info tags) and
    exposes each entry in this format.  ``namespace`` and ``prefix`` are
    ``None`` for non-namespaced entries.

    Attributes:
        namespace: XML namespace URI, or ``None``.
        prefix: Namespace prefix (e.g. ``"pdf"``), or ``None``.
        key: Metadata key (e.g. ``"Producer"``).
        value: Metadata value as a string.
    """

    model_config = ConfigDict(extra="ignore")

    namespace: str | None = None
    prefix: str | None = None
    key: str
    value: str


class DocumentMetadata(BaseModel):
    """Extended file-level metadata for a document.

    Returned by ``GET /api/documents/{id}/metadata/`` and optionally attached
    to a :class:`Document` when :meth:`~easypaperless.PaperlessClient.get_document`
    is called with ``include_metadata=True``.

    Because reading metadata requires disk I/O it is **not** included in
    document list responses; it must be requested explicitly.

    Attributes:
        original_checksum: MD5 checksum of the original uploaded file.
        original_size: Size of the original file in bytes.
        original_mime_type: MIME type of the original file
            (e.g. ``"application/pdf"``).
        media_filename: Path of the archived file relative to the
            paperless-ngx media root.
        has_archive_version: ``True`` when paperless-ngx has produced an
            archived (post-processed) PDF in addition to the original.
        original_metadata: File-level metadata entries extracted from the
            original document (PDF XMP/info tags, etc.).
        archive_checksum: MD5 checksum of the archived file, or ``None`` if
            no archive version exists.
        archive_size: Size of the archived file in bytes, or ``None``.
        archive_metadata: File-level metadata entries from the archived
            document, or ``None``.
    """

    model_config = ConfigDict(extra="ignore")

    original_checksum: str | None = None
    original_size: int | None = None
    original_mime_type: str | None = None
    media_filename: str | None = None
    has_archive_version: bool | None = None
    original_metadata: list[FileMetadataEntry] = Field(default_factory=list)
    archive_checksum: str | None = None
    archive_size: int | None = None
    archive_metadata: list[FileMetadataEntry] | None = None


class Document(BaseModel):
    """A paperless-ngx document.

    Attributes:
        id: Unique document ID.
        title: Document title.
        content: Full OCR text content, if available.
        tags: List of tag IDs assigned to this document.
        document_type: ID of the assigned document type, or ``None``.
        correspondent: ID of the assigned correspondent, or ``None``.
        storage_path: ID of the assigned storage path, or ``None``.
        created: Full creation datetime.
        created_date: Date portion of creation (``date`` object).
        archive_serial_number: Archive serial number (ASN), or ``None``.
        custom_fields: List of :class:`CustomFieldValue` instances.
        notes: User notes attached to this document.
        search_hit: Full-text search relevance metadata, populated only when
            the document was returned by a full-text search.
        metadata: Extended file-level metadata (checksums, sizes, MIME type).
            ``None`` unless the document was fetched with
            ``include_metadata=True`` or enriched via
            :meth:`~easypaperless.PaperlessClient.get_document_metadata`.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    id: int
    title: str
    content: str | None = None
    tags: list[int] = Field(default_factory=list)
    document_type: int | None = None
    correspondent: int | None = None
    storage_path: int | None = None
    created: datetime | None = None
    created_date: date | None = None
    modified: datetime | None = None
    added: datetime | None = None
    archive_serial_number: int | None = None
    original_file_name: str | None = None
    archived_file_name: str | None = None
    owner: int | None = None
    user_can_change: bool | None = None
    is_shared_by_requester: bool | None = None
    notes: list[DocumentNote] = Field(default_factory=list)
    custom_fields: list[CustomFieldValue] = Field(default_factory=list)
    search_hit: SearchHit | None = Field(default=None, alias="__search_hit__")
    metadata: DocumentMetadata | None = None
