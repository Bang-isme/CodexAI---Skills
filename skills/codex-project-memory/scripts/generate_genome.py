#!/usr/bin/env python3
"""
Generate Project Genome: multi-layer context documentation for AI agents.
Combines output from build_knowledge_graph.py and analyze_patterns.py
into human/AI-readable markdown files.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


SKIP_DIRS = {
    "node_modules",
    ".git",
    "__pycache__",
    ".next",
    "dist",
    "build",
    ".venv",
    "venv",
    ".codex",
    ".idea",
    ".vscode",
    ".yarn",
    "coverage",
    ".cache",
    ".parcel-cache",
    "target",
}

CODE_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".vue",
    ".css",
    ".scss",
    ".html",
    ".java",
    ".kt",
    ".swift",
    ".go",
    ".rs",
    ".rb",
    ".php",
    ".c",
    ".cpp",
    ".h",
    ".cs",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".md",
}

CODE_EXTENSIONS_FOR_MODULE = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".mjs",
    ".cjs",
    ".vue",
    ".java",
    ".kt",
    ".swift",
    ".go",
    ".rs",
    ".rb",
    ".php",
    ".c",
    ".cpp",
    ".h",
    ".cs",
}

MAX_FILE_SIZE = 1_000_000
NOISE_MODEL_NAMES = {"index", "init", "setup", "connection", "db"}
STYLE_EXTENSIONS = {".css", ".scss", ".sass", ".less", ".styl", ".pcss"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate Project Genome: multi-layer context documentation for AI agents.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python generate_genome.py --project-root .\n"
            "  python generate_genome.py --project-root . --depth full --force\n\n"
            "Output:\n"
            "  Creates .codex/context/genome.md and optionally .codex/context/modules/*.md\n"
            "  Also outputs JSON summary to stdout."
        ),
    )
    parser.add_argument("--project-root", required=True, help="Project root directory")
    parser.add_argument(
        "--depth",
        choices=["shallow", "full", "auto"],
        default="auto",
        help="Generation depth: shallow (genome only), full (genome + modules), auto (detect)",
    )
    parser.add_argument("--force", action="store_true", help="Re-generate even if genome.md exists")
    return parser.parse_args()


def emit(payload: Dict[str, object]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def parse_json_from_stdout(stdout: str) -> Optional[Dict[str, Any]]:
    text = stdout.strip()
    if not text:
        return None

    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    starts = [idx for idx, ch in enumerate(text) if ch == "{"]
    for idx in reversed(starts):
        try:
            parsed = json.loads(text[idx:])
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return None


def run_helper_script(
    script_name: str,
    project_root: Path,
    extra_args: Optional[List[str]] = None,
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Run a sibling script and parse its JSON output."""
    script_path = Path(__file__).parent / script_name
    if not script_path.exists():
        return None, f"{script_name} not found."

    command = [sys.executable, str(script_path), "--project-root", str(project_root)]
    if extra_args:
        command.extend(extra_args)

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return None, f"{script_name} timed out after 120s."
    except OSError as exc:
        return None, f"{script_name} failed to run: {exc}"

    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        message = stderr.splitlines()[-1] if stderr else f"{script_name} exited with code {result.returncode}."
        return None, message

    payload = parse_json_from_stdout(result.stdout or "")
    if payload is None:
        return None, f"{script_name} returned non-JSON output."
    return payload, None


def count_project_files(project_root: Path) -> Tuple[int, int, Dict[str, int]]:
    """Count files, lines, and files per top-level directory."""
    total_files = 0
    total_lines = 0
    dir_file_counts: Dict[str, int] = defaultdict(int)

    for root_str, dirs, files in os.walk(project_root):
        dirs[:] = [item for item in dirs if item not in SKIP_DIRS]
        root_path = Path(root_str)
        rel_root = root_path.relative_to(project_root)
        parts = rel_root.parts
        top_dir = parts[0] if parts else "."

        for fname in files:
            fpath = root_path / fname
            if fpath.suffix.lower() not in CODE_EXTENSIONS:
                continue
            try:
                if fpath.stat().st_size > MAX_FILE_SIZE:
                    continue
            except OSError:
                continue

            total_files += 1
            dir_file_counts[top_dir] += 1
            try:
                with fpath.open("r", encoding="utf-8", errors="ignore") as handle:
                    total_lines += sum(1 for _ in handle)
            except OSError:
                pass

    return total_files, total_lines, dict(dir_file_counts)


