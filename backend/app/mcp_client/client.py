from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from agents.mcp import MCPServerStdio
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.mcp_client.tools import ensure_allowed_tool, projectlens_tool_filter
from app.models import McpEvidence


SENSITIVE_KEY_HINTS = ("key", "token", "secret", "password", "authorization", "cookie")
MAX_LOG_STRING_LENGTH = 12_000


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _mcp_server_dir() -> Path:
    return _project_root() / "mcp-server"


def _mcp_server_script() -> Path:
    return _mcp_server_dir() / "server.py"


def _mcp_env() -> dict[str, str]:
    env = {
        "PYTHONUNBUFFERED": "1",
        "MCP_TIMEOUT_SECONDS": str(settings.mcp_request_timeout_seconds),
        "MCP_BODY_SIZE_LIMIT_BYTES": str(settings.mcp_body_size_limit_bytes),
        "MCP_MAIN_TEXT_LIMIT_CHARS": str(settings.mcp_main_text_limit_chars),
        "MCP_MAX_LINKS": str(settings.mcp_max_links),
        "MCP_MAX_REDIRECTS": str(settings.mcp_max_redirects),
    }
    if os.environ.get("PATH"):
        env["PATH"] = os.environ["PATH"]
    if os.environ.get("VIRTUAL_ENV"):
        env["VIRTUAL_ENV"] = os.environ["VIRTUAL_ENV"]
    return env


def create_projectlens_mcp_server() -> MCPServerStdio:
    command = settings.mcp_server_command or sys.executable
    return MCPServerStdio(
        params={
            "command": command,
            "args": [str(_mcp_server_script())],
            "cwd": _mcp_server_dir(),
            "env": _mcp_env(),
        },
        name="projectlens-local-private-mcp",
        cache_tools_list=True,
        client_session_timeout_seconds=settings.mcp_request_timeout_seconds + 2,
        tool_filter=projectlens_tool_filter(),
        require_approval="never",
        use_structured_content=True,
    )


def get_projectlens_mcp_servers() -> list[MCPServerStdio]:
    """Return local/private MCP servers for an Agents SDK Agent."""

    return [create_projectlens_mcp_server()]


def _is_sensitive_key(key: str) -> bool:
    lowered = key.lower()
    return any(hint in lowered for hint in SENSITIVE_KEY_HINTS)


def _redact_url(value: str) -> str:
    try:
        parsed = urlsplit(value)
    except ValueError:
        return value
    if parsed.scheme not in {"http", "https"}:
        return value

    netloc = parsed.hostname or ""
    try:
        port = parsed.port
    except ValueError:
        port = None
    if port:
        netloc = f"{netloc}:{port}"

    query = [
        (key, "[REDACTED]" if _is_sensitive_key(key) else val)
        for key, val in parse_qsl(parsed.query, keep_blank_values=True)
    ]
    return urlunsplit((parsed.scheme, netloc, parsed.path, urlencode(query), ""))


def _truncate_log_string(value: str) -> str:
    if len(value) <= MAX_LOG_STRING_LENGTH:
        return value
    return value[: MAX_LOG_STRING_LENGTH - 15].rstrip() + "...[truncated]"


def _scrub_for_log(value: Any, *, key: str | None = None) -> Any:
    if key is not None and _is_sensitive_key(key):
        return "[REDACTED]"
    if isinstance(value, dict):
        return {
            item_key: _scrub_for_log(item_value, key=item_key)
            for item_key, item_value in value.items()
        }
    if isinstance(value, list):
        return [_scrub_for_log(item) for item in value]
    if isinstance(value, str):
        scrubbed = _redact_url(value) if key == "url" else value
        return _truncate_log_string(scrubbed)
    return value


def _decode_tool_result(result: Any) -> dict[str, Any] | list[Any] | str | None:
    structured = getattr(result, "structuredContent", None)
    if structured is not None:
        return structured

    content = getattr(result, "content", None) or []
    texts = [item.text for item in content if getattr(item, "type", None) == "text"]
    if not texts:
        return None
    if len(texts) == 1:
        try:
            return json.loads(texts[0])
        except json.JSONDecodeError:
            return texts[0]
    return {"content": texts}


async def record_mcp_evidence(
    db: AsyncSession,
    *,
    tool_name: str,
    arguments: dict[str, Any],
    result: Any = None,
    success: bool,
    error_message: str | None = None,
    post_id: int | None = None,
    report_id: int | None = None,
) -> McpEvidence:
    evidence = McpEvidence(
        post_id=post_id,
        report_id=report_id,
        tool_name=tool_name,
        arguments=_scrub_for_log(arguments),
        result=_scrub_for_log(result),
        success=success,
        error_message=_truncate_log_string(error_message) if error_message else None,
    )
    db.add(evidence)
    await db.flush()
    return evidence


async def call_mcp_tool(
    tool_name: str,
    arguments: dict[str, Any],
    *,
    db: AsyncSession | None = None,
    post_id: int | None = None,
    report_id: int | None = None,
    commit: bool = False,
) -> Any:
    ensure_allowed_tool(tool_name)

    server = create_projectlens_mcp_server()
    result_payload: Any = None
    error_message: str | None = None
    try:
        await server.connect()
        result = await server.call_tool(tool_name, arguments)
        result_payload = _decode_tool_result(result)

        if getattr(result, "isError", False):
            error_message = str(result_payload)
            if db is not None:
                await record_mcp_evidence(
                    db,
                    tool_name=tool_name,
                    arguments=arguments,
                    result=result_payload,
                    success=False,
                    error_message=error_message,
                    post_id=post_id,
                    report_id=report_id,
                )
                if commit:
                    await db.commit()
            raise RuntimeError(error_message)

        if db is not None:
            await record_mcp_evidence(
                db,
                tool_name=tool_name,
                arguments=arguments,
                result=result_payload,
                success=True,
                post_id=post_id,
                report_id=report_id,
            )
            if commit:
                await db.commit()
        return result_payload
    except Exception as exc:
        error_message = error_message or str(exc)
        if db is not None and result_payload is None:
            await record_mcp_evidence(
                db,
                tool_name=tool_name,
                arguments=arguments,
                result=None,
                success=False,
                error_message=error_message,
                post_id=post_id,
                report_id=report_id,
            )
            if commit:
                await db.commit()
        raise
    finally:
        await server.cleanup()
