from __future__ import annotations

import asyncio
import ipaddress
import socket
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin, urlsplit

import httpx


DEFAULT_TIMEOUT_SECONDS = 5.0
DEFAULT_BODY_SIZE_LIMIT_BYTES = 1_500_000
DEFAULT_MAX_REDIRECTS = 5
DEFAULT_USER_AGENT = "ProjectLens-MCP/0.1 (+local-private-site-evidence)"
Origin = tuple[str, str, int]

REDIRECT_STATUS_CODES = {301, 302, 303, 307, 308}
LOCALHOST_NAMES = {"localhost"}


class SafetyError(ValueError):
    """Raised when a URL violates the ProjectLens SSRF policy."""


class BodyTooLargeError(SafetyError):
    """Raised when a response body exceeds the configured evidence limit."""


@dataclass(frozen=True)
class FetchResult:
    requested_url: str
    final_url: str
    status_code: int
    headers: dict[str, str]
    content: bytes
    response_time_ms: int


def _port_for_url(parsed: Any) -> int:
    if parsed.port is not None:
        return parsed.port
    if parsed.scheme == "https":
        return 443
    return 80


def origin_for_url(url: str) -> Origin:
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise SafetyError("URL must include an http(s) origin.")
    return (parsed.scheme, _hostname_for_checks(parsed.hostname), _port_for_url(parsed))


def is_same_origin(url: str, origin: Origin) -> bool:
    try:
        return origin_for_url(url) == origin
    except (SafetyError, ValueError):
        return False


def _hostname_for_checks(hostname: str) -> str:
    return hostname.strip().rstrip(".").lower()


def _is_blocked_hostname(hostname: str) -> bool:
    normalized = _hostname_for_checks(hostname)
    return normalized in LOCALHOST_NAMES or normalized.endswith(".localhost")


def _is_blocked_ip(ip: ipaddress._BaseAddress) -> bool:
    return (
        ip.is_loopback
        or ip.is_private
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    )


async def resolve_host_ips(hostname: str, port: int) -> list[ipaddress._BaseAddress]:
    """Resolve a hostname and return unique IP addresses for safety checks."""

    def _resolve() -> list[ipaddress._BaseAddress]:
        infos = socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)
        addresses: list[ipaddress._BaseAddress] = []
        seen: set[str] = set()
        for info in infos:
            raw_ip = info[4][0]
            if raw_ip in seen:
                continue
            seen.add(raw_ip)
            addresses.append(ipaddress.ip_address(raw_ip))
        return addresses

    try:
        return await asyncio.to_thread(_resolve)
    except socket.gaierror as exc:
        raise SafetyError(f"Could not resolve hostname: {hostname}") from exc


async def validate_public_url(url: str) -> str:
    """Validate a URL before any request is made.

    The external document reached through this URL is untrusted evidence only. This
    function only decides whether the URL may be fetched; it never treats remote
    content as instructions.
    """

    if not isinstance(url, str) or not url.strip():
        raise SafetyError("URL is required.")

    parsed = urlsplit(url.strip())
    if parsed.scheme not in {"http", "https"}:
        raise SafetyError("Only http and https URLs are allowed.")
    if not parsed.hostname:
        raise SafetyError("URL must include a hostname.")
    if parsed.username or parsed.password:
        raise SafetyError("URLs with embedded credentials are not allowed.")

    hostname = parsed.hostname
    try:
        port = _port_for_url(parsed)
    except ValueError as exc:
        raise SafetyError("URL has an invalid port.") from exc

    if _is_blocked_hostname(hostname):
        raise SafetyError("Localhost URLs are blocked by the SSRF policy.")

    try:
        direct_ip = ipaddress.ip_address(hostname)
    except ValueError:
        direct_ip = None

    if direct_ip is not None:
        if _is_blocked_ip(direct_ip):
            raise SafetyError(f"Blocked internal or non-public IP address: {direct_ip}")
        return parsed.geturl()

    ascii_hostname = hostname.encode("idna").decode("ascii")
    resolved_ips = await resolve_host_ips(ascii_hostname, port)
    if not resolved_ips:
        raise SafetyError(f"Could not resolve hostname: {hostname}")

    blocked_ips = [ip for ip in resolved_ips if _is_blocked_ip(ip)]
    if blocked_ips:
        blocked = ", ".join(str(ip) for ip in blocked_ips)
        raise SafetyError(f"Blocked hostname resolving to internal or non-public IP: {blocked}")

    return parsed.geturl()


async def _read_limited(response: httpx.Response, max_bytes: int) -> bytes:
    chunks: list[bytes] = []
    total = 0
    async for chunk in response.aiter_bytes():
        total += len(chunk)
        if total > max_bytes:
            raise BodyTooLargeError(f"Response body exceeds limit of {max_bytes} bytes.")
        chunks.append(chunk)
    return b"".join(chunks)


async def fetch_with_safety(
    url: str,
    *,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    max_bytes: int = DEFAULT_BODY_SIZE_LIMIT_BYTES,
    max_redirects: int = DEFAULT_MAX_REDIRECTS,
    user_agent: str = DEFAULT_USER_AGENT,
    read_body: bool = True,
    transport: httpx.AsyncBaseTransport | None = None,
    allowed_origin: Origin | None = None,
) -> FetchResult:
    """Fetch one URL with ProjectLens SSRF protection and bounded body reads."""

    requested_url = await validate_public_url(url)
    if allowed_origin is not None and not is_same_origin(requested_url, allowed_origin):
        raise SafetyError("URL is outside the allowed origin.")
    current_url = requested_url
    started = time.perf_counter()

    timeout = httpx.Timeout(timeout_seconds)
    headers = {"User-Agent": user_agent, "Accept": "text/html, text/plain;q=0.9, */*;q=0.5"}
    async with httpx.AsyncClient(
        timeout=timeout,
        headers=headers,
        follow_redirects=False,
        transport=transport,
    ) as client:
        for _redirect_count in range(max_redirects + 1):
            await validate_public_url(current_url)
            if allowed_origin is not None and not is_same_origin(current_url, allowed_origin):
                raise SafetyError("URL is outside the allowed origin.")
            async with client.stream("GET", current_url) as response:
                status_code = response.status_code
                location = response.headers.get("location")
                if status_code in REDIRECT_STATUS_CODES and location:
                    next_url = urljoin(str(response.url), location)
                    current_url = await validate_public_url(next_url)
                    if allowed_origin is not None and not is_same_origin(current_url, allowed_origin):
                        raise SafetyError("Redirected URL is outside the allowed origin.")
                    continue

                content = await _read_limited(response, max_bytes) if read_body else b""
                final_url = await validate_public_url(str(response.url))
                if allowed_origin is not None and not is_same_origin(final_url, allowed_origin):
                    raise SafetyError("Final URL is outside the allowed origin.")
                elapsed_ms = int((time.perf_counter() - started) * 1000)
                return FetchResult(
                    requested_url=requested_url,
                    final_url=final_url,
                    status_code=status_code,
                    headers=dict(response.headers),
                    content=content,
                    response_time_ms=elapsed_ms,
                )

    raise SafetyError(f"Too many redirects. Maximum allowed redirects: {max_redirects}")
