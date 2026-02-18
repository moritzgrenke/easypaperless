"""Name-to-ID resolution with per-resource caching."""

from __future__ import annotations

from easypaperless.exceptions import NotFoundError


class NameResolver:
    def __init__(self, session: object) -> None:
        # Circular import avoided by type: HttpSession passed as generic object,
        # accessed only through its async methods.
        self._session = session
        self._cache: dict[str, dict[str, int]] = {}

    async def resolve(self, resource: str, value: int | str) -> int:
        if isinstance(value, int):
            return value
        await self._ensure_loaded(resource)
        key = value.lower()
        if key not in self._cache[resource]:
            raise NotFoundError(f"{resource!r} item with name {value!r} not found")
        return self._cache[resource][key]

    async def resolve_list(self, resource: str, values: list[int | str]) -> list[int]:
        result = []
        for v in values:
            result.append(await self.resolve(resource, v))
        return result

    async def _ensure_loaded(self, resource: str) -> None:
        if resource in self._cache:
            return
        items = await self._session.get_all_pages(f"/{resource}/")
        self._cache[resource] = {item["name"].lower(): item["id"] for item in items}

    def invalidate(self, resource: str) -> None:
        self._cache.pop(resource, None)
