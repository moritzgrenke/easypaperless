"""Tests for PaperlessClient tag and other resource CRUD methods."""

from __future__ import annotations

import json

import pytest
from httpx import Response

from easypaperless.exceptions import NotFoundError
from easypaperless.models._base import MatchingAlgorithm
from easypaperless.models.correspondents import Correspondent
from easypaperless.models.custom_fields import CustomField
from easypaperless.models.document_types import DocumentType
from easypaperless.models.permissions import PermissionSet, SetPermissions
from easypaperless.models.storage_paths import StoragePath
from easypaperless.models.tags import Tag


def _capturing_side_effect(captured: dict, response_data: dict, *, status: int = 200):
    """Return a respx side-effect that stores URL params and returns response_data."""
    def _side_effect(request):
        captured["params"] = dict(request.url.params)
        return Response(status, json=response_data)
    return _side_effect


def _json_capturing_side_effect(captured: dict, response_data: dict, *, status: int = 200):
    """Return a respx side-effect that stores the JSON body and returns response_data."""
    def _side_effect(request):
        captured["body"] = json.loads(request.content)
        return Response(status, json=response_data)
    return _side_effect


TAG_DATA = {"id": 1, "name": "invoice"}
TAG_DATA_FULL = {
    "id": 1,
    "name": "invoice",
    "slug": "invoice",
    "color": "#ff0000",
    "text_color": "#ffffff",
    "match": "invoice",
    "matching_algorithm": 3,
    "is_insensitive": True,
    "is_inbox_tag": False,
    "document_count": 42,
    "owner": 1,
    "user_can_change": True,
    "parent": None,
    "children": [2, 3],
}
TAG_LIST = {"count": 1, "next": None, "previous": None, "results": [TAG_DATA]}


async def test_list_tags(client, mock_router):
    mock_router.get("/tags/").mock(return_value=Response(200, json=TAG_LIST))
    tags = await client.list_tags()
    assert len(tags) == 1
    assert isinstance(tags[0], Tag)
    assert tags[0].name == "invoice"


async def test_get_tag(client, mock_router):
    mock_router.get("/tags/1/").mock(return_value=Response(200, json=TAG_DATA))
    tag = await client.get_tag(1)
    assert tag.id == 1


async def test_create_tag(client, mock_router):
    mock_router.post("/tags/").mock(return_value=Response(201, json=TAG_DATA))
    tag = await client.create_tag(name="invoice")
    assert tag.name == "invoice"


async def test_update_tag(client, mock_router):
    mock_router.patch("/tags/1/").mock(return_value=Response(200, json={**TAG_DATA, "name": "receipt"}))
    tag = await client.update_tag(1, name="receipt")
    assert tag.name == "receipt"


async def test_delete_tag(client, mock_router):
    mock_router.delete("/tags/1/").mock(return_value=Response(204))
    await client.delete_tag(1)


async def test_create_tag_invalidates_cache(client, mock_router):
    mock_router.get("/tags/").mock(return_value=Response(200, json=TAG_LIST))
    mock_router.post("/tags/").mock(return_value=Response(201, json={"id": 2, "name": "new"}))
    # Load cache
    await client.list_tags()
    # Create invalidates
    await client.create_tag(name="new")
    assert "tags" not in client._resolver._cache


# ---------------------------------------------------------------------------
# Tag model – all fields
# ---------------------------------------------------------------------------

async def test_tag_model_all_fields(client, mock_router):
    mock_router.get("/tags/1/").mock(return_value=Response(200, json=TAG_DATA_FULL))
    tag = await client.get_tag(1)
    assert tag.id == 1
    assert tag.name == "invoice"
    assert tag.slug == "invoice"
    assert tag.color == "#ff0000"
    assert tag.text_color == "#ffffff"
    assert tag.match == "invoice"
    assert tag.matching_algorithm == MatchingAlgorithm.EXACT
    assert tag.is_insensitive is True
    assert tag.is_inbox_tag is False
    assert tag.document_count == 42
    assert tag.owner == 1
    assert tag.user_can_change is True
    assert tag.parent is None
    assert tag.children == [2, 3]


# ---------------------------------------------------------------------------
# Tag 404 / NotFoundError tests
# ---------------------------------------------------------------------------

async def test_get_tag_not_found(client, mock_router):
    mock_router.get("/tags/999/").mock(return_value=Response(404, json={"detail": "Not found."}))
    with pytest.raises(NotFoundError):
        await client.get_tag(999)


async def test_update_tag_not_found(client, mock_router):
    mock_router.patch("/tags/999/").mock(return_value=Response(404, json={"detail": "Not found."}))
    with pytest.raises(NotFoundError):
        await client.update_tag(999, name="gone")


async def test_delete_tag_not_found(client, mock_router):
    mock_router.delete("/tags/999/").mock(return_value=Response(404, json={"detail": "Not found."}))
    with pytest.raises(NotFoundError):
        await client.delete_tag(999)


# ---------------------------------------------------------------------------
# create_tag – full payload with all optional parameters
# ---------------------------------------------------------------------------

