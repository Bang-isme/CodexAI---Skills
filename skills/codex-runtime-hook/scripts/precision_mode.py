#!/usr/bin/env python3
"""Session precision mode for the CodexAI smallest-complete-change ladder.

Resolution order is explicit ``CODEX_PRECISION_MODE``, then project config JSON,
then ``full``. One-shot command names are never accepted as a latched level.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any, Mapping


VALID_LEVELS = ("off", "lite", "full", "ultra")
DEFAULT_LEVEL = "full"
ENV_NAME = "CODEX_PRECISION_MODE"
CONFIG_KEYS = ("precision_mode", "CODEX_PRECISION_MODE")
ONE_SHOT_COMMANDS = ("review", "audit", "debt", "help")
DEACTIVATE_MESSAGES = ("off", "stop", "normal mode")
TRAILING_PUNCTUATION = ".!?;,"
LEVEL_WORDS = frozenset(VALID_LEVELS)

_HEADING_RE = re.compile(r"^(#+)\s+(.*)$")
_BULLET_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
_EXAMPLE_LINE_RE = re.compile(r"^(?:>\s*)?(?:example|e\.g\.)\b(.*)$", re.IGNORECASE)
_LEVEL_WORD_RE = re.compile(r"\b(lite|full|ultra|off)\b", re.IGNORECASE)
_SEPARATOR_CELL_RE = re.compile(r":?-{3,}:?")


def coerce_level(value: object) -> str | None:
    """Return a latched intensity, or None when the value is blank, unknown, or one-shot."""
    if not isinstance(value, str):
        return None
    token = value.strip().lower()
    if token.startswith("$"):
        token = token[1:].strip()
    if token in ONE_SHOT_COMMANDS or token not in VALID_LEVELS:
        return None
    return token


def strip_bom(raw: str) -> str:
    if raw.startswith("\ufeff"):
        return raw[1:]
    return raw


def parse_config_json(raw: str) -> dict[str, Any]:
    """Parse a config object, removing a leading UTF-8 BOM before ``json.loads``."""
    cleaned = strip_bom(raw).strip()
    if not cleaned:
        return {}
    payload = json.loads(cleaned)
    if not isinstance(payload, dict):
        raise ValueError("precision config must be a JSON object")
    return payload


def _config_level(config: Mapping[str, Any] | None) -> str | None:
    if not isinstance(config, Mapping):
        return None
    for key in CONFIG_KEYS:
        chosen = coerce_level(config.get(key))
        if chosen is not None:
            return chosen
    return None


def resolve_precision_mode(
    environ: Mapping[str, str] | None = None,
    config_text: str | None = None,
    config: Mapping[str, Any] | None = None,
) -> str:
    """Resolve lite, full, ultra, or off.

    Explicit environment wins when it is a real intensity. One-shot names
    (``review``, ``audit``, ``debt``, ``help``) are rejected and do not stick.
    Invalid environment or config values fall through. The default is ``full``.
    """
    env_map = os.environ if environ is None else environ
    if ENV_NAME in env_map:
        chosen = coerce_level(env_map.get(ENV_NAME))
        if chosen is not None:
            return chosen
    data = config
    if data is None and config_text is not None:
        try:
            data = parse_config_json(config_text)
        except (json.JSONDecodeError, ValueError):
            data = None
    chosen = _config_level(data)
    if chosen is not None:
        return chosen
    return DEFAULT_LEVEL


def merge_precision_config(existing_raw: str, updates: Mapping[str, Any]) -> dict[str, Any]:
    """Overlay ``updates`` onto existing JSON without deleting unrelated keys."""
    merged = dict(parse_config_json(existing_raw))
    for key, value in updates.items():
        merged[key] = value
    return merged


def write_precision_config(path: Path, updates: Mapping[str, Any]) -> dict[str, Any]:
    """Merge ``updates`` into ``path`` and write UTF-8 JSON without a BOM."""
    existing_raw = path.read_text(encoding="utf-8") if path.exists() else "{}"
    merged = merge_precision_config(existing_raw, updates)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return merged


def normalize_project_path(project_path: str) -> str:
    """Trim surrounding space and one trailing separator without rewriting separators.

    ``C:\\proj`` and ``C:/proj`` stay distinct so their session files cannot collide.
    """
    if not isinstance(project_path, str):
        raise TypeError("project path must be a string")
    text = project_path.strip()
    while len(text) > 1 and text[-1] in "/\\":
        if len(text) == 3 and text[1] == ":" and text[2] in "/\\":
            break
        text = text[:-1]
    return text


def project_state_id(project_path: str) -> str:
    """SHA-256 of the normalized project path. Separators are part of the key."""
    normalized = normalize_project_path(project_path)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def session_state_path(state_dir: Path, project_path: str) -> Path:
    return Path(state_dir) / f"{project_state_id(project_path)}.json"


def read_session_state(state_dir: Path, project_path: str) -> dict[str, Any] | None:
    path = session_state_path(state_dir, project_path)
    if not path.is_file():
        return None
    data = parse_config_json(path.read_text(encoding="utf-8"))
    expected = project_state_id(project_path)
    stored = data.get("project_id")
    if isinstance(stored, str) and stored != expected:
        return None
    return data


def write_session_state(state_dir: Path, project_path: str, level: str) -> Path:
    chosen = coerce_level(level)
    if chosen is None:
        raise ValueError("invalid precision level")
    path = session_state_path(state_dir, project_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "level": chosen,
        "project_path": normalize_project_path(project_path),
        "project_id": project_state_id(project_path),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def resolve_session_level(source: str, live_level: str | None, default_level: str) -> str:
    """Compaction keeps the live level. A fresh start uses the resolved default."""
    default = coerce_level(default_level) or DEFAULT_LEVEL
    if source == "compact":
        live = coerce_level(live_level)
        if live is not None:
            return live
    return default


def start_precision_session(
    state_dir: Path,
    project_path: str,
    *,
    source: str,
    default_level: str,
) -> str:
    existing = read_session_state(state_dir, project_path)
    live = existing.get("level") if isinstance(existing, dict) else None
    level = resolve_session_level(source, live if isinstance(live, str) else None, default_level)
    if source == "compact" and coerce_level(live if isinstance(live, str) else None) == level:
        return level
    write_session_state(state_dir, project_path, level)
    return level


def _strip_command_message(message: str) -> str:
    text = message.strip()
    while text and text[-1] in TRAILING_PUNCTUATION:
        text = text[:-1].rstrip()
    return text.lower()


def track_prompt_command(message: str, current_level: str, default_level: str) -> dict[str, Any]:
    """Apply one user message to the session intensity.

    Deactivation (``off``, ``stop``, ``normal mode``) matches only the whole
    trimmed message, ignoring trailing punctuation. A longer sentence that
    merely mentions those words does not change the level. Bare ``on`` reports
    the current level when it is already active, or activates the default
    (``full`` when the default itself is ``off``). Unknown text is ignored.
    ``$review``, ``$audit``, ``$debt``, and ``$help`` do not latch.
    """
    current = current_level if current_level in VALID_LEVELS else DEFAULT_LEVEL
    default = default_level if default_level in VALID_LEVELS else DEFAULT_LEVEL
    normalized = _strip_command_message(message)

    def result(level: str, action: str, one_shot: str | None = None) -> dict[str, Any]:
        return {
            "level": level,
            "previous_level": current,
            "changed": level != current,
            "action": action,
            "one_shot": one_shot,
        }

    if not normalized:
        return result(current, "unchanged")

    first = normalized.split()[0]
    first_bare = first[1:] if first.startswith("$") else first
    if first.startswith("$") and first_bare in ONE_SHOT_COMMANDS:
        return result(current, "one_shot", first_bare)
    if normalized in ONE_SHOT_COMMANDS:
        return result(current, "one_shot", normalized)

    if normalized in DEACTIVATE_MESSAGES:
        return result("off", "deactivate")

    if normalized == "on":
        if current != "off":
            return result(current, "report")
        target = DEFAULT_LEVEL if default == "off" else default
        return result(target, "activate")

    if normalized in {"lite", "full", "ultra"}:
        return result(normalized, "set")

    prefixed = re.fullmatch(r"(?:\$|/)?precision(?:\s+|:)(off|lite|full|ultra)", normalized)
    if prefixed:
        return result(prefixed.group(1), "set")
    return result(current, "unchanged")


def _table_cells(line: str) -> list[str] | None:
    stripped = line.strip()
    if not stripped.startswith("|") or stripped.count("|") < 2:
        return None
    return [cell.strip().lower() for cell in stripped.strip("|").split("|")]


def _is_separator_row(cells: list[str]) -> bool:
    return bool(cells) and all(_SEPARATOR_CELL_RE.fullmatch(cell) for cell in cells)


def _row_levels(cells: list[str]) -> set[str]:
    return {cell for cell in cells if cell in LEVEL_WORDS}


def _title_levels(title: str) -> set[str]:
    return {match.group(1).lower() for match in _LEVEL_WORD_RE.finditer(title)}


def filter_instructions(markdown_text: str, level: str) -> str:
    """Drop other-level table rows and examples. Keep rule bullets.

    A bullet whose label is a level word (``- lite: ...``) is a rule, so it
    stays even when the active intensity is different. Table rows and example
    sections tagged with another intensity are removed.
    """
    active = level.strip().lower() if isinstance(level, str) else ""
    if active not in LEVEL_WORDS:
        active = DEFAULT_LEVEL
    lines = markdown_text.splitlines()
    output: list[str] = []
    in_fence = False
    drop_fence = False
    skip_example = False
    skip_rank = 0
    skip_inline = False

    for line in lines:
        stripped = line.strip()
        if in_fence:
            if stripped.startswith("```"):
                in_fence = False
                if not drop_fence and not skip_example:
                    output.append(line)
                drop_fence = False
            elif not drop_fence and not skip_example:
                output.append(line)
            continue

        if stripped.startswith("```"):
            info = stripped[3:].strip().split()
            lang = info[0].lower() if info else ""
            in_fence = True
            drop_fence = lang in LEVEL_WORDS and lang != active
            if not drop_fence and not skip_example:
                output.append(line)
            continue

        heading = _HEADING_RE.match(stripped)
        if heading:
            rank = len(heading.group(1))
            title = heading.group(2)
            if skip_example and rank <= skip_rank:
                skip_example = False
            skip_inline = False
            title_levels = _title_levels(title)
            is_example = re.search(r"\bexamples?\b", title, re.IGNORECASE) is not None
            if is_example and title_levels and active not in title_levels:
                skip_example = True
                skip_rank = rank
                continue
            if not skip_example:
                output.append(line)
            continue

        if skip_example:
            continue
        if skip_inline:
            if stripped == "":
                skip_inline = False
            continue

        if _BULLET_RE.match(line):
            output.append(line)
            continue

        cells = _table_cells(line)
        if cells is not None:
            if _is_separator_row(cells):
                output.append(line)
                continue
            tagged = _row_levels(cells)
            if tagged and active not in tagged:
                continue
            output.append(line)
            continue

        example_line = _EXAMPLE_LINE_RE.match(stripped)
        if example_line:
            tagged = _title_levels(example_line.group(1))
            if tagged and active not in tagged:
                skip_inline = True
                continue
        output.append(line)

    trailing = "\n" if markdown_text.endswith("\n") else ""
    return "\n".join(output) + trailing


class InstructionReinjectionTracker:
    """Append a ruleset only when the level changes or context was compacted."""

    def __init__(self) -> None:
        self.signature: str | None = None

    def append_rules(self, prompt: str, level: str, ruleset: str, *, compacted: bool = False) -> str:
        filtered = filter_instructions(ruleset, level)
        signature = hashlib.sha256(f"{level}\n{filtered}".encode("utf-8")).hexdigest()
        if not compacted and signature == self.signature:
            return prompt
        self.signature = signature
        if not filtered:
            return prompt
        if not prompt:
            return filtered
        separator = "" if prompt.endswith("\n") else "\n"
        return prompt + separator + filtered


class PrecisionSession:
    """Per-project intensity: fresh start, compaction, and prompt commands."""

    def __init__(
        self,
        project_path: str,
        *,
        environ: Mapping[str, str] | None = None,
        config_text: str | None = None,
        state_dir: Path | None = None,
    ) -> None:
        self.project_path = project_path
        self.state_dir = state_dir
        self.default_level = resolve_precision_mode(environ=environ, config_text=config_text)
        self.level = self.default_level
        self.source = "fresh"
        self.tracker = InstructionReinjectionTracker()

    def start(self, source: str = "fresh") -> str:
        self.source = source
        if self.state_dir is not None:
            self.level = start_precision_session(
                self.state_dir,
                self.project_path,
                source=source,
                default_level=self.default_level,
            )
        else:
            self.level = resolve_session_level(source, self.level, self.default_level)
        return self.level

    def handle(self, message: str) -> dict[str, Any]:
        result = track_prompt_command(message, self.level, self.default_level)
        if result["action"] != "one_shot":
            self.level = str(result["level"])
            if self.state_dir is not None:
                write_session_state(self.state_dir, self.project_path, self.level)
        return result

    def inject(self, prompt: str, ruleset: str) -> str:
        compacted = self.source == "compact"
        rendered = self.tracker.append_rules(prompt, self.level, ruleset, compacted=compacted)
        if compacted:
            self.source = "live"
        return rendered


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Resolve CodexAI precision mode for a project session.")
    parser.add_argument("--project-path", default="", help="Project path used for the session key")
    parser.add_argument("--config", default="", help="Optional precision config JSON file")
    parser.add_argument("--state-dir", default="", help="Directory for per-project session files")
    parser.add_argument("--source", choices=("fresh", "compact"), default="fresh")
    parser.add_argument("--message", default="", help="Optional user message to apply to the session")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    args = parser.parse_args(argv)
    config_text = None
    if args.config:
        config_text = Path(args.config).read_text(encoding="utf-8")
    default_level = resolve_precision_mode(config_text=config_text)
    level = default_level
    if args.project_path and args.state_dir:
        level = start_precision_session(
            Path(args.state_dir),
            args.project_path,
            source=args.source,
            default_level=default_level,
        )
    command = None
    if args.message:
        command = track_prompt_command(args.message, level, default_level)
        level = str(command["level"])
        if args.project_path and args.state_dir and command["action"] != "one_shot":
            write_session_state(Path(args.state_dir), args.project_path, level)
    payload = {"level": level, "default_level": default_level, "command": command}
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(level)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
