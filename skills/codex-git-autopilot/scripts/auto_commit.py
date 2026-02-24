#!/usr/bin/env python3
"""
Auto-commit with CI/CD gate, conventional commit message, GPG signing, and auto-push.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

COMMIT_TYPES = {
    "feat": ["models", "controllers", "services", "routes", "components", "pages"],
    "fix": ["fix", "bug", "patch", "hotfix"],
    "docs": ["docs", "README", "CHANGELOG", "*.md"],
    "style": ["*.css", "*.scss", "*.less", "*.styl"],
    "refactor": ["refactor", "cleanup", "restructure"],
    "test": ["tests", "__tests__", "*.test.*", "*.spec.*"],
    "chore": ["scripts", "config", ".codex", "package.json", ".eslintrc"],
    "ci": [".github", "Dockerfile", "docker-compose", ".gitlab-ci"],
    "perf": ["perf", "optimize", "cache", "workers"],
}

SKIP_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".next",
    "dist",
    "build",
    ".codex",
    ".vscode",
    ".idea",
}

_GPG_PATH: str = ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Auto-commit with CI/CD gate, GPG signing, and conventional commits.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            """\
            Examples:
              # Auto-commit task-related files (interactive)
              python auto_commit.py --project-root ./ --files src/models/User.js src/routes/user.routes.js
              # Auto-commit with explicit message
              python auto_commit.py --project-root ./ --files src/models/User.js --message "feat(user): add email validation"
              # Dry-run (preview only)
              python auto_commit.py --project-root ./ --files src/models/User.js --dry-run
              # Skip tests for faster commit
              python auto_commit.py --project-root ./ --files src/models/User.js --skip-tests
        """
        ),
    )
    parser.add_argument("--project-root", default="", help="Project root directory")
    parser.add_argument("--files", nargs="+", default=[], help="Specific files to commit (task-scoped)")
    parser.add_argument("--message", "-m", default="", help="Custom commit message (auto-generate if empty)")
    parser.add_argument("--type", choices=list(COMMIT_TYPES.keys()), help="Commit type override")
    parser.add_argument("--scope", default="", help="Commit scope override")
    parser.add_argument("--skip-tests", action="store_true", help="Skip test runner in pre-commit gate")
    parser.add_argument("--dry-run", action="store_true", help="Preview commit without executing")
    parser.add_argument("--no-push", action="store_true", help="Commit only, do not push")
    parser.add_argument("--setup-gpg", action="store_true", help="Interactive GPG setup wizard")
    return parser.parse_args()


def emit(payload: Dict[str, object]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def run_git(project_root: Path, args: List[str], timeout: int = 60) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=project_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(
            args=["git", *args],
            returncode=1,
            stdout="",
            stderr="git operation timed out",
        )


def git_ready(project_root: Path) -> bool:
    result = run_git(project_root, ["rev-parse", "--is-inside-work-tree"])
    return result.returncode == 0 and result.stdout.strip().lower() == "true"


def get_git_config(key: str) -> str:
    try:
        result = subprocess.run(
            ["git", "config", "--global", key],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=10,
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except (subprocess.TimeoutExpired, OSError):
        return ""


def get_current_branch(project_root: Path) -> str:
    result = run_git(project_root, ["branch", "--show-current"])
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def find_gpg_executable() -> str:
    """Find gpg executable, checking PATH and known install locations."""
    try:
        result = subprocess.run(
            ["gpg", "--version"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            check=False,
        )
        if result.returncode == 0:
            return "gpg"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    except OSError:
        pass

    if sys.platform == "win32":
        candidates = [
            Path(r"C:\Program Files\GnuPG\bin\gpg.exe"),
            Path(r"C:\Program Files (x86)\GnuPG\bin\gpg.exe"),
            Path(r"C:\ProgramData\chocolatey\bin\gpg.exe"),
            Path(r"C:\Program Files\Git\usr\bin\gpg.exe"),
        ]
        for candidate in candidates:
            if not candidate.exists():
                continue
            try:
                result = subprocess.run(
                    [str(candidate), "--version"],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=10,
                    check=False,
                )
                if result.returncode == 0:
                    return str(candidate)
            except (subprocess.TimeoutExpired, OSError):
                continue

    return ""


def get_gpg_cmd() -> str:
    """Get resolved GPG command path. Cached after first call."""
    global _GPG_PATH
    if not _GPG_PATH:
        _GPG_PATH = find_gpg_executable()
    return _GPG_PATH


def check_gpg_available() -> bool:
    return bool(get_gpg_cmd())


def get_gpg_signing_key() -> str:
    return get_git_config("user.signingkey")


def is_gpg_configured() -> Tuple[bool, str]:
    if not check_gpg_available():
        return False, "GPG not installed. Run: winget install GnuPG.GnuPG"

    key = get_gpg_signing_key()
    if not key:
        return False, "No signing key configured. Run: python auto_commit.py --setup-gpg"

    try:
        result = subprocess.run(
            [get_gpg_cmd(), "--list-secret-keys", key],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if result.returncode != 0:
            return False, f"Signing key {key} not found in GPG keyring"
    except (subprocess.TimeoutExpired, OSError):
        return False, "Failed to verify GPG key"

    return True, f"GPG ready (key: ...{key[-8:]})"


def setup_gpg_wizard() -> Dict[str, object]:
    """Fully automated GPG setup. Only manual step: paste key into GitHub."""
    email = get_git_config("user.email")
    name = get_git_config("user.name")
    clipboard_ok = False
    public_key = ""
    key_id = ""

    if not email:
        emit(
            {
                "status": "error",
                "message": "git user.email not configured. Run: git config --global user.email your@email.com",
            }
        )
        return {"status": "error"}

    if not check_gpg_available():
        emit({"status": "installing", "step": "1/5", "message": "Installing GPG..."})

        for installer_cmd in [
            [
                "winget",
                "install",
                "--id",
                "GnuPG.GnuPG",
                "-e",
                "--accept-source-agreements",
                "--accept-package-agreements",
            ],
            ["choco", "install", "gnupg", "-y"],
        ]:
            try:
                install_result = subprocess.run(
                    installer_cmd,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=120,
                    check=False,
                )
                if install_result.returncode == 0:
                    break
            except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
                continue

        if not check_gpg_available():
            emit(
                {
                    "status": "error",
                    "message": "GPG auto-install failed. Please install manually:",
                    "commands": [
                        "winget install GnuPG.GnuPG",
                        "# OR: choco install gnupg",
                        "# Then restart terminal and re-run --setup-gpg",
                    ],
                }
            )
            return {"status": "error"}

        emit({"status": "progress", "step": "1/5", "message": "GPG installed [OK]"})
    else:
        emit({"status": "progress", "step": "1/5", "message": "GPG already installed [OK]"})

    key_id = find_existing_gpg_key(email)
    if key_id:
        emit({"status": "progress", "step": "2/5", "message": f"Found existing GPG key: ...{key_id[-8:]}"})
    else:
        identity = f"{name} <{email}>" if name else email
        emit({"status": "generating", "step": "2/5", "message": f"Generating GPG key for {email}..."})
        result: Optional[subprocess.CompletedProcess[str]] = None

        try:
            result = subprocess.run(
                [get_gpg_cmd(), "--batch", "--quick-generate-key", identity, "rsa4096", "sign", "never"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=60,
                check=False,
            )
        except subprocess.TimeoutExpired:
            emit({"status": "error", "message": "GPG key generation timed out"})
            return {"status": "error"}
        except OSError as exc:
            emit({"status": "error", "message": f"GPG key generation failed: {exc}"})
            return {"status": "error"}

        if result.returncode != 0:
            try:
                result = subprocess.run(
                    [
                        get_gpg_cmd(),
                        "--batch",
                        "--passphrase",
                        "",
                        "--quick-generate-key",
                        identity,
                        "rsa4096",
                        "sign",
                        "never",
                    ],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=60,
                    check=False,
                )
            except subprocess.TimeoutExpired:
                emit({"status": "error", "message": "GPG key generation timed out"})
                return {"status": "error"}
            except OSError as exc:
                emit({"status": "error", "message": f"GPG key generation failed: {exc}"})
                return {"status": "error"}

            if result.returncode != 0:
                emit(
                    {
                        "status": "error",
                        "message": "GPG key generation failed",
                        "stderr": (result.stderr or "").strip()[:200],
                        "manual_command": f'gpg --quick-generate-key "{identity}" rsa4096 sign never',
                    }
                )
                return {"status": "error"}

        key_id = find_existing_gpg_key(email)
        if not key_id:
            emit({"status": "error", "message": "Key generated but could not find key ID"})
            return {"status": "error"}

        emit({"status": "progress", "step": "2/5", "message": f"GPG key generated: ...{key_id[-8:]} [OK]"})

    emit({"status": "configuring", "step": "3/5", "message": "Configuring git signing..."})
    configs = [
        ["config", "--global", "user.signingkey", key_id],
        ["config", "--global", "commit.gpgsign", "true"],
    ]
    gpg_path = detect_gpg_program_path()
    if gpg_path:
        configs.append(["config", "--global", "gpg.program", gpg_path])

    for config_args in configs:
        subprocess.run(
            ["git", *config_args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            check=False,
        )
    emit({"status": "progress", "step": "3/5", "message": "Git signing configured [OK]"})

    emit({"status": "exporting", "step": "4/5", "message": "Exporting public key..."})
    try:
        export_result = subprocess.run(
            [get_gpg_cmd(), "--armor", "--export", key_id],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            check=False,
        )
        public_key = export_result.stdout.strip() if export_result.returncode == 0 else ""
    except (subprocess.TimeoutExpired, OSError):
        public_key = ""

    if public_key:
        try:
            clip_result = subprocess.run(
                ["clip"],
                input=public_key,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=5,
                check=False,
            )
            clipboard_ok = clip_result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            clipboard_ok = False

        if clipboard_ok:
            emit({"status": "progress", "step": "4/5", "message": "Public key copied to clipboard [OK]"})
        else:
            emit({"status": "progress", "step": "4/5", "message": "Public key exported (clipboard copy failed, see output)"})
    else:
        emit({"status": "progress", "step": "4/5", "message": "Public key export failed"})

    emit({"status": "progress", "step": "5/5", "message": "Opening GitHub GPG settings..."})
    github_url = "https://github.com/settings/gpg/new"
    browser_opened = False
    try:
        if sys.platform == "win32":
            os.startfile(github_url)  # type: ignore[attr-defined]
        else:
            subprocess.run(["xdg-open", github_url], check=False, timeout=5)
        browser_opened = True
    except (OSError, subprocess.TimeoutExpired):
        browser_opened = False

    emit(
        {
            "status": "setup_complete",
            "message": "GPG setup complete! Just paste your key into GitHub.",
            "key_id": f"...{key_id[-8:]}" if key_id else "",
            "email": email,
            "clipboard": "Public key copied to clipboard" if clipboard_ok else "Copy manually from below",
            "github_url": github_url,
            "browser_opened": browser_opened,
            "next_step": 'Paste the key in GitHub -> Save -> Done! All future commits will show "Verified [OK]"',
            "public_key": "(in clipboard)" if clipboard_ok else public_key,
        }
    )
    return {"status": "setup_complete", "key_id": key_id}


def find_existing_gpg_key(email: str) -> str:
    """Find existing GPG secret key ID for given email."""
    try:
        result = subprocess.run(
            [get_gpg_cmd(), "--list-secret-keys", "--keyid-format=long", email],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            check=False,
        )
        if result.returncode != 0:
            return ""
        for line in result.stdout.splitlines():
            match = re.search(r"sec\s+\w+/([A-F0-9]+)", line, re.IGNORECASE)
            if match:
                return match.group(1)
    except (subprocess.TimeoutExpired, OSError):
        return ""
    return ""


def detect_gpg_program_path() -> str:
    """Detect GPG executable path for git config."""
    path = find_gpg_executable()
    return path if path != "gpg" else ""


def collect_task_files(project_root: Path, explicit_files: List[str]) -> List[str]:
    valid: List[str] = []
    for item in explicit_files:
        fpath = Path(item)
        if not fpath.is_absolute():
            fpath = project_root / item
        if fpath.exists():
            try:
                rel = fpath.resolve().relative_to(project_root.resolve())
                valid.append(rel.as_posix())
            except ValueError:
                continue
    return sorted(set(valid))


def get_modified_files(project_root: Path) -> List[str]:
    result = run_git(project_root, ["status", "--porcelain", "-uall"])
    if result.returncode != 0:
        return []

    files: List[str] = []
    for line in result.stdout.splitlines():
        if len(line) < 4:
            continue
        fpath = line[3:].strip()
        if " -> " in fpath:
            fpath = fpath.split(" -> ")[-1]
        files.append(fpath.replace("\\", "/"))
    return sorted(set(files))


def parse_json_from_output(stdout: str) -> Optional[Dict[str, Any]]:
    text = stdout.strip()
    if not text:
        return None
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        pass

    decoder = json.JSONDecoder()
    for idx in range(len(text) - 1, -1, -1):
        if text[idx] != "{":
            continue
        try:
            obj, end = decoder.raw_decode(text[idx:])
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and idx + end <= len(text):
            return obj
    return None


def run_pre_commit_gate(project_root: Path, skip_tests: bool = False) -> Dict[str, Any]:
    gate_script = (
        Path(__file__).parent.parent.parent
        / "codex-execution-quality-gate"
        / "scripts"
        / "pre_commit_check.py"
    )
    if not gate_script.exists():
        return {"passed": True, "warnings": ["pre_commit_check.py not found, skipping gate"]}

    cmd = [sys.executable, str(gate_script), "--project-root", str(project_root)]
    if skip_tests:
        cmd.append("--skip-tests")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {"passed": False, "blocking": ["Pre-commit gate timed out after 120s"]}
    except OSError as exc:
        return {"passed": False, "blocking": [f"Failed to run gate: {exc}"]}

    payload = parse_json_from_output(result.stdout)
    if payload is not None:
        return payload

    return {"passed": result.returncode == 0, "warnings": ["Could not parse gate output"]}


def detect_commit_type(files: List[str]) -> str:
    scores: Dict[str, int] = {ctype: 0 for ctype in COMMIT_TYPES}
    for file_path in files:
        lowered = file_path.lower()
        for ctype, hints in COMMIT_TYPES.items():
            for hint in hints:
                if hint.startswith("*."):
                    if lowered.endswith(hint[1:]):
                        scores[ctype] += 2
                elif "/" + hint.lower() + "/" in "/" + lowered + "/":
                    scores[ctype] += 2
                elif hint.lower() in lowered:
                    scores[ctype] += 1
    best = max(scores.items(), key=lambda item: item[1])
    return best[0] if best[1] > 0 else "chore"


def detect_scope(files: List[str]) -> str:
    if not files:
        return ""
    dirs: Set[str] = set()
    for file_path in files:
        parts = Path(file_path).parts
        if parts and parts[0].lower() in ("src", "app", "lib"):
            if len(parts) > 1:
                dirs.add(parts[1].lower())
        elif parts:
            dirs.add(parts[0].lower())
    if len(dirs) == 1:
        scope = dirs.pop()
        return re.sub(r"\..*$", "", scope)
    return ""


def build_commit_message(
    files: List[str],
    msg_type: str = "",
    scope: str = "",
    description: str = "",
) -> str:
    if not msg_type:
        msg_type = detect_commit_type(files)
    if not scope:
        scope = detect_scope(files)

    if not description:
        description = f"update {Path(files[0]).name}" if len(files) == 1 else f"update {len(files)} files"

    header = f"{msg_type}{f'({scope})' if scope else ''}: {description}"

    body_lines = ["", "Files:"]
    for file_path in files[:15]:
        body_lines.append(f"- {file_path}")
    if len(files) > 15:
        body_lines.append(f"- ... +{len(files) - 15} more")

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    footer = f"", f"Committed-at: {timestamp}"
    return header + "\n" + "\n".join(body_lines) + "\n" + "\n".join(footer)


def stage_files(project_root: Path, files: List[str]) -> Tuple[bool, str]:
    if not files:
        return False, "No files to stage"
    result = run_git(project_root, ["add", "--"] + files)
    if result.returncode != 0:
        return False, f"git add failed: {result.stderr.strip()}"
    return True, f"Staged {len(files)} file(s)"


def git_commit(project_root: Path, message: str, sign: bool = True) -> Tuple[bool, str]:
    cmd = ["commit", "-m", message]
    if sign:
        cmd.append("-S")

    result = run_git(project_root, cmd, timeout=30)
    if result.returncode != 0:
        stderr = result.stderr.strip()
        if "gpg" in stderr.lower():
            fallback = run_git(project_root, ["commit", "-m", message], timeout=30)
            if fallback.returncode == 0:
                return True, "Committed (unsigned - GPG error, use --setup-gpg to fix)"
            return False, f"Commit failed: {stderr}"
        return False, f"Commit failed: {stderr}"

    match = re.search(r"\[[\w/-]+\s+([a-f0-9]+)\]", result.stdout)
    commit_hash = match.group(1) if match else "unknown"
    return True, f"Committed ({'signed' if sign else 'unsigned'}): {commit_hash}"


def git_push(project_root: Path) -> Tuple[bool, str]:
    branch = get_current_branch(project_root)
    result = run_git(project_root, ["push", "origin", branch], timeout=120)
    if result.returncode != 0:
        return False, f"Push failed: {result.stderr.strip()}"
    return True, f"Pushed to origin/{branch}"


def main() -> int:
    args = parse_args()

    if args.setup_gpg:
        setup_gpg_wizard()
        return 0

    if not args.project_root:
        emit({"status": "error", "message": "--project-root is required unless --setup-gpg is used"})
        return 1

    project_root = Path(args.project_root).expanduser().resolve()
    if not project_root.exists() or not project_root.is_dir():
        emit({"status": "error", "message": f"Not a directory: {project_root}"})
        return 1

    if not git_ready(project_root):
        emit({"status": "error", "message": "Not a git repository"})
        return 1

    files = collect_task_files(project_root, args.files) if args.files else get_modified_files(project_root)
    if not files:
        emit({"status": "skip", "message": "No files to commit"})
        return 0

    ok, stage_message = stage_files(project_root, files)
    if not ok:
        emit({"status": "error", "message": stage_message})
        return 1

    gate = run_pre_commit_gate(project_root, skip_tests=args.skip_tests)
    blocking = gate.get("blocking", [])
    if blocking:
        run_git(project_root, ["reset", "HEAD", "--"] + files)
        emit(
            {
                "status": "blocked",
                "message": "Pre-commit gate FAILED. Commit aborted.",
                "blocking": blocking,
                "warnings": gate.get("warnings", []),
            }
        )
        return 1

    message = args.message or build_commit_message(
        files,
        msg_type=args.type or "",
        scope=args.scope,
    )
    gpg_ready, gpg_message = is_gpg_configured()

    if args.dry_run:
        emit(
            {
                "status": "dry_run",
                "files": files,
                "message": message,
                "gpg": gpg_message,
                "gate": "passed",
                "would_push": not args.no_push,
                "branch": get_current_branch(project_root),
            }
        )
        run_git(project_root, ["reset", "HEAD", "--"] + files)
        return 0

    ok, commit_status = git_commit(project_root, message, sign=gpg_ready)
    if not ok:
        emit({"status": "error", "message": commit_status})
        return 1

    push_status = "skipped"
    if not args.no_push:
        ok, push_message = git_push(project_root)
        push_status = push_message
        if not ok:
            emit(
                {
                    "status": "partial",
                    "message": f"Committed but push failed: {push_message}",
                    "commit": commit_status,
                    "files": files,
                }
            )
            return 1

    emit(
        {
            "status": "ok",
            "commit": commit_status,
            "push": push_status,
            "files": files,
            "message": message.splitlines()[0],
            "gpg": gpg_message,
            "branch": get_current_branch(project_root),
        }
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