async def test_create_tag_all_params(client, mock_router):
    captured: dict = {}
    mock_router.post("/tags/").mock(side_effect=_json_capturing_side_effect(
        captured, TAG_DATA_FULL, status=201,
    ))
    perms = SetPermissions(
        view=PermissionSet(users=[2], groups=[]),
        change=PermissionSet(users=[], groups=[1]),
    )
    tag = await client.create_tag(
        name="invoice",
        color="#ff0000",
        is_inbox_tag=False,
        match="invoice",
        matching_algorithm=MatchingAlgorithm.EXACT,
        is_insensitive=True,
        parent=None,
        owner=1,
        set_permissions=perms,
    )
    body = captured["body"]
    assert body["name"] == "invoice"
    assert body["color"] == "#ff0000"
    assert body["is_inbox_tag"] is False
    assert body["match"] == "invoice"
    assert body["matching_algorithm"] == 3
    assert body["is_insensitive"] is True
    assert body["owner"] == 1
    assert body["set_permissions"]["view"]["users"] == [2]
    assert body["set_permissions"]["change"]["groups"] == [1]
    assert isinstance(tag, Tag)


# ---------------------------------------------------------------------------
# update_tag – PATCH semantics (only non-None fields sent)
# ---------------------------------------------------------------------------

async def test_update_tag_only_sends_provided_fields(client, mock_router):
    captured: dict = {}
    mock_router.patch("/tags/1/").mock(side_effect=_json_capturing_side_effect(
        captured, {**TAG_DATA, "name": "receipt"},
    ))
    await client.update_tag(1, name="receipt")
    body = captured["body"]
    assert body == {"name": "receipt"}


async def test_update_tag_empty_patch(client, mock_router):
    captured: dict = {}
    mock_router.patch("/tags/1/").mock(side_effect=_json_capturing_side_effect(
        captured, TAG_DATA,
    ))
    await client.update_tag(1)
    assert captured["body"] == {}


# ---------------------------------------------------------------------------
# update_tag / delete_tag – cache invalidation
# ---------------------------------------------------------------------------

async def test_update_tag_invalidates_cache(client, mock_router):
    mock_router.get("/tags/").mock(return_value=Response(200, json=TAG_LIST))
    updated = {**TAG_DATA, "name": "receipt"}
    mock_router.patch("/tags/1/").mock(return_value=Response(200, json=updated))
    await client.list_tags()
    await client.update_tag(1, name="receipt")
    assert "tags" not in client._resolver._cache


async def test_delete_tag_invalidates_cache(client, mock_router):
    mock_router.get("/tags/").mock(return_value=Response(200, json=TAG_LIST))
    mock_router.delete("/tags/1/").mock(return_value=Response(204))
    await client.list_tags()
    await client.delete_tag(1)
    assert "tags" not in client._resolver._cache


# Correspondents
CORR_DATA = {"id": 1, "name": "ACME"}
CORR_DATA_FULL = {
    "id": 1,
    "name": "ACME",
    "slug": "acme",
    "match": "acme corp",
    "matching_algorithm": 3,
    "is_insensitive": True,
    "document_count": 15,
    "last_correspondence": "2026-01-15",
    "owner": 1,
    "user_can_change": True,
}
CORR_LIST = {"count": 1, "next": None, "previous": None, "results": [CORR_DATA]}


async def test_list_correspondents(client, mock_router):
    mock_router.get("/correspondents/").mock(return_value=Response(200, json=CORR_LIST))
    corrs = await client.list_correspondents()
    assert isinstance(corrs[0], Correspondent)


async def test_get_correspondent(client, mock_router):
    mock_router.get("/correspondents/1/").mock(return_value=Response(200, json=CORR_DATA))
    c = await client.get_correspondent(1)
    assert c.id == 1
    assert c.name == "ACME"


async def test_create_correspondent(client, mock_router):
    mock_router.post("/correspondents/").mock(return_value=Response(201, json=CORR_DATA))
    c = await client.create_correspondent(name="ACME")
    assert c.name == "ACME"


async def test_update_correspondent(client, mock_router):
    mock_router.patch("/correspondents/1/").mock(return_value=Response(200, json={**CORR_DATA, "name": "ACME Inc."}))
    c = await client.update_correspondent(1, name="ACME Inc.")
    assert c.name == "ACME Inc."


async def test_delete_correspondent(client, mock_router):
    mock_router.delete("/correspondents/1/").mock(return_value=Response(204))
    await client.delete_correspondent(1)


# ---------------------------------------------------------------------------
# Correspondent model – all fields
# ---------------------------------------------------------------------------

async def test_correspondent_model_all_fields(client, mock_router):
    mock_router.get("/correspondents/1/").mock(return_value=Response(200, json=CORR_DATA_FULL))
    c = await client.get_correspondent(1)
    assert c.id == 1
    assert c.name == "ACME"
    assert c.slug == "acme"
    assert c.match == "acme corp"
    assert c.matching_algorithm == MatchingAlgorithm.EXACT
    assert c.is_insensitive is True
    assert c.document_count == 15
    assert c.last_correspondence is not None
    assert c.last_correspondence.isoformat() == "2026-01-15"
    assert c.owner == 1
    assert c.user_can_change is True


# ---------------------------------------------------------------------------
# Correspondent 404 / NotFoundError tests
# ---------------------------------------------------------------------------

async def test_get_correspondent_not_found(client, mock_router):
    mock_router.get("/correspondents/999/").mock(return_value=Response(404, json={"detail": "Not found."}))
    with pytest.raises(NotFoundError):
        await client.get_correspondent(999)


async def test_update_correspondent_not_found(client, mock_router):
    mock_router.patch("/correspondents/999/").mock(return_value=Response(404, json={"detail": "Not found."}))
    with pytest.raises(NotFoundError):
        await client.update_correspondent(999, name="gone")


async def test_delete_correspondent_not_found(client, mock_router):
    mock_router.delete("/correspondents/999/").mock(return_value=Response(404, json={"detail": "Not found."}))
    with pytest.raises(NotFoundError):
        await client.delete_correspondent(999)


# ---------------------------------------------------------------------------
# create_correspondent – full payload with all optional parameters
# ---------------------------------------------------------------------------

