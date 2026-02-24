#!/usr/bin/env python3
"""
Generate a portable project handoff markdown for any AI tool.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple


SKIP_DIRS = {
    ".git",
    "node_modules",
    "dist",
    "build",
    "__pycache__",
    ".next",
    ".venv",
    "venv",
    ".codex",
    ".idea",
    ".vscode",
    ".yarn",
}
TEXT_SCAN_LIMIT = 250_000
MAX_TREE_ITEMS_PER_DIR = 40

LANGUAGE_BY_EXT = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript (JSX)",
    ".ts": "TypeScript",
    ".tsx": "TypeScript (TSX)",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".kt": "Kotlin",
    ".swift": "Swift",
    ".rb": "Ruby",
    ".php": "PHP",
    ".c": "C",
    ".cpp": "C++",
    ".cs": "C#",
}

FRAMEWORK_MAP = {
    "react": "React",
    "next": "Next.js",
    "vue": "Vue",
    "nuxt": "Nuxt",
    "svelte": "Svelte",
    "@angular/core": "Angular",
    "fastapi": "FastAPI",
    "django": "Django",
    "flask": "Flask",
    "express": "Express",
    "nestjs": "NestJS",
}

DATABASE_KEYWORDS = {
    "postgres": "PostgreSQL",
    "pg": "PostgreSQL",
    "mysql": "MySQL",
    "mariadb": "MariaDB",
    "sqlite": "SQLite",
    "mongodb": "MongoDB",
    "mongoose": "MongoDB",
    "redis": "Redis",
    "prisma": "Prisma",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(

        description="Generate project handoff markdown.",

        formatter_class=argparse.RawDescriptionHelpFormatter,

        epilog=(

            "Examples:\n"

            "  python generate_handoff.py --project-root <path>\n"

            "  python generate_handoff.py --help\n\n"

            "Output:\n  JSON to stdout: {\"status\": \"...\", ...}"

        ),

    )
    parser.add_argument("--project-root", required=True, help="Project root path")
    parser.add_argument("--output", default="", help="Output markdown path")
    parser.add_argument("--max-depth", type=int, default=3, help="Folder tree depth")
    parser.add_argument("--include-decisions", dest="include_decisions", action="store_true", default=True)
    parser.add_argument("--no-include-decisions", dest="include_decisions", action="store_false")
    parser.add_argument("--include-git-status", dest="include_git_status", action="store_true", default=True)
    parser.add_argument("--no-include-git-status", dest="include_git_status", action="store_false")
    return parser.parse_args()


def emit(payload: Dict[str, object]) -> None:
    print(json.dumps(payload, ensure_ascii=False))


def safe_read(path: Path) -> str:
    try:
        if path.stat().st_size > TEXT_SCAN_LIMIT:
            return ""
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def run_git(project_root: Path, args: List[str]) -> Optional[subprocess.CompletedProcess]:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=project_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        return None


def git_ready(project_root: Path) -> bool:
    check = run_git(project_root, ["rev-parse", "--is-inside-work-tree"])
    if check is None:
        return False
    return check.returncode == 0 and check.stdout.strip().lower() == "true"


def load_package_json(project_root: Path) -> Dict[str, object]:
    pkg_path = project_root / "package.json"
    if not pkg_path.exists():
        return {}
    try:
        return json.loads(safe_read(pkg_path))
    except json.JSONDecodeError:
        return {}


def detect_runtime(project_root: Path) -> List[str]:
    runtime: List[str] = []
    if (project_root / "package.json").exists():
        runtime.append("Node.js")
    if (project_root / "pyproject.toml").exists() or (project_root / "requirements.txt").exists():
        runtime.append("Python")
    if (project_root / "Cargo.toml").exists():
        runtime.append("Rust")
    if (project_root / "go.mod").exists():
        runtime.append("Go")
    if not runtime:
        runtime.append("Unknown")
    return runtime


def detect_frameworks(project_root: Path) -> List[str]:
    frameworks: Set[str] = set()
    package_data = load_package_json(project_root)
    deps: Dict[str, str] = {}
    for section in ("dependencies", "devDependencies"):
        section_data = package_data.get(section)
        if isinstance(section_data, dict):
            deps.update({str(k).lower(): str(v) for k, v in section_data.items()})

    for dep_name in deps:
        if dep_name in FRAMEWORK_MAP:
            frameworks.add(FRAMEWORK_MAP[dep_name])

    pyproject = safe_read(project_root / "pyproject.toml").lower()
    requirements = safe_read(project_root / "requirements.txt").lower()
    for key, value in FRAMEWORK_MAP.items():
        if key in pyproject or key in requirements:
            frameworks.add(value)

    return sorted(frameworks)


def detect_databases(project_root: Path) -> List[str]:
    found: Set[str] = set()
    package_data = load_package_json(project_root)
    deps: Dict[str, str] = {}
    for section in ("dependencies", "devDependencies"):
        data = package_data.get(section)
        if isinstance(data, dict):
            deps.update({str(k).lower(): str(v) for k, v in data.items()})

    for name, db in DATABASE_KEYWORDS.items():
        if name in deps:
            found.add(db)

    scan_files = [
        project_root / "pyproject.toml",
        project_root / "requirements.txt",
        project_root / "docker-compose.yml",
        project_root / "docker-compose.yaml",
        project_root / ".env",
        project_root / ".env.local",
        project_root / ".env.development",
        project_root / "prisma" / "schema.prisma",
    ]
    for file_path in scan_files:
        content = safe_read(file_path).lower()
        if not content:
            continue
        for token, db in DATABASE_KEYWORDS.items():
            if token in content:
                found.add(db)

    return sorted(found)


def detect_languages(project_root: Path) -> List[str]:
    counts: Counter[str] = Counter()
    for current_root, dirs, files in os.walk(project_root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            ext = Path(name).suffix.lower()
            language = LANGUAGE_BY_EXT.get(ext)
            if language:
                counts[language] += 1
    if not counts:
        return ["Unknown"]
    return [name for name, _ in counts.most_common(4)]


def build_tree_lines(
    root: Path,
    max_depth: int,
) -> List[str]:
    lines: List[str] = [f"{root.name}/"]

    def recurse(path: Path, depth: int, prefix: str) -> None:
        if depth >= max_depth:
            return
        try:
            entries = [entry for entry in path.iterdir() if entry.name not in SKIP_DIRS]
        except OSError:
            return
        entries.sort(key=lambda e: (not e.is_dir(), e.name.lower()))

        truncated = False
        if len(entries) > MAX_TREE_ITEMS_PER_DIR:
            entries = entries[:MAX_TREE_ITEMS_PER_DIR]
            truncated = True

        for idx, entry in enumerate(entries):
            last = idx == len(entries) - 1 and not truncated
            branch = "`-- " if last else "|-- "
            suffix = "/" if entry.is_dir() else ""
            lines.append(f"{prefix}{branch}{entry.name}{suffix}")
            if entry.is_dir():
                next_prefix = f"{prefix}{'    ' if last else '|   '}"
                recurse(entry, depth + 1, next_prefix)

        if truncated:
            lines.append(f"{prefix}`-- ... (truncated)")

    recurse(root, 0, "")
    return lines


def detect_key_files(project_root: Path) -> List[str]:
    keys: Set[Path] = set()
    candidates = [
        "package.json",
        "requirements.txt",
        "pyproject.toml",
        "tsconfig.json",
        ".eslintrc",
        ".eslintrc.json",
        ".eslintrc.js",
        "eslint.config.js",
        "eslint.config.mjs",
        ".prettierrc",
        ".prettierrc.json",
        ".prettierrc.js",
        "prettier.config.js",
        "README.md",
        "docker-compose.yml",
        "docker-compose.yaml",
    ]
    for rel in candidates:
        path = project_root / rel
        if path.exists() and path.is_file():
            keys.add(path)

    globs = [
        "src/main.*",
        "src/index.*",
        "app/main.*",
        "app/index.*",
        "server.*",
        "src/**/routes.*",
        "src/**/router.*",
        "src/**/*route*.*",
        "src/**/*controller*.*",
        "src/**/*model*.*",
        "src/**/*schema*.*",
    ]
    for pattern in globs:
        for path in project_root.glob(pattern):
            if path.is_file():
                keys.add(path)

    ordered = sorted(keys, key=lambda p: p.as_posix().lower())
    return [path.resolve().relative_to(project_root.resolve()).as_posix() for path in ordered[:30]]


def load_recent_decisions(project_root: Path) -> List[str]:
    decisions_dir = project_root / ".codex" / "decisions"
    if not decisions_dir.exists() or not decisions_dir.is_dir():
        return []
    files = sorted(
        [path for path in decisions_dir.glob("*.md") if path.is_file()],
        key=lambda path: path.name,
        reverse=True,
    )
    result: List[str] = []
    for path in files[:5]:
        text = safe_read(path)
        title_match = re.search(r"^#\s*Decision:\s*(.+)$", text, flags=re.MULTILINE)
        date_match = re.search(r"^Date:\s*(.+)$", text, flags=re.MULTILINE)
        title = title_match.group(1).strip() if title_match else path.stem
        date_text = date_match.group(1).strip() if date_match else path.name[:10]
        result.append(f"- [{date_text}] {title} (`{path.name}`)")
    return result


def load_project_patterns(project_root: Path) -> List[str]:
    profile_path = project_root / ".codex" / "project-profile.json"
    if not profile_path.exists():
        return []
    try:
        profile = json.loads(safe_read(profile_path))
    except json.JSONDecodeError:
        return ["- Unable to parse `.codex/project-profile.json`."]

    bullets: List[str] = []
    if isinstance(profile, dict):
        patterns = profile.get("patterns")
        if isinstance(patterns, list):
            for item in patterns[:12]:
                bullets.append(f"- {item}")
        known = profile.get("known_patterns")
        if isinstance(known, list):
            for item in known[:12]:
                bullets.append(f"- {item}")
        if not bullets:
            for key in sorted(profile.keys()):
                value = profile[key]
                if isinstance(value, (str, int, float, bool)):
                    bullets.append(f"- {key}: {value}")
    if not bullets:
        bullets.append("- `.codex/project-profile.json` exists but no recognized `patterns` entries were found.")
    return bullets


def load_current_issues(project_root: Path) -> List[str]:
    codex_dir = project_root / ".codex"
    if not codex_dir.exists():
        return []
    candidates = sorted(
        [path for path in codex_dir.rglob("*.json") if path.is_file() and "tech" in path.name.lower()],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for path in candidates:
        try:
            payload = json.loads(safe_read(path))
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        if "summary" in payload and "total_issues" in payload:
            rel = path.resolve().relative_to(project_root.resolve()).as_posix()
            return [
                f"- Source: `{rel}`",
                f"- Summary: {payload.get('summary')}",
                f"- Total issues: {payload.get('total_issues')}",
            ]
    return []


def detect_conventions(project_root: Path) -> List[str]:
    notes: List[str] = []
    package_data = load_package_json(project_root)

    if package_data.get("eslintConfig"):
        notes.append("- ESLint config detected in `package.json`.")
    elif any((project_root / name).exists() for name in [".eslintrc", ".eslintrc.json", ".eslintrc.js", "eslint.config.js", "eslint.config.mjs"]):
        notes.append("- ESLint config file detected.")

    if package_data.get("prettier") is not None:
        notes.append("- Prettier config detected in `package.json`.")
    elif any((project_root / name).exists() for name in [".prettierrc", ".prettierrc.json", ".prettierrc.js", "prettier.config.js"]):
        notes.append("- Prettier config file detected.")

    tsconfig_path = project_root / "tsconfig.json"
    if tsconfig_path.exists():
        try:
            tsconfig = json.loads(safe_read(tsconfig_path))
        except json.JSONDecodeError:
            tsconfig = {}
        compiler_opts = tsconfig.get("compilerOptions", {}) if isinstance(tsconfig, dict) else {}
        if isinstance(compiler_opts, dict):
            strict_value = compiler_opts.get("strict")
            if strict_value is True:
                notes.append("- TypeScript strict mode is enabled (`tsconfig.json`).")
            elif strict_value is False:
                notes.append("- TypeScript strict mode is explicitly disabled (`tsconfig.json`).")
            else:
                notes.append("- TypeScript config detected (`tsconfig.json`).")

    pyproject = safe_read(project_root / "pyproject.toml")
    if "[tool.ruff]" in pyproject:
        notes.append("- Ruff linting config detected (`pyproject.toml`).")
    if "[tool.black]" in pyproject:
        notes.append("- Black formatting config detected (`pyproject.toml`).")

    if not notes:
        notes.append("- No explicit ESLint/Prettier/tsconfig strict conventions detected.")
    return notes


def format_tech_stack(project_root: Path) -> List[str]:
    runtime = ", ".join(detect_runtime(project_root))
    frameworks = ", ".join(detect_frameworks(project_root)) or "Unknown"
    databases = ", ".join(detect_databases(project_root)) or "Unknown"
    languages = ", ".join(detect_languages(project_root))
    return [
        f"- Runtime: {runtime}",
        f"- Framework: {frameworks}",
        f"- Database: {databases}",
        f"- Language: {languages}",
    ]


def generate_handoff(
    project_root: Path,
    output_path: Path,
    max_depth: int,
    include_decisions: bool,
    include_git_status: bool,
) -> Dict[str, object]:
    warnings: List[str] = []
    sections = 0
    lines: List[str] = []

    project_name = project_root.name
    generated_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines.append(f"# Project Handoff: {project_name}")
    lines.append(f"Generated: {generated_time}")
    lines.append("")

    lines.append("## Tech Stack")
    lines.extend(format_tech_stack(project_root))
    lines.append("")
    sections += 1

    lines.append("## Project Structure")
    lines.extend(build_tree_lines(project_root, max_depth=max_depth))
    lines.append("")
    sections += 1

    lines.append("## Key Files")
    key_files = detect_key_files(project_root)
    if key_files:
        lines.extend([f"- `{path}`" for path in key_files])
    else:
        lines.append("- No key files detected.")
    lines.append("")
    sections += 1

    git_ok = git_ready(project_root)
    if include_git_status and git_ok:
        lines.append("## Recent Changes (git)")
        log_result = run_git(project_root, ["log", "--oneline", "-10"])
        if log_result is None:
            lines.append("Recent commit list timed out after 60s.")
            warnings.append("Git log command timed out after 60s; skipped commit list.")
        elif log_result.returncode == 0 and log_result.stdout.strip():
            lines.append(log_result.stdout.strip())
        else:
            lines.append("No recent commits found.")
        status_result = run_git(project_root, ["status", "--short"])
        if status_result is None:
            status_text = ""
            warnings.append("Git status command timed out after 60s; skipped uncommitted changes.")
        else:
            status_text = status_result.stdout.strip() if status_result.returncode == 0 else ""
        if status_text:
            lines.append("")
            lines.append("Uncommitted changes:")
            lines.append(status_text)
        lines.append("")
        sections += 1
    elif include_git_status and not git_ok:
        warnings.append("Git unavailable or project is not a git repository. Skipped git sections.")

    if include_decisions:
        decisions = load_recent_decisions(project_root)
        if decisions:
            lines.append("## Active Decisions")
            lines.extend(decisions)
            lines.append("")
            sections += 1

    patterns = load_project_patterns(project_root)
    if patterns:
        lines.append("## Known Patterns")
        lines.extend(patterns)
        lines.append("")
        sections += 1

    issues = load_current_issues(project_root)
    if issues:
        lines.append("## Current Issues")
        lines.extend(issues)
        lines.append("")
        sections += 1

    lines.append("## Conventions")
    lines.extend(detect_conventions(project_root))
    lines.append("")
    sections += 1

    content = "\n".join(lines).rstrip() + "\n"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)

    payload: Dict[str, object] = {
        "status": "generated",
        "path": output_path.as_posix(),
        "sections": sections,
        "size_bytes": output_path.stat().st_size,
    }
    if warnings:
        payload["warnings"] = warnings
    return payload


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).expanduser().resolve()

    if not project_root.exists() or not project_root.is_dir():
        emit(
            {
                "status": "error",
                "path": "",
                "message": f"Project root does not exist or is not a directory: {project_root}",
            }
        )
        return 1

    output_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else (project_root / ".codex" / "handoff.md").resolve()
    )

    try:
        result = generate_handoff(
            project_root=project_root,
            output_path=output_path,
            max_depth=max(1, args.max_depth),
            include_decisions=args.include_decisions,
            include_git_status=args.include_git_status,
        )
    except PermissionError as exc:
        emit({"status": "error", "path": "", "message": f"Permission denied: {exc}"})
        return 1
    except OSError as exc:
        emit({"status": "error", "path": "", "message": f"I/O failure: {exc}"})
        return 1
    except Exception as exc:  # pragma: no cover - defensive
        emit({"status": "error", "path": "", "message": f"Unexpected error: {exc}"})
        return 1

    emit(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
