"""Generic paged result model."""

from __future__ import annotations

from typing import Generic, List, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PagedResult(BaseModel, Generic[T]):
    """Wrapper returned by all ``list()`` methods.

    Holds the pagination metadata returned by paperless-ngx alongside the
    deserialized resource items.

    Attributes:
        count: Total number of matching items as reported by the server on
            the first fetched page.
        next: URL of the next page as returned by the API, or ``None``.
            Always ``None`` when auto-pagination is active (the default
            ``page=None``), because the navigation URL is meaningless once
            all pages have been consumed by the library.
        previous: URL of the previous page as returned by the API, or
            ``None``.  Always ``None`` when auto-pagination is active.
        all: All matching item IDs when the API includes them; ``None``
            otherwise.
        results: The deserialized resource items for this page / all fetched
            pages.
    """

    count: int
    next: str | None = None
    previous: str | None = None
    all: List[int] | None = None
    results: List[T] = Field(default_factory=list)
