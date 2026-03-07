"""Integration tests: CRUD for tags, correspondents, document_types, storage_paths, custom_fields."""

from __future__ import annotations

import pytest

from easypaperless import PaperlessClient


@pytest.mark.integration
async def test_tag_crud(client: PaperlessClient, uid: str) -> None:
    tag = await client.create_tag(name=f"__integration_tag_{uid}__")
    try:
        assert tag.name == f"__integration_tag_{uid}__"
        fetched = await client.get_tag(tag.id)
        assert fetched.id == tag.id
        updated = await client.update_tag(tag.id, name=f"__integration_tag_{uid}_updated__")
        assert updated.name == f"__integration_tag_{uid}_updated__"
        tags = await client.list_tags()
        ids = [t.id for t in tags]
        assert tag.id in ids
    finally:
        await client.delete_tag(tag.id)


@pytest.mark.integration
async def test_correspondent_crud(client: PaperlessClient, uid: str) -> None:
    corr = await client.create_correspondent(name=f"__integration_correspondent_{uid}__")
    try:
        assert corr.name == f"__integration_correspondent_{uid}__"
        fetched = await client.get_correspondent(corr.id)
        assert fetched.id == corr.id
        updated = await client.update_correspondent(corr.id, name=f"__integration_correspondent_{uid}_updated__")
        assert updated.name == f"__integration_correspondent_{uid}_updated__"
        items = await client.list_correspondents()
        ids = [c.id for c in items]
        assert corr.id in ids
    finally:
        await client.delete_correspondent(corr.id)


@pytest.mark.integration
async def test_document_type_crud(client: PaperlessClient, uid: str) -> None:
    dt = await client.create_document_type(name=f"__integration_doctype_{uid}__")
    try:
        assert dt.name == f"__integration_doctype_{uid}__"
        fetched = await client.get_document_type(dt.id)
        assert fetched.id == dt.id
        updated = await client.update_document_type(dt.id, name=f"__integration_doctype_{uid}_updated__")
        assert updated.name == f"__integration_doctype_{uid}_updated__"
        items = await client.list_document_types()
        ids = [d.id for d in items]
        assert dt.id in ids
    finally:
        await client.delete_document_type(dt.id)


@pytest.mark.integration
async def test_storage_path_crud(client: PaperlessClient, uid: str) -> None:
    sp = await client.create_storage_path(name=f"__integration_storagepath_{uid}__", path="integration/{created}")
    try:
        assert sp.name == f"__integration_storagepath_{uid}__"
        fetched = await client.get_storage_path(sp.id)
        assert fetched.id == sp.id
        updated = await client.update_storage_path(sp.id, name=f"__integration_storagepath_{uid}_updated__")
        assert updated.name == f"__integration_storagepath_{uid}_updated__"
        items = await client.list_storage_paths()
        ids = [s.id for s in items]
        assert sp.id in ids
    finally:
        await client.delete_storage_path(sp.id)


@pytest.mark.integration
async def test_custom_field_crud(client: PaperlessClient, uid: str) -> None:
    cf = await client.create_custom_field(name=f"__integration_field_{uid}__", data_type="string")
    try:
        assert cf.name == f"__integration_field_{uid}__"
        fetched = await client.get_custom_field(cf.id)
        assert fetched.id == cf.id
        updated = await client.update_custom_field(cf.id, name=f"__integration_field_{uid}_updated__")
        assert updated.name == f"__integration_field_{uid}_updated__"
        items = await client.list_custom_fields()
        ids = [f.id for f in items]
        assert cf.id in ids
    finally:
        await client.delete_custom_field(cf.id)
