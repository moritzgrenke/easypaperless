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
    DocumentMetadata,
    DocumentNote,
    DocumentType,
    FieldDataType,
    FileMetadataEntry,
    PermissionSet,
    SearchHit,
    SetPermissions,
    StoragePath,
    Tag,
    Task,
    TaskStatus,
)
from easypaperless._embedding import OllamaProvider, SentenceTransformerProvider
from easypaperless.store import DocumentStore
from easypaperless.sync import SyncPaperlessClient

logging.getLogger("easypaperless").addHandler(logging.NullHandler())

__all__ = [
    # Clients
    "PaperlessClient",
    "SyncPaperlessClient",
    "DocumentStore",
    # Embedding providers
    "OllamaProvider",
    "SentenceTransformerProvider",
    # Models
    "Correspondent",
    "CustomField",
    "CustomFieldValue",
    "Document",
    "DocumentMetadata",
    "DocumentNote",
    "DocumentType",
    "FieldDataType",
    "FileMetadataEntry",
    "PermissionSet",
    "SearchHit",
    "SetPermissions",
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
