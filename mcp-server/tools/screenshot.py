from __future__ import annotations

import hashlib
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tools.safety import SafetyError, validate_public_url


DEFAULT_SCREENSHOT_TIMEOUT_SECONDS = 10.0
DEFAULT_VIEWPORT = {"width": 1365, "height": 768}
VISIBLE_TEXT_LIMIT_CHARS = 1_000


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


def _artifact_dir() -> Path:
    path = Path(tempfile.gettempdir()) / "projectlens-mcp" / "screenshots"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _existing_chromium_executable() -> str | None:
    configured = os.getenv("PLAYWRIGHT_CHROMIUM_EXECUTABLE")
    if configured and Path(configured).exists():
        return configured

    cache = Path.home() / "Library" / "Caches" / "ms-playwright"
    if not cache.exists():
        return None

    candidates: list[Path] = []
    candidates.extend(cache.glob("chromium_headless_shell-*/**/chrome-headless-shell"))
    candidates.extend(cache.glob("chromium-*/**/Chromium.app/Contents/MacOS/Chromium"))
    existing = [path for path in candidates if path.exists()]
    existing.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return str(existing[0]) if existing else None


async def capture_screenshot(url: str) -> dict[str, Any]:
    """Capture the submitted URL's first viewport and return metadata only."""

    timeout_seconds = _env_float("MCP_SCREENSHOT_TIMEOUT_SECONDS", DEFAULT_SCREENSHOT_TIMEOUT_SECONDS)
    timeout_ms = int(timeout_seconds * 1000)
    browser = None
    try:
        requested_url = await validate_public_url(url)
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            return {
                "success": False,
                "url": url,
                "error_message": (
                    "Playwright is not installed in the backend interpreter. "
                    "Install it and run `python -m playwright install chromium`."
                ),
                "captured_at": _utc_now(),
            }

        async with async_playwright() as playwright:
            executable_path = _existing_chromium_executable()
            browser = await playwright.chromium.launch(
                headless=True,
                executable_path=executable_path,
            )
            page = await browser.new_page(viewport=DEFAULT_VIEWPORT)
            response = await page.goto(requested_url, wait_until="domcontentloaded", timeout=timeout_ms)
            final_url = await validate_public_url(page.url)
            visible_text = await page.evaluate("() => document.body ? document.body.innerText : ''")
            visible_text_sample = str(visible_text or "").strip()[:VISIBLE_TEXT_LIMIT_CHARS]

            artifact_path = _artifact_dir() / f"{hashlib.sha256(final_url.encode('utf-8')).hexdigest()[:16]}.png"
            await page.screenshot(path=str(artifact_path), full_page=False, timeout=timeout_ms)
            image_size_bytes = artifact_path.stat().st_size
            return {
                "success": True,
                "url": requested_url,
                "final_url": final_url,
                "status_code": response.status if response is not None else None,
                "viewport": DEFAULT_VIEWPORT,
                "screenshot_saved": True,
                "artifact_path": str(artifact_path),
                "image_sha256": _sha256(artifact_path),
                "image_size_bytes": image_size_bytes,
                "visible_text_sample": visible_text_sample,
                "render_notes": ["first viewport rendered"],
                "captured_at": _utc_now(),
            }
    except SafetyError as exc:
        return {
            "success": False,
            "url": url,
            "error_message": str(exc),
            "captured_at": _utc_now(),
        }
    except Exception as exc:
        return {
            "success": False,
            "url": url,
            "error_message": f"{exc.__class__.__name__}: {exc}",
            "captured_at": _utc_now(),
        }
    finally:
        if browser is not None:
            await browser.close()
