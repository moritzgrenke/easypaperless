"""Embedding providers for DocumentStore semantic search."""

from __future__ import annotations

import asyncio
from typing import Protocol

import httpx


class EmbeddingProvider(Protocol):
    """Protocol for embedding providers used by DocumentStore."""

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of texts and return a list of embedding vectors."""
        ...


class SentenceTransformerProvider:
    """Embedding provider backed by sentence-transformers (local model).

    Requires the ``sentence-transformers`` package::

        pip install easypaperless[embeddings-st]

    The model is lazy-loaded on the first :meth:`embed` call.

    Args:
        model: Sentence-transformers model name.
    """

    def __init__(self, model: str = "paraphrase-multilingual-mpnet-base-v2") -> None:
        self._model_name = model
        self._model = None

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed texts using the sentence-transformers model.

        The underlying ``model.encode()`` call is CPU-bound and is run in a
        thread pool to avoid blocking the event loop.

        Args:
            texts: List of strings to embed.

        Returns:
            List of embedding vectors (one per input string).

        Raises:
            ImportError: If ``sentence-transformers`` is not installed.
        """
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:
                raise ImportError(
                    "sentence-transformers is required for SentenceTransformerProvider. "
                    "Install it with: pip install easypaperless[embeddings-st]"
                ) from exc
            loop = asyncio.get_event_loop()
            self._model = await loop.run_in_executor(
                None, SentenceTransformer, self._model_name
            )
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(None, self._model.encode, texts)
        return [e.tolist() for e in embeddings]


class OllamaProvider:
    """Embedding provider backed by a local Ollama instance.

    Uses the ``/api/embed`` endpoint which accepts a list of inputs in one
    request.  No extra dependencies are required beyond ``httpx``.

    Args:
        model: Ollama model name (e.g. ``"nomic-embed-text"``).
        url: Base URL of the Ollama server.
    """

    def __init__(self, model: str, url: str = "http://localhost:11434") -> None:
        self._model = model
        self._url = url.rstrip("/")

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed texts via the Ollama ``/api/embed`` endpoint.

        Args:
            texts: List of strings to embed.

        Returns:
            List of embedding vectors (one per input string).

        Raises:
            httpx.HTTPStatusError: If the Ollama server returns an error.
        """
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self._url}/api/embed",
                json={"model": self._model, "input": texts},
            )
            resp.raise_for_status()
            return resp.json()["embeddings"]
