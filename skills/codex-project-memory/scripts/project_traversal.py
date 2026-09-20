#!/usr/bin/env python3
"""Shared deterministic project traversal for knowledge index and graph builders."""
from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable


HARD_CODED_SKIP_DIRS = {
    ".git",
    ".next",
    ".pytest_cache",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "target",
    "vendor",
    ".venv",
    "venv",
    ".codex",
    ".codexai",
    ".codexai-backups",
    ".idea",
    ".vscode",
    ".yarn",
}


def atomic_write_text(path: Path, text: str, encoding: str = "utf-8") -> None:
    """Write text via a same-directory temp file + os.replace so readers never see a partial artifact."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    try:
        tmp_path.write_text(text, encoding=encoding)
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass


def atomic_write_json(path: Path, payload: Any, indent: int = 2, trailing_newline: bool = True) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=indent)
    atomic_write_text(path, text + ("\n" if trailing_newline else ""))


def git_head(project_root: Path) -> str:
    """Return the current git HEAD sha or an empty string when git is unavailable or the root is not a repo."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""


def tree_fingerprint(files: Iterable[Any]) -> str:
    """Stable sha256 over sorted (rel_path, size_bytes) pairs; deterministic across runs and OSes."""
    rows: list[str] = []
    for entry in files:
        rel = getattr(entry, "rel_path", None)
        size = getattr(entry, "size_bytes", None)
        if rel is None and isinstance(entry, dict):
            rel = entry.get("rel_path") or entry.get("path")
            size = entry.get("size_bytes", entry.get("size"))
        if rel is None:
            continue
        rows.append(f"{rel}\0{int(size or 0)}")
    digest = hashlib.sha256()
    for row in sorted(rows):
        digest.update(row.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def source_snapshot(project_root: Path, files: Iterable[Any]) -> dict[str, Any]:
    """Provenance block stored on generated indexes so memory_status can detect staleness."""
    listed = list(files)
    return {
        "git_head": git_head(project_root),
        "tree_fingerprint": tree_fingerprint(listed),
        "fingerprint_inputs": "sorted(rel_path, size_bytes)",
        "files_counted": len(listed),
    }

BINARY_EXTENSIONS = {
    ".7z",
    ".a",
    ".bin",
    ".bmp",
    ".class",
    ".dll",
    ".dmg",
    ".doc",
    ".docx",
    ".ds_store",
    ".exe",
    ".gif",
    ".gz",
    ".ico",
    ".jar",
    ".jpeg",
    ".jpg",
    ".lockb",
    ".mov",
    ".mp3",
    ".mp4",
    ".o",
    ".otf",
    ".pdf",
    ".png",
    ".pyc",
    ".rar",
    ".so",
    ".sqlite",
    ".tar",
    ".ttf",
    ".wasm",
    ".webp",
    ".woff",
    ".woff2",
    ".zip",
}

SYMBOL_MARKERS = (
    "class ",
    "def ",
    "async def ",
    "function ",
    "export ",
    "const ",
    "let ",
    "var ",
    "interface ",
    "type ",
    "struct ",
    "enum ",
    "func ",
    "fn ",
    "import ",
    "from ",
    "require(",
    "router.",
    "app.",
)


@dataclass(frozen=True)
class TraversalWarning:
    type: str
    path: str
    reason: str
    severity: str = "warning"

    def to_dict(self) -> dict[str, str]:
        return {"type": self.type, "path": self.path, "reason": self.reason, "severity": self.severity}


@dataclass(frozen=True)
class ListedFile:
    path: Path
    rel_path: str
    size_bytes: int


@dataclass(frozen=True)
class TraversedFile:
    path: Path
    rel_path: str
    size_bytes: int
    bytes_read: int
    content: str
    lines: list[str]
    large_file: bool = False


@dataclass
class TraversalConfig:
    include: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)
    max_files: int = 1000
    max_file_bytes: int = 256 * 1024
    max_total_bytes: int = 20 * 1024 * 1024
    follow_symlinks: bool = False
    hard_skip_dirs: set[str] = field(default_factory=lambda: set(HARD_CODED_SKIP_DIRS))


