#!/usr/bin/env python3
"""Scaffold and run DESIGN.md contract workflows."""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - exercised in clean Python environments
    yaml = None  # type: ignore[assignment]


SOURCE_REPO_ENV_VAR = "CODEX_DESIGN_MD_SOURCE_REPO"
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scaffold and run DESIGN.md contract workflows from the CodexAI skill pack.",
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

    doctor = subparsers.add_parser("doctor", help="Report available DESIGN.md runtimes and source paths.")
    doctor.add_argument(
        "--source-repo",
        default="",
        help=f"Optional path to an upstream design.md source repo. If omitted, auto-discovery checks `{SOURCE_REPO_ENV_VAR}` and nearby folders.",
    )
    doctor.add_argument("--prefer", choices=("auto", "local", "npx"), default="auto", help="Runner preference")
    doctor.add_argument("--format", choices=("json", "text"), default="json", help="Output format")

    lint = subparsers.add_parser("lint", help="Validate a DESIGN.md contract.")
    lint.add_argument("file", help="Path to DESIGN.md")
    lint.add_argument("--format", default="json", help="Output format: json or text")
    add_proxy_common_args(lint)

    diff = subparsers.add_parser("diff", help="Compare two DESIGN.md contracts.")
    diff.add_argument("before", help="Before DESIGN.md path")
    diff.add_argument("after", help="After DESIGN.md path")
    diff.add_argument("--format", default="json", help="Output format: json or text")
    add_proxy_common_args(diff)

    export = subparsers.add_parser("export", help="Export DESIGN.md tokens to other formats.")
    export.add_argument("file", help="Path to DESIGN.md")
    export.add_argument("--format", choices=("tailwind", "dtcg"), required=True, help="Export format")
    add_proxy_common_args(export)

    spec = subparsers.add_parser("spec", help="Print the DESIGN.md specification.")
    spec.add_argument("--rules", action="store_true", help="Append bundled lint-rule descriptions")
    spec.add_argument("--rules-only", action="store_true", help="Output only bundled lint-rule descriptions")
    spec.add_argument("--format", choices=("markdown", "json"), default="markdown", help="Output format")
    add_proxy_common_args(spec)

    return parser.parse_args()


def add_proxy_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--source-repo",
        default="",
        help=f"Optional path to an upstream design.md source repo. If omitted, auto-discovery checks `{SOURCE_REPO_ENV_VAR}` and nearby folders.",
    )
    parser.add_argument("--prefer", choices=("auto", "local", "npx"), default="auto", help="Runner preference")


def emit(payload: Dict[str, object], fmt: str) -> None:
    if fmt == "text":
        for key, value in payload.items():
            print(f"{key}: {value}")
        return
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def is_upstream_source_repo(candidate: Path) -> bool:
    if not candidate.exists():
        return False
    has_spec = (candidate / "docs" / "spec.md").exists()
    has_cli = (
        (candidate / "packages" / "cli" / "src" / "index.ts").exists()
        or (candidate / "packages" / "cli" / "dist" / "index.js").exists()
    )
    return has_spec and has_cli


def resolve_source_repo(source_repo_arg: str) -> Optional[Path]:
    explicit = source_repo_arg.strip()
    if explicit:
        return Path(explicit).expanduser().resolve()

    env_value = os.environ.get(SOURCE_REPO_ENV_VAR, "").strip()
    if env_value:
        return Path(env_value).expanduser().resolve()

    search_roots: List[Path] = [Path.cwd().resolve(), *Path.cwd().resolve().parents, *SCRIPT_DIR.resolve().parents]
    seen: set[Path] = set()
    for root in search_roots:
        if root in seen:
            continue
        seen.add(root)
        if is_upstream_source_repo(root):
            return root
        for child_name in ("design.md-main", "design.md"):
            candidate = root / child_name
            if is_upstream_source_repo(candidate):
                return candidate.resolve()
    return None


def detect_runtime_paths(source_repo: Optional[Path]) -> Dict[str, object]:
    node_path = shutil.which("node")
    npx_path = shutil.which("npx")
    bun_path = shutil.which("bun")
    local_dist = source_repo / "packages" / "cli" / "dist" / "index.js" if source_repo else None
    local_src = source_repo / "packages" / "cli" / "src" / "index.ts" if source_repo else None
    local_spec = source_repo / "docs" / "spec.md" if source_repo else None
    return {
        "source_repo": str(source_repo) if source_repo else "",
        "source_exists": source_repo.exists() if source_repo else False,
        "node_path": node_path or "",
        "npx_path": npx_path or "",
        "bun_path": bun_path or "",
        "local_dist": str(local_dist) if local_dist else "",
        "local_dist_exists": local_dist.exists() if local_dist else False,
        "local_src": str(local_src) if local_src else "",
        "local_src_exists": local_src.exists() if local_src else False,
        "local_spec": str(local_spec) if local_spec else "",
        "local_spec_exists": local_spec.exists() if local_spec else False,
    }


def resolve_upstream_runner(source_repo: Optional[Path], prefer: str) -> tuple[Optional[List[str]], str]:
    runtime = detect_runtime_paths(source_repo)
    node_path = str(runtime["node_path"])
    npx_path = str(runtime["npx_path"])
    bun_path = str(runtime["bun_path"])

    local_candidates: List[tuple[List[str], str]] = []
    if runtime["local_dist_exists"] and node_path:
        local_candidates.append(([node_path, str(runtime["local_dist"])], "local-dist"))
    if runtime["local_src_exists"] and bun_path:
        local_candidates.append(([bun_path, "run", str(runtime["local_src"])], "local-bun"))

    npx_candidate: Optional[tuple[List[str], str]] = None
    if npx_path:
        npx_candidate = (
            [npx_path, "--yes", "--package", "@google/design.md", "design.md"],
            "npx-package",
        )

    if prefer == "local":
        if local_candidates:
            return local_candidates[0]
        return None, "local-unavailable"
    if prefer == "npx":
        if npx_candidate:
            return npx_candidate
        return None, "npx-unavailable"

    if local_candidates:
        return local_candidates[0]
    if npx_candidate:
        return npx_candidate
    return None, "no-upstream-runner"


