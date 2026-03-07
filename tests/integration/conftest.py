"""Fixtures for integration tests against a live paperless-ngx instance."""

from __future__ import annotations

import os
import uuid
from pathlib import Path

import pytest
import pytest_asyncio
from dotenv import load_dotenv

from easypaperless import PaperlessClient, SyncPaperlessClient

load_dotenv(dotenv_path=Path(__file__).parent / ".env")


def _require_env() -> tuple[str, str]:
    url = os.getenv("PAPERLESS_URL")
    key = os.getenv("PAPERLESS_API_KEY")
    if not url or not key:
        pytest.skip("Integration env vars not set (PAPERLESS_URL, PAPERLESS_API_KEY)")
    return url, key


@pytest_asyncio.fixture
async def client() -> object:
    url, key = _require_env()
    async with PaperlessClient(url=url, api_key=key) as c:
        yield c


@pytest.fixture
def uid() -> str:
    """Short unique ID to avoid name collisions between test runs."""
    return uuid.uuid4().hex[:8]


@pytest.fixture
def sync_client() -> object:
    url, key = _require_env()
    with SyncPaperlessClient(url=url, api_key=key) as c:
        yield c
