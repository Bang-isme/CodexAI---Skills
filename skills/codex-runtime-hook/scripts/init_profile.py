#!/usr/bin/env python3
"""Create a project-local CodexAI profile at .codex/profile.json."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


VALID_DOMAINS = {"frontend", "backend", "fullstack", "mobile", "devops", "qa", "unknown"}
VALID_TEST_FRAMEWORKS = {"jest", "vitest", "pytest", "mocha", "playwright", "cypress", "none", "unknown"}
VALID_DEPLOY_TARGETS = {"vercel", "cloudflare", "docker", "kubernetes", "github-actions", "gitlab", "manual", "none", "unknown"}


SCHEMA_VERSION = "1.0"


def parse_csv(value: str, *, lower: bool = True) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in value.split(","):
        normalized = item.strip().replace("\\", "/")
        key = normalized.lower()
        value_to_store = key if lower else normalized
        if normalized and key not in seen:
            result.append(value_to_store)
            seen.add(key)
    return result


def validate_project_root(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"Project root does not exist: {resolved}")
    if not resolved.is_dir():
        raise NotADirectoryError(f"Project root is not a directory: {resolved}")
    return resolved


def read_package_json(project_root: Path) -> dict[str, Any]:
    path = project_root / "package.json"
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def infer_from_project(project_root: Path) -> dict[str, Any]:
    package = read_package_json(project_root)
    deps: set[str] = set()
    for key in ("dependencies", "devDependencies", "peerDependencies"):
        section = package.get(key, {})
        if isinstance(section, dict):
            deps.update(str(name).lower() for name in section)

    stack: list[str] = []
    for name in ("react", "next", "vue", "svelte", "vite", "express", "fastify", "django", "flask", "fastapi", "prisma", "mongoose", "sequelize"):
        if name in deps:
            stack.append(name)

    frontend = bool({"react", "next", "vue", "svelte", "vite"} & deps) or any((project_root / name).exists() for name in ("src", "app", "components"))
    backend = bool({"express", "fastify", "django", "flask", "fastapi"} & deps) or any((project_root / name).exists() for name in ("api", "server", "routes", "controllers"))
    devops = any((project_root / path).exists() for path in (".github/workflows", "Dockerfile", "docker-compose.yml", "infra", "k8s", "terraform"))
    tests = []
    for name in ("jest", "vitest", "pytest", "mocha", "playwright", "cypress"):
        if name in deps or (project_root / f"{name}.config.js").exists() or (project_root / f"{name}.config.ts").exists():
            tests.append(name)

    primary_domain = "fullstack" if frontend and backend else ("frontend" if frontend else ("backend" if backend else ("devops" if devops else "unknown")))
    deploy_target = "docker" if (project_root / "Dockerfile").exists() or (project_root / "docker-compose.yml").exists() else ("github-actions" if (project_root / ".github" / "workflows").exists() else "unknown")
    return {
        "stack": stack,
        "primary_domain": primary_domain,
        "test_framework": tests[0] if tests else "unknown",
        "deploy_target": deploy_target,
    }


def validate_reference_path(value: str) -> str:
    normalized = value.strip().replace("\\", "/")
    path = Path(normalized)
    if not normalized:
        raise ValueError("custom reference path cannot be empty")
    if path.is_absolute() or normalized.startswith("/") or ":" in normalized.split("/", 1)[0]:
        raise ValueError(f"custom reference must be repo-relative: {value}")
    if any(part == ".." for part in normalized.split("/")):
        raise ValueError(f"custom reference cannot escape project root: {value}")
    return normalized


def render_profile(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Initialize .codex/profile.json for CodexAI routing.")
    parser.add_argument("--project-root", required=True, help="Project root path")
    parser.add_argument("--name", default="", help="Project name. Defaults to project directory name")
    parser.add_argument("--stack", default="", help="Comma-separated stack values, e.g. react,express,postgres")
    parser.add_argument("--primary-domain", choices=sorted(VALID_DOMAINS), default="", help="Primary domain override")
    parser.add_argument("--test-framework", choices=sorted(VALID_TEST_FRAMEWORKS), default="", help="Test framework override")
    parser.add_argument("--deploy-target", choices=sorted(VALID_DEPLOY_TARGETS), default="", help="Deploy target override")
    parser.add_argument("--custom-references", default="", help="Comma-separated project-specific reference files")
    parser.add_argument("--language", default="en", help="Preferred response/document language")
    parser.add_argument("--output-style", default="evidence-first", help="Preferred output style")
    parser.add_argument("--verification-preference", default="auto_gate_full", help="Preferred verification gate")
    parser.add_argument("--force", action="store_true", help="Overwrite existing profile")
    parser.add_argument("--dry-run", action="store_true", help="Preview profile payload without writing")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    return parser.parse_args()


def build_profile(project_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    inferred = infer_from_project(project_root)
    stack = parse_csv(args.stack) if args.stack else inferred["stack"]
    references = [
        {"path": validate_reference_path(path), "type": "reference", "trusted": False}
        for path in parse_csv(args.custom_references, lower=False)
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "name": args.name.strip() or project_root.name,
        "stack": stack,
        "primary_domain": args.primary_domain or inferred["primary_domain"],
        "test_framework": args.test_framework or inferred["test_framework"],
        "deploy_target": args.deploy_target or inferred["deploy_target"],
        "custom_references": references,
        "preferences": {
            "response_language": args.language.strip() or "en",
            "output_style": args.output_style.strip() or "evidence-first",
            "verification_preference": args.verification_preference.strip() or "auto_gate_full",
        },
    }


def main() -> int:
    args = parse_args()
    try:
        project_root = validate_project_root(Path(args.project_root))
        profile_path = project_root / ".codex" / "profile.json"
        profile = build_profile(project_root, args)
        existed = profile_path.exists()
        if args.dry_run:
            status = "dry_run"
        elif profile_path.exists() and not args.force:
            status = "skipped"
        else:
            profile_path.parent.mkdir(parents=True, exist_ok=True)
            profile_path.write_text(render_profile(profile), encoding="utf-8")
            status = "updated" if existed else "created"
        payload = {"status": status, "path": str(profile_path), "profile": profile}
    except Exception as exc:
        payload = {"status": "error", "message": str(exc)}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1

    if args.format == "text":
        print(f"{payload['status']}: {payload['path']}")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