def build_doctor_payload(source_repo: Optional[Path], prefer: str) -> Dict[str, object]:
    runtime = detect_runtime_paths(source_repo)
    runner, runner_kind = resolve_upstream_runner(source_repo, prefer)
    payload: Dict[str, object] = {
        "status": "checked",
        "bundled_engine": True,
        "source_repo_env_var": SOURCE_REPO_ENV_VAR,
        "source_repo": {
            "path": str(source_repo) if source_repo else "",
            "exists": runtime["source_exists"],
        },
        "local_repo": {
            "dist_available": runtime["local_dist_exists"],
            "src_available": runtime["local_src_exists"],
            "spec_available": runtime["local_spec_exists"],
        },
        "runtimes": {
            "node": bool(runtime["node_path"]),
            "npx": bool(runtime["npx_path"]),
            "bun": bool(runtime["bun_path"]),
        },
        "selected_runner": "bundled-python" if prefer == "auto" else runner_kind,
        "selected_command": [] if prefer == "auto" else (runner or []),
        "upstream_runner": runner_kind,
        "upstream_command": runner or [],
    }
    return payload


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
            if isinstance(value, str) and not HEX_COLOR_PATTERN.fullmatch(value):
                findings.append(make_finding("warning", f"colors.{key}", f"Color token `{key}` should be a 6-digit hex value."))
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


def run_upstream_capture(base_command: Sequence[str], extra_args: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [*base_command, *extra_args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def maybe_emit_upstream(result: subprocess.CompletedProcess[str]) -> bool:
    stdout = (result.stdout or "").strip()
    stderr = (result.stderr or "").strip()
    if result.returncode != 0:
        if result.stdout:
            sys.stdout.write(result.stdout)
        if result.stderr:
            sys.stderr.write(result.stderr)
        return True
    if stdout:
        sys.stdout.write(result.stdout)
        if result.stderr:
            sys.stderr.write(result.stderr)
        return True
    if stderr:
        sys.stderr.write(result.stderr)
    return False


def render_spec_payload(source_repo: Optional[Path], include_rules: bool, rules_only: bool) -> Dict[str, Any]:
    spec_path = source_repo / "docs" / "spec.md" if source_repo else None
    fallback_summary_path = SKILL_DIR / "references" / "spec-essentials.md"
    if spec_path and spec_path.exists():
        spec_text = spec_path.read_text(encoding="utf-8")
    elif fallback_summary_path.exists():
        spec_text = fallback_summary_path.read_text(encoding="utf-8")
    else:
        spec_text = "# DESIGN.md Format\n\nBundled spec summary is not available.\n"
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


def execute_bundled(args: argparse.Namespace) -> int:
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
        payload = render_spec_payload(resolve_source_repo(args.source_repo), args.rules, args.rules_only)
        if args.format == "markdown":
            if args.rules_only:
                lines = ["## Bundled Lint Rules", ""]
                for rule in payload["rules"]:
                    lines.append(f"- `{rule['name']}` ({rule['severity']}): {rule['description']}")
                sys.stdout.write("\n".join(lines) + "\n")
            else:
                sys.stdout.write(payload["spec"])
                if args.rules:
                    sys.stdout.write("\n\n## Bundled Lint Rules\n\n")
                    for rule in payload["rules"]:
                        sys.stdout.write(f"- `{rule['name']}` ({rule['severity']}): {rule['description']}\n")
                if not payload["spec"].endswith("\n"):
                    sys.stdout.write("\n")
        else:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    raise ValueError(f"Unsupported command: {args.command}")


def handle_proxy(args: argparse.Namespace) -> int:
    source_repo = resolve_source_repo(args.source_repo)
    if args.prefer != "auto":
        base_command, _runner_kind = resolve_upstream_runner(source_repo, args.prefer)
        if base_command is not None:
            if args.command == "lint":
                result = run_upstream_capture(base_command, ["lint", args.file, "--format", args.format])
            elif args.command == "diff":
                result = run_upstream_capture(base_command, ["diff", args.before, args.after, "--format", args.format])
            elif args.command == "export":
                result = run_upstream_capture(base_command, ["export", args.file, "--format", args.format])
            elif args.command == "spec":
                extra_args = ["spec", "--format", args.format]
                if args.rules:
                    extra_args.append("--rules")
                if args.rules_only:
                    extra_args.append("--rules-only")
                result = run_upstream_capture(base_command, extra_args)
            else:
                raise ValueError(f"Unsupported proxy command: {args.command}")

            if maybe_emit_upstream(result):
                return result.returncode
            sys.stderr.write("warning: upstream DESIGN.md CLI produced no stdout; falling back to bundled engine.\n")
        elif args.prefer == "npx":
            sys.stderr.write("warning: requested npx runner is unavailable; falling back to bundled engine.\n")
        elif args.prefer == "local":
            sys.stderr.write("warning: requested local upstream runner is unavailable; falling back to bundled engine.\n")

    return execute_bundled(args)


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
        source_repo = resolve_source_repo(args.source_repo)
        payload = build_doctor_payload(source_repo, args.prefer)
        emit(payload, args.format)
        return 0
    return handle_proxy(args)


if __name__ == "__main__":
    sys.exit(main())
