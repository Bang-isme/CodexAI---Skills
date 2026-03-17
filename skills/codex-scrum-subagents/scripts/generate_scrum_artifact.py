#!/usr/bin/env python3
"""Generate Scrum artifacts from bundled markdown templates."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List


SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = SCRIPT_DIR.parent / "assets" / "artifact-templates"
PLACEHOLDER_PATTERN = re.compile(r"\{\{([a-z0-9_]+)\}\}")


def available_templates() -> List[str]:
    return sorted(path.stem for path in TEMPLATES_DIR.glob("*.md"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a Scrum artifact from a bundled markdown template.",
    )
    parser.add_argument("--template", choices=available_templates(), required=True, help="Template name")
    parser.add_argument(
        "--field",
        action="append",
        default=[],
        help="Template value in key=value form. Repeat as needed.",
    )
    parser.add_argument(
        "--allow-placeholders",
        action="store_true",
        help="Allow scaffold output with _TODO_ placeholders instead of requiring every template field",
    )
    parser.add_argument("--output", help="Optional output markdown path")
    parser.add_argument("--format", choices=("json", "markdown"), default="json", help="Output format")
    return parser.parse_args()


def parse_fields(values: List[str]) -> Dict[str, str]:
    fields: Dict[str, str] = {}
    for raw in values:
        if "=" not in raw:
            raise ValueError(f"Invalid --field value: {raw}")
        key, value = raw.split("=", 1)
        key = key.strip().lower().replace("-", "_")
        if not key:
            raise ValueError(f"Invalid --field key in: {raw}")
        fields[key] = value.strip() or "_TODO_"
    return fields


def template_path(template_name: str) -> Path:
    return TEMPLATES_DIR / f"{template_name}.md"


def template_fields(template_name: str) -> List[str]:
    text = template_path(template_name).read_text(encoding="utf-8")
    ordered_keys: List[str] = []
    for key in PLACEHOLDER_PATTERN.findall(text):
        if key not in ordered_keys:
            ordered_keys.append(key)
    return ordered_keys


def missing_template_fields(template_name: str, fields: Dict[str, str]) -> List[str]:
    return [key for key in template_fields(template_name) if not fields.get(key, "").strip()]


def render_template(template_name: str, fields: Dict[str, str]) -> str:
    text = template_path(template_name).read_text(encoding="utf-8")

    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        return fields.get(key, "_TODO_")

    return PLACEHOLDER_PATTERN.sub(replace, text)


def build_artifact_payload(template_name: str, fields: Dict[str, str], allow_placeholders: bool) -> Dict[str, object]:
    missing_fields = missing_template_fields(template_name, fields)
    if missing_fields and not allow_placeholders:
        raise ValueError(f"Missing required fields for template '{template_name}': {', '.join(missing_fields)}")

    markdown = render_template(template_name, fields)
    return {
        "status": "scaffold" if missing_fields else "ok",
        "template": template_name,
        "fields": fields,
        "missing_fields": missing_fields,
        "markdown": markdown,
    }


def emit(payload: Dict[str, object], fmt: str) -> None:
    if fmt == "markdown":
        sys.stdout.write(str(payload["markdown"]))
        if not str(payload["markdown"]).endswith("\n"):
            sys.stdout.write("\n")
        return
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> int:
    args = parse_args()
    try:
        fields = parse_fields(args.field)
        payload = build_artifact_payload(args.template, fields, args.allow_placeholders)
    except (OSError, ValueError) as exc:
        print(json.dumps({"status": "error", "message": str(exc)}, indent=2))
        return 1

    output_path = ""
    if args.output:
        target = Path(args.output).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(str(payload["markdown"]), encoding="utf-8", newline="\n")
        output_path = target.as_posix()

    payload["path"] = output_path
    emit(payload, args.format)
    return 0


if __name__ == "__main__":
    sys.exit(main())