async def test_create_correspondent_all_params(client, mock_router):
    captured: dict = {}
    mock_router.post("/correspondents/").mock(side_effect=_json_capturing_side_effect(
        captured, CORR_DATA_FULL, status=201,
    ))
    perms = SetPermissions(
        view=PermissionSet(users=[2], groups=[]),
        change=PermissionSet(users=[], groups=[1]),
    )
    c = await client.create_correspondent(
        name="ACME",
        match="acme corp",
        matching_algorithm=MatchingAlgorithm.EXACT,
        is_insensitive=True,
        owner=1,
        set_permissions=perms,
    )
    body = captured["body"]
    assert body["name"] == "ACME"
    assert body["match"] == "acme corp"
    assert body["matching_algorithm"] == 3
    assert body["is_insensitive"] is True
    assert body["owner"] == 1
    assert body["set_permissions"]["view"]["users"] == [2]
    assert body["set_permissions"]["change"]["groups"] == [1]
    assert isinstance(c, Correspondent)


# ---------------------------------------------------------------------------
# update_correspondent – PATCH semantics (only non-None fields sent)
# ---------------------------------------------------------------------------

async def test_update_correspondent_only_sends_provided_fields(client, mock_router):
    captured: dict = {}
    mock_router.patch("/correspondents/1/").mock(side_effect=_json_capturing_side_effect(
        captured, {**CORR_DATA, "name": "ACME Inc."},
    ))
    await client.update_correspondent(1, name="ACME Inc.")
    body = captured["body"]
    assert body == {"name": "ACME Inc."}


async def test_update_correspondent_empty_patch(client, mock_router):
    captured: dict = {}
    mock_router.patch("/correspondents/1/").mock(side_effect=_json_capturing_side_effect(
        captured, CORR_DATA,
    ))
    await client.update_correspondent(1)
    assert captured["body"] == {}


# ---------------------------------------------------------------------------
# Correspondent cache invalidation
# ---------------------------------------------------------------------------

async def test_create_correspondent_invalidates_cache(client, mock_router):
    mock_router.get("/correspondents/").mock(return_value=Response(200, json=CORR_LIST))
    mock_router.post("/correspondents/").mock(return_value=Response(201, json={"id": 2, "name": "NewCorp"}))
    await client.list_correspondents()
    await client.create_correspondent(name="NewCorp")
    assert "correspondents" not in client._resolver._cache


async def test_update_correspondent_invalidates_cache(client, mock_router):
    mock_router.get("/correspondents/").mock(return_value=Response(200, json=CORR_LIST))
    updated = {**CORR_DATA, "name": "ACME Inc."}
    mock_router.patch("/correspondents/1/").mock(return_value=Response(200, json=updated))
    await client.list_correspondents()
    await client.update_correspondent(1, name="ACME Inc.")
    assert "correspondents" not in client._resolver._cache


async def test_delete_correspondent_invalidates_cache(client, mock_router):
    mock_router.get("/correspondents/").mock(return_value=Response(200, json=CORR_LIST))
    mock_router.delete("/correspondents/1/").mock(return_value=Response(204))
    await client.list_correspondents()
    await client.delete_correspondent(1)
    assert "correspondents" not in client._resolver._cache


# Document Types
DT_DATA = {"id": 1, "name": "Invoice"}
DT_DATA_FULL = {
    "id": 1,
    "name": "Invoice",
    "slug": "invoice",
    "match": "invoice",
    "matching_algorithm": 3,
    "is_insensitive": True,
    "document_count": 25,
    "owner": 1,
    "user_can_change": True,
}
DT_LIST = {"count": 1, "next": None, "previous": None, "results": [DT_DATA]}


async def test_list_document_types(client, mock_router):
    mock_router.get("/document_types/").mock(return_value=Response(200, json=DT_LIST))
    dts = await client.list_document_types()
    assert isinstance(dts[0], DocumentType)


async def test_get_document_type(client, mock_router):
    mock_router.get("/document_types/1/").mock(return_value=Response(200, json=DT_DATA))
    dt = await client.get_document_type(1)
    assert dt.id == 1
    assert dt.name == "Invoice"


async def test_create_document_type(client, mock_router):
    mock_router.post("/document_types/").mock(return_value=Response(201, json=DT_DATA))
    dt = await client.create_document_type(name="Invoice")
    assert dt.name == "Invoice"


async def test_update_document_type(client, mock_router):
    updated = {**DT_DATA, "name": "Receipt"}
    mock_router.patch("/document_types/1/").mock(
        return_value=Response(200, json=updated),
    )
    dt = await client.update_document_type(1, name="Receipt")
    assert dt.name == "Receipt"


async def test_delete_document_type(client, mock_router):
    mock_router.delete("/document_types/1/").mock(return_value=Response(204))
    await client.delete_document_type(1)


# ---------------------------------------------------------------------------
# DocumentType model – all fields
# ---------------------------------------------------------------------------

async def test_document_type_model_all_fields(client, mock_router):
    mock_router.get("/document_types/1/").mock(return_value=Response(200, json=DT_DATA_FULL))
    dt = await client.get_document_type(1)
    assert dt.id == 1
    assert dt.name == "Invoice"
    assert dt.slug == "invoice"
    assert dt.match == "invoice"
    assert dt.matching_algorithm == MatchingAlgorithm.EXACT
    assert dt.is_insensitive is True
    assert dt.document_count == 25
    assert dt.owner == 1
    assert dt.user_can_change is True


# ---------------------------------------------------------------------------
# DocumentType 404 / NotFoundError tests
# ---------------------------------------------------------------------------

