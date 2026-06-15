from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlsplit

from tools.safety import SafetyError, validate_public_url
from tools.screenshot import _existing_chromium_executable
from tools.site import _compact_text, _limit_text


DEFAULT_RENDERED_TIMEOUT_SECONDS = 12.0
DEFAULT_RENDERED_TEXT_LIMIT_CHARS = 4_000
DEFAULT_RENDERED_MAX_LINKS = 20

BLOCK_STATUS_CODES = {401, 403, 429}
BLOCK_PATTERNS: tuple[tuple[str, str], ...] = (
    ("captcha", "captcha"),
    ("verify you are human", "human_verification"),
    ("checking your browser", "browser_challenge"),
    ("enable js", "javascript_required"),
    ("enable javascript", "javascript_required"),
    ("disable any ad blocker", "ad_blocker_challenge"),
    ("access denied", "access_denied"),
    ("temporarily blocked", "temporary_block"),
    ("unusual traffic", "unusual_traffic"),
    ("automated access", "automated_access_blocked"),
)


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def detect_block_reason(
    *,
    status_code: int | None,
    title: str | None = None,
    h1: str | None = None,
    visible_text: str | None = None,
) -> str | None:
    if status_code in BLOCK_STATUS_CODES:
        return f"http_status_{status_code}"

    haystack = _compact_text(" ".join(
        part for part in (title or "", h1 or "", visible_text or "") if part
    )).lower()
    for needle, reason in BLOCK_PATTERNS:
        if needle in haystack:
            return reason
    return None


async def fetch_rendered_site_overview(url: str) -> dict[str, Any]:
    """Render a public URL in Chromium and return bounded text evidence only.

    This is a JavaScript-rendered fallback for legitimate public project pages.
    It deliberately does not attempt to bypass anti-bot protections.
    """

    timeout_seconds = _env_float("MCP_RENDERED_TIMEOUT_SECONDS", DEFAULT_RENDERED_TIMEOUT_SECONDS)
    timeout_ms = int(timeout_seconds * 1000)
    text_limit = _env_int("MCP_RENDERED_TEXT_LIMIT_CHARS", DEFAULT_RENDERED_TEXT_LIMIT_CHARS)
    max_links = _env_int("MCP_MAX_LINKS", DEFAULT_RENDERED_MAX_LINKS)
    browser = None
    blocked_request_errors: list[str] = []
    validated_origins: set[tuple[str, str, int | None]] = set()

    async def _guard_public_request(route: Any) -> None:
        request_url = route.request.url
        parsed = urlsplit(request_url)
        if parsed.scheme not in {"http", "https"}:
            await route.abort()
            return

        origin_key = (parsed.scheme, parsed.hostname or "", parsed.port)
        if origin_key not in validated_origins:
            try:
                await validate_public_url(request_url)
                validated_origins.add(origin_key)
            except SafetyError as exc:
                blocked_request_errors.append(str(exc))
                await route.abort()
                return

        await route.continue_()

    try:
        requested_url = await validate_public_url(url)
        try:
            from playwright.async_api import TimeoutError as PlaywrightTimeoutError
            from playwright.async_api import async_playwright
        except ImportError:
            return {
                "success": False,
                "url": url,
                "error_message": (
                    "Playwright is not installed in the backend interpreter. "
                    "Install it and run `python -m playwright install chromium`."
                ),
                "rendered_at": _utc_now(),
            }

        async with async_playwright() as playwright:
            executable_path = _existing_chromium_executable()
            browser = await playwright.chromium.launch(
                headless=True,
                executable_path=executable_path,
            )
            page = await browser.new_page(viewport={"width": 1365, "height": 768})
            await page.route("**/*", _guard_public_request)
            try:
                response = await page.goto(requested_url, wait_until="domcontentloaded", timeout=timeout_ms)
            except Exception as exc:
                if blocked_request_errors:
                    raise SafetyError(
                        f"Browser request blocked by SSRF policy: {blocked_request_errors[0]}"
                    ) from exc
                raise
            try:
                await page.wait_for_load_state("networkidle", timeout=min(3_000, timeout_ms))
            except PlaywrightTimeoutError:
                pass

            if blocked_request_errors:
                raise SafetyError(
                    f"Browser request blocked by SSRF policy: {blocked_request_errors[0]}"
                )
            final_url = await validate_public_url(page.url)
            rendered = await page.evaluate(
                """(maxLinks) => {
                    const meta =
                        document.querySelector('meta[name="description"]') ||
                        document.querySelector('meta[property="og:description"]');
                    const h1 = document.querySelector('h1');
                    const links = Array.from(document.querySelectorAll('a[href]'))
                        .slice(0, maxLinks)
                        .map((anchor) => ({
                            url: anchor.href || '',
                            text: (anchor.innerText || anchor.textContent || '')
                                .replace(/\\s+/g, ' ')
                                .trim()
                                .slice(0, 160),
                        }))
                        .filter((link) => link.url);
                    return {
                        title: document.title || '',
                        description: meta ? meta.getAttribute('content') || '' : '',
                        h1: h1 ? (h1.innerText || h1.textContent || '') : '',
                        visible_text: document.body ? document.body.innerText || '' : '',
                        links,
                    };
                }""",
                max_links,
            )

            title = _limit_text(str(rendered.get("title") or ""), 180) or ""
            description = _limit_text(str(rendered.get("description") or ""), 300) or ""
            h1 = _limit_text(str(rendered.get("h1") or ""), 180) or ""
            visible_text = _limit_text(str(rendered.get("visible_text") or ""), text_limit) or ""
            status_code = response.status if response is not None else None
            block_reason = detect_block_reason(
                status_code=status_code,
                title=title,
                h1=h1,
                visible_text=visible_text,
            )

            links = rendered.get("links") if isinstance(rendered.get("links"), list) else []
            bounded_links = [
                {
                    "url": str(link.get("url") or ""),
                    "text": _limit_text(str(link.get("text") or ""), 160) or "",
                }
                for link in links[:max_links]
                if isinstance(link, dict) and str(link.get("url") or "").startswith(("http://", "https://"))
            ]
            return {
                "success": True,
                "url": requested_url,
                "final_url": final_url,
                "status_code": status_code,
                "title": title,
                "description": description,
                "h1": h1,
                "visible_text": visible_text,
                "links": bounded_links,
                "blocked_by_site": block_reason is not None,
                "block_reason": block_reason,
                "rendered_at": _utc_now(),
            }
    except SafetyError as exc:
        return {
            "success": False,
            "url": url,
            "error_message": str(exc),
            "rendered_at": _utc_now(),
        }
    except Exception as exc:
        return {
            "success": False,
            "url": url,
            "error_message": f"{exc.__class__.__name__}: {exc}",
            "rendered_at": _utc_now(),
        }
    finally:
        if browser is not None:
            await browser.close()
