from __future__ import annotations

import os
import re
import time
from datetime import datetime, timezone
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urljoin, urlsplit

import httpx

from tools.safety import (
    DEFAULT_BODY_SIZE_LIMIT_BYTES,
    DEFAULT_MAX_REDIRECTS,
    DEFAULT_TIMEOUT_SECONDS,
    SafetyError,
    fetch_with_safety,
    validate_public_url,
)


DEFAULT_MAIN_TEXT_LIMIT_CHARS = 4_000
DEFAULT_MAX_LINKS = 20
DEPLOY_PROBE_TIMEOUT_SECONDS = 5.0

SKIPPED_TEXT_TAGS = {"script", "style", "noscript", "svg", "template"}


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


def _compact_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _limit_text(value: str | None, limit: int) -> str | None:
    if value is None:
        return None
    compacted = _compact_text(value)
    if len(compacted) <= limit:
        return compacted
    return compacted[: max(0, limit - 1)].rstrip() + "..."


def _decode_body(content: bytes, headers: dict[str, str]) -> str:
    content_type = headers.get("content-type", "")
    charset_match = re.search(r"charset=([^\s;]+)", content_type, flags=re.IGNORECASE)
    encoding = charset_match.group(1).strip("\"'") if charset_match else "utf-8"
    try:
        return content.decode(encoding, errors="replace")
    except LookupError:
        return content.decode("utf-8", errors="replace")


def _is_http_url(url: str) -> bool:
    return urlsplit(url).scheme in {"http", "https"}


class SiteOverviewParser(HTMLParser):
    """Extract bounded, plain-text evidence from an HTML document.

    Remote text is deliberately flattened into evidence fields. It is not an
    instruction channel, and callers must not execute or obey commands found in
    the page body.
    """

    def __init__(self, base_url: str, max_links: int) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.max_links = max_links
        self.title_parts: list[str] = []
        self.description: str | None = None
        self.h1_parts: list[str] = []
        self.text_parts: list[str] = []
        self.links: list[dict[str, str]] = []
        self._skip_depth = 0
        self._in_title = False
        self._capture_h1 = False
        self._h1_done = False
        self._current_link: dict[str, Any] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attrs_dict = {key.lower(): value for key, value in attrs if key}

        if tag in SKIPPED_TEXT_TAGS:
            self._skip_depth += 1
            return

        if self._skip_depth:
            return

        if tag == "title":
            self._in_title = True
        elif tag == "meta":
            name = (attrs_dict.get("name") or attrs_dict.get("property") or "").lower()
            content = attrs_dict.get("content")
            if content and name in {"description", "og:description"} and not self.description:
                self.description = content
        elif tag == "h1" and not self._h1_done:
            self._capture_h1 = True
        elif tag == "a" and len(self.links) < self.max_links and self._current_link is None:
            href = attrs_dict.get("href")
            if href:
                absolute_url = urljoin(self.base_url, href)
                if _is_http_url(absolute_url):
                    self._current_link = {"url": absolute_url, "text_parts": []}

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in SKIPPED_TEXT_TAGS and self._skip_depth:
            self._skip_depth -= 1
            return

        if self._skip_depth:
            return

        if tag == "title":
            self._in_title = False
        elif tag == "h1" and self._capture_h1:
            self._capture_h1 = False
            self._h1_done = True
        elif tag == "a" and self._current_link is not None:
            text = _compact_text(" ".join(self._current_link["text_parts"]))
            self.links.append({"url": self._current_link["url"], "text": text})
            self._current_link = None

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        if not data or not data.strip():
            return

        if self._in_title:
            self.title_parts.append(data)
        if self._capture_h1:
            self.h1_parts.append(data)
        if self._current_link is not None:
            self._current_link["text_parts"].append(data)
        self.text_parts.append(data)

    def result(self, *, main_text_limit: int) -> dict[str, Any]:
        return {
            "title": _limit_text(" ".join(self.title_parts), 180),
            "description": _limit_text(self.description, 300),
            "h1": _limit_text(" ".join(self.h1_parts), 180),
            "main_text": _limit_text(" ".join(self.text_parts), main_text_limit) or "",
            "links": self.links[: self.max_links],
        }


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


async def fetch_site_overview(url: str) -> dict[str, Any]:
    """Fetch a public site and return bounded, untrusted evidence fields only."""

    timeout_seconds = _env_float("MCP_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS)
    body_limit = _env_int("MCP_BODY_SIZE_LIMIT_BYTES", DEFAULT_BODY_SIZE_LIMIT_BYTES)
    max_redirects = _env_int("MCP_MAX_REDIRECTS", DEFAULT_MAX_REDIRECTS)
    main_text_limit = _env_int("MCP_MAIN_TEXT_LIMIT_CHARS", DEFAULT_MAIN_TEXT_LIMIT_CHARS)
    max_links = _env_int("MCP_MAX_LINKS", DEFAULT_MAX_LINKS)

    fetched = await fetch_with_safety(
        url,
        timeout_seconds=timeout_seconds,
        max_bytes=body_limit,
        max_redirects=max_redirects,
    )
    body = _decode_body(fetched.content, fetched.headers)
    parser = SiteOverviewParser(fetched.final_url, max_links=max_links)
    parser.feed(body)
    parsed = parser.result(main_text_limit=main_text_limit)

    return {
        "url": fetched.final_url,
        "status_code": fetched.status_code,
        "title": parsed["title"],
        "description": parsed["description"],
        "h1": parsed["h1"],
        "main_text": parsed["main_text"],
        "links": parsed["links"],
        "fetched_at": _utc_now(),
    }


async def check_deploy_status(url: str) -> dict[str, Any]:
    """Check whether a public deployment URL responds without reading its body."""

    timeout_seconds = _env_float("MCP_TIMEOUT_SECONDS", DEPLOY_PROBE_TIMEOUT_SECONDS)
    max_redirects = _env_int("MCP_MAX_REDIRECTS", DEFAULT_MAX_REDIRECTS)
    started = time.perf_counter()

    try:
        await validate_public_url(url)
        fetched = await fetch_with_safety(
            url,
            timeout_seconds=timeout_seconds,
            max_redirects=max_redirects,
            read_body=False,
        )
        return {
            "is_reachable": True,
            "status_code": fetched.status_code,
            "response_time_ms": fetched.response_time_ms,
            "final_url": fetched.final_url,
        }
    except SafetyError:
        raise
    except httpx.RequestError:
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return {
            "is_reachable": False,
            "status_code": None,
            "response_time_ms": elapsed_ms,
            "final_url": url,
        }
