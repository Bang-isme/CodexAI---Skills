#!/usr/bin/env python3
"""Evaluate live deploy probes and release hygiene from a local manifest.

This module does not fetch URLs. Callers pass HTTP status codes they already
collected. A page that returns 200 is still a failure when a required script,
stylesheet, or image returns 404 or 5xx. A 301 or 302 passes only when its
terminal status is healthy.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


DEFAULT_MAX_UPLOAD_BYTES = 50 * 1024 * 1024
HEALTHY_STATUSES = frozenset({200, 304})
REDIRECT_STATUSES = frozenset({301, 302})
AUTH_PRESENT_STATUSES = frozenset({400, 401, 403})
CHECKED_KINDS = frozenset({"script", "stylesheet", "image"})
POSITIVE_CODES = frozenset({"auth_gate_present", "private_asset_protected"})
ASK_USER_CODES = frozenset({"upload_exceeds_50mb"})
FINAL_STATUS_KEYS = (
    "final_status",
    "resolved_status",
    "resolved_to",
    "terminal_status",
    "followed_status",
    "location_status",
)
KIND_ALIASES = {
    "script": "script",
    "scripts": "script",
    "javascript": "script",
    "js": "script",
    "module": "script",
    "stylesheet": "stylesheet",
    "style": "stylesheet",
    "css": "stylesheet",
    "image": "image",
    "img": "image",
    "picture": "image",
    "icon": "image",
}
EXTENSION_KINDS = {
    ".js": "script",
    ".mjs": "script",
    ".cjs": "script",
    ".css": "stylesheet",
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".gif": "image",
    ".webp": "image",
    ".svg": "image",
    ".ico": "image",
    ".avif": "image",
    ".bmp": "image",
}


def force_utf8_stdio() -> None:
    """Keep reports printable on Windows consoles that use a legacy code page."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (ValueError, OSError):
                pass


def _status_code(value: object) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        text = value.strip()
        if text.isdigit() or (text.startswith("-") and text[1:].isdigit()):
            return int(text)
    return None


