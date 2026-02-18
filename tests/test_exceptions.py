"""Tests for the exception hierarchy."""

from easypaperless.exceptions import (
    AuthError,
    NotFoundError,
    PaperlessError,
    ServerError,
    TaskTimeoutError,
    UploadError,
    ValidationError,
)


def test_base_exception_stores_status_code():
    exc = PaperlessError("oops", status_code=400)
    assert str(exc) == "oops"
    assert exc.status_code == 400


def test_base_exception_status_code_defaults_to_none():
    exc = PaperlessError("oops")
    assert exc.status_code is None


def test_subclass_inheritance():
    for cls in (AuthError, NotFoundError, ValidationError, ServerError, UploadError):
        exc = cls("msg", status_code=999)
        assert isinstance(exc, PaperlessError)
        assert exc.status_code == 999


def test_task_timeout_has_no_status_code():
    exc = TaskTimeoutError("timed out")
    assert isinstance(exc, PaperlessError)
    assert exc.status_code is None


def test_auth_error():
    exc = AuthError("forbidden", status_code=403)
    assert exc.status_code == 403


def test_not_found_error():
    exc = NotFoundError("not found", status_code=404)
    assert exc.status_code == 404


def test_upload_error():
    exc = UploadError("upload failed", status_code=None)
    assert exc.status_code is None