async def test_get_document_type_not_found(client, mock_router):
    not_found = Response(404, json={"detail": "Not found."})
    mock_router.get("/document_types/999/").mock(return_value=not_found)
    with pytest.raises(NotFoundError):
        await client.get_document_type(999)


async def test_update_document_type_not_found(client, mock_router):
    not_found = Response(404, json={"detail": "Not found."})
    mock_router.patch("/document_types/999/").mock(return_value=not_found)
    with pytest.raises(NotFoundError):
        await client.update_document_type(999, name="gone")


async def test_delete_document_type_not_found(client, mock_router):
    not_found = Response(404, json={"detail": "Not found."})
    mock_router.delete("/document_types/999/").mock(return_value=not_found)
    with pytest.raises(NotFoundError):
        await client.delete_document_type(999)


# ---------------------------------------------------------------------------
# create_document_type – full payload with all optional parameters
# ---------------------------------------------------------------------------

async def test_create_document_type_all_params(client, mock_router):
    captured: dict = {}
    mock_router.post("/document_types/").mock(side_effect=_json_capturing_side_effect(
        captured, DT_DATA_FULL, status=201,
    ))
    perms = SetPermissions(
        view=PermissionSet(users=[2], groups=[]),
        change=PermissionSet(users=[], groups=[1]),
    )
    dt = await client.create_document_type(
        name="Invoice",
        match="invoice",
        matching_algorithm=MatchingAlgorithm.EXACT,
        is_insensitive=True,
        owner=1,
        set_permissions=perms,
    )
    body = captured["body"]
    assert body["name"] == "Invoice"
    assert body["match"] == "invoice"
    assert body["matching_algorithm"] == 3
    assert body["is_insensitive"] is True
    assert body["owner"] == 1
    assert body["set_permissions"]["view"]["users"] == [2]
    assert body["set_permissions"]["change"]["groups"] == [1]
    assert isinstance(dt, DocumentType)


# ---------------------------------------------------------------------------
# update_document_type – PATCH semantics (only non-None fields sent)
# ---------------------------------------------------------------------------

async def test_update_document_type_only_sends_provided_fields(client, mock_router):
    captured: dict = {}
    mock_router.patch("/document_types/1/").mock(side_effect=_json_capturing_side_effect(
        captured, {**DT_DATA, "name": "Receipt"},
    ))
    await client.update_document_type(1, name="Receipt")
    body = captured["body"]
    assert body == {"name": "Receipt"}


async def test_update_document_type_empty_patch(client, mock_router):
    captured: dict = {}
    mock_router.patch("/document_types/1/").mock(side_effect=_json_capturing_side_effect(
        captured, DT_DATA,
    ))
    await client.update_document_type(1)
    assert captured["body"] == {}


# ---------------------------------------------------------------------------
# DocumentType cache invalidation
# ---------------------------------------------------------------------------

async def test_create_document_type_invalidates_cache(client, mock_router):
    mock_router.get("/document_types/").mock(return_value=Response(200, json=DT_LIST))
    new_dt = {"id": 2, "name": "Receipt"}
    mock_router.post("/document_types/").mock(return_value=Response(201, json=new_dt))
    await client.list_document_types()
    await client.create_document_type(name="Receipt")
    assert "document_types" not in client._resolver._cache


async def test_update_document_type_invalidates_cache(client, mock_router):
    mock_router.get("/document_types/").mock(return_value=Response(200, json=DT_LIST))
    updated = {**DT_DATA, "name": "Receipt"}
    mock_router.patch("/document_types/1/").mock(return_value=Response(200, json=updated))
    await client.list_document_types()
    await client.update_document_type(1, name="Receipt")
    assert "document_types" not in client._resolver._cache


async def test_delete_document_type_invalidates_cache(client, mock_router):
    mock_router.get("/document_types/").mock(return_value=Response(200, json=DT_LIST))
    mock_router.delete("/document_types/1/").mock(return_value=Response(204))
    await client.list_document_types()
    await client.delete_document_type(1)
    assert "document_types" not in client._resolver._cache


# Storage Paths
SP_DATA = {"id": 1, "name": "Archive", "path": "/docs/{created_year}/"}
SP_DATA_FULL = {
    "id": 1,
    "name": "Archive",
    "slug": "archive",
    "path": "{created_year}/{correspondent}/{title}",
    "match": "archive",
    "matching_algorithm": 3,
    "is_insensitive": True,
    "document_count": 30,
    "owner": 1,
    "user_can_change": True,
}
SP_LIST = {"count": 1, "next": None, "previous": None, "results": [SP_DATA]}


async def test_list_storage_paths(client, mock_router):
    mock_router.get("/storage_paths/").mock(return_value=Response(200, json=SP_LIST))
    sps = await client.list_storage_paths()
    assert isinstance(sps[0], StoragePath)
    assert sps[0].path == "/docs/{created_year}/"


async def test_get_storage_path(client, mock_router):
    mock_router.get("/storage_paths/1/").mock(return_value=Response(200, json=SP_DATA))
    sp = await client.get_storage_path(1)
    assert sp.id == 1
    assert sp.name == "Archive"


async def test_create_storage_path(client, mock_router):
    mock_router.post("/storage_paths/").mock(return_value=Response(201, json=SP_DATA))
    sp = await client.create_storage_path(name="Archive")
    assert sp.name == "Archive"


async def test_update_storage_path(client, mock_router):
    updated = {**SP_DATA, "name": "Deep Archive"}
    mock_router.patch("/storage_paths/1/").mock(return_value=Response(200, json=updated))
    sp = await client.update_storage_path(1, name="Deep Archive")
    assert sp.name == "Deep Archive"


