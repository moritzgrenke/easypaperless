"""Tests for SyncPaperlessClient."""

from __future__ import annotations

import respx
from httpx import Response

from easypaperless.sync import SyncPaperlessClient

BASE_URL = "http://paperless.test"
API_KEY = "test-key"

DOC_DATA = {"id": 1, "title": "Test", "tags": []}
DOC_LIST = {"count": 1, "next": None, "previous": None, "results": [DOC_DATA]}


def test_sync_client_get_document():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.get("/documents/1/").mock(return_value=Response(200, json=DOC_DATA))
        client = SyncPaperlessClient(url=BASE_URL, api_key=API_KEY)
        doc = client.get_document(1)
        client.close()
    assert doc.id == 1
    assert doc.title == "Test"


def test_sync_client_list_documents():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.get("/documents/").mock(return_value=Response(200, json=DOC_LIST))
        client = SyncPaperlessClient(url=BASE_URL, api_key=API_KEY)
        docs = client.list_documents()
        client.close()
    assert len(docs) == 1


def test_sync_client_context_manager():
    with respx.mock(base_url=BASE_URL + "/api", assert_all_called=False) as router:
        router.get("/documents/1/").mock(return_value=Response(200, json=DOC_DATA))
        with SyncPaperlessClient(url=BASE_URL, api_key=API_KEY) as client:
            doc = client.get_document(1)
    assert doc.id == 1
