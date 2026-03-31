"""Integration tests: document thumbnail — feature #0038.

Verifies that documents.thumbnail(id) returns non-empty image bytes from
the GET /api/documents/{id}/thumb/ endpoint.
"""

from __future__ import annotations

import pytest

from easypaperless import PaperlessClient
from easypaperless.models.documents import Document

# Known image magic bytes
_PNG_MAGIC = b"\x89PNG"
_WEBP_MAGIC = b"RIFF"
_JPEG_MAGIC = b"\xff\xd8\xff"
_KNOWN_IMAGE_MAGICS = (_PNG_MAGIC, _WEBP_MAGIC, _JPEG_MAGIC)


@pytest.mark.integration
async def test_thumbnail_returns_image_bytes(
    client: PaperlessClient, temp_documents: list[Document]
) -> None:
    """Thumbnail endpoint returns non-empty bytes starting with a known image magic."""
    doc = temp_documents[0]
    data = await client.documents.thumbnail(doc.id)

    assert isinstance(data, bytes), "thumbnail() must return bytes"
    assert len(data) > 0, "thumbnail() must not return empty bytes"
    assert any(data.startswith(magic) for magic in _KNOWN_IMAGE_MAGICS), (
        f"Expected image magic bytes (PNG/WebP/JPEG) but got {data[:8]!r}. "
        "The thumbnail endpoint may not be returning an image."
    )
