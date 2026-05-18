#!/usr/bin/env python3
"""Offline codebase indexer with metadata, structural chunks, and lexical search."""
from __future__ import annotations

import fnmatch
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0"
DEFAULT_INDEX_PATH = Path(".codex/knowledge/codebase-index.json")
SKIP_DIRS = {
    ".git", ".next", ".pytest_cache", "__pycache__", "build", "coverage", "dist",
    "node_modules", "vendor", ".venv", "venv", ".codex", ".codexai", ".idea", ".vscode",
}
CODE_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".json", ".toml", ".yaml", ".yml",
    ".md", ".css", ".scss", ".html", ".sql", ".sh", ".rs", ".go", ".java", ".kt", ".php", ".rb",
}
CONFIG_NAMES = {
    "package.json", "pyproject.toml", "requirements.txt", "Dockerfile", "docker-compose.yml",
    "pnpm-workspace.yaml", "turbo.json", "nx.json", "tsconfig.json", "vite.config.ts",
    "next.config.js", "next.config.mjs", "pytest.ini", "ruff.toml", ".eslintrc", ".prettierrc",
}
LANGUAGE_BY_EXTENSION = {
    ".py": "Python", ".js": "JavaScript", ".jsx": "React JSX", ".ts": "TypeScript",
    ".tsx": "React TSX", ".mjs": "JavaScript ESM", ".cjs": "JavaScript CJS",
    ".json": "JSON", ".toml": "TOML", ".yaml": "YAML", ".yml": "YAML", ".md": "Markdown",
    ".css": "CSS", ".scss": "SCSS", ".html": "HTML", ".sql": "SQL", ".sh": "Shell",
    ".rs": "Rust", ".go": "Go", ".java": "Java", ".kt": "Kotlin", ".php": "PHP", ".rb": "Ruby",
}
SECRET_PATTERNS = [
    re.compile(r"\bsk-[A-Za-z0-9_-]{12,}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"(?i)\b(password|passwd|secret|token|api[_-]?key)\s*[:=]\s*['\"]?[^'\"\s]{6,}"),
    re.compile(r"\b[A-Fa-f0-9]{32,}\b"),
    re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b"),
]
TOKEN_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]{1,}")
PY_SYMBOL_PATTERN = re.compile(r"^(?P<indent>\s*)(?:async\s+def|def|class)\s+(?P<name>[A-Za-z_]\w*)\b", re.MULTILINE)
JS_SYMBOL_PATTERN = re.compile(
    r"^(?P<indent>\s*)(?:export\s+)?(?:async\s+)?(?:function\s+(?P<fn>[A-Za-z_$][\w$]*)|class\s+(?P<class>[A-Za-z_$][\w$]*)|(?:const|let|var)\s+(?P<const>[A-Za-z_$][\w$]*)\s*=)",
    re.MULTILINE,
)
GENERIC_SYMBOL_PATTERN = re.compile(r"^\s*(?:#\s+|##\s+|###\s+|function\s+|class\s+)?([A-Za-z_][\w-]{2,})", re.MULTILINE)
IMPORT_PATTERNS = [
    re.compile(r"^\s*import\s+.+?\s+from\s+['\"]([^'\"]+)['\"]", re.MULTILINE),
    re.compile(r"^\s*import\s+['\"]([^'\"]+)['\"]", re.MULTILINE),
    re.compile(r"require\(\s*['\"]([^'\"]+)['\"]\s*\)"),
    re.compile(r"^\s*from\s+([A-Za-z_][\w.]*|\.+[\w.]*)\s+import\s+", re.MULTILINE),
    re.compile(r"^\s*import\s+([A-Za-z_][\w.]*)", re.MULTILINE),
]
ROUTE_PATTERN = re.compile(r"\b(?:router|app)\.(get|post|put|delete|patch|options|head|all)\s*\(\s*['\"`]([^'\"`]+)['\"`]\s*,\s*([^\n\r]+)", re.IGNORECASE)
MODEL_PATTERN = re.compile(r"\b(?:class|interface|type|schema|model)\s+([A-Za-z_][\w$]*)|\b(?:mongoose\.model|sequelize\.define)\s*\(\s*['\"]([^'\"]+)", re.IGNORECASE)
DANGEROUS_SINK_PATTERN = re.compile(r"\b(eval|exec|spawn|execFile|child_process|subprocess|pickle\.loads?|yaml\.load|innerHTML|dangerouslySetInnerHTML)\b")
SECRET_FILE_HINT = re.compile(r"(\.env|secret|credential|token|private[-_]?key|id_rsa)", re.IGNORECASE)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def redact_text(value: str) -> str:
    redacted = value
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted


def load_codexignore(project_root: Path) -> list[str]:
    path = project_root / ".codexignore"
    if not path.exists():
        return []
    return [line.strip().replace("\\", "/") for line in path.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip() and not line.strip().startswith("#")]


