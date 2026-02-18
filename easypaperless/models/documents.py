"""Document-related Pydantic models."""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TaskStatus(StrEnum):
    PENDING = "PENDING"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    RETRY = "RETRY"
    REVOKED = "REVOKED"


class Task(BaseModel):
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
    model_config = ConfigDict(extra="ignore")

    score: float | None = None
    highlights: str | None = None
    note_highlights: str | None = None
    rank: int | None = None


class CustomFieldValue(BaseModel):
    model_config = ConfigDict(extra="ignore")

    field: int
    value: Any = None


class DocumentNote(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int | None = None
    note: str
    created: datetime | None = None
    document: int | None = None
    user: int | None = None


class Document(BaseModel):
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
