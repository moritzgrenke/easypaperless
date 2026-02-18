"""CustomField Pydantic model."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict


class FieldDataType(StrEnum):
    string = "string"
    boolean = "boolean"
    integer = "integer"
    float = "float"
    monetary = "monetary"
    date = "date"
    url = "url"
    documentlink = "documentlink"
    select = "select"


class CustomField(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    name: str
    data_type: FieldDataType
    extra_data: Any = None
    document_count: int | None = None
