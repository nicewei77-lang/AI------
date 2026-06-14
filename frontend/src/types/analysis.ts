import type {AnalysisStatus} from "./post";

export type ReportStatus = "completed" | "need_more_info" | "failed" | "refused";
export type AnalysisBadgeStatus = AnalysisStatus | ReportStatus;
export type EvidenceKind = "post_body" | "mcp_site" | "deploy_status" | "inferred" | "rag";
export type ConfidenceKind = "confirmed" | "inferred";
export type Severity = "low" | "medium" | "high";
export type Priority = "P0" | "P1" | "P2";

export interface ServiceUnderstanding {
    one_line_summary: string;
    detailed_summary: string;
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
}

export interface Diagnosis {
    strengths: Strength[];
    weaknesses: Weakness[];
    improvement_plan: ImprovementAction[];
}

export interface McpSource {
    tool_name: string;
    evidence_kind: "mcp_site" | "deploy_status";
    based_on: "mcp_site" | "deploy_status";
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
    evidence_kind: "rag";
    based_on: "rag";
    summary?: string | null;
}

export interface EvidenceBlock {
    mcp_sources: McpSource[];
    rag_sources: RagSource[];
}

export interface ReportStatusBlock {
    status: ReportStatus;
    missing_fields: string[];
    questions: string[];
    error?: string | null;
}

export interface ProjectAnalysisReport {
    service_understanding: ServiceUnderstanding;
    diagnosis: Diagnosis;
    evidence: EvidenceBlock;
    status: ReportStatusBlock;
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
