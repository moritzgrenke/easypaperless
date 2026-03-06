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
    MatchingAlgorithm,
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
from easypaperless.sync import SyncPaperlessClient

logging.getLogger("easypaperless").addHandler(logging.NullHandler())

__all__ = [
    # Clients
    "PaperlessClient",
    "SyncPaperlessClient",
    # Models
    "MatchingAlgorithm",
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
