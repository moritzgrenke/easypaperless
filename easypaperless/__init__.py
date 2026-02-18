"""easypaperless — Python API wrapper for paperless-ngx."""

import logging

from easypaperless.client import PaperlessClient
from easypaperless.exceptions import (
    AuthError,
    NotFoundError,
    PaperlessError,
    ServerError,
    TaskTimeoutError,
    UploadError,
    ValidationError,
)
from easypaperless.models import (
    Correspondent,
    CustomField,
    CustomFieldValue,
    Document,
    DocumentNote,
    DocumentType,
    FieldDataType,
    SearchHit,
    StoragePath,
    Tag,
    Task,
    TaskStatus,
)
from easypaperless.store import DocumentStore
from easypaperless.sync import SyncPaperlessClient

logging.getLogger("easypaperless").addHandler(logging.NullHandler())

__all__ = [
    # Clients
    "PaperlessClient",
    "SyncPaperlessClient",
    "DocumentStore",
    # Models
    "Correspondent",
    "CustomField",
    "CustomFieldValue",
    "Document",
    "DocumentNote",
    "DocumentType",
    "FieldDataType",
    "SearchHit",
    "StoragePath",
    "Tag",
    "Task",
    "TaskStatus",
    # Exceptions
    "PaperlessError",
    "AuthError",
    "NotFoundError",
    "ValidationError",
    "ServerError",
    "UploadError",
    "TaskTimeoutError",
]
