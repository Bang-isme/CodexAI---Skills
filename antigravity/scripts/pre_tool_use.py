#!/usr/bin/env python3
"""Antigravity PreToolUse hook: remind on UI writes, fail open, JSON stdin/stdout."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path


UI_SUFFIXES = {".css", ".scss", ".less", ".html", ".vue", ".jsx", ".tsx", ".svg"}
WRITE_TOOLS = {
    "replace_file_content",
    "write_to_file",
    "write_file",
    "edit_file",
    "multi_replace_file_content",
}


def allow(note: str, extra: dict | None = None) -> dict:
    payload = {"permission": "allow", "continue": True, "note": note}
    if extra:
        payload.update(extra)
    return payload


def tool_name(payload: dict) -> str:
    for key in ("toolName", "tool_name", "name", "tool"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def target_path(payload: dict) -> str:
    tool_input = payload.get("toolInput") or payload.get("tool_input") or payload.get("input") or {}
    if not isinstance(tool_input, dict):
        return ""
    for key in ("path", "file_path", "filePath", "target"):
        value = tool_input.get(key)
        if isinstance(value, str):
            return value
    return ""


def is_ui_path(path_value: str) -> bool:
    suffix = Path(path_value).suffix.lower()
    return suffix in UI_SUFFIXES or "/components/" in path_value.replace("\\", "/").lower()


def main() -> int:
    raw = sys.stdin.read() if not sys.stdin.isatty() else ""
    try:
        payload = json.loads(raw) if raw.strip() else {}
        if not isinstance(payload, dict):
            payload = {}
    except json.JSONDecodeError:
        print(json.dumps(allow("fail_open_invalid_json", {"warning": "invalid_hook_stdin"})))
        return 0

    name = tool_name(payload)
    path_value = target_path(payload)
    note = "pass_through"
    extra: dict = {}
    if name in WRITE_TOOLS and is_ui_path(path_value):
        extra["warning"] = "ui_write"
        extra["required_evidence"] = ["mechanical_visual_gate", "desktop_mobile_review"]
        extra["independent_reviewer"] = "visual-quality-reviewer"
        note = "UI write: keep approved direction; do not self-approve visual quality."
    if os.environ.get("CODEXAI_AGY_HOOK_DRY_FAIL"):
        extra["warning"] = extra.get("warning") or "forced_fail_open"
    print(json.dumps(allow(note, extra)))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - fail-open
        print(json.dumps({"permission": "allow", "continue": True, "note": "fail_open", "warning": str(exc)}))
        raise SystemExit(0)
