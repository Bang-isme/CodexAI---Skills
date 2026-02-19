#!/usr/bin/env python3
"""
Start one or more servers, wait for ports, run a command, then cleanup.
"""

from __future__ import annotations

import argparse
import json
import socket
import subprocess
import sys
import time
from typing import Dict, List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a command with one or more server processes managed automatically.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            '  python with_server.py --server "npm run dev" --port 5173 -- python smoke_test.py\n'
            '  python with_server.py --server "cd backend && python app.py" --port 3000 --server "cd frontend && npm run dev" --port 5173 -- python e2e.py\n'
            "  python with_server.py --help\n\n"
            'Output:\n  JSON events to stdout: {"status":"ready",...}, {"status":"completed",...}'
        ),
    )
    parser.add_argument("--server", action="append", dest="servers", required=True, help="Server command (repeatable)")
    parser.add_argument("--port", action="append", dest="ports", required=True, type=int, help="Port for each server command")
    parser.add_argument("--timeout", type=int, default=30, help="Port wait timeout in seconds (default: 30)")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="Command to run after '--'")
    return parser.parse_args()


def emit(payload: Dict[str, object]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2), flush=True)


def wait_port_ready(port: int, timeout: int) -> bool:
    started = time.time()
    while (time.time() - started) < timeout:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return True
        except (socket.error, OSError):
            time.sleep(0.4)
    return False


def cleanup(processes: List[subprocess.Popen]) -> None:
    for process in processes:
        if process.poll() is not None:
            continue
        try:
            process.terminate()
            process.wait(timeout=5)
        except (subprocess.TimeoutExpired, OSError):
            try:
                process.kill()
                process.wait(timeout=5)
            except OSError:
                pass


def main() -> int:
    args = parse_args()
    command = list(args.command)
    if command and command[0] == "--":
        command = command[1:]

    if not command:
        emit({"status": "error", "message": "No command specified to run after '--'."})
        return 1

    if len(args.servers) != len(args.ports):
        emit({"status": "error", "message": "The number of --server and --port arguments must match."})
        return 1

    processes: List[subprocess.Popen] = []
    try:
        for server_cmd, port in zip(args.servers, args.ports):
            proc = subprocess.Popen(
                server_cmd,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            processes.append(proc)
            if not wait_port_ready(port, args.timeout):
                raise RuntimeError(f"Server failed to become ready on port {port} within {args.timeout}s.")

        emit({"status": "ready", "servers": args.servers, "ports": args.ports, "timeout": args.timeout})

        run_proc = subprocess.run(command, check=False)
        emit({"status": "completed", "command": command, "exit_code": run_proc.returncode})
        return int(run_proc.returncode)
    except RuntimeError as exc:
        emit({"status": "error", "message": str(exc)})
        return 1
    except OSError as exc:
        emit({"status": "error", "message": f"Process execution failed: {exc}"})
        return 1
    finally:
        cleanup(processes)


if __name__ == "__main__":
    sys.exit(main())