async def test_delete_storage_path(client, mock_router):
    mock_router.delete("/storage_paths/1/").mock(return_value=Response(204))
    await client.delete_storage_path(1)


# ---------------------------------------------------------------------------
# StoragePath model – all fields
# ---------------------------------------------------------------------------

async def test_storage_path_model_all_fields(client, mock_router):
    mock_router.get("/storage_paths/1/").mock(return_value=Response(200, json=SP_DATA_FULL))
    sp = await client.get_storage_path(1)
    assert sp.id == 1
    assert sp.name == "Archive"
    assert sp.slug == "archive"
    assert sp.path == "{created_year}/{correspondent}/{title}"
    assert sp.match == "archive"
    assert sp.matching_algorithm == MatchingAlgorithm.EXACT
    assert sp.is_insensitive is True
    assert sp.document_count == 30
    assert sp.owner == 1
    assert sp.user_can_change is True


# ---------------------------------------------------------------------------
# StoragePath 404 / NotFoundError tests
# ---------------------------------------------------------------------------

async def test_get_storage_path_not_found(client, mock_router):
    not_found = Response(404, json={"detail": "Not found."})
    mock_router.get("/storage_paths/999/").mock(return_value=not_found)
    with pytest.raises(NotFoundError):
        await client.get_storage_path(999)


async def test_update_storage_path_not_found(client, mock_router):
    not_found = Response(404, json={"detail": "Not found."})
    mock_router.patch("/storage_paths/999/").mock(return_value=not_found)
    with pytest.raises(NotFoundError):
        await client.update_storage_path(999, name="gone")


async def test_delete_storage_path_not_found(client, mock_router):
    not_found = Response(404, json={"detail": "Not found."})
    mock_router.delete("/storage_paths/999/").mock(return_value=not_found)
    with pytest.raises(NotFoundError):
        await client.delete_storage_path(999)


# ---------------------------------------------------------------------------
# create_storage_path – full payload with all optional parameters
# ---------------------------------------------------------------------------

async def test_create_storage_path_all_params(client, mock_router):
    captured: dict = {}
    mock_router.post("/storage_paths/").mock(side_effect=_json_capturing_side_effect(
        captured, SP_DATA_FULL, status=201,
    ))
    perms = SetPermissions(
        view=PermissionSet(users=[2], groups=[]),
        change=PermissionSet(users=[], groups=[1]),
    )
    sp = await client.create_storage_path(
        name="Archive",
        path="{created_year}/{correspondent}/{title}",
        match="archive",
        matching_algorithm=MatchingAlgorithm.EXACT,
        is_insensitive=True,
        owner=1,
        set_permissions=perms,
    )
    body = captured["body"]
    assert body["name"] == "Archive"
    assert body["path"] == "{created_year}/{correspondent}/{title}"
    assert body["match"] == "archive"
    assert body["matching_algorithm"] == 3
    assert body["is_insensitive"] is True
    assert body["owner"] == 1
    assert body["set_permissions"]["view"]["users"] == [2]
    assert body["set_permissions"]["change"]["groups"] == [1]
    assert isinstance(sp, StoragePath)


# ---------------------------------------------------------------------------
# update_storage_path – PATCH semantics (only non-None fields sent)
# ---------------------------------------------------------------------------

async def test_update_storage_path_only_sends_provided_fields(client, mock_router):
    captured: dict = {}
    mock_router.patch("/storage_paths/1/").mock(side_effect=_json_capturing_side_effect(
        captured, {**SP_DATA, "name": "Deep Archive"},
    ))
    await client.update_storage_path(1, name="Deep Archive")
    body = captured["body"]
    assert body == {"name": "Deep Archive"}


async def test_update_storage_path_empty_patch(client, mock_router):
    captured: dict = {}
    mock_router.patch("/storage_paths/1/").mock(side_effect=_json_capturing_side_effect(
        captured, SP_DATA,
    ))
    await client.update_storage_path(1)
    assert captured["body"] == {}


async def test_update_storage_path_path_field(client, mock_router):
    captured: dict = {}
    updated = {**SP_DATA, "path": "{title}"}
    mock_router.patch("/storage_paths/1/").mock(side_effect=_json_capturing_side_effect(
        captured, updated,
    ))
    sp = await client.update_storage_path(1, path="{title}")
    assert captured["body"] == {"path": "{title}"}
    assert sp.path == "{title}"


# ---------------------------------------------------------------------------
# StoragePath cache invalidation
# ---------------------------------------------------------------------------

async def test_create_storage_path_invalidates_cache(client, mock_router):
    mock_router.get("/storage_paths/").mock(
        return_value=Response(200, json=SP_LIST),
    )
    new_sp = {"id": 2, "name": "NewPath"}
    mock_router.post("/storage_paths/").mock(
        return_value=Response(201, json=new_sp),
    )
    await client.list_storage_paths()
    await client.create_storage_path(name="NewPath")
    assert "storage_paths" not in client._resolver._cache


async def test_update_storage_path_invalidates_cache(client, mock_router):
    mock_router.get("/storage_paths/").mock(return_value=Response(200, json=SP_LIST))
    updated = {**SP_DATA, "name": "Deep Archive"}
    mock_router.patch("/storage_paths/1/").mock(return_value=Response(200, json=updated))
    await client.list_storage_paths()
    await client.update_storage_path(1, name="Deep Archive")
    assert "storage_paths" not in client._resolver._cache


