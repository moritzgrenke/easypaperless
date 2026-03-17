"""Shared fixtures for the test suite."""

from __future__ import annotations

import pytest
import respx

from easypaperless.client import PaperlessClient

BASE_URL = "http://paperless.test"
API_KEY = "test-api-key"
API_BASE = BASE_URL + "/api"


@pytest.fixture
def mock_router():
    """respx router that intercepts all httpx requests."""
    with respx.mock(base_url=API_BASE, assert_all_called=False) as router:
        yield router


@pytest.fixture
async def client(mock_router):
    """PaperlessClient wired to the respx mock."""
    async with PaperlessClient(url=BASE_URL, api_token=API_KEY) as c:
        yield c
