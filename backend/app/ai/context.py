from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CollectedMcpEvidence:
    tool_name: str
    arguments: dict[str, Any]
    result: Any
    success: bool
    error_message: str | None = None


@dataclass
class AnalysisToolContext:
    post_id: int
    service_url: str | None = None
    github_url: str | None = None
    mcp_evidence: list[CollectedMcpEvidence] = field(default_factory=list)

