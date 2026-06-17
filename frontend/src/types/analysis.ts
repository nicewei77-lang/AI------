import type {AnalysisStatus} from "./post";

export type ReportStatus = "completed" | "need_more_info" | "failed" | "refused";
export type AnalysisBadgeStatus = AnalysisStatus | ReportStatus;
export type EvidenceKind =
    | "post_body"
    | "mcp_site"
    | "deploy_status"
    | "github_readme"
    | "site_context"
    | "rendered_site"
    | "screenshot"
    | "lighthouse"
    | "inferred"
    | "rag";
export type ConfidenceKind = "confirmed" | "inferred";
export type Severity = "low" | "medium" | "high";
export type Priority = "P0" | "P1" | "P2";
export type RagRankingMode = "cosine" | "weighted";
export type ActionEffort = "low" | "medium" | "high";
export type AnalysisConfidenceLevel = "low" | "medium" | "high";

export interface ServiceUnderstanding {
    one_line_summary: string;
    detailed_summary: string;
    site_structure_summary: string;
    service_essence: string;
    key_insight: string;
    target_users: string[];
    core_features: string[];
    confirmed_facts: string[];
    inferred_facts: string[];
    auto_tags: string[];
}

export interface Strength {
    title: string;
    reason: string;
    evidence_kind: EvidenceKind;
    based_on: EvidenceKind;
    confidence: ConfidenceKind;
}

export interface Weakness {
    title: string;
    reason: string;
    severity: Severity;
    evidence_kind: EvidenceKind;
    based_on: EvidenceKind;
    confidence: ConfidenceKind;
}

export interface ImprovementAction {
    priority: Priority;
    action: string;
    expected_effect: string;
    based_on: EvidenceKind;
    impact: ActionEffort;
    difficulty: ActionEffort;
    evidence_refs: string[];
}

export interface Diagnosis {
    strengths: Strength[];
    weaknesses: Weakness[];
    improvement_plan: ImprovementAction[];
}

export interface McpSource {
    tool_name: string;
    evidence_kind: "mcp_site" | "deploy_status" | "github_readme" | "site_context" | "rendered_site" | "screenshot" | "lighthouse";
    based_on: "mcp_site" | "deploy_status" | "github_readme" | "site_context" | "rendered_site" | "screenshot" | "lighthouse";
    success: boolean;
    summary: string;
    url?: string | null;
    status_code?: number | null;
    final_url?: string | null;
    error_message?: string | null;
}

export interface RagSource {
    title: string;
    source_id?: number | null;
    similarity?: number | null;
    ranking_mode: RagRankingMode;
    match_reasons: string[];
    score_breakdown?: RagScoreBreakdown | null;
    evidence_kind: "rag";
    based_on: "rag";
    summary?: string | null;
}

export interface RagScoreBreakdown {
    semantic: number;
    tag_overlap: number;
    vote: number;
    recency: number;
    same_type: number;
}

export interface EvidenceFinding {
    id: string;
    kind: EvidenceKind;
    title: string;
    observed: string;
    source: string;
}

export interface EvidenceBlock {
    mcp_sources: McpSource[];
    rag_sources: RagSource[];
    findings: EvidenceFinding[];
}

export interface AnalysisConfidence {
    level: AnalysisConfidenceLevel;
    reasons: string[];
}

export interface ReviewSummary {
    one_line_review: string;
    strongest_signals: string[];
    main_risks: string[];
    priority_actions: string[];
}

export interface ReportStatusBlock {
    status: ReportStatus;
    missing_fields: string[];
    questions: string[];
    error?: string | null;
}

export interface PortfolioDraft {
    headline: string;
    problem: string;
    solution: string;
    impact: string;
    tech_highlights: string[];
    proof_points: string[];
    limitations: string[];
}

export interface PresentationDraft {
    opening: string;
    key_points: string[];
    demo_flow: string[];
    risks_or_next_steps: string[];
    closing: string;
}

export interface EvidenceLinkedText {
    text: string;
    source_finding_ids: string[];
}

export interface PresentationFlowTranslation {
    steps: string[];
    source_finding_ids: string[];
}

export interface ExpectedQuestion {
    question: string;
    why_this_question: string;
    source_finding_ids: string[];
}

export interface PortfolioTranslation {
    portfolio_sentence: EvidenceLinkedText;
    presentation_flow: PresentationFlowTranslation;
    expected_questions: ExpectedQuestion[];
}

export interface AnalysisLimitations {
    seen: string[];
    not_seen: string[];
    disclaimers: string[];
}

export interface ProjectAnalysisReport {
    report_version: string;
    summary: ReviewSummary;
    service_understanding: ServiceUnderstanding;
    diagnosis: Diagnosis;
    evidence: EvidenceBlock;
    status: ReportStatusBlock;
    portfolio: PortfolioDraft;
    presentation: PresentationDraft;
    analysis_confidence: AnalysisConfidence;
    portfolio_translation: PortfolioTranslation;
    limitations: AnalysisLimitations;
}

export interface AnalysisRunResponse {
    status: ReportStatus;
    reportId: number;
    report: ProjectAnalysisReport;
    error?: Record<string, unknown> | null;
}

export interface AnalysisLatestResponse extends AnalysisRunResponse {
    createdAt?: string | null;
    model?: string | null;
    reasoningEffort?: string | null;
    responseId?: string | null;
    traceId?: string | null;
    usage?: Record<string, unknown> | null;
}

export type AnalysisResponse = AnalysisRunResponse | AnalysisLatestResponse;

export interface AnalysisJobResponse {
    postId: number;
    status: AnalysisStatus;
    latestReportId?: number | null;
    latestReportStatus?: ReportStatus | null;
    message?: string | null;
}
