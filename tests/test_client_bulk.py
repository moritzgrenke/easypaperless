"""Tests for PaperlessClient bulk operations."""

from __future__ import annotations

import json

from httpx import Response

from easypaperless.models.permissions import PermissionSet, SetPermissions


def _payload(route) -> dict:
    """Extract the JSON payload from the last POST call on a respx route."""
    return json.loads(route.calls.last.request.content)


async def test_bulk_edit_raw(client, mock_router):
    route = mock_router.post("/documents/bulk_edit/").mock(return_value=Response(200, json={}))
    await client.documents.bulk_edit([1, 2, 3], "delete")
    body = _payload(route)
    assert body == {"documents": [1, 2, 3], "method": "delete", "parameters": {}}


async def test_bulk_delete(client, mock_router):
    route = mock_router.post("/documents/bulk_edit/").mock(return_value=Response(200, json={}))
    await client.documents.bulk_delete([1, 2])
    body = _payload(route)
    assert body["documents"] == [1, 2]
    assert body["method"] == "delete"
    assert body["parameters"] == {}


async def test_bulk_add_tag_by_id(client, mock_router):
    route = mock_router.post("/documents/bulk_edit/").mock(return_value=Response(200, json={}))
    await client.documents.bulk_add_tag([1, 2], 5)
    body = _payload(route)
    assert body["documents"] == [1, 2]
    assert body["method"] == "add_tag"
    assert body["parameters"] == {"tag": 5}


async def test_bulk_add_tag_by_name(client, mock_router):
    tags_resp = {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [{"id": 5, "name": "urgent"}],
    }
    mock_router.get("/tags/").mock(return_value=Response(200, json=tags_resp))
    route = mock_router.post("/documents/bulk_edit/").mock(return_value=Response(200, json={}))
    await client.documents.bulk_add_tag([1], "urgent")
    body = _payload(route)
    assert body["documents"] == [1]
    assert body["method"] == "add_tag"
    assert body["parameters"] == {"tag": 5}


async def test_bulk_remove_tag(client, mock_router):
    route = mock_router.post("/documents/bulk_edit/").mock(return_value=Response(200, json={}))
    await client.documents.bulk_remove_tag([1, 2], 5)
    body = _payload(route)
    assert body["documents"] == [1, 2]
    assert body["method"] == "remove_tag"
    assert body["parameters"] == {"tag": 5}


async def test_bulk_modify_tags(client, mock_router):
    route = mock_router.post("/documents/bulk_edit/").mock(return_value=Response(200, json={}))
    await client.documents.bulk_modify_tags([1, 2], add_tags=[3], remove_tags=[4])
    body = _payload(route)
    assert body["documents"] == [1, 2]
    assert body["method"] == "modify_tags"
    assert body["parameters"] == {"add_tags": [3], "remove_tags": [4]}


async def test_bulk_set_correspondent_by_id(client, mock_router):
    route = mock_router.post("/documents/bulk_edit/").mock(return_value=Response(200, json={}))
    await client.documents.bulk_set_correspondent([1, 2], 10)
    body = _payload(route)
    assert body["documents"] == [1, 2]
    assert body["method"] == "set_correspondent"
    assert body["parameters"] == {"correspondent": 10}


async def test_bulk_set_correspondent_by_name(client, mock_router):
    cors_resp = {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [{"id": 10, "name": "Acme Corp"}],
    }
    mock_router.get("/correspondents/").mock(return_value=Response(200, json=cors_resp))
    route = mock_router.post("/documents/bulk_edit/").mock(return_value=Response(200, json={}))
    await client.documents.bulk_set_correspondent([1, 2], "Acme Corp")
    body = _payload(route)
    assert body["parameters"] == {"correspondent": 10}


async def test_bulk_set_correspondent_none(client, mock_router):
    route = mock_router.post("/documents/bulk_edit/").mock(return_value=Response(200, json={}))
    await client.documents.bulk_set_correspondent([1, 2], None)
    body = _payload(route)
    assert body["method"] == "set_correspondent"
    assert body["parameters"] == {"correspondent": None}


