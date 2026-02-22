"""Tests for embedding providers and _chunk_text helper."""

from __future__ import annotations

import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import respx
import httpx

from easypaperless._embedding import OllamaProvider, SentenceTransformerProvider
from easypaperless.store import _chunk_text


# ------------------------------------------------------------------
# _chunk_text
# ------------------------------------------------------------------


def test_chunk_text_short_returns_one_chunk():
    chunks = _chunk_text("hello world", chunk_size=100, overlap=20)
    assert chunks == ["hello world"]


def test_chunk_text_empty_returns_empty():
    assert _chunk_text("", chunk_size=100, overlap=20) == []


def test_chunk_text_basic_overlap():
    text = "a" * 200
    chunks = _chunk_text(text, chunk_size=100, overlap=20)
    # step = 80; starts: 0, 80, 160 → 3 chunks
    assert len(chunks) == 3
    assert len(chunks[0]) == 100
    assert len(chunks[1]) == 100
    assert len(chunks[2]) == 40  # remainder
    # Verify overlap: last 20 chars of chunk 0 equal first 20 chars of chunk 1
    assert chunks[0][-20:] == chunks[1][:20]


def test_chunk_text_exact_size():
    text = "b" * 100
    chunks = _chunk_text(text, chunk_size=100, overlap=10)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_chunk_text_no_overlap():
    text = "x" * 300
    chunks = _chunk_text(text, chunk_size=100, overlap=0)
    assert len(chunks) == 3
    for chunk in chunks:
        assert len(chunk) == 100


# ------------------------------------------------------------------
# OllamaProvider
# ------------------------------------------------------------------


@respx.mock
async def test_ollama_provider_calls_correct_endpoint():
    expected_embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
    route = respx.post("http://localhost:11434/api/embed").mock(
        return_value=httpx.Response(200, json={"embeddings": expected_embeddings})
    )

    provider = OllamaProvider(model="nomic-embed-text")
    result = await provider.embed(["hello", "world"])

    assert route.called
    request_body = route.calls[0].request
    import json
    body = json.loads(request_body.content)
    assert body["model"] == "nomic-embed-text"
    assert body["input"] == ["hello", "world"]
    assert result == expected_embeddings


@respx.mock
async def test_ollama_provider_custom_url():
    route = respx.post("http://nas:11434/api/embed").mock(
        return_value=httpx.Response(200, json={"embeddings": [[0.1]]})
    )

    provider = OllamaProvider(model="mymodel", url="http://nas:11434")
    result = await provider.embed(["test"])

    assert route.called
    assert result == [[0.1]]


@respx.mock
async def test_ollama_provider_strips_trailing_slash():
    route = respx.post("http://localhost:11434/api/embed").mock(
        return_value=httpx.Response(200, json={"embeddings": [[0.5]]})
    )

    provider = OllamaProvider(model="m", url="http://localhost:11434/")
    await provider.embed(["x"])
    assert route.called


# ------------------------------------------------------------------
# SentenceTransformerProvider
# ------------------------------------------------------------------


async def test_sentence_transformer_import_error(monkeypatch):
    monkeypatch.setitem(sys.modules, "sentence_transformers", None)

    provider = SentenceTransformerProvider()
    with pytest.raises(ImportError, match="sentence-transformers"):
        await provider.embed(["hello"])


async def test_sentence_transformer_embeds_via_executor():
    import numpy as np

    fake_model = MagicMock()
    fake_model.encode.return_value = np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])

    fake_st_module = MagicMock()
    fake_st_module.SentenceTransformer.return_value = fake_model

    with patch.dict(sys.modules, {"sentence_transformers": fake_st_module}):
        provider = SentenceTransformerProvider(model="test-model")
        result = await provider.embed(["hello", "world"])

    assert len(result) == 2
    assert result[0] == pytest.approx([0.1, 0.2, 0.3])
    assert result[1] == pytest.approx([0.4, 0.5, 0.6])
    fake_model.encode.assert_called_once_with(["hello", "world"])