def count_code_files_per_dir(project_root: Path) -> Dict[str, int]:
    """Count code files per top-level directory (exclude docs/config-only extensions)."""
    code_counts: Dict[str, int] = defaultdict(int)
    for root_str, dirs, files in os.walk(project_root):
        dirs[:] = [item for item in dirs if item not in SKIP_DIRS]
        root_path = Path(root_str)
        rel_root = root_path.relative_to(project_root)
        parts = rel_root.parts
        top_dir = parts[0] if parts else "."

        for fname in files:
            if Path(fname).suffix.lower() in CODE_EXTENSIONS_FOR_MODULE:
                code_counts[top_dir] += 1

    return dict(code_counts)


def detect_depth(total_files: int, user_choice: str) -> str:
    if user_choice != "auto":
        return user_choice
    return "full" if total_files >= 50 else "shallow"


def pick_primary_language(dir_counts: Dict[str, int], patterns_profile: Optional[Dict[str, Any]]) -> str:
    if patterns_profile:
        entry = str(patterns_profile.get("structure", {}).get("entry_point", ""))
        if entry.endswith(".py"):
            return "Python"
        if entry.endswith((".ts", ".tsx")):
            return "TypeScript"
        if entry.endswith((".js", ".jsx", ".mjs", ".cjs")):
            return "JavaScript"
    return "Mixed"


def normalize_route_stem(value: str) -> str:
    lowered = value.lower().replace("_", "").replace("-", "")
    for suffix in (".routes", ".route", "routes", "route", "router"):
        if lowered.endswith(suffix):
            lowered = lowered[: -len(suffix)]
            break
    return lowered


def apply_mount_prefix(prefix: str, path: str) -> str:
    clean_path = path if path.startswith("/") else f"/{path}"
    if not prefix:
        return clean_path
    clean_prefix = prefix.rstrip("/")
    if clean_path == "/":
        return clean_prefix or "/"
    return f"{clean_prefix}{clean_path}" if clean_prefix else clean_path


def extract_route_mount_prefixes(project_root: Path) -> Dict[str, str]:
    """Extract app.use('/prefix', routerVar) mount mappings from common app entry files."""
    prefixes: Dict[str, str] = {}
    candidates = [
        "src/app.js",
        "src/index.js",
        "app.js",
        "index.js",
        "src/app.ts",
        "src/index.ts",
        "server.js",
        "server.ts",
    ]

    mount_pattern = re.compile(r"""app\.use\(\s*['"]([^'"]+)['"]\s*,\s*([A-Za-z_$][\w$]*)""")
    import_default_pattern = re.compile(
        r"""^\s*import\s+([A-Za-z_$][\w$]*)\s+from\s+['"]([^'"]+)['"]""",
        re.MULTILINE,
    )
    require_alias_pattern = re.compile(
        r"""^\s*(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*require\(\s*['"]([^'"]+)['"]\s*\)""",
        re.MULTILINE,
    )

    for rel_path in candidates:
        file_path = project_root / rel_path
        if not file_path.exists() or not file_path.is_file():
            continue
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        alias_to_stem: Dict[str, str] = {}
        for pattern in (import_default_pattern, require_alias_pattern):
            for match in pattern.finditer(content):
                alias = normalize_route_stem(match.group(1))
                module_path = match.group(2)
                module_stem = normalize_route_stem(Path(module_path).stem)
                if module_stem:
                    alias_to_stem[alias] = module_stem

        for match in mount_pattern.finditer(content):
            prefix = match.group(1)
            router_var = normalize_route_stem(match.group(2))
            route_stem = alias_to_stem.get(router_var, router_var)
            if route_stem:
                prefixes[route_stem] = prefix

    return prefixes


