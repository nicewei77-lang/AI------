from __future__ import annotations

import base64
import binascii
import os
import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlsplit

import httpx


OWNER_REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
DEFAULT_TIMEOUT_SECONDS = 5.0
DEFAULT_README_LIMIT_CHARS = 6_000
GITHUB_API_BASE = "https://api.github.com"


class GitHubUrlError(ValueError):
    pass


async def fetch_github_readme(github_url: str) -> dict[str, Any]:
    """Fetch bounded README evidence from GitHub REST API.

    The user supplied URL is never fetched directly. We parse owner/repo, then
    construct fixed api.github.com endpoints server-side.
    """

    try:
        owner, repo = parse_github_owner_repo(github_url)
    except GitHubUrlError as exc:
        return _failure(repo=None, status_code=None, error_message=str(exc))

    repo_full_name = f"{owner}/{repo}"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "ProjectLens-MCP/0.1 (+github-readme-evidence)",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    timeout = float(os.getenv("MCP_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS))
    readme_limit = _env_int("MCP_GITHUB_README_LIMIT_CHARS", DEFAULT_README_LIMIT_CHARS)

    async with httpx.AsyncClient(timeout=httpx.Timeout(timeout), headers=headers) as client:
        try:
            repo_response = await client.get(f"{GITHUB_API_BASE}/repos/{owner}/{repo}")
        except httpx.RequestError as exc:
            return _failure(repo=repo_full_name, status_code=None, error_message=str(exc))

        if repo_response.status_code >= 400:
            return _failure(
                repo=repo_full_name,
                status_code=repo_response.status_code,
                error_message=_github_error_message(repo_response, "GitHub repository is unavailable."),
            )

        repo_payload = repo_response.json()
        metadata = _repo_metadata(repo_full_name, repo_payload)

        try:
            readme_response = await client.get(f"{GITHUB_API_BASE}/repos/{owner}/{repo}/readme")
        except httpx.RequestError as exc:
            return {
                **metadata,
                "success": False,
                "status_code": None,
                "readme": "",
                "readme_path": None,
                "error_message": str(exc),
                "fetched_at": _utc_now(),
            }

        if readme_response.status_code >= 400:
            return {
                **metadata,
                "success": False,
                "status_code": readme_response.status_code,
                "readme": "",
                "readme_path": None,
                "error_message": _github_error_message(readme_response, "README is unavailable."),
                "fetched_at": _utc_now(),
            }

        readme_payload = readme_response.json()
        readme_text = _decode_readme(readme_payload)
        return {
            **metadata,
            "success": True,
            "status_code": readme_response.status_code,
            "readme": _limit_text(readme_text, readme_limit),
            "readme_path": readme_payload.get("path"),
            "error_message": None,
            "fetched_at": _utc_now(),
        }


def parse_github_owner_repo(github_url: str) -> tuple[str, str]:
    if not isinstance(github_url, str) or not github_url.strip():
        raise GitHubUrlError("GitHub URL is required.")

    parsed = urlsplit(github_url.strip())
    if parsed.scheme not in {"http", "https"}:
        raise GitHubUrlError("GitHub URL must use http or https.")
    hostname = (parsed.hostname or "").lower().rstrip(".")
    if hostname != "github.com":
        raise GitHubUrlError("Only github.com repository URLs are allowed.")

    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) < 2:
        raise GitHubUrlError("GitHub URL must include owner and repository.")

    owner = parts[0]
    repo = parts[1].removesuffix(".git")
    if not OWNER_REPO_RE.match(owner) or not OWNER_REPO_RE.match(repo):
        raise GitHubUrlError("GitHub owner or repository contains invalid characters.")
    return owner, repo


def _repo_metadata(repo_full_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "repo": repo_full_name,
        "html_url": payload.get("html_url"),
        "description": payload.get("description"),
        "stars": payload.get("stargazers_count"),
        "language": payload.get("language"),
        "topics": payload.get("topics") or [],
        "default_branch": payload.get("default_branch"),
    }


def _decode_readme(payload: dict[str, Any]) -> str:
    content = payload.get("content")
    encoding = payload.get("encoding")
    if not isinstance(content, str):
        return ""
    if encoding != "base64":
        return content
    compact = "".join(content.split())
    try:
        return base64.b64decode(compact).decode("utf-8", errors="replace")
    except (binascii.Error, ValueError):
        return ""


def _github_error_message(response: httpx.Response, fallback: str) -> str:
    try:
        payload = response.json()
    except ValueError:
        return fallback
    message = payload.get("message")
    return str(message) if message else fallback


def _failure(repo: str | None, status_code: int | None, error_message: str) -> dict[str, Any]:
    return {
        "success": False,
        "repo": repo,
        "status_code": status_code,
        "readme": "",
        "description": None,
        "stars": None,
        "language": None,
        "topics": [],
        "html_url": None,
        "error_message": error_message,
        "fetched_at": _utc_now(),
    }


def _limit_text(value: str, limit: int) -> str:
    compacted = re.sub(r"\s+", " ", value).strip()
    if len(compacted) <= limit:
        return compacted
    return compacted[: max(0, limit - 1)].rstrip() + "..."


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