async def test_bulk_set_document_type_by_id(client, mock_router):
    route = mock_router.post("/documents/bulk_edit/").mock(return_value=Response(200, json={}))
    await client.documents.bulk_set_document_type([1, 2], 3)
    body = _payload(route)
    assert body["documents"] == [1, 2]
    assert body["method"] == "set_document_type"
    assert body["parameters"] == {"document_type": 3}


async def test_bulk_set_document_type_by_name(client, mock_router):
    dt_resp = {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [{"id": 3, "name": "Invoice"}],
    }
    mock_router.get("/document_types/").mock(return_value=Response(200, json=dt_resp))
    route = mock_router.post("/documents/bulk_edit/").mock(return_value=Response(200, json={}))
    await client.documents.bulk_set_document_type([1, 2], "Invoice")
    body = _payload(route)
    assert body["parameters"] == {"document_type": 3}


async def test_bulk_set_document_type_none(client, mock_router):
    route = mock_router.post("/documents/bulk_edit/").mock(return_value=Response(200, json={}))
    await client.documents.bulk_set_document_type([1, 2], None)
    body = _payload(route)
    assert body["method"] == "set_document_type"
    assert body["parameters"] == {"document_type": None}


async def test_bulk_set_storage_path_by_id(client, mock_router):
    route = mock_router.post("/documents/bulk_edit/").mock(return_value=Response(200, json={}))
    await client.documents.bulk_set_storage_path([1, 2], 7)
    body = _payload(route)
    assert body["documents"] == [1, 2]
    assert body["method"] == "set_storage_path"
    assert body["parameters"] == {"storage_path": 7}


async def test_bulk_set_storage_path_by_name(client, mock_router):
    sp_resp = {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [{"id": 7, "name": "Archive/2024"}],
    }
    mock_router.get("/storage_paths/").mock(return_value=Response(200, json=sp_resp))
    route = mock_router.post("/documents/bulk_edit/").mock(return_value=Response(200, json={}))
    await client.documents.bulk_set_storage_path([1, 2], "Archive/2024")
    body = _payload(route)
    assert body["parameters"] == {"storage_path": 7}


async def test_bulk_set_storage_path_none(client, mock_router):
    route = mock_router.post("/documents/bulk_edit/").mock(return_value=Response(200, json={}))
    await client.documents.bulk_set_storage_path([1, 2], None)
    body = _payload(route)
    assert body["method"] == "set_storage_path"
    assert body["parameters"] == {"storage_path": None}


async def test_bulk_modify_custom_fields(client, mock_router):
    route = mock_router.post("/documents/bulk_edit/").mock(return_value=Response(200, json={}))
    await client.documents.bulk_modify_custom_fields(
        [1, 2],
        add_fields=[{"field": 1, "value": "hello"}],
        remove_fields=[2],
    )
    body = _payload(route)
    assert body["documents"] == [1, 2]
    assert body["method"] == "modify_custom_fields"
    assert body["parameters"] == {
        "add_custom_fields": [{"field": 1, "value": "hello"}],
        "remove_custom_fields": [2],
    }


async def test_bulk_modify_custom_fields_defaults(client, mock_router):
    route = mock_router.post("/documents/bulk_edit/").mock(return_value=Response(200, json={}))
    await client.documents.bulk_modify_custom_fields([1, 2])
    body = _payload(route)
    assert body["method"] == "modify_custom_fields"
    assert body["parameters"] == {"add_custom_fields": [], "remove_custom_fields": []}


async def test_bulk_set_permissions(client, mock_router):
    route = mock_router.post("/documents/bulk_edit/").mock(return_value=Response(200, json={}))
    perms = SetPermissions(
        view=PermissionSet(users=[1, 2], groups=[]),
        change=PermissionSet(users=[1], groups=[]),
    )
    await client.documents.bulk_set_permissions([1, 2], set_permissions=perms, owner=1)
    body = _payload(route)
    assert body["documents"] == [1, 2]
    assert body["method"] == "set_permissions"
    assert body["parameters"]["owner"] == 1
    assert body["parameters"]["merge"] is False
    assert body["parameters"]["set_permissions"] == {
        "view": {"users": [1, 2], "groups": []},
        "change": {"users": [1], "groups": []},
    }