def render_genome_md(
    project_root: Path,
    total_files: int,
    total_lines: int,
    dir_counts: Dict[str, int],
    patterns_data: Optional[Dict[str, Any]],
    graph_data: Optional[Dict[str, Any]],
    helper_warnings: List[str],
) -> str:
    """Render Layer 1: genome.md content."""
    project_name = project_root.name
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    profile = patterns_data.get("profile", {}) if isinstance(patterns_data, dict) else {}

    lines: List[str] = []
    lines.append(f"# Project DNA: {project_name}")
    lines.append(f"Generated: {now} | Files: {total_files} | Lines: ~{total_lines}")
    lines.append("")

    lines.append("## Snapshot")
    lines.append(
        "This genome summarizes architecture-level context so AI agents can reason with less scanning and less guessing."
    )
    lines.append(
        f"The project has about {total_files} relevant files and {total_lines} lines in scannable source/docs."
    )
    lines.append("")

    lines.append("## Tech Stack")
    primary_language = pick_primary_language(dir_counts, profile if isinstance(profile, dict) else None)
    lines.append(f"- Language: {primary_language}")
    if isinstance(profile, dict):
        patterns = profile.get("patterns", {})
        imports = profile.get("imports", {})
        error_handling = profile.get("error_handling", {})
        if isinstance(patterns, dict):
            routing_all = patterns.get("routing_all", [])
            routing = patterns.get("routing", "unknown")
            if isinstance(routing_all, list) and routing_all:
                lines.append(f"- Routing: {', '.join(str(item) for item in routing_all)}")
            elif routing != "unknown":
                lines.append(f"- Routing: {routing}")

            orm_all = patterns.get("orm_all", [])
            orm = patterns.get("orm", "unknown")
            if isinstance(orm_all, list) and orm_all:
                lines.append(f"- Database: {', '.join(str(item) for item in orm_all)}")
            elif orm != "unknown":
                lines.append(f"- Database: {orm}")

            auth_all = patterns.get("auth_all", [])
            auth = patterns.get("auth", "unknown")
            if isinstance(auth_all, list) and auth_all:
                lines.append(f"- Auth: {', '.join(str(item) for item in auth_all)}")
            elif auth != "unknown":
                lines.append(f"- Auth: {auth}")

            state_all = patterns.get("state_management_all", [])
            state = patterns.get("state_management", "unknown")
            if isinstance(state_all, list) and state_all:
                lines.append(f"- State: {', '.join(str(item) for item in state_all)}")
            elif state != "unknown":
                lines.append(f"- State: {state}")
        if isinstance(imports, dict):
            lines.append(f"- Module system: {imports.get('module_system', 'unknown')}")
        if isinstance(error_handling, dict):
            lines.append(f"- Error handling style: {error_handling.get('primary_style', 'unknown')}")
    lines.append("")

    lines.append("## Directory Map")
    for dirname, count in sorted(dir_counts.items(), key=lambda item: item[1], reverse=True)[:12]:
        lines.append(f"- `{dirname}/` - {count} files")
    lines.append("")

    if isinstance(profile, dict):
        structure = profile.get("structure", {})
        naming = profile.get("naming", {})
        code_style = profile.get("code_style", {})
        if isinstance(structure, dict):
            entry = structure.get("entry_point")
            if entry:
                lines.append("## Entry Point")
                lines.append(f"- `{entry}`")
                lines.append("")
        if isinstance(naming, dict) or isinstance(code_style, dict):
            lines.append("## Coding Conventions")
            if isinstance(naming, dict):
                lines.append(f"- File naming: {naming.get('files', 'unknown')}")
                lines.append(f"- Function naming: {naming.get('functions', 'unknown')}")
                lines.append(f"- Test pattern: {naming.get('test_pattern', 'unknown')}")
            if isinstance(code_style, dict):
                lines.append(f"- Quotes: {code_style.get('quotes', 'unknown')}")
                lines.append(f"- Semicolons: {code_style.get('semicolons', 'unknown')}")
                lines.append(f"- Indent: {code_style.get('indent', 'unknown')}")
            lines.append("")

    if isinstance(graph_data, dict):
        models = graph_data.get("data_models", {})
        if isinstance(models, dict) and models:
            real_models: Dict[str, Dict[str, Any]] = {}
            for model_name, model_data in models.items():
                if not isinstance(model_data, dict):
                    continue
                if model_name.lower() in NOISE_MODEL_NAMES:
                    continue
                model_type = model_data.get("type", "unknown")
                fields = model_data.get("fields")
                if model_type == "unknown" and not fields:
                    continue
                real_models[model_name] = model_data

            lines.append(f"## Key Data Models ({len(real_models)})")
            for model_name, model_data in list(real_models.items())[:20]:
                fields = model_data.get("fields", []) if isinstance(model_data, dict) else []
                field_list = ", ".join(fields[:6]) if isinstance(fields, list) else ""
                if isinstance(fields, list) and len(fields) > 6:
                    field_list += f", ... (+{len(fields) - 6})"
                model_type = model_data.get("type", "unknown") if isinstance(model_data, dict) else "unknown"
                lines.append(f"- **{model_name}** ({model_type}): {field_list or 'no fields parsed'}")
            lines.append("")

        routes = graph_data.get("api_routes", [])
        if isinstance(routes, list) and routes:
            mount_prefixes = extract_route_mount_prefixes(project_root)
            file_routes: Dict[str, List[str]] = defaultdict(list)
            for route in routes:
                if not isinstance(route, dict):
                    continue
                route_file = str(route.get("file", "unknown"))
                method = str(route.get("method", "?"))
                path = str(route.get("path", "/"))
                file_routes[route_file].append(f"{method} {path}")
            lines.append("## API Surface")
            for route_file in sorted(file_routes.keys()):
                route_list = file_routes[route_file]
                route_name = Path(route_file).stem
                route_stem = normalize_route_stem(route_name)
                prefix = ""
                for stem, mount in mount_prefixes.items():
                    if stem == route_stem or route_stem.startswith(stem) or stem.startswith(route_stem):
                        prefix = mount
                        break

                display_routes: List[str] = []
                for route_desc in route_list[:5]:
                    if " " not in route_desc:
                        display_routes.append(route_desc)
                        continue
                    method, path = route_desc.split(" ", 1)
                    display_path = apply_mount_prefix(prefix, path)
                    display_routes.append(f"{method} {display_path}")

                lines.append(f"- **{route_name}** ({len(route_list)} routes): {', '.join(display_routes)}")
                if len(route_list) > 5:
                    lines.append(f"  ... +{len(route_list) - 5} more")
            lines.append("")

        boundaries = graph_data.get("module_boundaries", {})
        if isinstance(boundaries, dict) and boundaries:
            lines.append("## Module Dependencies")
            for module_name, module_data in sorted(boundaries.items()):
                if not isinstance(module_data, dict):
                    continue
                imports_from = module_data.get("imports_from", [])
                imported_by = module_data.get("imported_by", [])
                in_count = len(imports_from) if isinstance(imports_from, list) else 0
                out_count = len(imported_by) if isinstance(imported_by, list) else 0
                lines.append(f"- `{module_name}`: imports {in_count} modules, imported by {out_count} modules")
            lines.append("")

        cycles = graph_data.get("circular_dependencies", [])
        if isinstance(cycles, list) and cycles:
            lines.append("## Circular Dependencies")
            for cycle in cycles[:5]:
                if isinstance(cycle, list):
                    if len(cycle) <= 3:
                        lines.append(f"- Direct cycle: {' -> '.join(str(item) for item in cycle)}")
                    else:
                        preview = " -> ".join(str(item) for item in cycle[:4])
                        lines.append(
                            f"- Indirect chain ({len(cycle)} modules): {preview} ... "
                            "(run build_knowledge_graph.py for details)"
                        )
            lines.append("")

    if helper_warnings:
        lines.append("## Generation Notes")
        for warning in helper_warnings:
            lines.append(f"- {warning}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def render_module_md(
    module_name: str,
    graph_data: Optional[Dict[str, Any]],
    dir_counts: Dict[str, int],
    mount_prefixes: Optional[Dict[str, str]] = None,
) -> Optional[str]:
    """Render Layer 2: per-module map."""
    if module_name in {"."}:
        return None
    mount_prefixes = mount_prefixes or {}

    lines: List[str] = []
    lines.append(f"# Module: {module_name}/")
    lines.append("")
    lines.append(f"Files: {dir_counts.get(module_name, 0)}")
    lines.append("")

    if isinstance(graph_data, dict):
        boundaries = graph_data.get("module_boundaries", {})
        if isinstance(boundaries, dict):
            module_data = boundaries.get(module_name, {})
            if isinstance(module_data, dict):
                imports_from = module_data.get("imports_from", [])
                imported_by = module_data.get("imported_by", [])
                if isinstance(imports_from, list) and imports_from:
                    lines.append("## Imports From")
                    for item in sorted(imports_from)[:12]:
                        lines.append(f"- `{item}`")
                    lines.append("")
                if isinstance(imported_by, list) and imported_by:
                    lines.append("## Imported By")
                    for item in sorted(imported_by)[:12]:
                        lines.append(f"- `{item}`")
                    lines.append("")

        file_dependencies = graph_data.get("file_dependencies", {})
        if isinstance(file_dependencies, dict):
            module_files = [
                name
                for name in file_dependencies.keys()
                if str(name).startswith(f"{module_name}/") and Path(str(name)).suffix.lower() not in STYLE_EXTENSIONS
            ]
            if module_files:
                lines.append("## Key Files")
                for rel_file in sorted(module_files)[:15]:
                    item = file_dependencies.get(rel_file, {})
                    imports = item.get("imports", []) if isinstance(item, dict) else []
                    imported_by = item.get("imported_by", []) if isinstance(item, dict) else []
                    in_count = len(imports) if isinstance(imports, list) else 0
                    out_count = len(imported_by) if isinstance(imported_by, list) else 0
                    lines.append(f"- `{rel_file}` (imports: {in_count}, imported_by: {out_count})")
                lines.append("")

        routes = graph_data.get("api_routes", [])
        if isinstance(routes, list):
            module_routes = [
                route
                for route in routes
                if isinstance(route, dict) and str(route.get("file", "")).startswith(f"{module_name}/")
            ]
            if module_routes:
                lines.append("## Route Surface")
                for route in module_routes[:10]:
                    method = str(route.get("method", ""))
                    path = str(route.get("path", ""))
                    handler = str(route.get("handler", ""))
                    route_file = str(route.get("file", ""))
                    route_stem = normalize_route_stem(Path(route_file).stem)
                    prefix = ""
                    for stem, mount in mount_prefixes.items():
                        if stem == route_stem or route_stem.startswith(stem) or stem.startswith(route_stem):
                            prefix = mount
                            break
                    display_path = apply_mount_prefix(prefix, path)
                    lines.append(f"- `{method} {display_path}` -> `{handler}`")
                lines.append("")

    if len(lines) <= 3:
        return None
    return "\n".join(lines).rstrip() + "\n"


