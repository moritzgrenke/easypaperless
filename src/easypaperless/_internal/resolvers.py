"""Name-to-ID resolution with per-resource caching."""

from __future__ import annotations

import logging
from typing import Any, Protocol

from easypaperless.exceptions import NotFoundError

logger = logging.getLogger(__name__)


class _PageFetcher(Protocol):
    async def get_all_pages(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]: ...


class NameResolver:
    def __init__(self, session: _PageFetcher) -> None:
        self._session = session
        self._cache: dict[str, dict[str, int]] = {}

    async def resolve(self, resource: str, value: int | str) -> int:
        if isinstance(value, int):
            return value
        await self._ensure_loaded(resource)
        key = value.lower()
        if key not in self._cache[resource]:
            msg = f"{resource!r} item with name {value!r} not found"
            if value.isdigit():
                msg += (
                    f". Hint: you passed the string {value!r} which looks like an"
                    " integer ID — use int({value}) instead of a string if you meant"
                    " to pass an ID"
                )
            raise NotFoundError(msg)
        resolved_id = self._cache[resource][key]
        logger.debug("Resolved %s %r -> %d", resource, value, resolved_id)
        return resolved_id

    async def resolve_list(self, resource: str, values: list[int | str]) -> list[int]:
        result = []
        for v in values:
            result.append(await self.resolve(resource, v))
        return result

    async def _ensure_loaded(self, resource: str) -> None:
        if resource in self._cache:
            logger.debug("Cache hit for %r (%d entries)", resource, len(self._cache[resource]))
            return
        logger.debug("Cache miss for %r — fetching from API", resource)
        items = await self._session.get_all_pages(f"/{resource}/")
        self._cache[resource] = {item["name"].lower(): item["id"] for item in items}
        logger.debug("Cache populated for %r: %d names loaded", resource, len(self._cache[resource]))

    def invalidate(self, resource: str) -> None:
        if resource in self._cache:
            self._cache.pop(resource)
            logger.debug("Cache invalidated for %r", resource)
