"""Sentinel value for unset optional parameters."""

from __future__ import annotations

from typing import Final


class _Unset:
    """Sentinel type signalling that a parameter was not provided.

    Use the singleton :data:`UNSET` constant — do not instantiate directly.
    """

    __slots__ = ()

    def __repr__(self) -> str:
        return "UNSET"


UNSET: Final = _Unset()
