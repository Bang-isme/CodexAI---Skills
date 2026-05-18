"""Shared redaction helpers for project-memory knowledge artifacts."""
from __future__ import annotations

import copy
import re
from typing import Any

REDACTION_PATTERNS_VERSION = "2026-05-18.1"
REDACTION_TOKEN = "[REDACTED]"
SECRET_PATTERNS = [
    re.compile(r"\bsk-[A-Za-z0-9_-]{12,}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"(?i)\b(password|passwd|secret|token|api[_-]?key)\s*[:=]\s*['\"]?[^'\"\s]{6,}"),
    re.compile(r"(?i)\b(password|passwd|secret|token|api[_-]?key)\b"),
    re.compile(r"\b[A-Fa-f0-9]{32,}\b"),
    re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b"),
]


def redact_text(value: str) -> str:
    """Return value with secret-like tokens, long hashes, and emails replaced."""
    return redact_text_with_count(value)[0]


def redact_text_with_count(value: str) -> tuple[str, int]:
    """Return the redacted text and number of pattern replacements made."""
    redacted = value
    count = 0
    for pattern in SECRET_PATTERNS:
        redacted, replacements = pattern.subn(REDACTION_TOKEN, redacted)
        count += replacements
    return redacted, count


def _redact_value(value: Any) -> tuple[Any, int]:
    if isinstance(value, str):
        return redact_text_with_count(value)
    if isinstance(value, list):
        items: list[Any] = []
        total = 0
        for item in value:
            redacted_item, count = _redact_value(item)
            items.append(redacted_item)
            total += count
        return items, total
    if isinstance(value, tuple):
        items = []
        total = 0
        for item in value:
            redacted_item, count = _redact_value(item)
            items.append(redacted_item)
            total += count
        return tuple(items), total
    if isinstance(value, dict):
        output: dict[Any, Any] = {}
        total = 0
        for key, item in value.items():
            # Preserve map keys (file paths, module names, etc.). Redacting keys can
            # collapse distinct entries such as src/token.py and src/secret.py.
            redacted_item, item_count = _redact_value(item)
            output[key] = redacted_item
            total += item_count
        return output, total
    return value, 0


def redaction_metadata(artifact_name: str, count: int, enabled: bool = True) -> dict[str, Any]:
    """Build consistent per-artifact redaction metadata."""
    return {
        "redaction_applied": bool(enabled),
        "redaction_patterns_version": REDACTION_PATTERNS_VERSION,
        "redaction_count": count,
        "redaction_counts": {artifact_name: count},
        "warnings": [] if enabled else ["Redaction disabled; artifact may contain secrets."],
    }


def redact_artifact(payload: dict[str, Any], artifact_name: str, enabled: bool = True) -> tuple[dict[str, Any], int]:
    """Return a disk-safe artifact payload with redaction metadata attached."""
    cloned = copy.deepcopy(payload)
    if enabled:
        redacted, count = _redact_value(cloned)
    else:
        redacted, count = cloned, 0
    if not isinstance(redacted, dict):
        raise TypeError("redact_artifact expects a dictionary payload")
    redacted["redaction_applied"] = bool(enabled)
    redacted["redaction_patterns_version"] = REDACTION_PATTERNS_VERSION
    redacted["redaction_count"] = count
    redacted["redaction_counts"] = {artifact_name: count}
    if not enabled:
        warnings = redacted.get("warnings", [])
        if not isinstance(warnings, list):
            warnings = [str(warnings)]
        warnings.append("Redaction disabled; artifact may contain secrets.")
        redacted["warnings"] = sorted(dict.fromkeys(str(item) for item in warnings))
    return redacted, count