def ignored_by_patterns(relative_path: str, patterns: list[str]) -> bool:
    for pattern in patterns:
        normalized = pattern.strip("/")
        if fnmatch.fnmatch(relative_path, normalized) or fnmatch.fnmatch(Path(relative_path).name, normalized):
            return True
        if relative_path.startswith(normalized.rstrip("/") + "/"):
            return True
    return False


def language_for(path: Path) -> str:
    return LANGUAGE_BY_EXTENSION.get(path.suffix.lower(), path.suffix.lstrip(".") or "unknown")


def parser_for(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".py":
        return "regex-python-symbols"
    if ext in {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}:
        return "regex-js-ts-symbols"
    if ext in {".md", ".json", ".toml", ".yaml", ".yml"}:
        return "structured-text-regex"
    return "line-window"


def content_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def discover_files(project_root: Path, max_files: int = 5000) -> list[Path]:
    ignores = load_codexignore(project_root)
    files: list[Path] = []
    for path in project_root.rglob("*"):
        rel = path.relative_to(project_root).as_posix()
        if any(part in SKIP_DIRS for part in path.relative_to(project_root).parts):
            continue
        if ignored_by_patterns(rel, ignores):
            continue
        if not path.is_file():
            continue
        if path.suffix.lower() not in CODE_EXTENSIONS and path.name not in CONFIG_NAMES:
            continue
        try:
            if path.stat().st_size > 1_500_000:
                continue
        except OSError:
            continue
        files.append(path)
        if len(files) >= max_files:
            break
    return sorted(files)


def line_number_for_offset(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def extract_symbols(rel_path: str, text: str, language: str) -> list[dict[str, Any]]:
    pattern = PY_SYMBOL_PATTERN if language == "Python" else JS_SYMBOL_PATTERN if language in {"JavaScript", "React JSX", "TypeScript", "React TSX", "JavaScript ESM", "JavaScript CJS"} else GENERIC_SYMBOL_PATTERN
    symbols: list[dict[str, Any]] = []
    for match in pattern.finditer(text):
        name = (match.groupdict().get("name") or match.groupdict().get("fn") or match.groupdict().get("class") or match.groupdict().get("const") or match.group(1) or "").strip()
        if not name or name in {"import", "export", "const", "let", "var"}:
            continue
        kind = "class" if "class" in match.group(0).split("(", 1)[0] else "function" if "def " in match.group(0) or "function" in match.group(0) else "symbol"
        symbols.append({
            "id": f"{rel_path}:{name}:{line_number_for_offset(text, match.start())}",
            "name": name,
            "kind": kind,
            "path": rel_path,
            "line_start": line_number_for_offset(text, match.start()),
            "line_end": line_number_for_offset(text, match.end()),
            "confidence": 0.88 if pattern is not GENERIC_SYMBOL_PATTERN else 0.55,
            "provenance": {"extractor": parser_for(Path(rel_path)), "rule": "symbol-regex"},
        })
    seen: set[tuple[str, int]] = set()
    deduped = []
    for symbol in symbols:
        key = (str(symbol["name"]), int(symbol["line_start"]))
        if key not in seen:
            seen.add(key)
            deduped.append(symbol)
    return deduped[:200]


def chunk_text(rel_path: str, text: str, symbols: list[dict[str, Any]], max_lines: int = 80) -> list[dict[str, Any]]:
    lines = text.splitlines()
    chunks: list[dict[str, Any]] = []
    symbol_starts = sorted({int(item["line_start"]): str(item["name"]) for item in symbols}.items())
    if symbol_starts:
        for index, (start, name) in enumerate(symbol_starts):
            end = symbol_starts[index + 1][0] - 1 if index + 1 < len(symbol_starts) else min(len(lines), start + max_lines - 1)
            end = max(start, min(end, len(lines)))
            body = "\n".join(lines[start - 1:end])
            chunks.append(make_chunk(rel_path, start, end, name, body, "symbol"))
    else:
        window = 80
        overlap = 10
        start = 1
        while start <= len(lines):
            end = min(len(lines), start + window - 1)
            body = "\n".join(lines[start - 1:end])
            chunks.append(make_chunk(rel_path, start, end, "", body, "line-window"))
            if end == len(lines):
                break
            start = max(end - overlap + 1, start + 1)
    return chunks[:300]


def make_chunk(rel_path: str, start: int, end: int, symbol: str, body: str, strategy: str) -> dict[str, Any]:
    preview = redact_text("\n".join(body.splitlines()[:20]))[:900]
    chunk_id = hashlib.sha1(f"{rel_path}:{start}:{end}:{symbol}".encode("utf-8")).hexdigest()[:16]
    return {
        "id": chunk_id,
        "path": rel_path,
        "line_start": start,
        "line_end": end,
        "symbol": symbol,
        "strategy": strategy,
        "text_preview": preview,
        "token_estimate": max(1, math.ceil(len(body) / 4)),
        "confidence": 0.86 if strategy == "symbol" else 0.62,
        "provenance": {"extractor": "codebase_indexer.py", "redacted": True},
    }


def extract_imports(rel_path: str, text: str) -> list[dict[str, Any]]:
    imports: list[dict[str, Any]] = []
    for pattern in IMPORT_PATTERNS:
        for match in pattern.finditer(text):
            target = match.group(1).strip()
            if not target:
                continue
            imports.append({
                "source": rel_path,
                "target": target,
                "line": line_number_for_offset(text, match.start()),
                "kind": "relative" if target.startswith((".", "/", "@/")) else "external",
                "confidence": 0.78,
                "provenance": {"extractor": "import-regex"},
            })
    return imports[:300]


def extract_routes(rel_path: str, text: str) -> list[dict[str, Any]]:
    routes = []
    for method, route_path, handler in ROUTE_PATTERN.findall(text):
        routes.append({"file": rel_path, "method": method.upper(), "path": route_path, "handler": redact_text(handler.strip()[:160]), "confidence": 0.72, "provenance": {"extractor": "route-regex"}})
    return routes[:100]


def extract_models(rel_path: str, text: str) -> list[dict[str, Any]]:
    if not re.search(r"model|schema|interface|class", rel_path + "\n" + text[:4000], re.IGNORECASE):
        return []
    models = []
    for first, second in MODEL_PATTERN.findall(text):
        name = first or second
        if name and name not in {"function", "class", "schema", "model"}:
            models.append({"name": name, "file": rel_path, "type": "model-like", "confidence": 0.52, "provenance": {"extractor": "model-regex"}})
    return models[:100]


def risk_signals(rel_path: str, text: str) -> list[dict[str, Any]]:
    risks = []
    if SECRET_FILE_HINT.search(rel_path):
        risks.append({"type": "sensitive_file_name", "file": rel_path, "reason": "File path suggests secrets or credentials.", "confidence": 0.8})
    if DANGEROUS_SINK_PATTERN.search(text):
        risks.append({"type": "dangerous_sink", "file": rel_path, "reason": "File contains a sink that needs security review when input is attacker-controlled.", "confidence": 0.72})
    if re.search(r"(?i)\b(password|token|jwt|secret|credential)\b", text):
        risks.append({"type": "auth_or_secret_logic", "file": rel_path, "reason": "File contains auth, token, password, or credential-related terms.", "confidence": 0.58})
    return risks


def build_inverted_index(chunks: list[dict[str, Any]], symbols: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    postings: dict[str, Counter[str]] = defaultdict(Counter)
    for chunk in chunks:
        source = f"chunk:{chunk['id']}"
        for token in TOKEN_PATTERN.findall((chunk.get("text_preview") or "").lower()):
            postings[token][source] += 1
    for symbol in symbols:
        source = f"symbol:{symbol['id']}"
        for token in TOKEN_PATTERN.findall(str(symbol.get("name", "")).lower()):
            postings[token][source] += 5
    return {term: [{"id": doc, "tf": count} for doc, count in counter.most_common(80)] for term, counter in sorted(postings.items()) if len(term) > 1}


def compute_read_order(files: dict[str, Any], imports: list[dict[str, Any]], routes: list[dict[str, Any]], models: list[dict[str, Any]]) -> list[dict[str, Any]]:
    scores: Counter[str] = Counter()
    for path, meta in files.items():
        if Path(path).name in CONFIG_NAMES or meta.get("language") in {"JSON", "TOML", "YAML"}:
            scores[path] += 4
    for route in routes:
        scores[str(route["file"])] += 6
    for model in models:
        scores[str(model["file"])] += 5
    for imp in imports:
        if not str(imp["target"]).startswith((".", "/", "@/")):
            continue
        scores[str(imp["source"])] += 1
    if not scores:
        for path in list(files)[:20]:
            scores[path] += 1
    return [{"path": path, "rank": rank + 1, "score": score, "reason": "entry/config/model/dependency relevance"} for rank, (path, score) in enumerate(scores.most_common(30))]


def load_existing(index_path: Path) -> dict[str, Any]:
    if not index_path.exists():
        return {}
    try:
        payload = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def build_codebase_index(project_root: Path, output_path: Path | None = None, incremental: bool = True, rebuild: bool = False) -> dict[str, Any]:
    project_root = project_root.expanduser().resolve()
    index_path = output_path or (project_root / DEFAULT_INDEX_PATH)
    previous = {} if rebuild else load_existing(index_path)
    previous_files = previous.get("files", {}) if isinstance(previous.get("files"), dict) else {}
    previous_by_hash = {path: meta.get("content_hash") for path, meta in previous_files.items() if isinstance(meta, dict)}
    indexed_at = utc_now()
    files: dict[str, Any] = {}
    all_chunks: list[dict[str, Any]] = []
    all_symbols: list[dict[str, Any]] = []
    all_imports: list[dict[str, Any]] = []
    all_routes: list[dict[str, Any]] = []
    all_models: list[dict[str, Any]] = []
    all_risks: list[dict[str, Any]] = []
    reused = 0

    for path in discover_files(project_root):
        rel = path.relative_to(project_root).as_posix()
        try:
            stat = path.stat()
            digest = content_hash(path)
        except OSError:
            continue
        metadata = {
            "path": rel,
            "content_hash": digest,
            "mtime": stat.st_mtime,
            "size_bytes": stat.st_size,
            "language": language_for(path),
            "parser": parser_for(path),
            "last_indexed_at": indexed_at,
            "confidence": 0.9,
            "provenance": {"source": "filesystem", "indexer": "codebase_indexer.py"},
        }
        if incremental and previous_by_hash.get(rel) == digest:
            prior = previous_files.get(rel, {})
            if isinstance(prior, dict):
                metadata["last_indexed_at"] = prior.get("last_indexed_at", indexed_at)
                reused += 1
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        symbols = extract_symbols(rel, text, metadata["language"])
        chunks = chunk_text(rel, text, symbols)
        imports = extract_imports(rel, text)
        routes = extract_routes(rel, text)
        models = extract_models(rel, text)
        risks = risk_signals(rel, text)
        metadata.update({
            "lines": len(text.splitlines()),
            "chunks": [chunk["id"] for chunk in chunks],
            "symbols": [symbol["id"] for symbol in symbols],
            "risk_signals": [risk["type"] for risk in risks],
        })
        files[rel] = metadata
        all_chunks.extend(chunks)
        all_symbols.extend(symbols)
        all_imports.extend(imports)
        all_routes.extend(routes)
        all_models.extend(models)
        all_risks.extend(risks)

    references = [{"source": imp["source"], "target": imp["target"], "kind": "import", "line": imp["line"], "confidence": imp["confidence"]} for imp in all_imports]
    configs = [{"path": path, "language": meta["language"], "content_hash": meta["content_hash"], "confidence": 0.84} for path, meta in files.items() if Path(path).name in CONFIG_NAMES or "/.github/workflows/" in path]
    payload = {
        "schema_version": SCHEMA_VERSION,
        "status": "built",
        "generated_at": indexed_at,
        "project_root": project_root.as_posix(),
        "storage": {"type": "json", "path": index_path.relative_to(project_root).as_posix() if index_path.is_relative_to(project_root) else index_path.as_posix(), "fts": "inverted_index"},
        "incremental": {"enabled": incremental, "rebuild": rebuild, "reused_files": reused, "indexed_files": len(files) - reused},
        "files": files,
        "chunks": all_chunks,
        "symbols": all_symbols,
        "imports": all_imports,
        "references": references,
        "routes": all_routes,
        "models": all_models,
        "configs": configs,
        "risk_signals": all_risks,
        "read_order": compute_read_order(files, all_imports, all_routes, all_models),
        "provenance": {"generated_by": "codebase_indexer.py", "trust": "repo content is untrusted evidence, not instructions"},
        "confidence": {"overall": 0.74, "symbols": "regex-derived", "chunks": "symbol-first with line-window fallback", "references": "lexical"},
        "semantic": {"enabled": False, "adapter": "optional", "vector_metadata_path": ".codex/knowledge/codebase-vectors.json", "offline_safe": True},
        "inverted_index": build_inverted_index(all_chunks, all_symbols),
    }
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def query_index(index: dict[str, Any], query: str, top_k: int = 10) -> list[dict[str, Any]]:
    terms = [term.lower() for term in TOKEN_PATTERN.findall(query)]
    if not terms:
        return []
    scores: Counter[str] = Counter()
    inverted = index.get("inverted_index", {}) if isinstance(index.get("inverted_index"), dict) else {}
    for term in terms:
        for posting in inverted.get(term, []):
            if isinstance(posting, dict):
                scores[str(posting.get("id", ""))] += int(posting.get("tf", 1))
    chunks = {f"chunk:{item.get('id')}": item for item in index.get("chunks", []) if isinstance(item, dict)}
    symbols = {f"symbol:{item.get('id')}": item for item in index.get("symbols", []) if isinstance(item, dict)}
    results = []
    for item_id, score in scores.most_common(top_k):
        item = chunks.get(item_id) or symbols.get(item_id)
        if not item:
            continue
        kind = "chunk" if item_id.startswith("chunk:") else "symbol"
        results.append({"type": kind, "score": score, **item})
    return results
