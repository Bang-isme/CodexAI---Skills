#!/usr/bin/env python3
"""Paired good/bad self-tests for safety and correctness edge cases.

The process exits 0 only when every good fixture passes and every bad fixture
is caught.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import re
import sqlite3
import tempfile
from pathlib import Path
from typing import Any, Callable


CASE_NAMES = (
    "safe_path",
    "rate_limit",
    "sql_query",
    "auth_token",
    "csv_sum",
    "email_validator",
    "singleflight_cache",
    "shared_transfer",
    "money_parser",
    "confirm_destructive_ui",
    "null_safe_request",
    "debounce_timing",
)
_FENCE_RE = re.compile(r"```[^\n`]*\n(.*?)```", re.DOTALL)
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\Z")
_INJECTION = "' OR '1'='1"


def good_safe_path(root: Path | str, user_path: str) -> str | None:
    root_path = Path(root).resolve()
    if not user_path or not user_path.strip():
        return None
    candidate = (root_path / user_path).resolve()
    if candidate != root_path and root_path not in candidate.parents:
        return None
    return str(candidate)


def bad_safe_path(root: Path | str, user_path: str) -> str | None:
    root_path = Path(root).resolve()
    candidate = (root_path / user_path).resolve()
    root_text = str(root_path)
    candidate_text = str(candidate)
    if candidate_text.startswith(root_text):
        return candidate_text
    return None


def _check_safe_path() -> tuple[bool, bool, str]:
    with tempfile.TemporaryDirectory() as temporary:
        base = Path(temporary)
        root = base / "app"
        evil = base / "app-evil"
        root.mkdir()
        evil.mkdir()
        (root / "ok.txt").write_text("ok", encoding="utf-8")
        (evil / "secret.txt").write_text("no", encoding="utf-8")
        normal = good_safe_path(root, "ok.txt")
        nested = good_safe_path(root, "nested/file.txt")
        traversal = good_safe_path(root, "../app-evil/secret.txt")
        climbed = good_safe_path(root, "../..")
        good_ok = normal is not None and nested is not None and traversal is None and climbed is None
        bad_rejected = bad_safe_path(root, "../app-evil/secret.txt") is not None
    return good_ok, bad_rejected, "relative path allowed; traversal and prefix collision rejected"


class GoodRateLimiter:
    def __init__(self, limit: int) -> None:
        self.limit = limit
        self._seen: dict[str, int] = {}

    def allow(self, key: str) -> bool:
        used = self._seen.get(key, 0)
        if used >= self.limit:
            return False
        self._seen[key] = used + 1
        return True


class BadRateLimiter:
    def __init__(self, limit: int) -> None:
        self.limit = limit
        self._seen = 0

    def allow(self, key: str) -> bool:
        if self._seen >= self.limit:
            return False
        self._seen += 1
        return True


def _check_rate_limit() -> tuple[bool, bool, str]:
    good = GoodRateLimiter(2)
    good_ok = good.allow("A") and good.allow("A") and not good.allow("A") and good.allow("B")
    bad = BadRateLimiter(2)
    bad.allow("A")
    bad.allow("A")
    bad_rejected = bad.allow("B") is False
    return good_ok, bad_rejected, "client A quota does not block client B"


def _query_users(user_input: str, parameterized: bool) -> list[int]:
    connection = sqlite3.connect(":memory:")
    try:
        connection.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
        connection.executemany("INSERT INTO users (name) VALUES (?)", [("alice",), ("bob",)])
        if parameterized:
            rows = connection.execute("SELECT id FROM users WHERE name = ?", (user_input,)).fetchall()
        else:
            rows = connection.execute(f"SELECT id FROM users WHERE name = '{user_input}'").fetchall()
        return [int(row[0]) for row in rows]
    finally:
        connection.close()


def good_sql_query(user_input: str) -> list[int]:
    return _query_users(user_input, True)


def bad_sql_query(user_input: str) -> list[int]:
    return _query_users(user_input, False)


def _check_sql_query() -> tuple[bool, bool, str]:
    good_ok = good_sql_query(_INJECTION) == [] and good_sql_query("alice") == [1]
    try:
        bad_rejected = len(bad_sql_query(_INJECTION)) > 0
    except sqlite3.Error:
        bad_rejected = True
    return good_ok, bad_rejected, "interpolated tautology returns unauthorized rows; parameters return none"


def _digest(key_bytes: bytes, message: str) -> str:
    return hmac.new(key_bytes, message.encode("utf-8"), hashlib.sha256).hexdigest()


def signed_message(key_bytes: bytes, message: str) -> str:
    return f"{message}.{_digest(key_bytes, message)}"


def good_auth_token(key_bytes: bytes, message: str, provided: str) -> bool:
    expected = _digest(key_bytes, message)
    provided_message, separator, provided_digest = provided.partition(".")
    if separator != "." or provided_message != message or len(provided_digest) != len(expected):
        return False
    return hmac.compare_digest(expected, provided_digest)


def bad_auth_token(key_bytes: bytes, message: str, provided: str) -> bool:
    del key_bytes
    return provided.split(".", 1)[0] == message


def _check_auth_token() -> tuple[bool, bool, str]:
    key_bytes = b"codexai-precision-check"
    valid = signed_message(key_bytes, "admin")
    tampered = "admin.deadbeef"
    good_ok = good_auth_token(key_bytes, "admin", valid) and not good_auth_token(key_bytes, "admin", tampered)
    bad_rejected = bad_auth_token(key_bytes, "admin", tampered) is True
    return good_ok, bad_rejected, "constant-time digest rejects a tampered suffix; naive split accepts it"


def good_csv_sum(text: str, code: str = "351") -> int:
    total = 0
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        cells = [cell.strip() for cell in line.split(",")]
        if len(cells) < 2 or cells[0] != code:
            continue
        try:
            total += int(cells[1])
        except ValueError:
            continue
    return total


def bad_csv_sum(text: str, code: str = "351") -> int:
    total = 0
    for raw_line in text.splitlines():
        if code not in raw_line:
            continue
        cells = [cell.strip() for cell in raw_line.split(",")]
        total += int(cells[1])
    return total


def _check_csv_sum() -> tuple[bool, bool, str]:
    clean = "351,10\n13510,7\n351,5\n"
    dirty = clean + "351,bad\n"
    good_ok = good_csv_sum(clean) == 15 and good_csv_sum(dirty) == 15
    bad_rejected = False
    try:
        if bad_csv_sum(clean) != 15:
            bad_rejected = True
    except (ValueError, IndexError):
        bad_rejected = True
    try:
        bad_csv_sum(dirty)
    except (ValueError, IndexError):
        bad_rejected = True
    return good_ok, bad_rejected, "351 matches the whole field; 13510 is not a match and malformed rows are skipped"


def good_email_validator(value: str) -> bool:
    if not isinstance(value, str) or any(char in value for char in "\r\n\x00"):
        return False
    return _EMAIL_RE.fullmatch(value) is not None


def bad_email_validator(value: str) -> bool:
    if not isinstance(value, str):
        return False
    return re.match(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", value) is not None


def _check_email_validator() -> tuple[bool, bool, str]:
    injected = "user@example.com\n<script>"
    good_ok = good_email_validator("user@example.com") and not good_email_validator(injected)
    bad_rejected = bad_email_validator(injected) is True
    return good_ok, bad_rejected, "trailing newline injection fails a full match and passes an unanchored match"


class _Flight:
    def __init__(self, compute: Callable[[], Any], once: bool) -> None:
        self._compute = compute
        self._once = once
        self.call_count = 0
        self._ready = False
        self._value: Any = None

    def __call__(self) -> Any:
        if self._once and self._ready:
            return self._value
        self.call_count += 1
        self._value = self._compute()
        self._ready = True
        return self._value


def good_singleflight_cache(compute: Callable[[], Any]) -> _Flight:
    return _Flight(compute, True)


def bad_singleflight_cache(compute: Callable[[], Any]) -> _Flight:
    return _Flight(compute, False)


def _check_singleflight_cache() -> tuple[bool, bool, str]:
    def compute_factory() -> tuple[dict[str, int], Callable[[], str]]:
        state = {"call_count": 0}

        def compute() -> str:
            state["call_count"] += 1
            return "cached"

        return state, compute

    good_state, good_compute = compute_factory()
    good_runner = good_singleflight_cache(good_compute)
    good_values = [good_runner(), good_runner(), good_runner()]
    good_ok = good_values == ["cached", "cached", "cached"] and good_runner.call_count == 1 and good_state["call_count"] == 1
    bad_state, bad_compute = compute_factory()
    bad_runner = bad_singleflight_cache(bad_compute)
    bad_runner()
    bad_runner()
    bad_runner()
    bad_rejected = bad_runner.call_count == 3 and bad_state["call_count"] == 3
    return good_ok, bad_rejected, "repeated reads reuse one computation"


def good_shared_transfer(balances: dict[str, int], src: str, dst: str, amount: int) -> bool:
    if amount <= 0 or balances.get(src, 0) < amount:
        return False
    balances[src] -= amount
    balances[dst] = balances.get(dst, 0) + amount
    return True


def bad_shared_transfer(balances: dict[str, int], src: str, dst: str, amount: int) -> bool:
    balances[src] = balances.get(src, 0) - amount
    balances[dst] = balances.get(dst, 0) + amount
    return True


def _check_shared_transfer() -> tuple[bool, bool, str]:
    good_balances = {"alice": 100, "bob": 0}
    first = good_shared_transfer(good_balances, "alice", "bob", 80)
    second = good_shared_transfer(good_balances, "alice", "bob", 80)
    good_ok = first and not second and good_balances["alice"] == 20 and good_balances["bob"] == 80
    bad_balances = {"alice": 100, "bob": 0}
    if bad_balances["alice"] >= 80:
        bad_shared_transfer(bad_balances, "alice", "bob", 80)
    bad_shared_transfer(bad_balances, "alice", "bob", 80)
    bad_rejected = bad_balances["alice"] < 0
    return good_ok, bad_rejected, "the shared transfer rejects the second caller; a caller-only check does not"


def good_money_parser(text: str) -> int:
    raw = text.strip()
    negative = False
    if raw.startswith("(") and raw.endswith(")"):
        negative = True
        raw = raw[1:-1].strip()
    if raw.startswith("-"):
        negative = True
        raw = raw[1:].strip()
    if raw.startswith("$"):
        raw = raw[1:].strip()
    if raw.startswith("-"):
        negative = True
        raw = raw[1:].strip()
    raw = raw.replace(",", "")
    if raw.count(".") > 1:
        raise ValueError("invalid money")
    if "." in raw:
        whole, frac = raw.split(".", 1)
        if whole == "":
            whole = "0"
        if not whole.isdigit() or not frac.isdigit():
            raise ValueError("invalid money")
        frac = (frac + "00")[:2]
        cents = int(whole) * 100 + int(frac)
    else:
        if not raw.isdigit():
            raise ValueError("invalid money")
        cents = int(raw) * 100
    return -cents if negative else cents


def bad_money_parser(text: str) -> int:
    cleaned = text.strip().replace("$", "").replace(",", "")
    if cleaned.startswith("(") and cleaned.endswith(")"):
        cleaned = "-" + cleaned[1:-1]
    return int(float(cleaned) * 100)


def _check_money_parser() -> tuple[bool, bool, str]:
    good_ok = (
        good_money_parser("$1,234.50") == 123450
        and good_money_parser("-$0.29") == -29
        and good_money_parser("$0.00") == 0
        and good_money_parser("($1,234.50)") == -123450
    )
    bad_rejected = bad_money_parser("$0.29") != 29
    return good_ok, bad_rejected, "cents are exact integers; float scaling drifts on $0.29"


def good_confirm_destructive_ui(confirmed: bool, on_delete: Callable[[], None]) -> dict[str, Any]:
    if confirmed is not True:
        return {"status": "blocked", "invoked": False}
    on_delete()
    return {"status": "deleted", "invoked": True}


def bad_confirm_destructive_ui(confirmed: bool, on_delete: Callable[[], None]) -> dict[str, Any]:
    del confirmed
    on_delete()
    return {"status": "deleted", "invoked": True}


def _check_confirm_destructive_ui() -> tuple[bool, bool, str]:
    good_calls: list[str] = []
    blocked = good_confirm_destructive_ui(False, lambda: good_calls.append("deleted"))
    allowed_calls: list[str] = []
    allowed = good_confirm_destructive_ui(True, lambda: allowed_calls.append("deleted"))
    good_ok = blocked["invoked"] is False and good_calls == [] and allowed["invoked"] is True and allowed_calls == ["deleted"]
    bad_calls: list[str] = []
    bad_confirm_destructive_ui(False, lambda: bad_calls.append("deleted"))
    return good_ok, bad_calls == ["deleted"], "delete runs only after explicit confirmation"


def good_null_safe_request(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {"status": 400, "error": "empty_payload"}
    if "name" not in payload or payload["name"] is None:
        return {"status": 422, "error": "missing_required_field"}
    if not isinstance(payload["name"], str):
        return {"status": 400, "error": "invalid_payload"}
    name = payload["name"].strip()
    if name == "":
        return {"status": 422, "error": "missing_required_field"}
    return {"status": 200, "name": name}


def bad_null_safe_request(payload: Any) -> dict[str, Any]:
    if isinstance(payload, dict):
        name = payload.get("name").strip()
    else:
        name = payload.name
    return {"status": 200, "name": name}


def _check_null_safe_request() -> tuple[bool, bool, str]:
    samples = (None, {}, {"name": None}, {"name": ""}, {"name": "  "}, [])
    good_ok = True
    for payload in samples:
        try:
            result = good_null_safe_request(payload)
        except (AttributeError, TypeError, KeyError):
            good_ok = False
            break
        if result["status"] not in (400, 422):
            good_ok = False
            break
    good_ok = good_ok and good_null_safe_request({"name": "ada"})["status"] == 200
    bad_rejected = False
    for payload in (None, {}, {"name": None}):
        try:
            bad_null_safe_request(payload)
        except (AttributeError, TypeError):
            bad_rejected = True
            break
    return good_ok, bad_rejected, "missing or empty payloads return 400 or 422"


class VirtualClock:
    def __init__(self) -> None:
        self.now = 0.0

    def time(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def good_debounce(callback: Callable[..., None], delay: float, clock: VirtualClock):
    state: dict[str, Any] = {"deadline": None, "args": ()}

    def submit(*args: Any) -> None:
        state["args"] = args
        state["deadline"] = clock.time() + delay

    def poll() -> None:
        deadline = state["deadline"]
        if deadline is not None and clock.time() >= deadline:
            callback(*state["args"])
            state["deadline"] = None

    return submit, poll


def bad_debounce(callback: Callable[..., None], delay: float, clock: VirtualClock):
    del delay, clock

    def submit(*args: Any) -> None:
        callback(*args)

    def poll() -> None:
        return None

    return submit, poll


def _check_debounce_timing() -> tuple[bool, bool, str]:
    clock = VirtualClock()
    hits: list[float] = []
    submit, poll = good_debounce(lambda: hits.append(clock.time()), 0.3, clock)
    submit()
    submit()
    submit()
    before = len(hits) == 0
    clock.advance(0.3)
    poll()
    poll()
    good_ok = before and hits == [0.3]
    bad_hits: list[int] = []
    bad_submit, _poll = bad_debounce(lambda: bad_hits.append(1), 0.3, clock)
    bad_submit()
    bad_submit()
    bad_submit()
    return good_ok, len(bad_hits) == 3, "rapid calls fire once after the delay"


CHECKS: dict[str, Callable[[], tuple[bool, bool, str]]] = {
    "safe_path": _check_safe_path,
    "rate_limit": _check_rate_limit,
    "sql_query": _check_sql_query,
    "auth_token": _check_auth_token,
    "csv_sum": _check_csv_sum,
    "email_validator": _check_email_validator,
    "singleflight_cache": _check_singleflight_cache,
    "shared_transfer": _check_shared_transfer,
    "money_parser": _check_money_parser,
    "confirm_destructive_ui": _check_confirm_destructive_ui,
    "null_safe_request": _check_null_safe_request,
    "debounce_timing": _check_debounce_timing,
}


def extract_fenced_code(text: str) -> list[str]:
    return [match.group(1).strip("\n") for match in _FENCE_RE.finditer(text) if match.group(1).strip()]


def extract_unfenced_code(text: str) -> list[str]:
    """Extract indented code that is not inside a markdown fence."""
    stripped = _FENCE_RE.sub("\n", text)
    snippets: list[str] = []
    block: list[str] = []

    def flush() -> None:
        if not block:
            return
        dedented: list[str] = []
        for line in block:
            if line.startswith("    "):
                dedented.append(line[4:])
            elif line.startswith("\t"):
                dedented.append(line[1:])
            else:
                dedented.append(line)
        snippet = "\n".join(dedented).strip("\n")
        if snippet.strip():
            snippets.append(snippet)
        block.clear()

    for line in stripped.splitlines():
        if line.startswith("    ") or line.startswith("\t"):
            block.append(line)
        else:
            flush()
    flush()
    return snippets


def run_case(name: str) -> dict[str, Any]:
    checker = CHECKS.get(name)
    if checker is None:
        return {
            "name": name,
            "good_passed": False,
            "bad_rejected": False,
            "ok": False,
            "detail": "unknown case",
        }
    try:
        good_passed, bad_rejected, detail = checker()
    except Exception as exc:
        return {
            "name": name,
            "good_passed": False,
            "bad_rejected": False,
            "ok": False,
            "detail": f"{type(exc).__name__}: {exc}",
        }
    passed = bool(good_passed)
    rejected = bool(bad_rejected)
    return {
        "name": name,
        "good_passed": passed,
        "bad_rejected": rejected,
        "ok": passed and rejected,
        "detail": detail,
    }


def run_safety_selftest() -> dict[str, Any]:
    cases = [run_case(name) for name in CASE_NAMES]
    good_passed = sum(1 for case in cases if case["good_passed"])
    bad_rejected = sum(1 for case in cases if case["bad_rejected"])
    ok = len(cases) == len(CASE_NAMES) and all(case["ok"] for case in cases)
    return {
        "ok": ok,
        "status": "pass" if ok else "fail",
        "case_count": len(cases),
        "good_passed": good_passed,
        "bad_rejected": bad_rejected,
        "cases": cases,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run paired good and bad safety self-tests.")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    parser.add_argument("--case", default="", help="Run one case instead of all 12")
    args = parser.parse_args(argv)
    if args.case:
        case = run_case(args.case)
        report = {
            "ok": case["ok"],
            "status": "pass" if case["ok"] else "fail",
            "case_count": 1,
            "good_passed": 1 if case["good_passed"] else 0,
            "bad_rejected": 1 if case["bad_rejected"] else 0,
            "cases": [case],
        }
    else:
        report = run_safety_selftest()
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"ok={report['ok']} good={report['good_passed']} bad_rejected={report['bad_rejected']}")
        for case in report["cases"]:
            print(f"{case['name']}: good={case['good_passed']} bad_rejected={case['bad_rejected']}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
