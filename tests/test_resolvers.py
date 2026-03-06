"""Tests for NameResolver — caching, misses, invalidation."""

from __future__ import annotations

import pytest

from easypaperless._internal.resolvers import NameResolver
from easypaperless.exceptions import NotFoundError


class FakeSession:
    """Minimal session stub that returns a fixed list of items."""

    def __init__(self, items: list[dict]):
        self._items = items
        self.call_count = 0

    async def get_all_pages(self, path: str, params=None) -> list[dict]:
        self.call_count += 1
        return list(self._items)


async def test_resolve_int_passthrough():
    session = FakeSession([])
    resolver = NameResolver(session)
    result = await resolver.resolve("tags", 42)
    assert result == 42
    assert session.call_count == 0


async def test_resolve_str_by_name():
    session = FakeSession([{"id": 7, "name": "invoice"}])
    resolver = NameResolver(session)
    result = await resolver.resolve("tags", "invoice")
    assert result == 7


async def test_resolve_str_case_insensitive():
    session = FakeSession([{"id": 7, "name": "Invoice"}])
    resolver = NameResolver(session)
    assert await resolver.resolve("tags", "INVOICE") == 7
    assert await resolver.resolve("tags", "invoice") == 7


async def test_resolve_str_not_found():
    session = FakeSession([{"id": 1, "name": "other"}])
    resolver = NameResolver(session)
    with pytest.raises(NotFoundError):
        await resolver.resolve("tags", "missing")


async def test_cache_prevents_repeated_fetches():
    session = FakeSession([{"id": 1, "name": "a"}])
    resolver = NameResolver(session)
    await resolver.resolve("tags", "a")
    await resolver.resolve("tags", "a")
    assert session.call_count == 1


async def test_invalidate_clears_cache():
    session = FakeSession([{"id": 1, "name": "a"}])
    resolver = NameResolver(session)
    await resolver.resolve("tags", "a")
    assert session.call_count == 1
    resolver.invalidate("tags")
    await resolver.resolve("tags", "a")
    assert session.call_count == 2


async def test_resolve_list():
    session = FakeSession([{"id": 1, "name": "a"}, {"id": 2, "name": "b"}])
    resolver = NameResolver(session)
    result = await resolver.resolve_list("tags", ["a", 2])
    assert result == [1, 2]


async def test_resolve_str_int_as_string_hint():
    """When user passes '42' (int as str), error should hint to use int."""
    session = FakeSession([{"id": 1, "name": "other"}])
    resolver = NameResolver(session)
    with pytest.raises(NotFoundError, match=r"looks like an integer ID"):
        await resolver.resolve("tags", "42")


async def test_resolve_empty_resource():
    """An empty resource listing should raise NotFoundError for any name."""
    session = FakeSession([])
    resolver = NameResolver(session)
    with pytest.raises(NotFoundError):
        await resolver.resolve("tags", "anything")


async def test_different_resources_cached_separately():
    session = FakeSession([{"id": 1, "name": "x"}])
    resolver = NameResolver(session)
    await resolver.resolve("tags", "x")
    await resolver.resolve("correspondents", "x")
    assert session.call_count == 2