def _as_bool(value: object, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value != 0
    if isinstance(value, str):
        token = value.strip().lower()
        if token in {"1", "true", "yes"}:
            return True
        if token in {"0", "false", "no"}:
            return False
    return default


def _unique(codes: list[str]) -> list[str]:
    unique: list[str] = []
    for code in codes:
        if code and code not in unique:
            unique.append(code)
    return unique


def _pack(codes: list[str], **extra: Any) -> dict[str, Any]:
    unique = _unique(codes)
    hard = [code for code in unique if code not in POSITIVE_CODES and code not in ASK_USER_CODES]
    asks = [code for code in unique if code in ASK_USER_CODES]
    if hard:
        ok, status, primary = False, "fail", hard[0]
    elif asks:
        ok, status, primary = False, "ask_user", asks[0]
    else:
        ok, status, primary = True, "pass", ""
    payload: dict[str, Any] = {"ok": ok, "status": status, "code": primary, "codes": unique}
    payload.update(extra)
    return payload


def _label(record: dict[str, Any], index: int) -> str:
    for key in ("path", "url", "name", "id"):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return f"[{index}]"


def _kind_from_content_type(value: str) -> str:
    token = value.split(";", 1)[0].strip().lower()
    if token == "text/css":
        return "stylesheet"
    if token in {"text/javascript", "application/javascript", "application/ecmascript", "text/ecmascript"}:
        return "script"
    if token.startswith("image/"):
        return "image"
    return ""


def _normalize_kind(asset: dict[str, Any]) -> str:
    for key in ("kind", "type", "role", "asset_type"):
        value = asset.get(key)
        if isinstance(value, str) and value.strip():
            token = value.strip().lower()
            return KIND_ALIASES.get(token, token)
    content_type = asset.get("content_type", asset.get("contentType", ""))
    if isinstance(content_type, str) and content_type.strip():
        mapped = _kind_from_content_type(content_type)
        if mapped:
            return mapped
    for key in ("path", "url", "name"):
        value = asset.get(key)
        if not isinstance(value, str) or "." not in value:
            continue
        clean = value.split("?", 1)[0].split("#", 1)[0]
        mapped = EXTENSION_KINDS.get(Path(clean).suffix.lower())
        if mapped:
            return mapped
    return ""


def _is_required(asset: dict[str, Any], kind: str) -> bool:
    if "required" in asset:
        return _as_bool(asset.get("required"), kind in CHECKED_KINDS)
    return kind in CHECKED_KINDS


def _explicit_final(record: dict[str, Any]) -> int | None:
    for key in FINAL_STATUS_KEYS:
        if key in record and record[key] is not None:
            return _status_code(record[key])
    chain = record.get("chain", record.get("statuses"))
    if isinstance(chain, list) and chain:
        return _status_code(chain[-1])
    return None


def _observed_status(record: dict[str, Any]) -> int | None:
    for key in ("status", "code", "http_status"):
        if key in record and record[key] is not None:
            parsed = _status_code(record[key])
            if parsed is not None:
                return parsed
    chain = record.get("chain", record.get("statuses"))
    if isinstance(chain, list) and chain:
        return _status_code(chain[0])
    return None


def _terminal(record: dict[str, Any]) -> tuple[int | None, str]:
    """Return the status a client ultimately receives.

    The second value is ``missing`` when no status was recorded and
    ``unresolved`` when a 301/302 has no concrete target.
    """
    status = _observed_status(record)
    if status is None:
        return None, "missing"
    if status in REDIRECT_STATUSES:
        final = _explicit_final(record)
        if final is None or final in REDIRECT_STATUSES:
            return status, "unresolved"
        return final, ""
    return status, ""


def _asset_problem(kind: str, required: bool, asset: dict[str, Any]) -> str:
    if not required or kind not in CHECKED_KINDS:
        return ""
    terminal, state = _terminal(asset)
    if state == "missing":
        return "asset_invalid"
    if state == "unresolved":
        return "redirect_unresolved"
    if terminal in HEALTHY_STATUSES:
        return ""
    return "required_asset_unavailable"


def evaluate_page_and_assets(page_status: int, assets: list[dict]) -> dict[str, Any]:
    """Fail a 200 page when any required script, stylesheet, or image is broken.

    404 and 5xx are failures. A 301 or 302 whose terminal status is 200 or 304
    is healthy. Any other terminal status for a required asset fails too.
    """
    codes: list[str] = []
    failures: list[dict[str, Any]] = []
    parsed_page = _status_code(page_status)
    if parsed_page is None:
        codes.append("page_status_invalid")
    elif parsed_page != 200:
        codes.append("page_not_ok")
    rows = assets if isinstance(assets, list) else []
    if not isinstance(assets, list):
        codes.append("assets_invalid")
    for index, asset in enumerate(rows):
        if not isinstance(asset, dict):
            codes.append("asset_invalid")
            failures.append({"index": index, "code": "asset_invalid"})
            continue
        kind = _normalize_kind(asset)
        problem = _asset_problem(kind, _is_required(asset, kind), asset)
        if not problem:
            continue
        codes.append(problem)
        failures.append(
            {
                "index": index,
                "path": _label(asset, index),
                "kind": kind,
                "status": _observed_status(asset),
                "code": problem,
            }
        )
    return _pack(codes, page_status=parsed_page, failures=failures)


def evaluate_auth_and_private_probes(auth_probe_status: int | None, private_probes: list[dict]) -> dict[str, Any]:
    """Require an auth challenge, and refuse private files that answer 200.

    404 on the auth route is ``auth_gate_missing``. 400, 401, and 403 are
    ``auth_gate_present``. A private file or route whose terminal status is
    2xx is ``private_asset_exposed``. 401 and 403 on a private probe pass.
    ``auth_probe_status is None`` means the auth probe was not collected.
    """
    codes: list[str] = []
    failures: list[dict[str, Any]] = []
    if auth_probe_status is not None:
        parsed = _status_code(auth_probe_status)
        if parsed is None:
            codes.append("auth_gate_unexpected")
            failures.append({"scope": "auth", "code": "auth_gate_unexpected"})
        elif parsed == 404:
            codes.append("auth_gate_missing")
            failures.append({"scope": "auth", "status": parsed, "code": "auth_gate_missing"})
        elif parsed in AUTH_PRESENT_STATUSES:
            codes.append("auth_gate_present")
        elif 200 <= parsed <= 299:
            codes.append("auth_gate_open")
            failures.append({"scope": "auth", "status": parsed, "code": "auth_gate_open"})
        else:
            codes.append("auth_gate_unexpected")
            failures.append({"scope": "auth", "status": parsed, "code": "auth_gate_unexpected"})

    probes = private_probes if isinstance(private_probes, list) else []
    if not isinstance(private_probes, list):
        codes.append("private_probe_invalid")
        failures.append({"scope": "private", "code": "private_probe_invalid"})
    protected = False
    for index, probe in enumerate(probes):
        if not isinstance(probe, dict):
            codes.append("private_probe_invalid")
            failures.append({"index": index, "scope": "private", "code": "private_probe_invalid"})
            continue
        terminal, state = _terminal(probe)
        label = _label(probe, index)
        if state == "missing":
            codes.append("private_probe_invalid")
            failures.append({"index": index, "path": label, "code": "private_probe_invalid"})
            continue
        if state == "unresolved":
            codes.append("private_probe_unresolved")
            failures.append({"index": index, "path": label, "code": "private_probe_unresolved"})
            continue
        if terminal is not None and 200 <= terminal <= 299:
            codes.append("private_asset_exposed")
            failures.append(
                {"index": index, "path": label, "status": terminal, "code": "private_asset_exposed"}
            )
            continue
        protected = True
    private_problems = {"private_asset_exposed", "private_probe_invalid", "private_probe_unresolved"}
    if protected and not private_problems.intersection(codes):
        codes.append("private_asset_protected")
    return _pack(codes, auth_probe_status=auth_probe_status if auth_probe_status is None else _status_code(auth_probe_status), failures=failures)


def evaluate_release_hygiene(
    upload_bytes: int,
    is_fast_forward: bool,
    worktree_dirty: bool,
    archiving_captures: bool,
    max_upload_bytes: int = DEFAULT_MAX_UPLOAD_BYTES,
) -> dict[str, Any]:
    """Pass uploads at or under 50 MiB and refuse unsafe publish actions.

    A size above ``max_upload_bytes`` returns ``status="ask_user"``,
    ``ok=False``, and code ``upload_exceeds_50mb``. A non-fast-forward push is
    ``non_fast_forward_refused``. Archiving captures while the worktree is
    dirty is ``dirty_worktree_capture_archive_refused``. Hard refusals win
    over the size question when both are present.
    """
    codes: list[str] = []
    size = upload_bytes
    limit = max_upload_bytes
    if (
        isinstance(upload_bytes, bool)
        or isinstance(max_upload_bytes, bool)
        or not isinstance(upload_bytes, int)
        or not isinstance(max_upload_bytes, int)
    ):
        codes.append("upload_invalid")
        size = 0
        limit = DEFAULT_MAX_UPLOAD_BYTES
    elif upload_bytes < 0 or max_upload_bytes < 0:
        codes.append("upload_invalid")
    elif upload_bytes > max_upload_bytes:
        codes.append("upload_exceeds_50mb")
    fast = _as_bool(is_fast_forward, False)
    dirty = _as_bool(worktree_dirty, True)
    archiving = _as_bool(archiving_captures, True)
    if not fast:
        codes.append("non_fast_forward_refused")
    if archiving and dirty:
        codes.append("dirty_worktree_capture_archive_refused")
    refused = "non_fast_forward_refused" in codes or "dirty_worktree_capture_archive_refused" in codes
    return _pack(
        codes,
        upload_bytes=size,
        max_upload_bytes=limit,
        is_fast_forward=fast,
        worktree_dirty=dirty,
        archiving_captures=archiving,
        refused=refused,
    )


def _release_source(manifest: dict[str, Any]) -> dict[str, Any] | None:
    release = manifest.get("release")
    if isinstance(release, dict):
        return release
    keys = ("upload_bytes", "is_fast_forward", "worktree_dirty", "archiving_captures", "max_upload_bytes")
    if any(key in manifest for key in keys):
        return manifest
    return None


def _pick(source: dict[str, Any], manifest: dict[str, Any], key: str, default: Any) -> Any:
    if key in source:
        return source[key]
    if source is not manifest and key in manifest:
        return manifest[key]
    return default


def evaluate_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    """Run every probe section present in a manifest and combine the verdict."""
    if not isinstance(manifest, dict):
        return _pack(["manifest_invalid"], checks={})
    checks: dict[str, Any] = {}
    codes: list[str] = []
    saw = False
    if "page_status" in manifest or "assets" in manifest:
        saw = True
        page = manifest.get("page_status", 0)
        assets = manifest.get("assets", [])
        check = evaluate_page_and_assets(page, assets)
        checks["page_and_assets"] = check
        codes.extend(check["codes"])
    if "auth_probe_status" in manifest or "private_probes" in manifest:
        saw = True
        probes = manifest.get("private_probes", [])
        check = evaluate_auth_and_private_probes(manifest.get("auth_probe_status"), probes)
        checks["auth_and_private"] = check
        codes.extend(check["codes"])
    source = _release_source(manifest)
    if source is not None:
        saw = True
        check = evaluate_release_hygiene(
            _pick(source, manifest, "upload_bytes", 0),
            _pick(source, manifest, "is_fast_forward", False),
            _pick(source, manifest, "worktree_dirty", False),
            _pick(source, manifest, "archiving_captures", False),
            _pick(source, manifest, "max_upload_bytes", DEFAULT_MAX_UPLOAD_BYTES),
        )
        checks["release_hygiene"] = check
        codes.extend(check["codes"])
    if not saw:
        codes.append("manifest_empty")
    return _pack(codes, checks=checks)


def render_text(report: dict[str, Any]) -> str:
    lines = [
        f"status={report.get('status', '')} ok={report.get('ok', False)}",
        f"code={report.get('code', '')}",
        "codes=" + ",".join(str(code) for code in report.get("codes") or []),
    ]
    checks = report.get("checks")
    if isinstance(checks, dict):
        for name, check in checks.items():
            status = check.get("status", "") if isinstance(check, dict) else ""
            lines.append(f"- {name}: {status}")
    return "\n".join(lines)


def _load_manifest(project_root: Path, manifest: str) -> dict[str, Any]:
    if not manifest.strip():
        raise ValueError("Pass --manifest with probe results")
    if not project_root.is_dir():
        raise ValueError(f"project root is not a directory: {project_root}")
    manifest_path = Path(manifest).expanduser()
    if not manifest_path.is_absolute():
        manifest_path = project_root / manifest_path
    payload = json.loads(manifest_path.resolve().read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("manifest must be a JSON object")
    return payload


def main(argv: list[str] | None = None) -> int:
    force_utf8_stdio()
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate live page assets, auth and private probes, and release hygiene "
            "from a local JSON manifest. Does not fetch URLs."
        )
    )
    parser.add_argument("--project-root", default=".", help="Project root used to resolve a relative --manifest path")
    parser.add_argument("--manifest", default="", help="JSON manifest of page, asset, auth, private, and release probe results")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    args = parser.parse_args(argv)
    project_root = Path(args.project_root).expanduser().resolve()
    manifest_path = Path(args.manifest).expanduser() if args.manifest else Path()
    if args.manifest and not manifest_path.is_absolute():
        manifest_path = project_root / manifest_path
    try:
        report = evaluate_manifest(_load_manifest(project_root, args.manifest))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        code = "manifest_required" if not str(args.manifest).strip() else "manifest_unreadable"
        report = _pack([code], message=str(exc), checks={})
    report["project_root"] = str(project_root)
    if args.manifest:
        report["manifest"] = str(manifest_path.resolve()) if manifest_path else ""
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(render_text(report))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