async def test_delete_storage_path_invalidates_cache(client, mock_router):
    mock_router.get("/storage_paths/").mock(return_value=Response(200, json=SP_LIST))
    mock_router.delete("/storage_paths/1/").mock(return_value=Response(204))
    await client.list_storage_paths()
    await client.delete_storage_path(1)
    assert "storage_paths" not in client._resolver._cache


# Custom Fields
CF_DATA = {"id": 1, "name": "Amount", "data_type": "monetary"}
CF_DATA_FULL = {
    "id": 1,
    "name": "Amount",
    "data_type": "monetary",
    "extra_data": None,
    "document_count": 10,
}
CF_DATA_SELECT = {
    "id": 2,
    "name": "Priority",
    "data_type": "select",
    "extra_data": {
        "select_options": [
            {"id": "abc123", "label": "High"},
            {"id": "def456", "label": "Low"},
        ],
    },
    "document_count": 5,
}
CF_LIST = {"count": 1, "next": None, "previous": None, "results": [CF_DATA]}


async def test_list_custom_fields(client, mock_router):
    mock_router.get("/custom_fields/").mock(return_value=Response(200, json=CF_LIST))
    cfs = await client.list_custom_fields()
    assert isinstance(cfs[0], CustomField)


async def test_get_custom_field(client, mock_router):
    mock_router.get("/custom_fields/1/").mock(return_value=Response(200, json=CF_DATA))
    cf = await client.get_custom_field(1)
    assert cf.id == 1
    assert cf.name == "Amount"


async def test_create_custom_field(client, mock_router):
    mock_router.post("/custom_fields/").mock(return_value=Response(201, json=CF_DATA))
    cf = await client.create_custom_field(name="Amount", data_type="monetary")
    assert cf.data_type.value == "monetary"


async def test_update_custom_field(client, mock_router):
    updated = {**CF_DATA, "name": "Total Amount"}
    mock_router.patch("/custom_fields/1/").mock(return_value=Response(200, json=updated))
    cf = await client.update_custom_field(1, name="Total Amount")
    assert cf.name == "Total Amount"


async def test_delete_custom_field(client, mock_router):
    mock_router.delete("/custom_fields/1/").mock(return_value=Response(204))
    await client.delete_custom_field(1)


# ---------------------------------------------------------------------------
# CustomField model – all fields
# ---------------------------------------------------------------------------

async def test_custom_field_model_all_fields(client, mock_router):
    mock_router.get("/custom_fields/1/").mock(return_value=Response(200, json=CF_DATA_FULL))
    cf = await client.get_custom_field(1)
    assert cf.id == 1
    assert cf.name == "Amount"
    assert cf.data_type.value == "monetary"
    assert cf.extra_data is None
    assert cf.document_count == 10


async def test_custom_field_model_select_type(client, mock_router):
    mock_router.get("/custom_fields/2/").mock(return_value=Response(200, json=CF_DATA_SELECT))
    cf = await client.get_custom_field(2)
    assert cf.id == 2
    assert cf.name == "Priority"
    assert cf.data_type.value == "select"
    assert cf.extra_data is not None
    assert len(cf.extra_data["select_options"]) == 2
    assert cf.extra_data["select_options"][0]["label"] == "High"
    assert cf.document_count == 5


# ---------------------------------------------------------------------------
# CustomField 404 / NotFoundError tests
# ---------------------------------------------------------------------------

async def test_get_custom_field_not_found(client, mock_router):
    not_found = Response(404, json={"detail": "Not found."})
    mock_router.get("/custom_fields/999/").mock(return_value=not_found)
    with pytest.raises(NotFoundError):
        await client.get_custom_field(999)


async def test_update_custom_field_not_found(client, mock_router):
    not_found = Response(404, json={"detail": "Not found."})
    mock_router.patch("/custom_fields/999/").mock(return_value=not_found)
    with pytest.raises(NotFoundError):
        await client.update_custom_field(999, name="gone")


async def test_delete_custom_field_not_found(client, mock_router):
    not_found = Response(404, json={"detail": "Not found."})
    mock_router.delete("/custom_fields/999/").mock(return_value=not_found)
    with pytest.raises(NotFoundError):
        await client.delete_custom_field(999)


# ---------------------------------------------------------------------------
# create_custom_field – full payload with all optional parameters
# ---------------------------------------------------------------------------

async def test_create_custom_field_all_params(client, mock_router):
    captured: dict = {}
    mock_router.post("/custom_fields/").mock(side_effect=_json_capturing_side_effect(
        captured, CF_DATA_FULL, status=201,
    ))
    perms = SetPermissions(
        view=PermissionSet(users=[2], groups=[]),
        change=PermissionSet(users=[], groups=[1]),
    )
    cf = await client.create_custom_field(
        name="Amount",
        data_type="monetary",
        owner=1,
        set_permissions=perms,
    )
    body = captured["body"]
    assert body["name"] == "Amount"
    assert body["data_type"] == "monetary"
    assert body["owner"] == 1
    assert body["set_permissions"]["view"]["users"] == [2]
    assert body["set_permissions"]["change"]["groups"] == [1]
    assert isinstance(cf, CustomField)


async def test_create_custom_field_select_with_extra_data(client, mock_router):
    captured: dict = {}
    mock_router.post("/custom_fields/").mock(side_effect=_json_capturing_side_effect(
        captured, CF_DATA_SELECT, status=201,
    ))
    cf = await client.create_custom_field(
        name="Priority",
        data_type="select",
        extra_data={"select_options": ["High", "Low"]},
    )
    body = captured["body"]
    assert body["name"] == "Priority"
    assert body["data_type"] == "select"
    assert body["extra_data"] == {"select_options": ["High", "Low"]}
    assert isinstance(cf, CustomField)
    assert cf.data_type.value == "select"