async def test_bulk_set_permissions_merge(client, mock_router):
    route = mock_router.post("/documents/bulk_edit/").mock(return_value=Response(200, json={}))
    await client.documents.bulk_set_permissions([1, 2], owner=5, merge=True)
    body = _payload(route)
    assert body["method"] == "set_permissions"
    assert body["parameters"]["owner"] == 5
    assert body["parameters"]["merge"] is True
    assert "set_permissions" not in body["parameters"]


async def test_bulk_edit_objects(client, mock_router):
    route = mock_router.post("/bulk_edit_objects/").mock(return_value=Response(200, json={}))
    await client.bulk_edit_objects("tags", [1, 2], "delete")
    body = _payload(route)
    assert body == {"objects": [1, 2], "object_type": "tags", "operation": "delete"}


async def test_bulk_delete_tags(client, mock_router):
    route = mock_router.post("/bulk_edit_objects/").mock(return_value=Response(200, json={}))
    await client.tags.bulk_delete([1, 2])
    body = _payload(route)
    assert body["object_type"] == "tags"
    assert body["objects"] == [1, 2]
    assert body["operation"] == "delete"


async def test_bulk_delete_correspondents(client, mock_router):
    route = mock_router.post("/bulk_edit_objects/").mock(return_value=Response(200, json={}))
    await client.correspondents.bulk_delete([3, 4])
    body = _payload(route)
    assert body["object_type"] == "correspondents"
    assert body["objects"] == [3, 4]
    assert body["operation"] == "delete"


async def test_bulk_delete_document_types(client, mock_router):
    route = mock_router.post("/bulk_edit_objects/").mock(return_value=Response(200, json={}))
    await client.document_types.bulk_delete([5, 6])
    body = _payload(route)
    assert body["object_type"] == "document_types"
    assert body["objects"] == [5, 6]
    assert body["operation"] == "delete"


async def test_bulk_delete_storage_paths(client, mock_router):
    route = mock_router.post("/bulk_edit_objects/").mock(return_value=Response(200, json={}))
    await client.storage_paths.bulk_delete([7, 8])
    body = _payload(route)
    assert body["object_type"] == "storage_paths"
    assert body["objects"] == [7, 8]
    assert body["operation"] == "delete"


async def test_bulk_set_permissions_tags(client, mock_router):
    route = mock_router.post("/bulk_edit_objects/").mock(return_value=Response(200, json={}))
    perms = SetPermissions(
        view=PermissionSet(users=[1], groups=[]),
        change=PermissionSet(users=[1], groups=[]),
    )
    await client.tags.bulk_set_permissions([1, 2], set_permissions=perms, owner=1)
    body = _payload(route)
    assert body["object_type"] == "tags"
    assert body["objects"] == [1, 2]
    assert body["operation"] == "set_permissions"
    assert body["owner"] == 1
    assert body["merge"] is False


async def test_bulk_set_permissions_correspondents(client, mock_router):
    route = mock_router.post("/bulk_edit_objects/").mock(return_value=Response(200, json={}))
    await client.correspondents.bulk_set_permissions([1, 2], owner=2, merge=True)
    body = _payload(route)
    assert body["object_type"] == "correspondents"
    assert body["operation"] == "set_permissions"
    assert body["owner"] == 2
    assert body["merge"] is True


async def test_bulk_set_permissions_document_types(client, mock_router):
    route = mock_router.post("/bulk_edit_objects/").mock(return_value=Response(200, json={}))
    await client.document_types.bulk_set_permissions([3], owner=5)
    body = _payload(route)
    assert body["object_type"] == "document_types"
    assert body["operation"] == "set_permissions"
    assert body["owner"] == 5


async def test_bulk_set_permissions_storage_paths(client, mock_router):
    route = mock_router.post("/bulk_edit_objects/").mock(return_value=Response(200, json={}))
    await client.storage_paths.bulk_set_permissions([4, 5], merge=True)
    body = _payload(route)
    assert body["object_type"] == "storage_paths"
    assert body["operation"] == "set_permissions"
    assert body["merge"] is True
