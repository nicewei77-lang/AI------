from __future__ import annotations

import os
import re
import time
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from tools.safety import (
    DEFAULT_BODY_SIZE_LIMIT_BYTES,
    DEFAULT_MAX_REDIRECTS,
    SafetyError,
    fetch_with_safety,
    is_same_origin,
    origin_for_url,
)
from tools.site import SiteOverviewParser, _decode_body


DEFAULT_CONTEXT_MAX_PAGES = 5
DEFAULT_CONTEXT_TEXT_LIMIT_CHARS = 12_000
DEFAULT_CONTEXT_TIMEOUT_SECONDS = 15.0
DEFAULT_PAGE_TEXT_LIMIT_CHARS = 4_000
DEFAULT_CONTEXT_MAX_LINKS = 40

PRIORITY_KEYWORDS = (
    "about",
    "features",
    "docs",
    "product",
    "service",
    "pricing",
    "portfolio",
    "projects",
    "demo",
    "case",
    "blog",
)
EXCLUDED_KEYWORDS = (
    "login",
    "log-in",
    "signin",
    "sign-in",
    "signup",
    "sign-up",
    "auth",
    "admin",
    "dashboard",
    "cart",
    "checkout",
    "privacy",
    "terms",
)
SKIPPED_EXTENSIONS = (
    ".avif",
    ".css",
    ".gif",
    ".ico",
    ".jpeg",
    ".jpg",
    ".js",
    ".pdf",
    ".png",
    ".svg",
    ".webp",
    ".zip",
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


def _compact_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _content_type_is_text(headers: dict[str, str]) -> bool:
    content_type = headers.get("content-type", "").lower()
    if not content_type:
        return True
    return (
        content_type.startswith("text/html")
        or content_type.startswith("text/plain")
        or "application/xhtml+xml" in content_type
    )


def _canonical_url(url: str) -> str:
    parsed = urlsplit(url)
    hostname = (parsed.hostname or "").lower()
    netloc = hostname
    if parsed.port is not None:
        default_port = 443 if parsed.scheme == "https" else 80
        if parsed.port != default_port:
            netloc = f"{netloc}:{parsed.port}"
    path = parsed.path or "/"
    return urlunsplit((parsed.scheme.lower(), netloc, path, parsed.query, ""))


def _skip_reason(candidate_url: str, start_origin: tuple[str, str, int]) -> str | None:
    parsed = urlsplit(candidate_url)
    if parsed.scheme not in {"http", "https"}:
        return "unsupported_scheme"
    if not is_same_origin(candidate_url, start_origin):
        return "external_origin"
    lowered = f"{parsed.path}?{parsed.query}".lower()
    if parsed.path.lower().endswith(SKIPPED_EXTENSIONS):
        return "non_text_asset"
    if any(keyword in lowered for keyword in EXCLUDED_KEYWORDS):
        return "excluded_low_value_link"
    return None


def _link_score(url: str, text: str) -> tuple[int, str]:
    haystack = f"{url} {text}".lower()
    for index, keyword in enumerate(PRIORITY_KEYWORDS):
        if keyword in haystack:
            return (100 - index, f"keyword:{keyword}")
    return (1, "internal_link")


def _selected_links(
    links: list[dict[str, str]],
    *,
    start_url: str,
    max_pages: int,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    start_origin = origin_for_url(start_url)
    start_key = _canonical_url(start_url)
    seen = {start_key}
    scored: list[tuple[int, str, str, str]] = []
    skipped: list[dict[str, str]] = []

    for link in links:
        raw_url = str(link.get("url") or "").strip()
        if not raw_url:
            continue
        if raw_url.startswith("#"):
            skipped.append({"url": start_url, "reason": "fragment_only"})
            continue
        try:
            canonical = _canonical_url(raw_url)
        except ValueError:
            skipped.append({"url": raw_url, "reason": "invalid_url"})
            continue
        if canonical in seen:
            skipped.append({"url": canonical, "reason": "duplicate"})
            continue
        reason = _skip_reason(canonical, start_origin)
        if reason:
            skipped.append({"url": canonical, "reason": reason})
            continue
        seen.add(canonical)
        score, selected_reason = _link_score(canonical, str(link.get("text") or ""))
        scored.append((score, canonical, selected_reason, str(link.get("text") or "")))

    scored.sort(key=lambda item: (-item[0], item[1]))
    selected = [
        {"url": url, "selected_reason": selected_reason, "link_text": text}
        for _score, url, selected_reason, text in scored[: max(0, max_pages - 1)]
    ]
    for _score, url, _selected_reason, _text in scored[max(0, max_pages - 1) :]:
        skipped.append({"url": url, "reason": "page_limit"})
    return selected, skipped[:50]


def _page_from_parsed(
    *,
    url: str,
    status_code: int,
    parsed: dict[str, Any],
    selected_reason: str,
    remaining_text_chars: int,
) -> dict[str, Any]:
    main_text = _compact_text(str(parsed.get("main_text") or ""))
    if len(main_text) > remaining_text_chars:
        main_text = main_text[: max(0, remaining_text_chars - 1)].rstrip() + "..."
    return {
        "url": url,
        "status_code": status_code,
        "title": parsed.get("title") or "",
        "description": parsed.get("description") or "",
        "h1": parsed.get("h1") or "",
        "main_text": main_text,
        "selected_reason": selected_reason,
    }


async def _fetch_context_page(
    url: str,
    *,
    selected_reason: str,
    timeout_seconds: float,
    body_limit: int,
    max_redirects: int,
    max_links: int,
    page_text_limit: int,
    allowed_origin: tuple[str, str, int] | None,
    remaining_text_chars: int,
) -> tuple[dict[str, Any] | None, list[dict[str, str]], str | None]:
    fetched = await fetch_with_safety(
        url,
        timeout_seconds=timeout_seconds,
        max_bytes=body_limit,
        max_redirects=max_redirects,
        allowed_origin=allowed_origin,
    )
    if not _content_type_is_text(fetched.headers):
        return None, [], "non_text_content_type"

    body = _decode_body(fetched.content, fetched.headers)
    parser = SiteOverviewParser(fetched.final_url, max_links=max_links)
    parser.feed(body)
    parsed = parser.result(main_text_limit=page_text_limit)
    return (
        _page_from_parsed(
            url=fetched.final_url,
            status_code=fetched.status_code,
            parsed=parsed,
            selected_reason=selected_reason,
            remaining_text_chars=remaining_text_chars,
        ),
        parsed.get("links") or [],
        None,
    )


async def fetch_site_context(url: str) -> dict[str, Any]:
    """Fetch bounded same-origin page context as untrusted evidence only."""

    started = time.perf_counter()
    max_pages = min(
        DEFAULT_CONTEXT_MAX_PAGES,
        max(1, _env_int("MCP_SITE_CONTEXT_MAX_PAGES", DEFAULT_CONTEXT_MAX_PAGES)),
    )
    total_text_limit = max(1, _env_int("MCP_SITE_CONTEXT_TEXT_LIMIT_CHARS", DEFAULT_CONTEXT_TEXT_LIMIT_CHARS))
    total_timeout = max(1.0, _env_float("MCP_SITE_CONTEXT_TIMEOUT_SECONDS", DEFAULT_CONTEXT_TIMEOUT_SECONDS))
    body_limit = _env_int("MCP_BODY_SIZE_LIMIT_BYTES", DEFAULT_BODY_SIZE_LIMIT_BYTES)
    max_redirects = _env_int("MCP_MAX_REDIRECTS", DEFAULT_MAX_REDIRECTS)
    page_text_limit = _env_int("MCP_MAIN_TEXT_LIMIT_CHARS", DEFAULT_PAGE_TEXT_LIMIT_CHARS)
    max_links = _env_int("MCP_MAX_LINKS", DEFAULT_CONTEXT_MAX_LINKS)

    pages: list[dict[str, Any]] = []
    skipped_links: list[dict[str, str]] = []

    try:
        remaining_timeout = max(1.0, total_timeout - (time.perf_counter() - started))
        start_page, links, skip_reason = await _fetch_context_page(
            url,
            selected_reason="start_url",
            timeout_seconds=remaining_timeout,
            body_limit=body_limit,
            max_redirects=max_redirects,
            max_links=max_links,
            page_text_limit=page_text_limit,
            allowed_origin=None,
            remaining_text_chars=total_text_limit,
        )
        if skip_reason:
            return {
                "success": False,
                "start_url": url,
                "page_count": 0,
                "pages": [],
                "skipped_links": [{"url": url, "reason": skip_reason}],
                "error_message": f"Start URL skipped: {skip_reason}",
                "fetched_at": _utc_now(),
            }
        if start_page is None:
            return {
                "success": False,
                "start_url": url,
                "page_count": 0,
                "pages": [],
                "skipped_links": [],
                "error_message": "Start URL did not return text or HTML evidence.",
                "fetched_at": _utc_now(),
            }

        pages.append(start_page)
        remaining_chars = max(0, total_text_limit - len(start_page.get("main_text") or ""))
        start_final_url = start_page["url"]
        start_origin = origin_for_url(start_final_url)
        selected_links, skipped = _selected_links(links, start_url=start_final_url, max_pages=max_pages)
        skipped_links.extend(skipped)

        for link in selected_links:
            if len(pages) >= max_pages or remaining_chars <= 0:
                break
            elapsed = time.perf_counter() - started
            remaining_timeout = total_timeout - elapsed
            if remaining_timeout <= 0:
                skipped_links.append({"url": link["url"], "reason": "timeout_budget_exhausted"})
                continue
            try:
                page, _child_links, skip_reason = await _fetch_context_page(
                    link["url"],
                    selected_reason=link["selected_reason"],
                    timeout_seconds=max(1.0, remaining_timeout),
                    body_limit=body_limit,
                    max_redirects=max_redirects,
                    max_links=0,
                    page_text_limit=min(page_text_limit, remaining_chars),
                    allowed_origin=start_origin,
                    remaining_text_chars=remaining_chars,
                )
                if page is None:
                    skipped_links.append({"url": link["url"], "reason": skip_reason or "not_fetchable"})
                    continue
                pages.append(page)
                remaining_chars = max(0, remaining_chars - len(page.get("main_text") or ""))
            except Exception as exc:
                skipped_links.append({"url": link["url"], "reason": str(exc)[:180]})

        return {
            "success": True,
            "start_url": url,
            "final_url": start_final_url,
            "page_count": len(pages),
            "pages": pages,
            "skipped_links": skipped_links[:50],
            "fetched_at": _utc_now(),
        }
    except SafetyError as exc:
        return {"success": False, "start_url": url, "error_message": str(exc), "fetched_at": _utc_now()}
    except Exception as exc:
        return {
            "success": False,
            "start_url": url,
            "error_message": f"{exc.__class__.__name__}: {exc}",
            "fetched_at": _utc_now(),
        }
