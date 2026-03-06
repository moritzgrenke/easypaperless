"""StoragePath Pydantic model."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from easypaperless.models._base import MatchingAlgorithm


class StoragePath(BaseModel):
    """A paperless-ngx storage path — controls where archived files are stored.

    Attributes:
        id: Unique storage-path ID.
        name: Storage-path name.
        path: Template string used to build the storage path, e.g.
            ``"{created_year}/{correspondent}/{title}"``.
        document_count: Number of documents using this storage path.
    """

    model_config = ConfigDict(extra="ignore")

    id: int
    name: str
    slug: str | None = None
    path: str | None = None
    match: str | None = None
    matching_algorithm: MatchingAlgorithm | None = None
    is_insensitive: bool | None = None
    document_count: int | None = None
    owner: int | None = None
    user_can_change: bool | None = None