@dataclass
class ListingResult:
    files: list[ListedFile]
    warnings: list[dict[str, str]]
    coverage: dict[str, object]
    skipped_reasons: dict[str, int]


@dataclass
class TraversalResult:
    files: list[TraversedFile]
    warnings: list[dict[str, str]]
    coverage: dict[str, object]


def parse_bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    raise ValueError(f"Expected boolean value, got: {value}")


def add_traversal_args(parser) -> None:  # type: ignore[no-untyped-def]
    parser.add_argument("--include", action="append", default=[], help="Include glob pattern; may be repeated")
    parser.add_argument("--exclude", action="append", default=[], help="Exclude glob pattern; may be repeated")
    parser.add_argument("--max-files", type=int, default=1000, help="Maximum files to scan")
    parser.add_argument("--max-file-bytes", type=int, default=256 * 1024, help="Maximum bytes sampled per file")
    parser.add_argument("--max-total-bytes", type=int, default=20 * 1024 * 1024, help="Maximum total bytes sampled")
    parser.add_argument("--follow-symlinks", default="false", help="Follow symlinks (true/false); default false")


def config_from_args(args) -> TraversalConfig:  # type: ignore[no-untyped-def]
    return TraversalConfig(
        include=list(getattr(args, "include", []) or []),
        exclude=list(getattr(args, "exclude", []) or []),
        max_files=int(getattr(args, "max_files", 1000)),
        max_file_bytes=int(getattr(args, "max_file_bytes", 256 * 1024)),
        max_total_bytes=int(getattr(args, "max_total_bytes", 20 * 1024 * 1024)),
        follow_symlinks=parse_bool(getattr(args, "follow_symlinks", False)),
    )


def normalize_rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def safe_rel(path: Path, root: Path) -> str:
    try:
        return normalize_rel(path, root)
    except (OSError, ValueError):
        try:
            return path.relative_to(root).as_posix()
        except ValueError:
            return path.as_posix()


