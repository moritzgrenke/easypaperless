"""Tests for Pydantic model parsing and edge cases."""

from __future__ import annotations

from datetime import date, datetime

from easypaperless.models._base import MatchingAlgorithm
from easypaperless.models.correspondents import Correspondent
from easypaperless.models.custom_fields import CustomField, FieldDataType
from easypaperless.models.documents import Document, Task, TaskStatus
from easypaperless.models.tags import Tag


def _doc_data(**overrides):
    base = {"id": 1, "title": "Test Doc"}
    base.update(overrides)
    return base


def test_document_minimal():
    doc = Document.model_validate({"id": 42, "title": "Hello"})
    assert doc.id == 42
    assert doc.title == "Hello"
    assert doc.tags == []
    assert doc.notes == []
    assert doc.custom_fields == []


def test_document_extra_fields_ignored():
    doc = Document.model_validate({"id": 1, "title": "X", "unknown_future_field": True})
    assert not hasattr(doc, "unknown_future_field")


def test_document_search_hit_alias():
    data = {
        "id": 1,
        "title": "T",
        "__search_hit__": {"score": 9.5, "rank": 1},
    }
    doc = Document.model_validate(data)
    assert doc.search_hit is not None
    assert doc.search_hit.score == 9.5
    assert doc.search_hit.rank == 1


def test_document_created_date_is_date_not_datetime():
    doc = Document.model_validate({"id": 1, "title": "T", "created_date": "2024-03-15"})
    assert isinstance(doc.created_date, date)


def test_document_created_is_datetime():
    doc = Document.model_validate({"id": 1, "title": "T", "created": "2024-03-15T10:00:00Z"})
    assert isinstance(doc.created, datetime)


def test_task_status_enum():
    for val in ("PENDING", "STARTED", "SUCCESS", "FAILURE", "RETRY", "REVOKED"):
        status = TaskStatus(val)
        assert status.value == val


def test_task_model():
    task = Task.model_validate(
        {
            "task_id": "abc-123",
            "status": "SUCCESS",
            "related_document": "7",
        }
    )
    assert task.task_id == "abc-123"
    assert task.status == TaskStatus.SUCCESS
    assert task.related_document == "7"


def test_tag_model():
    tag = Tag.model_validate({"id": 3, "name": "invoice"})
    assert tag.id == 3
    assert tag.name == "invoice"


def test_tag_model_all_fields():
    tag = Tag.model_validate(
        {
            "id": 3,
            "name": "invoice",
            "slug": "invoice",
            "color": "#ff0000",
            "text_color": "#ffffff",
            "match": "inv",
            "matching_algorithm": 3,
            "is_insensitive": True,
            "is_inbox_tag": False,
            "document_count": 10,
            "owner": 1,
            "user_can_change": True,
            "parent": 2,
            "children": [4, 5],
        }
    )
    assert tag.slug == "invoice"
    assert tag.color == "#ff0000"
    assert tag.text_color == "#ffffff"
    assert tag.match == "inv"
    assert tag.matching_algorithm == MatchingAlgorithm.EXACT
    assert tag.is_insensitive is True
    assert tag.is_inbox_tag is False
    assert tag.document_count == 10
    assert tag.owner == 1
    assert tag.user_can_change is True
    assert tag.parent == 2
    assert tag.children == [4, 5]


def test_tag_model_ignores_extra_fields():
    """Tag model should ignore unknown fields from the API."""
    tag = Tag.model_validate({"id": 1, "name": "test", "unknown_field": "ignored"})
    assert tag.id == 1
    assert not hasattr(tag, "unknown_field")


def test_correspondent_last_correspondence_is_date():
    c = Correspondent.model_validate({"id": 1, "name": "Bank", "last_correspondence": "2024-01-01"})
    assert isinstance(c.last_correspondence, date)


def test_custom_field_data_type_enum():
    cf = CustomField.model_validate({"id": 1, "name": "Amount", "data_type": "monetary"})
    assert cf.data_type == FieldDataType.monetary


def test_field_data_type_all_values():
    for val in (
        "string",
        "boolean",
        "integer",
        "float",
        "monetary",
        "date",
        "url",
        "documentlink",
        "select",
    ):
        assert FieldDataType(val).value == val
