#!/usr/bin/env python3
"""Native CodexAI DESIGN.md contract engine: scaffold, lint, diff, export, and spec."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - exercised in clean Python environments
    yaml = None  # type: ignore[assignment]


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
TEMPLATE_PATH = SKILL_DIR / "assets" / "design-md-template.md"
SECTION_SEQUENCE = [
    "overview",
    "colors",
    "typography",
    "layout",
    "elevation & depth",
    "shapes",
    "components",
    "do's and don'ts",
]
SECTION_ALIASES = {
    "overview": "overview",
    "brand & style": "overview",
    "colors": "colors",
    "typography": "typography",
    "layout": "layout",
    "layout & spacing": "layout",
    "elevation & depth": "elevation & depth",
    "elevation": "elevation & depth",
    "shapes": "shapes",
    "components": "components",
    "do's and don'ts": "do's and don'ts",
    "do's and dont's": "do's and don'ts",
    "dos and don'ts": "do's and don'ts",
}
TOKEN_REF_PATTERN = re.compile(r"^\{([A-Za-z0-9_.-]+)\}$")
HEX_COLOR_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")
OKLCH_COLOR_PATTERN = re.compile(r"^oklch\([^)]+\)$", re.IGNORECASE)


def is_allowed_color(value: str) -> bool:
    token = value.strip()
    return bool(HEX_COLOR_PATTERN.fullmatch(token) or OKLCH_COLOR_PATTERN.fullmatch(token))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scaffold and validate DESIGN.md contracts with the native CodexAI engine.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    scaffold = subparsers.add_parser("scaffold", help="Write a canonical DESIGN.md starter file.")
    scaffold.add_argument("--name", required=True, help="Design-system or product name")
    scaffold.add_argument("--description", default="Structured visual identity contract for the product.", help="Short contract description")
    scaffold.add_argument(
        "--overview",
        default="A modern, intentional interface with explicit tokens, clear hierarchy, and reusable component rules.",
        help="Overview text for the Overview section",
    )
    scaffold.add_argument("--output", default="DESIGN.md", help="Output file path")
    scaffold.add_argument("--force", action="store_true", help="Overwrite the target file if it already exists")
    scaffold.add_argument("--format", choices=("json", "markdown"), default="json", help="Output format")

    doctor = subparsers.add_parser("doctor", help="Report native CodexAI DESIGN.md contract engine readiness.")
    doctor.add_argument("--format", choices=("json", "text"), default="json", help="Output format")

    lint = subparsers.add_parser("lint", help="Validate a DESIGN.md contract.")
    lint.add_argument("file", help="Path to DESIGN.md")
    lint.add_argument("--format", default="json", help="Output format: json or text")

    diff = subparsers.add_parser("diff", help="Compare two DESIGN.md contracts.")
    diff.add_argument("before", help="Before DESIGN.md path")
    diff.add_argument("after", help="After DESIGN.md path")
    diff.add_argument("--format", default="json", help="Output format: json or text")

    export = subparsers.add_parser("export", help="Export DESIGN.md tokens to Tailwind or DTCG formats.")
    export.add_argument("file", help="Path to DESIGN.md")
    export.add_argument("--format", choices=("tailwind", "dtcg"), required=True, help="Export format")

    spec = subparsers.add_parser("spec", help="Print the DESIGN.md specification.")
    spec.add_argument("--rules", action="store_true", help="Append native lint-rule descriptions")
    spec.add_argument("--rules-only", action="store_true", help="Output only native lint-rule descriptions")
    spec.add_argument("--format", choices=("markdown", "json"), default="markdown", help="Output format")

    return parser.parse_args()


def emit(payload: Dict[str, object], fmt: str) -> None:
    if fmt == "text":
        for key, value in payload.items():
            print(f"{key}: {value}")
        return
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def build_doctor_payload() -> Dict[str, object]:
    spec_summary = SKILL_DIR / "references" / "spec-essentials.md"
    return {
        "status": "checked",
        "native_engine": True,
        "engine": "codexai-native-python",
        "template_exists": TEMPLATE_PATH.exists(),
        "spec_exists": spec_summary.exists(),
        "yaml_parser": "pyyaml" if yaml is not None else "builtin-simple-yaml",
    }


def normalize_newlines(content: str) -> str:
    return content.replace("\r\n", "\n").replace("\r", "\n")


def normalize_heading(heading: str) -> str:
    cleaned = heading.strip().lower().replace("\u2019", "'")
    return SECTION_ALIASES.get(cleaned, "")


def split_design_content(content: str) -> tuple[str, str, Optional[str]]:
    normalized = normalize_newlines(content)
    lines = normalized.splitlines()
    if not lines or lines[0].strip() != "---":
        return "", normalized, None
    closing_index = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            closing_index = index
            break
    if closing_index is None:
        return "", normalized, "Unterminated YAML frontmatter fence."
    frontmatter = "\n".join(lines[1:closing_index])
    body = "\n".join(lines[closing_index + 1 :])
    return frontmatter, body, None


def parse_simple_yaml_scalar(value: str) -> Any:
    text = value.strip()
    if not text:
        return ""
    if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
        return text[1:-1]
    lowered = text.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"null", "none", "~"}:
        return None
    if re.fullmatch(r"-?\d+", text):
        return int(text)
    return text


def simple_yaml_load(raw: str) -> Dict[str, Any]:
    root: Dict[str, Any] = {}
    stack: List[tuple[int, Dict[str, Any]]] = [(-1, root)]
    for line_number, raw_line in enumerate(raw.splitlines(), start=1):
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if "\t" in raw_line[: len(raw_line) - len(raw_line.lstrip(" "))]:
            raise ValueError(f"Tabs are not supported in frontmatter at line {line_number}.")
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        key, separator, value = raw_line.strip().partition(":")
        if not separator or not key:
            raise ValueError(f"Expected key/value frontmatter at line {line_number}.")
        while stack and indent <= stack[-1][0]:
            stack.pop()
        if not stack:
            raise ValueError(f"Invalid indentation at line {line_number}.")
        parent = stack[-1][1]
        if value.strip() == "":
            child: Dict[str, Any] = {}
            parent[key] = child
            stack.append((indent, child))
        else:
            parent[key] = parse_simple_yaml_scalar(value)
    return root


def safe_yaml_load(raw: str) -> tuple[Dict[str, Any], Optional[str]]:
    if not raw.strip():
        return {}, None
    try:
        payload = yaml.safe_load(raw) if yaml is not None else simple_yaml_load(raw)
    except Exception as exc:
        return {}, str(exc)
    if payload is None:
        return {}, None
    if not isinstance(payload, dict):
        return {}, "Frontmatter must decode to an object."
    return payload, None


def extract_sections(body: str) -> List[Dict[str, Any]]:
    sections: List[Dict[str, Any]] = []
    for line_number, line in enumerate(normalize_newlines(body).splitlines(), start=1):
        if line.startswith("## "):
            heading = line[3:].strip()
            sections.append(
                {
                    "heading": heading,
                    "canonical": normalize_heading(heading),
                    "line": line_number,
                }
            )
    return sections


def resolve_ref_path(root: Dict[str, Any], dotted_path: str) -> Any:
    current: Any = root
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            raise KeyError(dotted_path)
        current = current[part]
    return current


def iter_references(node: Any, path: str = "") -> Iterable[tuple[str, str]]:
    if isinstance(node, dict):
        for key, value in node.items():
            next_path = f"{path}.{key}" if path else str(key)
            yield from iter_references(value, next_path)
        return
    if isinstance(node, list):
        for index, value in enumerate(node):
            next_path = f"{path}[{index}]"
            yield from iter_references(value, next_path)
        return
    if isinstance(node, str):
        match = TOKEN_REF_PATTERN.fullmatch(node.strip())
        if match:
            yield path, match.group(1)


def make_finding(severity: str, path: str, message: str) -> Dict[str, str]:
    return {
        "severity": severity,
        "path": path,
        "message": message,
    }


def summarize_findings(findings: List[Dict[str, str]]) -> Dict[str, int]:
    summary = {"errors": 0, "warnings": 0, "info": 0}
    for finding in findings:
        severity = finding["severity"]
        if severity == "error":
            summary["errors"] += 1
        elif severity == "warning":
            summary["warnings"] += 1
        else:
            summary["info"] += 1
    return summary


def lint_content(content: str) -> Dict[str, Any]:
    findings: List[Dict[str, str]] = []
    frontmatter_raw, body, split_error = split_design_content(content)
    if split_error:
        findings.append(make_finding("error", "frontmatter", split_error))
        return {
            "findings": findings,
            "summary": summarize_findings(findings),
            "design_system": {},
            "sections": [],
        }

    tokens, yaml_error = safe_yaml_load(frontmatter_raw)
    if yaml_error:
        findings.append(make_finding("error", "frontmatter", f"Invalid YAML frontmatter: {yaml_error}"))
    elif not frontmatter_raw.strip():
        findings.append(make_finding("warning", "frontmatter", "No YAML frontmatter found. Tokens should live in the frontmatter block."))

    colors = tokens.get("colors", {})
    if isinstance(colors, dict):
        if colors and "primary" not in colors:
            findings.append(make_finding("warning", "colors.primary", "Colors are defined but no `primary` token exists."))
        for key, value in colors.items():
            if isinstance(value, str) and not is_allowed_color(value):
                findings.append(make_finding("warning", f"colors.{key}", f"Color token `{key}` should be a 6-digit hex or oklch() value."))
    elif "colors" in tokens:
        findings.append(make_finding("error", "colors", "`colors` must be an object."))

    for ref_path, ref_target in iter_references(tokens):
        try:
            resolve_ref_path(tokens, ref_target)
        except KeyError:
            findings.append(make_finding("error", ref_path, f"Broken token reference: {{{ref_target}}}"))

    sections = extract_sections(body)
    seen_sections: Dict[str, int] = {}
    last_index = -1
    for section in sections:
        canonical = section["canonical"]
        heading = section["heading"]
        if not canonical:
            continue
        if canonical in seen_sections:
            findings.append(
                make_finding(
                    "error",
                    f"sections.{canonical}",
                    f"Duplicate section heading `{heading}` found on line {section['line']}.",
                )
            )
            continue
        seen_sections[canonical] = section["line"]
        current_index = SECTION_SEQUENCE.index(canonical)
        if current_index < last_index:
            findings.append(
                make_finding(
                    "warning",
                    f"sections.{canonical}",
                    f"Section `{heading}` is out of canonical order.",
                )
            )
        last_index = max(last_index, current_index)

    return {
        "findings": findings,
        "summary": summarize_findings(findings),
        "design_system": tokens,
        "sections": sections,
    }


def diff_maps(before: Dict[str, Any], after: Dict[str, Any]) -> Dict[str, List[str]]:
    before = before or {}
    after = after or {}
    before_keys = set(before.keys())
    after_keys = set(after.keys())
    modified = sorted(key for key in before_keys & after_keys if before.get(key) != after.get(key))
    return {
        "added": sorted(after_keys - before_keys),
        "removed": sorted(before_keys - after_keys),
        "modified": modified,
    }


def export_tailwind(tokens: Dict[str, Any]) -> Dict[str, Any]:
    typography = tokens.get("typography", {}) if isinstance(tokens.get("typography"), dict) else {}
    font_family = {name: [entry["fontFamily"]] for name, entry in typography.items() if isinstance(entry, dict) and entry.get("fontFamily")}
    font_size = {
        name: [entry["fontSize"], {"lineHeight": entry.get("lineHeight", "normal")}]
        for name, entry in typography.items()
        if isinstance(entry, dict) and entry.get("fontSize")
    }
    return {
        "theme": {
            "extend": {
                "colors": tokens.get("colors", {}),
                "fontFamily": font_family,
                "fontSize": font_size,
                "borderRadius": tokens.get("rounded", {}),
                "spacing": tokens.get("spacing", {}),
            }
        }
    }


def export_dtcg(tokens: Dict[str, Any]) -> Dict[str, Any]:
    def wrap_color_group(group: Dict[str, Any]) -> Dict[str, Any]:
        return {key: {"$value": value, "$type": "color"} for key, value in group.items()}

    def wrap_dimension_group(group: Dict[str, Any]) -> Dict[str, Any]:
        return {key: {"$value": value, "$type": "dimension"} for key, value in group.items()}

    payload: Dict[str, Any] = {}
    if isinstance(tokens.get("colors"), dict):
        payload["colors"] = wrap_color_group(tokens["colors"])
    if isinstance(tokens.get("rounded"), dict):
        payload["rounded"] = wrap_dimension_group(tokens["rounded"])
    if isinstance(tokens.get("spacing"), dict):
        payload["spacing"] = wrap_dimension_group(tokens["spacing"])
    if isinstance(tokens.get("typography"), dict):
        payload["typography"] = {
            key: {"$value": value, "$type": "typography"} for key, value in tokens["typography"].items()
        }
    if isinstance(tokens.get("components"), dict):
        payload["components"] = {
            key: {"$value": value, "$type": "object"} for key, value in tokens["components"].items()
        }
    return payload


def load_file(path: str) -> str:
    return Path(path).expanduser().resolve().read_text(encoding="utf-8")


def render_text_lint(payload: Dict[str, Any]) -> str:
    lines = [
        "DESIGN.md lint report",
        f"errors: {payload['summary']['errors']}",
        f"warnings: {payload['summary']['warnings']}",
        f"info: {payload['summary']['info']}",
    ]
    for finding in payload["findings"]:
        lines.append(f"- [{finding['severity']}] {finding['path']}: {finding['message']}")
    return "\n".join(lines)


def render_text_diff(payload: Dict[str, Any]) -> str:
    lines = ["DESIGN.md diff report"]
    for group_name, group_payload in payload["tokens"].items():
        lines.append(f"{group_name}:")
        lines.append(f"  added: {', '.join(group_payload['added']) or '-'}")
        lines.append(f"  removed: {', '.join(group_payload['removed']) or '-'}")
        lines.append(f"  modified: {', '.join(group_payload['modified']) or '-'}")
    lines.append(f"regression: {payload['regression']}")
    return "\n".join(lines)


def render_spec_payload(include_rules: bool, rules_only: bool) -> Dict[str, Any]:
    spec_path = SKILL_DIR / "references" / "spec-essentials.md"
    if spec_path.exists():
        spec_text = spec_path.read_text(encoding="utf-8")
    else:
        spec_text = "# DESIGN.md Format\n\nNative spec summary is not available.\n"
    rules = [
        {"name": "broken-ref", "severity": "error", "description": "Token references must resolve to a defined token."},
        {"name": "duplicate-section", "severity": "error", "description": "Recognized sections cannot appear more than once."},
        {"name": "section-order", "severity": "warning", "description": "Recognized sections should follow canonical order."},
        {"name": "missing-primary", "severity": "warning", "description": "Color maps should include a primary token."},
    ]
    if rules_only:
        return {"status": "ok", "rules": rules}
    payload: Dict[str, Any] = {"status": "ok", "spec": spec_text}
    if include_rules:
        payload["rules"] = rules
    return payload


def render_scaffold(name: str, description: str, overview: str) -> str:
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    mapping = {
        "{{name}}": name.strip(),
        "{{description}}": description.strip(),
        "{{overview}}": overview.strip(),
    }
    output = template
    for key, value in mapping.items():
        output = output.replace(key, value)
    return output


def handle_scaffold(args: argparse.Namespace) -> int:
    target = Path(args.output).expanduser().resolve()
    if target.exists() and not args.force:
        emit(
            {
                "status": "error",
                "message": f"Refusing to overwrite existing file without --force: {target}",
            },
            "json",
        )
        return 1

    markdown = render_scaffold(args.name, args.description, args.overview)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(markdown, encoding="utf-8", newline="\n")

    payload = {
        "status": "scaffold",
        "path": str(target),
        "name": args.name.strip(),
        "markdown": markdown,
    }
    if args.format == "markdown":
        sys.stdout.write(markdown)
        if not markdown.endswith("\n"):
            sys.stdout.write("\n")
        return 0
    emit(payload, "json")
    return 0


def execute_native(args: argparse.Namespace) -> int:
    if args.command == "lint":
        report = lint_content(load_file(args.file))
        if args.format == "text":
            sys.stdout.write(render_text_lint(report) + "\n")
        else:
            print(json.dumps({"findings": report["findings"], "summary": report["summary"]}, ensure_ascii=False, indent=2))
        return 1 if report["summary"]["errors"] > 0 else 0

    if args.command == "diff":
        before_report = lint_content(load_file(args.before))
        after_report = lint_content(load_file(args.after))
        payload = {
            "tokens": {
                "colors": diff_maps(before_report["design_system"].get("colors", {}), after_report["design_system"].get("colors", {})),
                "typography": diff_maps(before_report["design_system"].get("typography", {}), after_report["design_system"].get("typography", {})),
                "rounded": diff_maps(before_report["design_system"].get("rounded", {}), after_report["design_system"].get("rounded", {})),
                "spacing": diff_maps(before_report["design_system"].get("spacing", {}), after_report["design_system"].get("spacing", {})),
            },
            "findings": {
                "before": before_report["summary"],
                "after": after_report["summary"],
                "delta": {
                    "errors": after_report["summary"]["errors"] - before_report["summary"]["errors"],
                    "warnings": after_report["summary"]["warnings"] - before_report["summary"]["warnings"],
                },
            },
        }
        payload["regression"] = bool(
            payload["findings"]["delta"]["errors"] > 0 or payload["findings"]["delta"]["warnings"] > 0
        )
        if args.format == "text":
            sys.stdout.write(render_text_diff(payload) + "\n")
        else:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1 if payload["regression"] else 0

    if args.command == "export":
        report = lint_content(load_file(args.file))
        tokens = report["design_system"]
        payload = export_tailwind(tokens) if args.format == "tailwind" else export_dtcg(tokens)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1 if report["summary"]["errors"] > 0 else 0

    if args.command == "spec":
        payload = render_spec_payload(args.rules, args.rules_only)
        if args.format == "markdown":
            if args.rules_only:
                lines = ["## Native Lint Rules", ""]
                for rule in payload["rules"]:
                    lines.append(f"- `{rule['name']}` ({rule['severity']}): {rule['description']}")
                sys.stdout.write("\n".join(lines) + "\n")
            else:
                sys.stdout.write(payload["spec"])
                if args.rules:
                    sys.stdout.write("\n\n## Native Lint Rules\n\n")
                    for rule in payload["rules"]:
                        sys.stdout.write(f"- `{rule['name']}` ({rule['severity']}): {rule['description']}\n")
                if not payload["spec"].endswith("\n"):
                    sys.stdout.write("\n")
        else:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    raise ValueError(f"Unsupported command: {args.command}")


def main() -> int:
    args = parse_args()
    if not TEMPLATE_PATH.exists():
        emit(
            {
                "status": "error",
                "message": f"Missing template: {TEMPLATE_PATH}",
            },
            "json",
        )
        return 1

    if args.command == "scaffold":
        return handle_scaffold(args)
    if args.command == "doctor":
        emit(build_doctor_payload(), args.format)
        return 0
    return execute_native(args)


if __name__ == "__main__":
    sys.exit(main())
