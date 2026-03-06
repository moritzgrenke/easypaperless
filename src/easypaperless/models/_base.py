"""Base model types used internally."""

from __future__ import annotations

from enum import IntEnum


class MatchingAlgorithm(IntEnum):
    """Auto-matching algorithm used by tags, correspondents, document types, and storage paths."""

    NONE = 0
    ANY_WORD = 1
    ALL_WORDS = 2
    EXACT = 3
    REGEX = 4
    FUZZY = 5
    AUTO = 6
