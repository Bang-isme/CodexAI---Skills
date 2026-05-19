#!/usr/bin/env python3
"""Generate a deterministic synthetic project tree for memory scale gates."""
from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from pathlib import Path
from typing import Callable


PolyglotTemplate = tuple[str, str, Callable[[int, int, int, random.Random], str]]


POLYGLOT_TEMPLATES: list[PolyglotTemplate] = [
    (
        ".py",
        "src/layer_{layer:02d}/module_{offset:04d}.py",
        lambda layer, offset, _seed, rng: (
            f"# synthetic python layer={layer} offset={offset}\n"
            f"VALUE = {rng.randint(0, 1_000_000)}\n"
            f"def handler_{layer}_{offset}():\n"
            f"    return VALUE + {offset}\n"
        ),
    ),
    (
        ".js",
        "src/layer_{layer:02d}/module_{offset:04d}.js",
        lambda layer, offset, _seed, rng: (
            f"// synthetic javascript layer={layer} offset={offset}\n"
            f"const VALUE = {rng.randint(0, 1_000_000)};\n"
            f"function handler_{layer}_{offset}() {{\n"
            f"  return VALUE + {offset};\n"
            f"}}\n"
            f"module.exports = {{ handler_{layer}_{offset} }};\n"
        ),
    ),
    (
        ".ts",
        "src/layer_{layer:02d}/module_{offset:04d}.ts",
        lambda layer, offset, _seed, rng: (
            f"// synthetic typescript layer={layer} offset={offset}\n"
            f"export const VALUE = {rng.randint(0, 1_000_000)};\n"
            f"export function handler_{layer}_{offset}(): number {{\n"
            f"  return VALUE + {offset};\n"
            f"}}\n"
        ),
    ),
    (
        ".tsx",
        "src/components/layer_{layer:02d}/Widget_{offset:04d}.tsx",
        lambda layer, offset, _seed, rng: (
            f"import React from 'react';\n"
            f"export function Widget_{layer}_{offset}() {{\n"
            f"  return <motion.div data-seed={{{offset}}} />;\n"
            f"}}\n"
        ),
    ),
    (
        ".go",
        "internal/layer_{layer:02d}/handler_{offset:04d}.go",
        lambda layer, offset, _seed, rng: (
            f"package layer{layer}\n\n"
            f"func Handler{layer}_{offset}() int {{\n"
            f"    return {rng.randint(0, 1_000_000)} + {offset}\n"
            f"}}\n"
        ),
    ),
    (
        ".java",
        "src/main/java/layer{layer}/Handler{offset}.java",
        lambda layer, offset, _seed, rng: (
            f"package layer{layer};\n"
            f"public final class Handler{layer}_{offset} {{\n"
            f"  public int value() {{ return {rng.randint(0, 1_000_000)} + {offset}; }}\n"
            f"}}\n"
        ),
    ),
    (
        ".rs",
        "src/rust/layer_{layer:02d}/handler_{offset:04d}.rs",
        lambda layer, offset, _seed, rng: (
            f"pub fn handler_{layer}_{offset}() -> i32 {{\n"
            f"    {rng.randint(0, 1_000_000)} + {offset}\n"
            f"}}\n"
        ),
    ),
    (
        ".sql",
        "db/migrations/layer_{layer:02d}/migration_{offset:04d}.sql",
        lambda layer, offset, _seed, _rng: (
            f"-- synthetic sql layer={layer} offset={offset}\n"
            f"CREATE TABLE IF NOT EXISTS sample_{layer}_{offset} (id INTEGER PRIMARY KEY);\n"
        ),
    ),
    (
        ".md",
        "docs/layer_{layer:02d}/note_{offset:04d}.md",
        lambda layer, offset, _seed, _rng: (
            f"# Note {layer}-{offset}\n\n"
            f"Synthetic documentation for scale gate layer {layer}.\n"
        ),
    ),
    (
        ".yaml",
        "config/layer_{layer:02d}/service_{offset:04d}.yaml",
        lambda layer, offset, _seed, rng: (
            f"service:\n"
            f"  name: svc-{layer}-{offset}\n"
            f"  port: {8000 + offset % 1000}\n"
            f"  replicas: {1 + rng.randint(0, 3)}\n"
        ),
    ),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate synthetic project files for scale testing.")
    parser.add_argument("--output-dir", required=True, help="Project root directory to populate")
    parser.add_argument("--file-count", type=int, default=2500, help="Number of source files to create")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for deterministic layout")
    parser.add_argument(
        "--include-package-json",
        action="store_true",
        help="Add package.json, tsconfig, pyproject, routes, and Dockerfile stubs",
    )
    parser.add_argument(
        "--polyglot",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Rotate file extensions across supported language templates (default: true)",
    )
    parser.add_argument("--format", choices=("json", "text"), default="json")
    return parser.parse_args()


def write_config_stubs(root: Path, created: list[str]) -> None:
    stubs = {
        "package.json": {
            "name": "scale-fixture",
            "version": "1.0.0",
            "dependencies": {"express": "^4.19.0", "react": "^18.0.0"},
        },
        "tsconfig.json": {
            "compilerOptions": {"target": "ES2020", "module": "commonjs", "jsx": "react-jsx"},
            "include": ["src/**/*.ts", "src/**/*.tsx"],
        },
        "pyproject.toml": '[project]\nname = "scale-fixture"\nversion = "1.0.0"\n',
        "Dockerfile": "FROM node:20-alpine\nWORKDIR /app\nCOPY . .\n",
    }
    for name, content in stubs.items():
        path = root / name
        text = json.dumps(content, indent=2) + "\n" if isinstance(content, dict) else content
        path.write_text(text, encoding="utf-8")
        created.append(name)

    routes_dir = root / "src" / "routes"
    routes_dir.mkdir(parents=True, exist_ok=True)
    route_path = routes_dir / "health.routes.js"
    route_path.write_text(
        "const router = require('express').Router();\n"
        "router.get('/health', (req, res) => res.json({ ok: true }));\n"
        "module.exports = router;\n",
        encoding="utf-8",
    )
    created.append("src/routes/health.routes.js")


def generate_fixture(
    output_dir: Path,
    file_count: int,
    seed: int,
    include_package_json: bool,
    polyglot: bool,
) -> dict[str, object]:
    if file_count < 1:
        raise ValueError("file-count must be at least 1")
    root = output_dir.expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    created: list[str] = []
    extension_counts: Counter[str] = Counter()
    templates = POLYGLOT_TEMPLATES if polyglot else [POLYGLOT_TEMPLATES[0]]
    layers = max(1, min(32, int(file_count**0.5)))
    per_layer = (file_count + layers - 1) // layers
    index = 0
    for layer in range(layers):
        for offset in range(per_layer):
            if index >= file_count:
                break
            ext, pattern, body_fn = templates[index % len(templates)]
            rel = pattern.format(layer=layer, offset=offset)
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body_fn(layer, offset, seed, rng), encoding="utf-8")
            created.append(rel)
            extension_counts[ext] += 1
            index += 1
        if index >= file_count:
            break

    if include_package_json:
        write_config_stubs(root, created)

    marker_path = root / ".scale-gate-fixture"
    marker_path.write_text(
        json.dumps({"schema_version": "1.0", "seed": seed, "file_count": file_count}, indent=2) + "\n",
        encoding="utf-8",
    )
    created.append(".scale-gate-fixture")

    return {
        "status": "generated",
        "output_dir": str(root),
        "file_count": file_count,
        "files_created": len(created),
        "seed": seed,
        "polyglot": polyglot,
        "include_package_json": include_package_json,
        "extension_counts": dict(sorted(extension_counts.items())),
        "sample_paths": created[:8],
    }


def main() -> int:
    args = parse_args()
    try:
        payload = generate_fixture(
            Path(args.output_dir),
            args.file_count,
            args.seed,
            args.include_package_json,
            args.polyglot,
        )
    except Exception as exc:
        payload = {"status": "error", "message": str(exc)}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1
    if args.format == "text":
        print(f"generated {payload['files_created']} files under {payload['output_dir']}")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
