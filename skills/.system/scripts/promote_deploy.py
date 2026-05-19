#!/usr/bin/env python3
"""Promote release ZIP to optional targets (S3, SSH) with post-extract smoke validation."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent


def run_json_validator(script: str, args: list[str]) -> tuple[bool, dict[str, Any]]:
    result = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / script), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
        check=False,
    )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        payload = {"status": "fail", "stderr": result.stderr[-2000:]}
    ok = result.returncode == 0 and payload.get("status") in {"pass", "warn"}
    return ok, payload


def smoke_extracted_root(extract_dir: Path) -> list[str]:
    failures: list[str] = []
    plugin_root = extract_dir
    if (extract_dir / "skills").is_dir() and (extract_dir / ".codex-plugin").is_dir():
        plugin_root = extract_dir
    elif list(extract_dir.iterdir()) == 1 and (extract_dir / next(iter(extract_dir.iterdir())) / ".codex-plugin").exists():
        plugin_root = extract_dir / next(iter(extract_dir.iterdir()))
    ok, payload = run_json_validator(
        "validate_codex_plugin.py",
        ["--plugin-root", str(plugin_root), "--strict", "--format", "json"],
    )
    if not ok:
        failures.append(f"validate_codex_plugin: {payload.get('status')}")
    ok, payload = run_json_validator(
        "validate_claude_plugin.py",
        ["--plugin-root", str(plugin_root), "--format", "json"],
    )
    if not ok:
        failures.append(f"validate_claude_plugin: {payload.get('status')}")
    return failures


def plan_s3(zip_path: Path, bucket: str, prefix: str) -> list[str]:
    key = f"{prefix.rstrip('/')}/{zip_path.name}" if prefix else zip_path.name
    return [f"aws s3 cp {zip_path} s3://{bucket}/{key}"]


def plan_ssh(zip_path: Path, host: str, user: str, remote_path: str) -> list[str]:
    dest = f"{user}@{host}:{remote_path.rstrip('/')}/{zip_path.name}"
    return [f"scp {zip_path} {dest}", f"ssh {user}@{host} unzip -o {remote_path.rstrip('/')}/{zip_path.name} -d {remote_path.rstrip('/')}/current"]


def run_commands(commands: list[str], dry_run: bool) -> None:
    for cmd in commands:
        if dry_run:
            print(cmd)
            continue
        subprocess.run(cmd, shell=True, check=True, timeout=600)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Promote release ZIP to S3 or SSH with smoke validation.")
    parser.add_argument("--zip", required=True, help="Path to release ZIP")
    parser.add_argument("--target", choices=("none", "s3", "ssh"), default="none")
    parser.add_argument("--environment", choices=("staging", "production"), default="staging")
    parser.add_argument("--dry-run", action="store_true", help="Print commands only; still run smoke unless --skip-smoke")
    parser.add_argument("--skip-smoke", action="store_true")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    zip_path = Path(args.zip).expanduser().resolve()
    if not zip_path.is_file():
        payload = {"status": "fail", "message": f"ZIP not found: {zip_path}"}
        print(json.dumps(payload, indent=2))
        return 1

    failures: list[str] = []
    smoke_ok = True
    if not args.skip_smoke:
        with tempfile.TemporaryDirectory(prefix="promote-smoke-") as tmp:
            extract_dir = Path(tmp) / "extract"
            extract_dir.mkdir()
            with zipfile.ZipFile(zip_path) as archive:
                archive.extractall(extract_dir)
            smoke_failures = smoke_extracted_root(extract_dir)
            if smoke_failures:
                smoke_ok = False
                failures.extend(smoke_failures)

    commands: list[str] = []
    if args.target == "s3":
        env_key = "S3_BUCKET_PRODUCTION" if args.environment == "production" else "S3_BUCKET_STAGING"
        bucket = os.environ.get(env_key, os.environ.get("S3_BUCKET", ""))
        prefix = os.environ.get("S3_PREFIX", "codexai-skill-pack")
        if not bucket:
            failures.append(f"missing env {env_key} or S3_BUCKET")
        else:
            commands = plan_s3(zip_path, bucket, prefix)
    elif args.target == "ssh":
        host_key = "SSH_HOST_PRODUCTION" if args.environment == "production" else "SSH_HOST_STAGING"
        host = os.environ.get(host_key, os.environ.get("SSH_HOST", ""))
        user = os.environ.get("SSH_USER", "deploy")
        remote_path = os.environ.get("SSH_DEPLOY_PATH", "/opt/codexai-skill-pack")
        if not host:
            failures.append(f"missing env {host_key} or SSH_HOST")
        else:
            commands = plan_ssh(zip_path, host, user, remote_path)

    if commands and not failures:
        try:
            run_commands(commands, args.dry_run)
        except subprocess.CalledProcessError as exc:
            failures.append(f"deploy command failed: {exc}")

    report = {
        "status": "pass" if smoke_ok and not failures else "fail",
        "target": args.target,
        "environment": args.environment,
        "zip": str(zip_path),
        "dry_run": args.dry_run,
        "commands": commands,
        "failures": failures,
    }
    if args.format == "text":
        print(json.dumps(report, indent=2))
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
