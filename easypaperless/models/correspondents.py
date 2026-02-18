"""Correspondent Pydantic model."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict


class Correspondent(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    name: str
    slug: str | None = None
    match: str | None = None
    matching_algorithm: int | None = None
    is_insensitive: bool | None = None
    document_count: int | None = None
    last_correspondence: date | None = None
    owner: int | None = None
    user_can_change: bool | None = None
