"""Tag Pydantic model."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class Tag(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    name: str
    slug: str | None = None
    color: str | None = None
    text_color: str | None = None
    match: str | None = None
    matching_algorithm: int | None = None
    is_insensitive: bool | None = None
    is_inbox_tag: bool | None = None
    document_count: int | None = None
    owner: int | None = None
    user_can_change: bool | None = None
    parent: int | None = None
    children: list[int] | None = None