def inside_root(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except (OSError, ValueError):
        return False


def structured_warning(warning_type: str, path: str, reason: str, severity: str = "warning") -> dict[str, str]:
    return TraversalWarning(warning_type, path, reason, severity).to_dict()


def read_ignore_file(path: Path) -> list[str]:
    if not path.exists() or not path.is_file():
        return []
    patterns: list[str] = []
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        patterns.append(stripped.replace("\\", "/"))
    return patterns


def load_ignore_patterns(project_root: Path) -> list[str]:
    patterns: list[str] = []
    for name in (".gitignore", ".codexignore"):
        patterns.extend(read_ignore_file(project_root / name))
    return patterns


def _match_single_pattern(rel_path: str, pattern: str) -> bool:
    normalized = pattern.strip()
    if not normalized:
        return False
    if normalized.startswith("!"):
        normalized = normalized[1:]
    normalized = normalized.strip("/")
    if not normalized:
        return False
    name = Path(rel_path).name
    if fnmatch.fnmatch(rel_path, normalized) or fnmatch.fnmatch(name, normalized):
        return True
    if "/" not in normalized and any(fnmatch.fnmatch(part, normalized) for part in Path(rel_path).parts):
        return True
    if rel_path.startswith(normalized.rstrip("/") + "/"):
        return True
    if fnmatch.fnmatch(rel_path, normalized.rstrip("/") + "/**"):
        return True
    return False


def ignored_by_patterns(rel_path: str, patterns: Iterable[str]) -> bool:
    ignored = False
    for raw in patterns:
        pattern = raw.strip()
        if not pattern:
            continue
        negated = pattern.startswith("!")
        if _match_single_pattern(rel_path, pattern):
            ignored = not negated
    return ignored


def included_by_patterns(rel_path: str, include: Iterable[str]) -> bool:
    patterns = list(include)
    return not patterns or any(_match_single_pattern(rel_path, pattern) for pattern in patterns)


def is_binary_path(path: Path) -> bool:
    return path.suffix.lower() in {ext.lower() for ext in BINARY_EXTENSIONS}


def has_null_byte(path: Path, sample_size: int = 8192) -> bool:
    with path.open("rb") as handle:
        return b"\0" in handle.read(sample_size)


def is_binary_file(path: Path) -> bool:
    if is_binary_path(path):
        return True
    return has_null_byte(path)


def sample_for_index(path: Path, max_bytes: int) -> tuple[str, int, bool]:
    size = path.stat().st_size
    if size <= max_bytes:
        raw = path.read_bytes()
        return raw.decode("utf-8", errors="replace"), len(raw), False

    head_budget = max(max_bytes // 2, 1)
    middle_budget = max(max_bytes // 3, 1)
    tail_budget = max(max_bytes - head_budget - middle_budget, 1)

    with path.open("rb") as handle:
        head = handle.read(head_budget)

        symbol_start = max(0, size // 2 - middle_budget // 2)
        handle.seek(symbol_start)
        middle_raw = handle.read(middle_budget * 2)

        handle.seek(max(0, size - tail_budget))
        tail = handle.read(tail_budget)

    middle_text = middle_raw.decode("utf-8", errors="replace")
    symbol_lines = [line for line in middle_text.splitlines() if any(marker in line for marker in SYMBOL_MARKERS)]
    if symbol_lines:
        middle = ("\n".join(symbol_lines[:80])).encode("utf-8", errors="replace")[:middle_budget]
    else:
        middle = middle_raw[:middle_budget]

    parts = [
        head.decode("utf-8", errors="replace"),
        "\n\n[... large file sampled: symbol window ...]\n\n",
        middle.decode("utf-8", errors="replace"),
        "\n\n[... large file sampled: tail metadata ...]\n\n",
        tail.decode("utf-8", errors="replace"),
    ]
    text = "".join(parts)
    return text, min(size, max_bytes), True


def list_project_files(
    project_root: Path,
    config: TraversalConfig | None = None,
    file_filter: Callable[[str, Path], bool] | None = None,
) -> ListingResult:
    """Discover files with shared ignore rules, then sort and cap. Does not read contents."""
    root = project_root.expanduser().resolve()
    cfg = config or TraversalConfig()
    ignore_patterns = load_ignore_patterns(root)
    warnings: list[dict[str, str]] = []
    skipped_reasons: dict[str, int] = {}
    candidates: list[ListedFile] = []
    candidate_files = 0

    def skip(reason: str, rel: str, warning_type: str = "skipped", severity: str = "info") -> None:
        skipped_reasons[reason] = skipped_reasons.get(reason, 0) + 1
        if warning_type != "ignored":
            warnings.append(structured_warning(warning_type, rel, reason, severity))

    for current_root, dirs, names in os.walk(root, topdown=True, followlinks=cfg.follow_symlinks):
        current_path = Path(current_root)
        dir_entries = sorted(dirs)
        kept_dirs: list[str] = []
        for dirname in dir_entries:
            dir_path = current_path / dirname
            rel = safe_rel(dir_path, root)
            if dirname in cfg.hard_skip_dirs:
                skip("hard-coded skip dir", rel, "ignored", "info")
                continue
            if ignored_by_patterns(rel, ignore_patterns) or ignored_by_patterns(rel + "/", ignore_patterns):
                skip("ignore pattern", rel, "ignored", "info")
                continue
            if dir_path.is_symlink():
                if not cfg.follow_symlinks:
                    skip("symlink traversal disabled", rel, "symlink_skipped", "warning")
                    continue
                if not inside_root(dir_path, root):
                    skip("symlink escapes project root", rel, "symlink_skipped", "warning")
                    continue
            kept_dirs.append(dirname)
        dirs[:] = kept_dirs

        for name in sorted(names):
            path = current_path / name
            rel = safe_rel(path, root)
            candidate_files += 1
            if path.is_symlink():
                if not cfg.follow_symlinks:
                    skip("symlink traversal disabled", rel, "symlink_skipped", "warning")
                    continue
                if not inside_root(path, root):
                    skip("symlink escapes project root", rel, "symlink_skipped", "warning")
                    continue
            if ignored_by_patterns(rel, ignore_patterns):
                skip("ignore pattern", rel, "ignored", "info")
                continue
            if not included_by_patterns(rel, cfg.include):
                skip("include pattern", rel, "ignored", "info")
                continue
            if ignored_by_patterns(rel, cfg.exclude):
                skip("exclude pattern", rel, "ignored", "info")
                continue
            if file_filter and not file_filter(rel, path):
                continue
            try:
                if not path.is_file():
                    continue
                size = path.stat().st_size
                if is_binary_file(path):
                    skip("binary file", rel, "binary_skipped", "warning")
                    continue
            except OSError as exc:
                skip(f"read error: {exc}", rel, "read_error", "warning")
                continue
            candidates.append(ListedFile(path=path.resolve(), rel_path=rel, size_bytes=size))

    candidates.sort(key=lambda item: item.rel_path)
    kept = candidates[: cfg.max_files]
    for extra in candidates[cfg.max_files :]:
        skip("max-files limit", extra.rel_path, "limit_exceeded", "warning")

    warnings.sort(key=lambda item: (item["severity"], item["type"], item["path"], item["reason"]))
    coverage = {
        "files_scanned": len(kept),
        "files_skipped": sum(skipped_reasons.values()),
        "candidate_files": candidate_files,
        "bytes_scanned": 0,
        "skipped_reasons": dict(sorted(skipped_reasons.items())),
        "warnings": len(warnings),
        "limits": {
            "max_files": cfg.max_files,
            "max_file_bytes": cfg.max_file_bytes,
            "max_total_bytes": cfg.max_total_bytes,
            "follow_symlinks": cfg.follow_symlinks,
        },
    }
    return ListingResult(files=kept, warnings=warnings, coverage=coverage, skipped_reasons=skipped_reasons)


def traverse_project(
    project_root: Path,
    config: TraversalConfig | None = None,
    file_filter: Callable[[str, Path], bool] | None = None,
) -> TraversalResult:
    cfg = config or TraversalConfig()
    listing = list_project_files(project_root, cfg, file_filter=file_filter)
    warnings = list(listing.warnings)
    skipped_reasons = dict(listing.skipped_reasons)
    files: list[TraversedFile] = []
    total_bytes = 0

    def skip(reason: str, rel: str, warning_type: str = "skipped", severity: str = "info") -> None:
        skipped_reasons[reason] = skipped_reasons.get(reason, 0) + 1
        if warning_type != "ignored":
            warnings.append(structured_warning(warning_type, rel, reason, severity))

    for entry in listing.files:
        if total_bytes >= cfg.max_total_bytes:
            skip("max-total-bytes limit", entry.rel_path, "limit_exceeded", "warning")
            continue
        remaining = max(cfg.max_total_bytes - total_bytes, 0)
        per_file_budget = max(min(cfg.max_file_bytes, remaining), 0)
        if per_file_budget <= 0:
            skip("max-total-bytes limit", entry.rel_path, "limit_exceeded", "warning")
            continue
        try:
            content, bytes_read, large = sample_for_index(entry.path, per_file_budget)
        except OSError as exc:
            skip(f"read error: {exc}", entry.rel_path, "read_error", "warning")
            continue
        total_bytes += bytes_read
        if large:
            warnings.append(
                structured_warning(
                    "large_file_sampled",
                    entry.rel_path,
                    f"sampled {bytes_read} of {entry.size_bytes} bytes",
                    "warning",
                )
            )
        files.append(
            TraversedFile(
                path=entry.path,
                rel_path=entry.rel_path,
                size_bytes=entry.size_bytes,
                bytes_read=bytes_read,
                content=content,
                lines=content.splitlines(),
                large_file=large,
            )
        )

    files.sort(key=lambda item: item.rel_path)
    warnings.sort(key=lambda item: (item["severity"], item["type"], item["path"], item["reason"]))
    coverage = {
        "files_scanned": len(files),
        "files_skipped": sum(skipped_reasons.values()),
        "candidate_files": listing.coverage.get("candidate_files", 0),
        "bytes_scanned": total_bytes,
        "skipped_reasons": dict(sorted(skipped_reasons.items())),
        "warnings": len(warnings),
        "limits": {
            "max_files": cfg.max_files,
            "max_file_bytes": cfg.max_file_bytes,
            "max_total_bytes": cfg.max_total_bytes,
            "follow_symlinks": cfg.follow_symlinks,
        },
    }
    return TraversalResult(files=files, warnings=warnings, coverage=coverage)
