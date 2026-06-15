from __future__ import annotations

import asyncio
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tools.safety import SafetyError, validate_public_url


DEFAULT_LIGHTHOUSE_TIMEOUT_SECONDS = 25.0
AUDIT_IDS = (
    "largest-contentful-paint",
    "interactive",
    "total-blocking-time",
    "cumulative-layout-shift",
    "color-contrast",
    "image-alt",
    "document-title",
    "meta-description",
)


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _lighthouse_command() -> str | None:
    configured = os.getenv("LIGHTHOUSE_CLI")
    if configured:
        return configured
    on_path = shutil.which("lighthouse")
    if on_path:
        return on_path
    local_bin = Path(__file__).resolve().parents[1] / "node_modules" / ".bin" / "lighthouse"
    if local_bin.exists():
        return str(local_bin)
    cwd_bin = Path.cwd() / "node_modules" / ".bin" / "lighthouse"
    if cwd_bin.exists():
        return str(cwd_bin)
    return None


def _score(categories: dict[str, Any], key: str) -> float | None:
    item = categories.get(key)
    if not isinstance(item, dict):
        return None
    value = item.get("score")
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _audit_summary(audits: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for audit_id in AUDIT_IDS:
        item = audits.get(audit_id)
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "id": audit_id,
                "title": str(item.get("title") or audit_id),
                "score": item.get("score") if isinstance(item.get("score"), (int, float)) else None,
                "display_value": item.get("displayValue"),
            }
        )
    return rows


async def run_lighthouse_summary(url: str) -> dict[str, Any]:
    """Run Lighthouse and return scores/audit summaries without raw reports."""

    timeout_seconds = _env_float("MCP_LIGHTHOUSE_TIMEOUT_SECONDS", DEFAULT_LIGHTHOUSE_TIMEOUT_SECONDS)
    try:
        requested_url = await validate_public_url(url)
        command = _lighthouse_command()
        if not command:
            return {
                "success": False,
                "url": requested_url,
                "error_message": "Lighthouse CLI is not installed or not on PATH.",
                "checked_at": _utc_now(),
            }

        process = await asyncio.create_subprocess_exec(
            command,
            requested_url,
            "--output=json",
            "--quiet",
            "--chrome-flags=--headless=new --no-sandbox",
            "--only-categories=performance,accessibility,best-practices,seo",
            "--max-wait-for-load=15000",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout_seconds)
        except asyncio.TimeoutError:
            process.kill()
            await process.communicate()
            return {
                "success": False,
                "url": requested_url,
                "error_message": f"Lighthouse timeout after {timeout_seconds:.1f}s.",
                "checked_at": _utc_now(),
            }

        if not stdout:
            return {
                "success": False,
                "url": requested_url,
                "error_message": (stderr.decode("utf-8", errors="replace") or "Lighthouse returned no JSON.")[:500],
                "checked_at": _utc_now(),
            }

        try:
            payload = json.loads(stdout.decode("utf-8", errors="replace"))
        except json.JSONDecodeError as exc:
            return {
                "success": False,
                "url": requested_url,
                "error_message": f"Lighthouse JSON parse failed: {exc}",
                "checked_at": _utc_now(),
            }

        final_url = (
            payload.get("finalDisplayedUrl")
            or payload.get("finalUrl")
            or payload.get("mainDocumentUrl")
            or payload.get("requestedUrl")
            or requested_url
        )
        final_url = await validate_public_url(str(final_url))
        categories = payload.get("categories") if isinstance(payload.get("categories"), dict) else {}
        audits = payload.get("audits") if isinstance(payload.get("audits"), dict) else {}
        warnings = payload.get("runWarnings") if isinstance(payload.get("runWarnings"), list) else []
        return {
            "success": process.returncode == 0,
            "url": requested_url,
            "final_url": final_url,
            "scores": {
                "performance": _score(categories, "performance"),
                "accessibility": _score(categories, "accessibility"),
                "best_practices": _score(categories, "best-practices"),
                "seo": _score(categories, "seo"),
            },
            "key_audits": _audit_summary(audits),
            "warnings": [str(item)[:240] for item in warnings[:5]],
            "error_message": None if process.returncode == 0 else (stderr.decode("utf-8", errors="replace") or None),
            "checked_at": _utc_now(),
        }
    except SafetyError as exc:
        return {"success": False, "url": url, "error_message": str(exc), "checked_at": _utc_now()}
    except Exception as exc:
        return {
            "success": False,
            "url": url,
            "error_message": f"{exc.__class__.__name__}: {exc}",
            "checked_at": _utc_now(),
        }