# ---------------------------------------------------------------------------
# update_custom_field – PATCH semantics (only non-None fields sent)
# ---------------------------------------------------------------------------

async def test_update_custom_field_only_sends_provided_fields(client, mock_router):
    captured: dict = {}
    mock_router.patch("/custom_fields/1/").mock(side_effect=_json_capturing_side_effect(
        captured, {**CF_DATA, "name": "Total Amount"},
    ))
    await client.update_custom_field(1, name="Total Amount")
    body = captured["body"]
    assert body == {"name": "Total Amount"}


async def test_update_custom_field_empty_patch(client, mock_router):
    captured: dict = {}
    mock_router.patch("/custom_fields/1/").mock(side_effect=_json_capturing_side_effect(
        captured, CF_DATA,
    ))
    await client.update_custom_field(1)
    assert captured["body"] == {}


async def test_update_custom_field_extra_data(client, mock_router):
    captured: dict = {}
    updated = {**CF_DATA_SELECT, "extra_data": {"select_options": [
        {"id": "abc123", "label": "High"},
        {"id": "def456", "label": "Low"},
        {"id": "ghi789", "label": "Medium"},
    ]}}
    mock_router.patch("/custom_fields/2/").mock(side_effect=_json_capturing_side_effect(
        captured, updated,
    ))
    await client.update_custom_field(
        2, extra_data={"select_options": ["High", "Low", "Medium"]},
    )
    body = captured["body"]
    assert body == {"extra_data": {"select_options": ["High", "Low", "Medium"]}}


# ---------------------------------------------------------------------------
# Custom Fields cache invalidation
# ---------------------------------------------------------------------------

async def test_create_custom_field_invalidates_cache(client, mock_router):
    mock_router.get("/custom_fields/").mock(
        return_value=Response(200, json=CF_LIST),
    )
    new_cf = {"id": 2, "name": "Priority", "data_type": "select"}
    mock_router.post("/custom_fields/").mock(
        return_value=Response(201, json=new_cf),
    )
    await client.list_custom_fields()
    await client.create_custom_field(name="Priority", data_type="select")
    assert "custom_fields" not in client._resolver._cache


async def test_update_custom_field_invalidates_cache(client, mock_router):
    mock_router.get("/custom_fields/").mock(return_value=Response(200, json=CF_LIST))
    updated = {**CF_DATA, "name": "Total Amount"}
    mock_router.patch("/custom_fields/1/").mock(return_value=Response(200, json=updated))
    await client.list_custom_fields()
    await client.update_custom_field(1, name="Total Amount")
    assert "custom_fields" not in client._resolver._cache


async def test_delete_custom_field_invalidates_cache(client, mock_router):
    mock_router.get("/custom_fields/").mock(return_value=Response(200, json=CF_LIST))
    mock_router.delete("/custom_fields/1/").mock(return_value=Response(204))
    await client.list_custom_fields()
    await client.delete_custom_field(1)
    assert "custom_fields" not in client._resolver._cache


# ---------------------------------------------------------------------------
# list_* filter parameters: ids and name_contains
# ---------------------------------------------------------------------------

# Tags

async def test_list_tags_ids(client, mock_router):
    captured: dict = {}
    mock_router.get("/tags/").mock(side_effect=_capturing_side_effect(captured, TAG_LIST))
    tags = await client.list_tags(ids=[1, 2])
    assert len(tags) == 1
    assert captured["params"]["id__in"] == "1,2"


async def test_list_tags_name_contains(client, mock_router):
    captured: dict = {}
    mock_router.get("/tags/").mock(side_effect=_capturing_side_effect(captured, TAG_LIST))
    await client.list_tags(name_contains="voice")
    assert captured["params"]["name__icontains"] == "voice"


async def test_list_tags_ids_and_name_contains(client, mock_router):
    captured: dict = {}
    mock_router.get("/tags/").mock(side_effect=_capturing_side_effect(captured, TAG_LIST))
    await client.list_tags(ids=[1], name_contains="inv")
    assert captured["params"]["id__in"] == "1"
    assert captured["params"]["name__icontains"] == "inv"


async def test_list_tags_no_filter_sends_no_params(client, mock_router):
    captured: dict = {}
    mock_router.get("/tags/").mock(side_effect=_capturing_side_effect(captured, TAG_LIST))
    await client.list_tags()
    assert "id__in" not in captured["params"]
    assert "name__icontains" not in captured["params"]


# Correspondents

async def test_list_correspondents_ids(client, mock_router):
    captured: dict = {}
    mock_router.get("/correspondents/").mock(side_effect=_capturing_side_effect(captured, CORR_LIST))
    corrs = await client.list_correspondents(ids=[1, 2])
    assert len(corrs) == 1
    assert captured["params"]["id__in"] == "1,2"


async def test_list_correspondents_name_contains(client, mock_router):
    captured: dict = {}
    mock_router.get("/correspondents/").mock(side_effect=_capturing_side_effect(captured, CORR_LIST))
    await client.list_correspondents(name_contains="ACM")
    assert captured["params"]["name__icontains"] == "ACM"


async def test_list_correspondents_ids_and_name_contains(client, mock_router):
    captured: dict = {}
    mock_router.get("/correspondents/").mock(side_effect=_capturing_side_effect(captured, CORR_LIST))
    await client.list_correspondents(ids=[1], name_contains="AC")
    assert captured["params"]["id__in"] == "1"
    assert captured["params"]["name__icontains"] == "AC"


# Document Types