def safe_module_filename(module_name: str) -> str:
    cleaned = module_name.replace("\\", "-").replace("/", "-").strip()
    cleaned = "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "-" for ch in cleaned)
    return cleaned or "module"


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).expanduser().resolve()
    if not project_root.exists() or not project_root.is_dir():
        emit({"status": "error", "message": f"Not a directory: {project_root}"})
        return 1

    context_dir = project_root / ".codex" / "context"
    genome_path = context_dir / "genome.md"
    modules_dir = context_dir / "modules"

    if genome_path.exists() and not args.force:
        emit(
            {
                "status": "skipped",
                "message": "genome.md already exists. Use --force to regenerate.",
                "path": genome_path.as_posix(),
            }
        )
        return 0

    total_files, total_lines, dir_counts = count_project_files(project_root)
    depth = detect_depth(total_files, args.depth)

    warnings: List[str] = []
    pattern_sample = "50" if total_files >= 50 else "20"
    patterns_data, patterns_warn = run_helper_script(
        "analyze_patterns.py",
        project_root,
        extra_args=["--sample-size", pattern_sample],
    )
    if patterns_warn:
        warnings.append(patterns_warn)

    graph_data, graph_warn = run_helper_script("build_knowledge_graph.py", project_root)
    if graph_warn:
        warnings.append(graph_warn)

    genome_content = render_genome_md(
        project_root=project_root,
        total_files=total_files,
        total_lines=total_lines,
        dir_counts=dir_counts,
        patterns_data=patterns_data,
        graph_data=graph_data,
        helper_warnings=warnings,
    )

    try:
        context_dir.mkdir(parents=True, exist_ok=True)
        genome_path.write_text(genome_content, encoding="utf-8")
    except OSError as exc:
        emit({"status": "error", "message": f"Failed to write genome.md: {exc}"})
        return 1

    module_count = 0
    if depth == "full":
        mount_prefixes = extract_route_mount_prefixes(project_root)
        try:
            modules_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            warnings.append(f"Failed to create modules directory: {exc}")
        else:
            code_dir_counts = count_code_files_per_dir(project_root)
            eligible_modules = {key: val for key, val in code_dir_counts.items() if key != "." and val >= 3}
            top_modules = sorted(eligible_modules.items(), key=lambda item: item[1], reverse=True)[:8]

            planned_files = {f"{safe_module_filename(module_name)}.md" for module_name, _ in top_modules}
            for existing in modules_dir.glob("*.md"):
                if existing.name in planned_files:
                    continue
                try:
                    existing.unlink()
                except OSError as exc:
                    warnings.append(f"Failed to remove stale module map {existing.name}: {exc}")

            for module_name, _count in top_modules:
                module_content = render_module_md(module_name, graph_data, dir_counts, mount_prefixes=mount_prefixes)
                if not module_content:
                    continue
                target = modules_dir / f"{safe_module_filename(module_name)}.md"
                try:
                    target.write_text(module_content, encoding="utf-8")
                except OSError as exc:
                    warnings.append(f"Failed to write module map for {module_name}: {exc}")
                    continue
                module_count += 1

    payload: Dict[str, object] = {
        "status": "ok",
        "project": project_root.name,
        "total_files": total_files,
        "total_lines": total_lines,
        "depth": depth,
        "genome_path": genome_path.as_posix(),
        "module_maps_count": module_count,
    }
    if warnings:
        payload["warnings"] = warnings

    emit(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
