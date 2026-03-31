"""
Helpers for normalizing tool inputs emitted by LangChain ReAct agents.
"""

from __future__ import annotations

import re


def parse_int(value, field_name: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be an integer, not a boolean")
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if value is None:
        raise ValueError(f"{field_name} is required")

    match = re.search(r"-?\d+", str(value))
    if not match:
        raise ValueError(f"{field_name} must contain an integer value")
    return int(match.group())


def parse_optional_text(value) -> str | None:
    if value is None:
        return None

    text = str(value).strip()
    if not text or text.lower() in {"none", "null", "n/a"}:
        return None
    return text
