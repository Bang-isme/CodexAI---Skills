#!/usr/bin/env python3
"""
Shared JavaScript/TypeScript function parser used by multiple quality scripts.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

FUNCTION_PATTERNS = [
    re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\("),
    re.compile(r"^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?\([^()]*\)\s*=>"),
    re.compile(r"^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?[A-Za-z_$][\w$]*\s*=>"),
    re.compile(r"^\s*(?:public|private|protected|static|async|\s)*([A-Za-z_$][\w$]*)\s*\([^;]*\)\s*\{"),
]
RESERVED_WORDS = {"if", "for", "while", "switch", "catch", "return", "new", "else", "try"}
SINGLE_ARROW_PARAM_PATTERN = re.compile(r"=\s*(?:async\s*)?([A-Za-z_$][\w$]*)\s*=>")
PAREN_PARAM_PATTERN = re.compile(r"\(([^)]*)\)")


@dataclass
class JsBraceState:
    in_block_comment: bool = False
    in_single: bool = False
    in_double: bool = False
    in_template: bool = False
    escaped: bool = False


def js_brace_counts(line: str, state: JsBraceState) -> Tuple[int, int, JsBraceState]:
    opens = 0
    closes = 0
    idx = 0
    in_line_comment = False

    while idx < len(line):
        ch = line[idx]
        nxt = line[idx + 1] if idx + 1 < len(line) else ""

        if in_line_comment:
            break
        if state.in_block_comment:
            if ch == "*" and nxt == "/":
                state.in_block_comment = False
                idx += 2
                continue
            idx += 1
            continue
        if state.in_single:
            if state.escaped:
                state.escaped = False
            elif ch == "\\":
                state.escaped = True
            elif ch == "'":
                state.in_single = False
            idx += 1
            continue
        if state.in_double:
            if state.escaped:
                state.escaped = False
            elif ch == "\\":
                state.escaped = True
            elif ch == '"':
                state.in_double = False
            idx += 1
            continue
        if state.in_template:
            if state.escaped:
                state.escaped = False
            elif ch == "\\":
                state.escaped = True
            elif ch == "`":
                state.in_template = False
            idx += 1
            continue

        if ch == "/" and nxt == "/":
            in_line_comment = True
            idx += 2
            continue
        if ch == "/" and nxt == "*":
            state.in_block_comment = True
            idx += 2
            continue
        if ch == "'":
            state.in_single = True
            idx += 1
            continue
        if ch == '"':
            state.in_double = True
            idx += 1
            continue
        if ch == "`":
            state.in_template = True
            idx += 1
            continue

        if ch == "{":
            opens += 1
        elif ch == "}":
            closes += 1
        idx += 1

    state.escaped = False
    return opens, closes, state


def estimate_js_end(lines: Sequence[str], start_idx: int) -> Optional[int]:
    if start_idx < 0 or start_idx >= len(lines):
        return None

    depth = 0
    opened = False
    state = JsBraceState()
    max_scan = min(start_idx + 2000, len(lines))
    for idx in range(start_idx, max_scan):
        open_count, close_count, state = js_brace_counts(lines[idx], state)
        if open_count > 0:
            opened = True
        depth += open_count
        depth -= close_count
        if opened and depth <= 0:
            return idx

    start_indent = len(lines[start_idx]) - len(lines[start_idx].lstrip())
    for idx in range(start_idx + 1, max_scan):
        stripped = lines[idx].lstrip()
        if not stripped:
            continue
        if (
            stripped.startswith(("export ", "function ", "class ", "const ", "let ", "var "))
            and not stripped.startswith(("const {", "const [", "let {"))
        ):
            indent = len(lines[idx]) - len(stripped)
            if indent <= start_indent:
                return idx - 1 if idx - 1 >= start_idx else start_idx

    return min(start_idx + 50, len(lines) - 1)


def _parse_js_params(raw: str) -> List[str]:
    cleaned: List[str] = []
    for part in raw.split(","):
        token = part.strip()
        if not token:
            continue
        token = token.strip("() ").lstrip(".")
        token = token.split("=", 1)[0].strip()
        match = re.match(r"^([A-Za-z_$][\w$]*)\s*:\s*.+$", token)
        if match:
            token = match.group(1)
        token = token.strip("() ").strip()
        if token in {"async", "()"}:
            continue
        if token:
            cleaned.append(token)
    return cleaned


def _extract_params_from_line(line: str) -> List[str]:
    arrow = SINGLE_ARROW_PARAM_PATTERN.search(line)
    if arrow:
        return _parse_js_params(arrow.group(1))
    paren = PAREN_PARAM_PATTERN.search(line)
    if paren:
        return _parse_js_params(paren.group(1))
    return []


def _match_function_name(line: str) -> Optional[str]:
    for pattern in FUNCTION_PATTERNS:
        match = pattern.search(line)
        if not match:
            continue
        candidate = match.group(1)
        if candidate in RESERVED_WORDS:
            continue
        return candidate
    return None


def _has_unclosed_block(lines: Sequence[str], start_idx: int, end_idx: int) -> bool:
    """Best-effort detection for unterminated function/class blocks."""
    state = JsBraceState()
    depth = 0
    opened = False
    limit = min(end_idx + 1, len(lines))
    for idx in range(start_idx, limit):
        open_count, close_count, state = js_brace_counts(lines[idx], state)
        if open_count > 0:
            opened = True
        depth += open_count
        depth -= close_count
    return opened and depth > 0


def count_js_functions(lines: Sequence[str], rel_file: str, warnings: List[str]) -> Tuple[int, int]:
    total = 0
    long_count = 0
    for idx, line in enumerate(lines):
        function_name = _match_function_name(line)
        if not function_name:
            continue

        end_idx = estimate_js_end(lines, idx)
        if end_idx is None:
            warnings.append(f"JS function parse failed for {rel_file}:{idx + 1}")
            continue

        total += 1
        if (end_idx - idx + 1) > 50:
            long_count += 1
    return total, long_count


def extract_js_blocks(lines: Sequence[str], rel_file: str, warnings: List[str]) -> List[Dict[str, object]]:
    """Extract JS/TS function-like blocks with line range and params."""
    blocks: List[Dict[str, object]] = []
    seen: set[Tuple[str, int, int]] = set()

    for idx, line in enumerate(lines):
        function_name = _match_function_name(line)
        if not function_name:
            continue

        end_idx = estimate_js_end(lines, idx)
        if end_idx is None:
            warnings.append(f"JS/TS block parse failed for {rel_file}:{idx + 1}")
            continue
        if _has_unclosed_block(lines, idx, end_idx):
            warnings.append(f"JS/TS block parse failed for {rel_file}:{idx + 1}")

        line_start = idx + 1
        line_end = end_idx + 1
        key = (function_name, line_start, line_end)
        if key in seen:
            continue
        seen.add(key)
        blocks.append(
            {
                "name": function_name,
                "line_start": line_start,
                "line_end": line_end,
                "params": _extract_params_from_line(line),
            }
        )

    blocks.sort(key=lambda item: (int(item["line_start"]), str(item["name"])))
    return blocks
