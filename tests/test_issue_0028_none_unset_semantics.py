"""Tests for issue #0028 — Fix None/Unset Semantics and Public Unset Alias.

Covers:
- Public Unset/UNSET alias exported from easypaperless namespace
- _create_resource three-way set_permissions logic (UNSET / None / SetPermissions)
- _update_resource three-way set_permissions logic (UNSET / None / SetPermissions)
- Non-nullable params default to UNSET (absent from payload when omitted)
- set_permissions pass-through in resource create() and update() methods
- CustomFieldsResource.update() has owner and set_permissions params
- Sync mirror pass-through for set_permissions
"""

from __future__ import annotations

import json

import pytest
import respx
from httpx import Response

from easypaperless._internal.sentinel import UNSET, _Unset
from easypaperless.client import PaperlessClient
from easypaperless.models.permissions import PermissionSet, SetPermissions
from easypaperless.sync import SyncPaperlessClient

BASE_URL = "http://paperless.test"
API_KEY = "test-api-key"
API_BASE = BASE_URL + "/api"

TAG_DATA = {"id": 1, "name": "invoice"}
CORR_DATA = {"id": 1, "name": "ACME"}
DT_DATA = {"id": 1, "name": "Invoice"}
SP_DATA = {"id": 1, "name": "archive", "path": "/archive/{title}"}
CF_DATA = {"id": 1, "name": "Amount", "data_type": "string"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _json_capture(captured: dict, response_data: dict, *, status: int = 200):
    """Side-effect that stores the parsed JSON body and returns response_data."""

    def _side_effect(request):
        captured["body"] = json.loads(request.content)
        return Response(status, json=response_data)

    return _side_effect


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_router():
    with respx.mock(base_url=API_BASE, assert_all_called=False) as router:
        yield router


@pytest.fixture
async def client(mock_router):
    async with PaperlessClient(url=BASE_URL, api_token=API_KEY) as c:
        yield c


# ===========================================================================
# 1. Public Unset alias
# ===========================================================================


def test_unset_type_importable_from_public_namespace():
    from easypaperless import Unset as PublicUnset

    assert PublicUnset is _Unset


def test_unset_type_in_package_all():
    import easypaperless

    assert "Unset" in easypaperless.__all__


def test_unset_constant_importable_from_public_namespace():
    from easypaperless import UNSET as PublicUNSET

    assert PublicUNSET is UNSET


def test_unset_constant_in_package_all():
    import easypaperless

    assert "UNSET" in easypaperless.__all__


def test_unset_value_is_instance_of_public_unset_type():
    from easypaperless import UNSET as PublicUNSET
    from easypaperless import Unset as PublicUnset

    assert isinstance(PublicUNSET, PublicUnset)


# ===========================================================================
# 2. _create_resource — three-way set_permissions logic
# ===========================================================================


async def test_create_resource_set_permissions_unset_omits_key(client, mock_router):
    """UNSET (default) must NOT include set_permissions in the POST body."""
    captured: dict = {}
    mock_router.post("/tags/").mock(side_effect=_json_capture(captured, TAG_DATA, status=201))
    await client.tags.create(name="test")
    assert "set_permissions" not in captured["body"]


async def test_create_resource_set_permissions_none_sends_empty(client, mock_router):
    """set_permissions=None must send SetPermissions().model_dump() in the POST body."""
    captured: dict = {}
    mock_router.post("/tags/").mock(side_effect=_json_capture(captured, TAG_DATA, status=201))
    await client.tags.create(name="test", set_permissions=None)
    assert "set_permissions" in captured["body"]
    expected = SetPermissions().model_dump()
    assert captured["body"]["set_permissions"] == expected


async def test_create_resource_set_permissions_value_sends_model_dump(client, mock_router):
    """set_permissions=SetPermissions(...) must send its model_dump() in the POST body."""
    captured: dict = {}
    mock_router.post("/tags/").mock(side_effect=_json_capture(captured, TAG_DATA, status=201))
    perms = SetPermissions(
        view=PermissionSet(users=[1, 2], groups=[]),
        change=PermissionSet(users=[3], groups=[10]),
    )
    await client.tags.create(name="test", set_permissions=perms)
    assert "set_permissions" in captured["body"]
    assert captured["body"]["set_permissions"] == perms.model_dump()


async def test_create_resource_set_permissions_explicit_unset_same_as_omitted(client, mock_router):
    """Passing set_permissions=UNSET explicitly is identical to omitting it."""
    captured: dict = {}
    mock_router.post("/tags/").mock(side_effect=_json_capture(captured, TAG_DATA, status=201))
    await client.tags.create(name="test", set_permissions=UNSET)
    assert "set_permissions" not in captured["body"]


# ===========================================================================
# 3. _update_resource — three-way set_permissions logic
# ===========================================================================


async def test_update_resource_set_permissions_unset_omits_key(client, mock_router):
    """UNSET (default) must NOT include set_permissions in the PATCH body."""
    captured: dict = {}
    mock_router.patch("/tags/1/").mock(side_effect=_json_capture(captured, TAG_DATA))
    await client.tags.update(1, name="receipt")
    assert "set_permissions" not in captured["body"]


async def test_update_resource_set_permissions_none_sends_empty(client, mock_router):
    """set_permissions=None must send SetPermissions().model_dump() in the PATCH body."""
    captured: dict = {}
    mock_router.patch("/tags/1/").mock(side_effect=_json_capture(captured, TAG_DATA))
    await client.tags.update(1, set_permissions=None)
    assert "set_permissions" in captured["body"]
    expected = SetPermissions().model_dump()
    assert captured["body"]["set_permissions"] == expected


async def test_update_resource_set_permissions_value_sends_model_dump(client, mock_router):
    """set_permissions=SetPermissions(...) must send its model_dump() in the PATCH body."""
    captured: dict = {}
    mock_router.patch("/tags/1/").mock(side_effect=_json_capture(captured, TAG_DATA))
    perms = SetPermissions(
        view=PermissionSet(users=[5], groups=[]),
        change=PermissionSet(users=[], groups=[]),
    )
    await client.tags.update(1, set_permissions=perms)
    assert "set_permissions" in captured["body"]
    assert captured["body"]["set_permissions"] == perms.model_dump()


async def test_update_resource_set_permissions_explicit_unset_same_as_omitted(client, mock_router):
    """Passing set_permissions=UNSET explicitly is identical to omitting it."""
    captured: dict = {}
    mock_router.patch("/tags/1/").mock(side_effect=_json_capture(captured, TAG_DATA))
    await client.tags.update(1, set_permissions=UNSET)
    assert "set_permissions" not in captured["body"]


# ===========================================================================
# 4. Non-nullable params absent from payload when UNSET
# ===========================================================================


async def test_tags_create_non_nullable_params_absent_when_omitted(client, mock_router):
    """color, is_inbox_tag, match, matching_algorithm must not appear when omitted."""
    captured: dict = {}
    mock_router.post("/tags/").mock(side_effect=_json_capture(captured, TAG_DATA, status=201))
    await client.tags.create(name="test")
    body = captured["body"]
    assert "color" not in body
    assert "is_inbox_tag" not in body
    assert "match" not in body
    assert "matching_algorithm" not in body


async def test_tags_update_non_nullable_params_absent_when_omitted(client, mock_router):
    """name, color, match, matching_algorithm, is_insensitive absent when omitted."""
    captured: dict = {}
    mock_router.patch("/tags/1/").mock(side_effect=_json_capture(captured, TAG_DATA))
    await client.tags.update(1)
    body = captured["body"]
    assert "name" not in body
    assert "color" not in body
    assert "match" not in body
    assert "matching_algorithm" not in body
    assert "is_insensitive" not in body


async def test_correspondents_create_non_nullable_params_absent_when_omitted(client, mock_router):
    """match and matching_algorithm must not appear in body when omitted."""
    captured: dict = {}
    mock_router.post("/correspondents/").mock(
        side_effect=_json_capture(captured, CORR_DATA, status=201)
    )
    await client.correspondents.create(name="ACME")
    body = captured["body"]
    assert "match" not in body
    assert "matching_algorithm" not in body


async def test_correspondents_update_non_nullable_params_absent_when_omitted(client, mock_router):
    """name, match, matching_algorithm, is_insensitive absent when omitted."""
    captured: dict = {}
    mock_router.patch("/correspondents/1/").mock(side_effect=_json_capture(captured, CORR_DATA))
    await client.correspondents.update(1)
    body = captured["body"]
    assert "name" not in body
    assert "match" not in body
    assert "matching_algorithm" not in body
    assert "is_insensitive" not in body


async def test_storage_paths_create_non_nullable_params_absent_when_omitted(client, mock_router):
    """path, match, matching_algorithm absent when omitted."""
    captured: dict = {}
    mock_router.post("/storage_paths/").mock(
        side_effect=_json_capture(captured, SP_DATA, status=201)
    )
    await client.storage_paths.create(name="archive")
    body = captured["body"]
    assert "path" not in body
    assert "match" not in body
    assert "matching_algorithm" not in body


async def test_storage_paths_update_non_nullable_params_absent_when_omitted(client, mock_router):
    """name, path, match, matching_algorithm, is_insensitive absent when omitted."""
    captured: dict = {}
    mock_router.patch("/storage_paths/1/").mock(side_effect=_json_capture(captured, SP_DATA))
    await client.storage_paths.update(1)
    body = captured["body"]
    assert "name" not in body
    assert "path" not in body
    assert "match" not in body
    assert "matching_algorithm" not in body
    assert "is_insensitive" not in body


# ===========================================================================
# 5. set_permissions pass-through across resources
# ===========================================================================


async def test_correspondents_create_set_permissions_none_sends_empty(client, mock_router):
    captured: dict = {}
    mock_router.post("/correspondents/").mock(
        side_effect=_json_capture(captured, CORR_DATA, status=201)
    )
    await client.correspondents.create(name="ACME", set_permissions=None)
    assert captured["body"]["set_permissions"] == SetPermissions().model_dump()


async def test_correspondents_update_set_permissions_none_sends_empty(client, mock_router):
    captured: dict = {}
    mock_router.patch("/correspondents/1/").mock(side_effect=_json_capture(captured, CORR_DATA))
    await client.correspondents.update(1, set_permissions=None)
    assert captured["body"]["set_permissions"] == SetPermissions().model_dump()


async def test_document_types_create_set_permissions_none_sends_empty(client, mock_router):
    captured: dict = {}
    mock_router.post("/document_types/").mock(
        side_effect=_json_capture(captured, DT_DATA, status=201)
    )
    await client.document_types.create(name="Invoice", set_permissions=None)
    assert captured["body"]["set_permissions"] == SetPermissions().model_dump()


async def test_document_types_update_set_permissions_none_sends_empty(client, mock_router):
    captured: dict = {}
    mock_router.patch("/document_types/1/").mock(side_effect=_json_capture(captured, DT_DATA))
    await client.document_types.update(1, set_permissions=None)
    assert captured["body"]["set_permissions"] == SetPermissions().model_dump()


async def test_storage_paths_create_set_permissions_value_sends_model_dump(client, mock_router):
    captured: dict = {}
    mock_router.post("/storage_paths/").mock(
        side_effect=_json_capture(captured, SP_DATA, status=201)
    )
    perms = SetPermissions(view=PermissionSet(users=[7], groups=[]), change=PermissionSet())
    await client.storage_paths.create(name="archive", set_permissions=perms)
    assert captured["body"]["set_permissions"] == perms.model_dump()


async def test_storage_paths_update_set_permissions_none_sends_empty(client, mock_router):
    captured: dict = {}
    mock_router.patch("/storage_paths/1/").mock(side_effect=_json_capture(captured, SP_DATA))
    await client.storage_paths.update(1, set_permissions=None)
    assert captured["body"]["set_permissions"] == SetPermissions().model_dump()


# ===========================================================================
# 6. CustomFieldsResource.update() — owner and set_permissions
# ===========================================================================


async def test_custom_fields_update_owner_none_sends_null(client, mock_router):
    """owner=None must include owner: null in PATCH body."""
    captured: dict = {}
    mock_router.patch("/custom_fields/1/").mock(side_effect=_json_capture(captured, CF_DATA))
    await client.custom_fields.update(1, owner=None)
    assert "owner" in captured["body"]
    assert captured["body"]["owner"] is None


async def test_custom_fields_update_owner_int_sends_value(client, mock_router):
    """owner=5 must send owner: 5 in PATCH body."""
    captured: dict = {}
    mock_router.patch("/custom_fields/1/").mock(side_effect=_json_capture(captured, CF_DATA))
    await client.custom_fields.update(1, owner=5)
    assert captured["body"]["owner"] == 5


async def test_custom_fields_update_owner_omitted_not_in_body(client, mock_router):
    """Omitting owner must NOT include owner in PATCH body."""
    captured: dict = {}
    mock_router.patch("/custom_fields/1/").mock(side_effect=_json_capture(captured, CF_DATA))
    await client.custom_fields.update(1, name="Amount")
    assert "owner" not in captured["body"]


async def test_custom_fields_update_set_permissions_none_sends_empty(client, mock_router):
    """set_permissions=None must send empty SetPermissions in PATCH body."""
    captured: dict = {}
    mock_router.patch("/custom_fields/1/").mock(side_effect=_json_capture(captured, CF_DATA))
    await client.custom_fields.update(1, set_permissions=None)
    assert captured["body"]["set_permissions"] == SetPermissions().model_dump()


async def test_custom_fields_update_set_permissions_unset_omits_key(client, mock_router):
    """Omitting set_permissions must NOT include it in PATCH body."""
    captured: dict = {}
    mock_router.patch("/custom_fields/1/").mock(side_effect=_json_capture(captured, CF_DATA))
    await client.custom_fields.update(1, name="Amount")
    assert "set_permissions" not in captured["body"]


async def test_custom_fields_update_set_permissions_value_sends_model_dump(client, mock_router):
    """set_permissions=SetPermissions(...) must send its model_dump() in PATCH body."""
    captured: dict = {}
    mock_router.patch("/custom_fields/1/").mock(side_effect=_json_capture(captured, CF_DATA))
    perms = SetPermissions(view=PermissionSet(users=[2], groups=[]), change=PermissionSet())
    await client.custom_fields.update(1, set_permissions=perms)
    assert captured["body"]["set_permissions"] == perms.model_dump()


# ===========================================================================
# 7. Sync mirror pass-through for set_permissions
# ===========================================================================


def test_sync_tags_create_set_permissions_none_sends_empty():
    """Sync: tags.create(set_permissions=None) sends empty SetPermissions."""
    captured: dict = {}

    def _side_effect(request):
        captured["body"] = json.loads(request.content)
        return Response(201, json=TAG_DATA)

    with respx.mock(base_url=API_BASE, assert_all_called=False) as router:
        router.post("/tags/").mock(side_effect=_side_effect)
        with SyncPaperlessClient(url=BASE_URL, api_token=API_KEY) as client:
            client.tags.create(name="test", set_permissions=None)

    assert captured["body"]["set_permissions"] == SetPermissions().model_dump()


def test_sync_tags_create_set_permissions_unset_omits_key():
    """Sync: tags.create() without set_permissions omits the key from body."""
    captured: dict = {}

    def _side_effect(request):
        captured["body"] = json.loads(request.content)
        return Response(201, json=TAG_DATA)

    with respx.mock(base_url=API_BASE, assert_all_called=False) as router:
        router.post("/tags/").mock(side_effect=_side_effect)
        with SyncPaperlessClient(url=BASE_URL, api_token=API_KEY) as client:
            client.tags.create(name="test")

    assert "set_permissions" not in captured["body"]


def test_sync_correspondents_update_set_permissions_none_sends_empty():
    """Sync: correspondents.update(set_permissions=None) sends empty SetPermissions."""
    captured: dict = {}

    def _side_effect(request):
        captured["body"] = json.loads(request.content)
        return Response(200, json=CORR_DATA)

    with respx.mock(base_url=API_BASE, assert_all_called=False) as router:
        router.patch("/correspondents/1/").mock(side_effect=_side_effect)
        with SyncPaperlessClient(url=BASE_URL, api_token=API_KEY) as client:
            client.correspondents.update(1, set_permissions=None)

    assert captured["body"]["set_permissions"] == SetPermissions().model_dump()


def test_sync_tags_update_set_permissions_value_sends_model_dump():
    """Sync: tags.update(set_permissions=...) sends the model_dump()."""
    captured: dict = {}
    perms = SetPermissions(view=PermissionSet(users=[9], groups=[]), change=PermissionSet())

    def _side_effect(request):
        captured["body"] = json.loads(request.content)
        return Response(200, json=TAG_DATA)

    with respx.mock(base_url=API_BASE, assert_all_called=False) as router:
        router.patch("/tags/1/").mock(side_effect=_side_effect)
        with SyncPaperlessClient(url=BASE_URL, api_token=API_KEY) as client:
            client.tags.update(1, set_permissions=perms)

    assert captured["body"]["set_permissions"] == perms.model_dump()


# ===========================================================================
# 8. Edge cases
# ===========================================================================


async def test_create_resource_set_permissions_none_and_owner_none_both_sent(client, mock_router):
    """Both set_permissions=None and owner=None can be sent in the same request."""
    captured: dict = {}
    mock_router.post("/tags/").mock(side_effect=_json_capture(captured, TAG_DATA, status=201))
    await client.tags.create(name="test", owner=None, set_permissions=None)
    body = captured["body"]
    assert body["owner"] is None
    assert body["set_permissions"] == SetPermissions().model_dump()


async def test_update_resource_set_permissions_none_owner_int_coexist(client, mock_router):
    """set_permissions=None and owner=5 can be sent together."""
    captured: dict = {}
    mock_router.patch("/tags/1/").mock(side_effect=_json_capture(captured, TAG_DATA))
    await client.tags.update(1, owner=5, set_permissions=None)
    body = captured["body"]
    assert body["owner"] == 5
    assert body["set_permissions"] == SetPermissions().model_dump()


async def test_non_nullable_params_sent_when_provided(client, mock_router):
    """When non-nullable params are provided they appear in the payload."""
    captured: dict = {}
    mock_router.post("/tags/").mock(side_effect=_json_capture(captured, TAG_DATA, status=201))
    await client.tags.create(name="test", color="#ff0000", match="invoice")
    body = captured["body"]
    assert body["color"] == "#ff0000"
    assert body["match"] == "invoice"
