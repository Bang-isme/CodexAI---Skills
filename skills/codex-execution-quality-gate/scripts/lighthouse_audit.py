#!/usr/bin/env python3
"""
Run Lighthouse CLI audits with graceful degradation.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Dict, List, Optional, Sequence, Tuple


CATEGORY_ALIASES = {
    "perf": "performance",
    "performance": "performance",
    "a11y": "accessibility",
    "accessibility": "accessibility",
    "seo": "seo",
    "best-practices": "best-practices",
    "best_practices": "best-practices",
}
DEFAULT_CATEGORY_ORDER = ["performance", "accessibility", "best-practices", "seo"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Lighthouse audit and extract summary metrics.")
    parser.add_argument("--url", required=True, help="URL to audit")
    parser.add_argument("--output-dir", default="", help="Output directory for Lighthouse JSON reports")
    parser.add_argument("--categories", default="perf,a11y,seo,best-practices", help="Comma-separated categories")
    parser.add_argument("--device", choices=["mobile", "desktop"], default="mobile", help="Audit preset")
    parser.add_argument("--runs", type=int, default=1, help="Number of audit runs")
    return parser.parse_args()


def emit(payload: Dict[str, object], exit_code: int = 0) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    raise SystemExit(exit_code)


def parse_categories(raw: str) -> List[str]:
    categories: List[str] = []
    for item in raw.split(","):
        token = item.strip().lower()
        if not token:
            continue
        resolved = CATEGORY_ALIASES.get(token)
        if resolved and resolved not in categories:
            categories.append(resolved)
    if not categories:
        return list(DEFAULT_CATEGORY_ORDER)
    return categories


def run_command(args: Sequence[str], timeout: int = 300) -> Tuple[Optional[subprocess.CompletedProcess], Optional[str]]:
    try:
        process = subprocess.run(
            list(args),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=False,
            check=False,
            timeout=timeout,
        )
        return process, None
    except FileNotFoundError:
        if os.name == "nt":
            try:
                cmd = subprocess.list2cmdline(list(args))
                process = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    shell=True,
                    check=False,
                    timeout=timeout,
                )
                return process, None
            except Exception as exc:  # pragma: no cover - defensive
                return None, str(exc)
        return None, "Command not found"
    except subprocess.TimeoutExpired:
        return None, "Command timed out"
    except OSError as exc:
        return None, str(exc)


def lighthouse_available() -> bool:
    process, error = run_command(["npx", "lighthouse", "--version"], timeout=60)
    if error is not None or process is None:
        return False
    return process.returncode == 0


def to_score(value: object) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(round(float(value) * 100))
    except (TypeError, ValueError):
        return None


def extract_metrics(report: Dict[str, object]) -> Dict[str, Optional[float]]:
    audits = report.get("audits", {}) if isinstance(report, dict) else {}
    if not isinstance(audits, dict):
        audits = {}

    def get_numeric(audit_id: str) -> Optional[float]:
        entry = audits.get(audit_id, {})
        if not isinstance(entry, dict):
            return None
        value = entry.get("numericValue")
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    return {
        "first_contentful_paint_ms": get_numeric("first-contentful-paint"),
        "largest_contentful_paint_ms": get_numeric("largest-contentful-paint"),
        "total_blocking_time_ms": get_numeric("total-blocking-time"),
        "cumulative_layout_shift": get_numeric("cumulative-layout-shift"),
        "speed_index_ms": get_numeric("speed-index"),
    }


def extract_opportunities(report: Dict[str, object], limit: int = 5) -> List[Dict[str, object]]:
    audits = report.get("audits", {}) if isinstance(report, dict) else {}
    if not isinstance(audits, dict):
        return []

    opportunities: List[Dict[str, object]] = []
    for audit_id, payload in audits.items():
        if not isinstance(payload, dict):
            continue
        details = payload.get("details", {})
        if not isinstance(details, dict):
            continue
        savings_ms = details.get("overallSavingsMs")
        savings_bytes = details.get("overallSavingsBytes")
        value_score = 0.0
        item: Dict[str, object] = {"audit": audit_id}
        has_savings = False
        if savings_ms is not None:
            try:
                ms_value = float(savings_ms)
                if ms_value > 0:
                    has_savings = True
                    item["savings_ms"] = int(round(ms_value))
                    value_score = max(value_score, ms_value)
            except (TypeError, ValueError):
                pass
        if savings_bytes is not None:
            try:
                bytes_value = float(savings_bytes)
                if bytes_value > 0:
                    has_savings = True
                    item["savings_bytes"] = int(round(bytes_value))
                    value_score = max(value_score, bytes_value / 1000.0)
            except (TypeError, ValueError):
                pass
        if has_savings:
            item["_score"] = value_score
            opportunities.append(item)

    opportunities.sort(key=lambda value: float(value.get("_score", 0.0)), reverse=True)
    trimmed: List[Dict[str, object]] = []
    for item in opportunities[:limit]:
        entry = {k: v for k, v in item.items() if k != "_score"}
        trimmed.append(entry)
    return trimmed


def extract_scores(report: Dict[str, object], categories: Sequence[str]) -> Dict[str, int]:
    result: Dict[str, int] = {}
    category_data = report.get("categories", {}) if isinstance(report, dict) else {}
    if not isinstance(category_data, dict):
        return result
    for category in categories:
        info = category_data.get(category, {})
        if not isinstance(info, dict):
            continue
        score = to_score(info.get("score"))
        if score is None:
            continue
        key = "best_practices" if category == "best-practices" else category
        result[key] = score
    return result


def median_of_values(items: List[Dict[str, Optional[float]]], key: str) -> Optional[float]:
    values = [float(item[key]) for item in items if item.get(key) is not None]
    if not values:
        return None
    return float(median(values))


def main() -> None:
    args = parse_args()
    categories = parse_categories(args.categories)
    runs = max(1, int(args.runs))
    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else (Path.cwd() / ".codex" / "lighthouse")
    output_dir.mkdir(parents=True, exist_ok=True)

    if not lighthouse_available():
        emit(
            {
                "status": "error",
                "message": "Lighthouse CLI not found",
                "install": "npm install -g lighthouse",
                "alternative": "Use Chrome DevTools > Lighthouse tab manually",
            },
            exit_code=0,
        )

    run_scores: List[Dict[str, int]] = []
    run_metrics: List[Dict[str, Optional[float]]] = []
    run_opportunities: List[List[Dict[str, object]]] = []
    warnings: List[str] = []
    report_paths: List[Path] = []
    timestamp_prefix = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    for index in range(runs):
        suffix = f"-{index + 1}" if runs > 1 else ""
        report_path = output_dir / f"lighthouse-{timestamp_prefix}{suffix}.json"
        command = [
            "npx",
            "lighthouse",
            args.url,
            "--output=json",
            f"--output-path={report_path.as_posix()}",
            '--chrome-flags=--headless --no-sandbox',
            f"--only-categories={','.join(categories)}",
            "--quiet",
        ]
        if args.device == "desktop":
            command.append("--preset=desktop")

        process, error = run_command(command, timeout=420)
        if error is not None or process is None:
            warnings.append(f"Run {index + 1}: {error or 'unknown execution error'}")
            continue
        if process.returncode != 0:
            message = process.stderr.strip() or process.stdout.strip() or "Lighthouse execution failed"
            warnings.append(f"Run {index + 1}: {message[:300]}")
            if not report_path.exists():
                continue

        if not report_path.exists():
            warnings.append(f"Run {index + 1}: output report not produced")
            continue

        try:
            payload = json.loads(report_path.read_text(encoding="utf-8", errors="ignore"))
        except json.JSONDecodeError as exc:
            warnings.append(f"Run {index + 1}: invalid JSON output ({exc})")
            continue
        except OSError as exc:
            warnings.append(f"Run {index + 1}: unable to read report ({exc})")
            continue

        scores = extract_scores(payload, categories)
        metrics = extract_metrics(payload)
        opportunities = extract_opportunities(payload)
        run_scores.append(scores)
        run_metrics.append(metrics)
        run_opportunities.append(opportunities)
        report_paths.append(report_path)

    if not run_scores:
        emit(
            {
                "status": "error",
                "message": "Lighthouse audit did not produce valid results",
                "install": "Ensure Lighthouse is installed and URL is reachable",
                "alternative": "Start local server and rerun, or use DevTools Lighthouse panel",
                "warnings": warnings,
            },
            exit_code=1,
        )

    aggregated_scores: Dict[str, int] = {}
    for key in {"performance", "accessibility", "best_practices", "seo"}:
        values = [score[key] for score in run_scores if key in score]
        if values:
            aggregated_scores[key] = int(round(median(values)))

    metric_keys = [
        "first_contentful_paint_ms",
        "largest_contentful_paint_ms",
        "total_blocking_time_ms",
        "cumulative_layout_shift",
        "speed_index_ms",
    ]
    aggregated_metrics: Dict[str, object] = {}
    for key in metric_keys:
        value = median_of_values(run_metrics, key)
        if value is None:
            aggregated_metrics[key] = None
        elif key == "cumulative_layout_shift":
            aggregated_metrics[key] = round(value, 3)
        else:
            aggregated_metrics[key] = int(round(value))

    chosen_opportunities = max(run_opportunities, key=lambda item: len(item), default=[])
    if not aggregated_scores:
        emit(
            {
                "status": "error",
                "message": "Lighthouse completed but no category scores were parsed.",
                "install": "Ensure target URL is reachable and not blocked by auth/redirect loops",
                "alternative": "Run Lighthouse manually in Chrome DevTools to inspect runtime errors",
                "report_path": report_paths[-1].as_posix() if report_paths else "",
                "warnings": warnings,
            },
            exit_code=1,
        )

    summary_parts = []
    for label, key in [
        ("Performance", "performance"),
        ("A11y", "accessibility"),
        ("Best Practices", "best_practices"),
        ("SEO", "seo"),
    ]:
        if key in aggregated_scores:
            summary_parts.append(f"{label}: {aggregated_scores[key]}")
    summary = ", ".join(summary_parts) if summary_parts else "No category scores parsed"

    payload: Dict[str, object] = {
        "status": "audited",
        "url": args.url,
        "device": args.device,
        "scores": aggregated_scores,
        "metrics": aggregated_metrics,
        "opportunities": chosen_opportunities,
        "report_path": report_paths[-1].as_posix() if report_paths else "",
        "summary": summary,
    }
    if warnings:
        payload["warnings"] = warnings
    emit(payload, exit_code=0)


if __name__ == "__main__":
    main()
