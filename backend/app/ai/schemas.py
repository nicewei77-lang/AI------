from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


ReportStatus = Literal["completed", "need_more_info", "failed", "refused"]
EvidenceKind = Literal[
    "post_body",
    "mcp_site",
    "deploy_status",
    "github_readme",
    "site_context",
    "screenshot",
    "lighthouse",
    "inferred",
    "rag",
]
ConfidenceKind = Literal["confirmed", "inferred"]
Severity = Literal["low", "medium", "high"]
Priority = Literal["P0", "P1", "P2"]
RagRankingMode = Literal["cosine", "weighted"]


class ProjectLensBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ServiceUnderstanding(ProjectLensBaseModel):
    one_line_summary: str = Field(description="A short Korean summary suitable for a card title.")
    detailed_summary: str
    site_structure_summary: str = Field(
        default="",
        description="Visible website/page structure from evidence: title, h1, main text, links, navigation, or an honest note when thin.",
    )
    service_essence: str = Field(
        default="",
        description="The core service/product essence inferred from confirmed evidence plus explicit uncertainty.",
    )
    key_insight: str = Field(
        default="",
        description="The most useful product/portfolio insight for the builder, grounded in evidence.",
    )
    target_users: list[str] = Field(default_factory=list)
    core_features: list[str] = Field(default_factory=list)
    confirmed_facts: list[str] = Field(default_factory=list)
    inferred_facts: list[str] = Field(default_factory=list)
    auto_tags: list[str] = Field(default_factory=list)


class Strength(ProjectLensBaseModel):
    title: str
    reason: str
    evidence_kind: EvidenceKind
    based_on: EvidenceKind
    confidence: ConfidenceKind


class Weakness(ProjectLensBaseModel):
    title: str
    reason: str
    severity: Severity
    evidence_kind: EvidenceKind
    based_on: EvidenceKind
    confidence: ConfidenceKind


class ImprovementAction(ProjectLensBaseModel):
    priority: Priority
    action: str
    expected_effect: str
    based_on: EvidenceKind


class Diagnosis(ProjectLensBaseModel):
    strengths: list[Strength] = Field(default_factory=list)
    weaknesses: list[Weakness] = Field(default_factory=list)
    improvement_plan: list[ImprovementAction] = Field(default_factory=list)


class McpSource(ProjectLensBaseModel):
    tool_name: str
    evidence_kind: Literal[
        "mcp_site",
        "deploy_status",
        "github_readme",
        "site_context",
        "screenshot",
        "lighthouse",
    ]
    based_on: Literal[
        "mcp_site",
        "deploy_status",
        "github_readme",
        "site_context",
        "screenshot",
        "lighthouse",
    ]
    success: bool
    summary: str
    url: str | None = None
    status_code: int | None = None
    final_url: str | None = None
    error_message: str | None = None


class RagScoreBreakdown(ProjectLensBaseModel):
    semantic: float = 0.0
    tag_overlap: float = 0.0
    vote: float = 0.0
    recency: float = 0.0
    same_type: float = 0.0


class RagSource(ProjectLensBaseModel):
    title: str
    source_id: int | None = None
    similarity: float | None = None
    ranking_mode: RagRankingMode = "cosine"
    match_reasons: list[str] = Field(default_factory=list)
    score_breakdown: RagScoreBreakdown | None = None
    evidence_kind: Literal["rag"] = "rag"
    based_on: Literal["rag"] = "rag"
    summary: str | None = None


class EvidenceBlock(ProjectLensBaseModel):
    mcp_sources: list[McpSource] = Field(default_factory=list)
    rag_sources: list[RagSource] = Field(default_factory=list)


class ReportStatusBlock(ProjectLensBaseModel):
    status: ReportStatus
    missing_fields: list[str] = Field(default_factory=list)
    questions: list[str] = Field(default_factory=list)
    error: str | None = None


class PortfolioDraft(ProjectLensBaseModel):
    headline: str = ""
    problem: str = ""
    solution: str = ""
    impact: str = ""
    tech_highlights: list[str] = Field(default_factory=list)
    proof_points: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class PresentationDraft(ProjectLensBaseModel):
    opening: str = ""
    key_points: list[str] = Field(default_factory=list)
    demo_flow: list[str] = Field(default_factory=list)
    risks_or_next_steps: list[str] = Field(default_factory=list)
    closing: str = ""


class ProjectAnalysisReport(ProjectLensBaseModel):
    service_understanding: ServiceUnderstanding
    diagnosis: Diagnosis
    evidence: EvidenceBlock
    status: ReportStatusBlock
    portfolio: PortfolioDraft = Field(default_factory=PortfolioDraft)
    presentation: PresentationDraft = Field(default_factory=PresentationDraft)
