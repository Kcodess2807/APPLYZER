"""Utility functions for the agent system.

Guidelines:
- Every function has a single responsibility and a full docstring.
- No global mutable state.
- No silent failures – callers get exceptions with context.
- Pure functions where possible (no side-effects).
"""

from __future__ import annotations

import re
from datetime import datetime
from io import StringIO
from typing import Any

import pandas as pd

from app.agents.constants import (
    CSV_COLUMN_MAPPINGS,
    REQUIRED_CSV_COLUMNS,
    SKILL_CATEGORIES,
)
from app.agents.exceptions import CSVParsingError


# ---------------------------------------------------------------------------
# CSV helpers
# ---------------------------------------------------------------------------


def normalize_column_name(column: str) -> str:
    """Lowercase and strip a column name, replacing spaces with underscores.

    Used for case- and whitespace-insensitive column matching.
    """
    return column.lower().strip().replace(" ", "_")


def find_csv_column(
    df: pd.DataFrame,
    target_column: str,
    mappings: dict[str, list[str]] | None = None,
) -> str | None:
    """Return the actual DataFrame column that corresponds to *target_column*.

    Looks up each accepted spelling from *mappings* (defaulting to
    ``CSV_COLUMN_MAPPINGS``) against the normalised column names in *df*.

    Args:
        df: DataFrame whose columns are searched.
        target_column: Canonical field name (e.g. ``"title"``).
        mappings: Override the default column-variant dictionary.

    Returns:
        The matching column name as it appears in *df*, or ``None`` if not found.
    """
    if mappings is None:
        mappings = CSV_COLUMN_MAPPINGS

    normalised = {normalize_column_name(col): col for col in df.columns}

    for variant in mappings.get(target_column, []):
        key = normalize_column_name(variant)
        if key in normalised:
            return normalised[key]

    return None


def parse_csv_content(csv_content: str) -> pd.DataFrame:
    """Parse a raw CSV string into a validated DataFrame.

    Args:
        csv_content: UTF-8 CSV text.

    Returns:
        Non-empty DataFrame with all required columns present.

    Raises:
        CSVParsingError: If the content cannot be parsed, is empty, or is
            missing required columns.
    """
    try:
        df = pd.read_csv(StringIO(csv_content))
    except Exception as exc:
        raise CSVParsingError(f"Failed to parse CSV: {exc}") from exc

    if df.empty:
        raise CSVParsingError("CSV file is empty")

    missing = [col for col in REQUIRED_CSV_COLUMNS if not find_csv_column(df, col)]
    if missing:
        raise CSVParsingError(
            f"Missing required columns: {', '.join(missing)}. "
            f"Available columns: {', '.join(df.columns)}"
        )

    return df


# ---------------------------------------------------------------------------
# Skill extraction
# ---------------------------------------------------------------------------


def extract_skills_from_text(text: str) -> list[str]:
    """Identify known technical skills mentioned in *text*.

    Uses whole-word regex matching against the ``SKILL_CATEGORIES`` taxonomy to
    avoid false positives (e.g. "go" inside "algorithm").

    Args:
        text: Free-form text such as a job description.

    Returns:
        Sorted, deduplicated list of matched skill names.
    """
    text_lower = text.lower()
    found: set[str] = set()

    for skills in SKILL_CATEGORIES.values():
        for skill in skills:
            pattern = r"\b" + re.escape(skill) + r"\b"
            if re.search(pattern, text_lower):
                found.add(skill)

    return sorted(found)


# ---------------------------------------------------------------------------
# Text utilities
# ---------------------------------------------------------------------------


def calculate_text_similarity(text1: str, text2: str) -> float:
    """Compute Jaccard similarity between two texts (word-level).

    Args:
        text1: First string.
        text2: Second string.

    Returns:
        Float in ``[0.0, 1.0]``; ``0.0`` if either string is empty.
    """
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())

    if not words1 or not words2:
        return 0.0

    return len(words1 & words2) / len(words1 | words2)


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Shorten *text* to *max_length* characters, appending *suffix* if cut.

    Args:
        text: Input string.
        max_length: Maximum number of characters in the result.
        suffix: String appended when truncation occurs.

    Returns:
        Original or truncated string.
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def validate_email(email: str) -> bool:
    """Return ``True`` if *email* matches a basic RFC-5322-ish pattern."""
    pattern = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_url(url: str) -> bool:
    """Return ``True`` if *url* starts with ``http://`` or ``https://``."""
    pattern = r"^https?://[^\s/$.?#].[^\s]*$"
    return bool(re.match(pattern, url))


# ---------------------------------------------------------------------------
# File / path helpers
# ---------------------------------------------------------------------------


def sanitize_filename(filename: str, max_length: int = 200) -> str:
    """Remove characters illegal in common file systems and trim length.

    Args:
        filename: Proposed filename, possibly with invalid characters.
        max_length: Hard cap on result length (default 200).

    Returns:
        Safe filename string.
    """
    sanitized = re.sub(r'[<>:"/\\|?*]', "", filename)
    sanitized = sanitized.replace(" ", "_")
    return sanitized[:max_length]


def format_timestamp(dt: datetime | None = None) -> str:
    """Format a datetime as ``YYYYMMDD_HHMMSS`` suitable for filenames.

    Args:
        dt: Datetime to format; defaults to ``datetime.utcnow()``.

    Returns:
        Formatted timestamp string.
    """
    return (dt or datetime.utcnow()).strftime("%Y%m%d_%H%M%S")


# ---------------------------------------------------------------------------
# Collection helpers
# ---------------------------------------------------------------------------


def merge_dicts_deep(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge *override* into *base*, returning a new dict.

    Nested dicts are merged rather than replaced. All other types follow
    last-write-wins semantics (override takes precedence).

    Args:
        base: Starting dictionary.
        override: Dictionary whose values take precedence.

    Returns:
        New merged dictionary (neither input is mutated).
    """
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts_deep(result[key], value)
        else:
            result[key] = value
    return result


def chunk_list(lst: list[Any], chunk_size: int) -> list[list[Any]]:
    """Split *lst* into sub-lists of at most *chunk_size* elements.

    Args:
        lst: Input list.
        chunk_size: Maximum length of each chunk.

    Returns:
        List of chunks; the last chunk may be shorter than *chunk_size*.

    Raises:
        ValueError: If *chunk_size* is less than 1.
    """
    if chunk_size < 1:
        raise ValueError(f"chunk_size must be >= 1, got {chunk_size}")
    return [lst[i : i + chunk_size] for i in range(0, len(lst), chunk_size)]