async def test_list_document_types_ids(client, mock_router):
    captured: dict = {}
    mock_router.get("/document_types/").mock(side_effect=_capturing_side_effect(captured, DT_LIST))
    dts = await client.list_document_types(ids=[1, 2])
    assert len(dts) == 1
    assert captured["params"]["id__in"] == "1,2"


async def test_list_document_types_name_contains(client, mock_router):
    captured: dict = {}
    mock_router.get("/document_types/").mock(side_effect=_capturing_side_effect(captured, DT_LIST))
    await client.list_document_types(name_contains="Inv")
    assert captured["params"]["name__icontains"] == "Inv"


async def test_list_document_types_ids_and_name_contains(client, mock_router):
    captured: dict = {}
    mock_router.get("/document_types/").mock(side_effect=_capturing_side_effect(captured, DT_LIST))
    await client.list_document_types(ids=[1], name_contains="Inv")
    assert captured["params"]["id__in"] == "1"
    assert captured["params"]["name__icontains"] == "Inv"


# Storage Paths

async def test_list_storage_paths_ids(client, mock_router):
    captured: dict = {}
    mock_router.get("/storage_paths/").mock(side_effect=_capturing_side_effect(captured, SP_LIST))
    sps = await client.list_storage_paths(ids=[1, 2])
    assert len(sps) == 1
    assert captured["params"]["id__in"] == "1,2"


async def test_list_storage_paths_name_contains(client, mock_router):
    captured: dict = {}
    mock_router.get("/storage_paths/").mock(side_effect=_capturing_side_effect(captured, SP_LIST))
    await client.list_storage_paths(name_contains="Arch")
    assert captured["params"]["name__icontains"] == "Arch"


async def test_list_storage_paths_ids_and_name_contains(client, mock_router):
    captured: dict = {}
    mock_router.get("/storage_paths/").mock(side_effect=_capturing_side_effect(captured, SP_LIST))
    await client.list_storage_paths(ids=[1], name_contains="Arch")
    assert captured["params"]["id__in"] == "1"
    assert captured["params"]["name__icontains"] == "Arch"


# ---------------------------------------------------------------------------
# page / page_size / ordering for all resource list methods
# ---------------------------------------------------------------------------

async def test_list_tags_page_size_ordering(client, mock_router):
    captured: dict = {}
    mock_router.get("/tags/").mock(side_effect=_capturing_side_effect(captured, TAG_LIST))
    await client.list_tags(page=2, page_size=10, ordering="name", descending=True)
    assert captured["params"]["page"] == "2"
    assert captured["params"]["page_size"] == "10"
    assert captured["params"]["ordering"] == "-name"


async def test_list_tags_ordering_asc(client, mock_router):
    captured: dict = {}
    mock_router.get("/tags/").mock(side_effect=_capturing_side_effect(captured, TAG_LIST))
    await client.list_tags(ordering="name")
    assert captured["params"]["ordering"] == "name"


async def test_list_correspondents_page_size_ordering(client, mock_router):
    captured: dict = {}
    mock_router.get("/correspondents/").mock(side_effect=_capturing_side_effect(captured, CORR_LIST))
    await client.list_correspondents(page=1, page_size=5, ordering="name", descending=True)
    assert captured["params"]["page"] == "1"
    assert captured["params"]["page_size"] == "5"
    assert captured["params"]["ordering"] == "-name"


async def test_list_document_types_page_size_ordering(client, mock_router):
    captured: dict = {}
    mock_router.get("/document_types/").mock(side_effect=_capturing_side_effect(captured, DT_LIST))
    await client.list_document_types(page=3, page_size=20, ordering="id")
    assert captured["params"]["page"] == "3"
    assert captured["params"]["page_size"] == "20"
    assert captured["params"]["ordering"] == "id"


async def test_list_document_types_descending(client, mock_router):
    captured: dict = {}
    mock_router.get("/document_types/").mock(side_effect=_capturing_side_effect(captured, DT_LIST))
    await client.list_document_types(ordering="name", descending=True)
    assert captured["params"]["ordering"] == "-name"


async def test_list_storage_paths_page_size_ordering(client, mock_router):
    captured: dict = {}
    mock_router.get("/storage_paths/").mock(side_effect=_capturing_side_effect(captured, SP_LIST))
    await client.list_storage_paths(page=2, page_size=10, ordering="name", descending=True)
    assert captured["params"]["page"] == "2"
    assert captured["params"]["page_size"] == "10"
    assert captured["params"]["ordering"] == "-name"


async def test_list_custom_fields_page_size_ordering(client, mock_router):
    captured: dict = {}
    mock_router.get("/custom_fields/").mock(side_effect=_capturing_side_effect(captured, CF_LIST))
    await client.list_custom_fields(page=1, page_size=50, ordering="name", descending=False)
    assert captured["params"]["page"] == "1"
    assert captured["params"]["page_size"] == "50"
    assert captured["params"]["ordering"] == "name"


async def test_list_custom_fields_ordering_desc(client, mock_router):
    captured: dict = {}
    mock_router.get("/custom_fields/").mock(side_effect=_capturing_side_effect(captured, CF_LIST))
    await client.list_custom_fields(ordering="id", descending=True)
    assert captured["params"]["ordering"] == "-id"


async def test_list_tags_no_pagination_params_sends_no_page(client, mock_router):
    """When page/page_size/ordering are omitted, they must not appear in the request."""
    captured: dict = {}
    mock_router.get("/tags/").mock(side_effect=_capturing_side_effect(captured, TAG_LIST))
    await client.list_tags()
    assert "page" not in captured["params"]
    assert "page_size" not in captured["params"]
    assert "ordering" not in captured["params"]
