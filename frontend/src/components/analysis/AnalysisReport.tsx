import {useState} from "react";
import type {
    AnalysisBadgeStatus,
    AnalysisConfidence,
    AnalysisLatestResponse,
    AnalysisResponse,
    EvidenceFinding,
    McpSource,
    ReportStatus,
} from "../../types/analysis";
import type {Post} from "../../types/post";
import AnalysisStatusBadge from "./AnalysisStatusBadge";
import DiagnosisCard from "./DiagnosisCard";
import ImprovementPromptCard from "./ImprovementPromptCard";
import ReviewSummaryCard from "./ReviewSummaryCard";
import ServiceUnderstandingCard from "./ServiceUnderstandingCard";
import SimilarProjectsCard from "./SimilarProjectsCard";

interface AnalysisReportProps {
    analysis: AnalysisResponse | null;
    post: Post;
    postStatus: AnalysisBadgeStatus;
    isLoading: boolean;
    isRunning: boolean;
    error: string | null;
    onRun: () => void;
}

const REPORT_TOC_ITEMS = [
    {id: "report-evidence", label: "확인된 근거"},
    {id: "report-status", label: "리뷰 상태"},
    {id: "report-summary", label: "요약"},
    {id: "report-service", label: "서비스 이해"},
    {id: "report-diagnosis", label: "AI 해석/리스크"},
    {id: "report-improvement-prompt", label: "개선 프롬프트"},
    {id: "report-similar", label: "유사 프로젝트"},
];

const REPORT_STATUS_COPY: Record<ReportStatus, {title: string; body: string}> = {
    completed: {
        title: "리뷰 완료",
        body: "공개 근거, AI 해석, 개선 액션, 한계를 카드로 정리했습니다.",
    },
    need_more_info: {
        title: "근거 보강 필요",
        body: "AI가 리뷰를 완성하기 전에 더 확인해야 할 입력이 있습니다.",
    },
    failed: {
        title: "분석 범위 한계",
        body: "이번 실행에서 확인하지 못한 공개 근거가 있어 한계를 먼저 표시합니다.",
    },
    refused: {
        title: "분석 제공 불가",
        body: "모델 안전 정책상 이 입력은 프로젝트 리뷰로 해석하지 않았습니다.",
    },
};

function hasLatestMetadata(analysis: AnalysisResponse): analysis is AnalysisLatestResponse {
    return "createdAt" in analysis;
}

const MCP_TOOL_LABELS: Record<string, string> = {
    fetch_site_overview: "사이트 개요",
    check_deploy_status: "배포 상태",
    fetch_github_readme: "GitHub README",
    fetch_site_context: "사이트 컨텍스트",
    fetch_rendered_site_overview: "브라우저 렌더링",
    capture_screenshot: "화면 캡처",
    run_lighthouse_summary: "Lighthouse summary",
};

const EVIDENCE_KIND_LABELS: Record<string, string> = {
    post_body: "게시글",
    mcp_site: "사이트",
    deploy_status: "배포 확인",
    github_readme: "GitHub README",
    site_context: "사이트 컨텍스트",
    rendered_site: "브라우저 렌더링",
    screenshot: "화면 캡처",
    lighthouse: "Lighthouse",
    inferred: "AI 해석",
    rag: "유사 프로젝트",
};

const CONFIDENCE_LABELS: Record<AnalysisConfidence["level"], {label: string; className: string}> = {
    low: {label: "낮음", className: "bg-amber-50 text-amber-800"},
    medium: {label: "중간", className: "bg-sky-50 text-sky-800"},
    high: {label: "높음", className: "bg-emerald-50 text-emerald-800"},
};

function mcpToolLabel(toolName: string) {
    return MCP_TOOL_LABELS[toolName] ?? toolName;
}

function RunButton({disabled, isRunning, onRun}: {disabled: boolean; isRunning: boolean; onRun: () => void}) {
    return (
        <button
            type="button"
            onClick={onRun}
            disabled={disabled}
            className="rounded bg-stone-900 px-4 py-2 text-sm font-semibold text-white hover:bg-stone-700 disabled:cursor-not-allowed disabled:bg-stone-300"
        >
            {isRunning ? "분석 중..." : "AI 분석 실행"}
        </button>
    );
}

function ReportToc() {
    return (
        <aside className="lg:sticky lg:top-4">
            <nav
                aria-label="보고서 목차"
                className="rounded border border-stone-200 bg-white p-3"
            >
                <h3 className="mb-2 text-sm font-bold text-stone-950">보고서 목차</h3>
                <div className="space-y-1">
                    {REPORT_TOC_ITEMS.map((item) => (
                        <a
                            key={item.id}
                            href={`#${item.id}`}
                            className="block rounded px-2 py-1 text-sm font-semibold text-stone-700 hover:bg-stone-100"
                        >
                            {item.label}
                        </a>
                    ))}
                </div>
            </nav>
        </aside>
    );
}

function StatusCard({analysis}: {analysis: AnalysisResponse}) {
    const status = analysis.report.status;
    const copy = REPORT_STATUS_COPY[status.status];
    const createdAt = hasLatestMetadata(analysis) && analysis.createdAt
        ? new Date(analysis.createdAt).toLocaleString()
        : null;

    return (
        <section className="rounded border border-stone-200 bg-white p-4">
            <div className="mb-3 flex flex-wrap items-start justify-between gap-2">
                <div>
                    <h3 className="text-base font-bold text-stone-950">{copy.title}</h3>
                    <p className="mt-1 text-sm text-stone-600">{copy.body}</p>
                </div>
                <AnalysisStatusBadge status={status.status} size="md" />
            </div>

            {status.missing_fields.length > 0 ? (
                <div className="mb-3">
                    <h4 className="mb-2 text-xs font-bold uppercase tracking-wide text-stone-500">
                        필요한 정보
                    </h4>
                    <div className="flex flex-wrap gap-2">
                        {status.missing_fields.map((field) => (
                            <span
                                key={field}
                                className="rounded-full bg-amber-50 px-2 py-1 text-xs font-semibold text-amber-800"
                            >
                                {field}
                            </span>
                        ))}
                    </div>
                </div>
            ) : null}

            {status.questions.length > 0 ? (
                <div className="mb-3">
                    <h4 className="mb-2 text-xs font-bold uppercase tracking-wide text-stone-500">
                        보강 질문
                    </h4>
                    <ul className="space-y-1 text-sm leading-6 text-stone-700">
                        {status.questions.map((question) => (
                            <li key={question} className="break-words">
                                {question}
                            </li>
                        ))}
                    </ul>
                </div>
            ) : null}

            {status.error ? (
                <div className="mb-3 rounded border border-amber-100 bg-amber-50 p-3">
                    <h4 className="mb-1 text-xs font-bold uppercase tracking-wide text-amber-800">
                        분석 범위 메모
                    </h4>
                    <p className="break-words text-sm leading-6 text-amber-900">
                        {status.error}
                    </p>
                </div>
            ) : null}

            <dl className="grid gap-2 text-xs text-stone-500 sm:grid-cols-2">
                <div>
                    <dt className="font-semibold">리포트 ID</dt>
                    <dd>{analysis.reportId}</dd>
                </div>
                {createdAt ? (
                    <div>
                        <dt className="font-semibold">생성 시각</dt>
                        <dd>{createdAt}</dd>
                    </div>
                ) : null}
                {hasLatestMetadata(analysis) && analysis.model ? (
                    <div>
                        <dt className="font-semibold">모델</dt>
                        <dd className="break-words">{analysis.model}</dd>
                    </div>
                ) : null}
                {hasLatestMetadata(analysis) && analysis.reasoningEffort ? (
                    <div>
                        <dt className="font-semibold">추론 강도</dt>
                        <dd>{analysis.reasoningEffort}</dd>
                    </div>
                ) : null}
            </dl>
        </section>
    );
}

function EvidenceSource({source}: {source: McpSource}) {
    const renderedSiteBlocked = source.tool_name === "fetch_rendered_site_overview"
        && source.success
        && ((source.status_code ?? 0) >= 400 || source.summary.includes("차단"));
    const state = evidenceState(source, renderedSiteBlocked);

    return (
        <li className="py-3">
            <div className="mb-1 flex flex-wrap items-center gap-2">
                <strong className="break-words text-sm text-stone-950">{mcpToolLabel(source.tool_name)}</strong>
                <span
                    className={`rounded-full px-2 py-0.5 text-xs font-semibold ${state.className}`}
                >
                    {state.label}
                </span>
                {source.status_code ? (
                    <span className="rounded-full bg-stone-100 px-2 py-0.5 text-xs font-semibold text-stone-600">
                        HTTP {source.status_code}
                    </span>
                ) : null}
            </div>
            <p className="break-words text-sm leading-6 text-stone-700">{source.summary}</p>
            {renderedSiteBlocked ? (
                <p className="mt-2 break-words rounded border border-amber-100 bg-amber-50 p-2 text-xs text-amber-800">
                    사이트가 자동 수집을 제한했습니다. GitHub URL, 더 긴 설명, 또는 직접 제출한 화면/텍스트 근거가 필요합니다.
                </p>
            ) : null}
            {source.url || source.final_url ? (
                <p className="mt-1 break-all text-xs text-stone-500">
                    {source.final_url ?? source.url}
                </p>
            ) : null}
            {source.error_message ? (
                <p className="mt-2 break-words text-xs text-amber-800">{source.error_message}</p>
            ) : null}
        </li>
    );
}

function evidenceState(source: McpSource, renderedSiteBlocked: boolean) {
    if (renderedSiteBlocked) {
        return {label: "자동 수집 제한", className: "bg-amber-50 text-amber-800"};
    }
    if (!source.success) {
        if (source.tool_name === "run_lighthouse_summary") {
            return {label: "측정 불가", className: "bg-amber-50 text-amber-800"};
        }
        if (source.tool_name === "fetch_github_readme") {
            return {label: "근거 부족", className: "bg-amber-50 text-amber-800"};
        }
        return {label: "확인 제한", className: "bg-stone-100 text-stone-700"};
    }
    return {label: "확인됨", className: "bg-emerald-50 text-emerald-800"};
}

function ConfidenceSummary({confidence}: {confidence: AnalysisConfidence}) {
    const state = CONFIDENCE_LABELS[confidence.level] ?? CONFIDENCE_LABELS.low;
    const reasons = confidence.reasons.filter((reason) => reason.trim());

    return (
        <div className="mb-4 rounded border border-stone-200 bg-stone-50 p-3">
            <div className="mb-2 flex flex-wrap items-center gap-2">
                <h4 className="text-xs font-bold uppercase tracking-wide text-stone-500">
                    분석 신뢰도
                </h4>
                <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${state.className}`}>
                    {state.label}
                </span>
            </div>
            {reasons.length > 0 ? (
                <ul className="space-y-1 text-xs leading-5 text-stone-600">
                    {reasons.map((reason) => (
                        <li key={reason} className="break-words">
                            {reason}
                        </li>
                    ))}
                </ul>
            ) : (
                <p className="text-xs leading-5 text-stone-600">
                    공개 근거 범위가 제한적이라 낮은 신뢰도로 표시합니다.
                </p>
            )}
        </div>
    );
}

function EvidenceFindingItem({finding}: {finding: EvidenceFinding}) {
    return (
        <li className="rounded border border-stone-200 bg-white p-3">
            <div className="mb-1 flex flex-wrap items-center gap-2">
                <code className="rounded bg-stone-900 px-2 py-0.5 text-xs font-bold text-white">
                    {finding.id}
                </code>
                <span className="rounded-full bg-stone-100 px-2 py-0.5 text-xs font-semibold text-stone-600">
                    {EVIDENCE_KIND_LABELS[finding.kind] ?? finding.kind}
                </span>
                {finding.source ? (
                    <span className="break-all text-xs text-stone-500">{finding.source}</span>
                ) : null}
            </div>
            <strong className="break-words text-sm text-stone-950">{finding.title}</strong>
            <p className="mt-1 break-words text-sm leading-6 text-stone-700">
                {finding.observed}
            </p>
        </li>
    );
}

function EvidenceCard({analysis}: {analysis: AnalysisResponse}) {
    const mcpSources = analysis.report.evidence.mcp_sources;
    const ragSources = analysis.report.evidence.rag_sources;
    const findings = analysis.report.evidence.findings ?? [];
    const confidence = analysis.report.analysis_confidence ?? {level: "low" as const, reasons: []};

    return (
        <section className="rounded border border-stone-200 bg-white p-4">
            <h3 className="mb-3 text-base font-bold text-stone-950">확인된 근거</h3>
            <ConfidenceSummary confidence={confidence} />
            {mcpSources.length === 0 && ragSources.length === 0 && findings.length === 0 ? (
                <p className="text-sm text-stone-500">아직 저장된 공개 근거가 없습니다.</p>
            ) : null}
            {findings.length > 0 ? (
                <div className="mb-4">
                    <h4 className="mb-2 text-xs font-bold uppercase tracking-wide text-stone-500">
                        근거 ID
                    </h4>
                    <ul className="grid gap-2">
                        {findings.map((finding) => (
                            <EvidenceFindingItem key={finding.id} finding={finding} />
                        ))}
                    </ul>
                </div>
            ) : null}
            {mcpSources.length > 0 ? (
                <div>
                    <h4 className="mb-1 text-xs font-bold uppercase tracking-wide text-stone-500">
                        공개 표면 근거
                    </h4>
                    <ul className="divide-y divide-stone-100">
                        {mcpSources.map((source, index) => (
                            <EvidenceSource key={`${source.tool_name}-${index}`} source={source} />
                        ))}
                    </ul>
                </div>
            ) : null}
            {ragSources.length > 0 ? (
                <div className="mt-4">
                    <h4 className="mb-2 text-xs font-bold uppercase tracking-wide text-stone-500">
                        유사 프로젝트 근거
                    </h4>
                    <ul className="space-y-2 text-sm text-stone-700">
                        {ragSources.map((source) => (
                            <li key={`${source.source_id ?? source.title}-${source.title}`} className="break-words">
                                {source.title}
                            </li>
                        ))}
                    </ul>
                </div>
            ) : null}
        </section>
    );
}

function AnalysisReport({
    analysis,
    post,
    postStatus,
    isLoading,
    isRunning,
    error,
    onRun,
}: AnalysisReportProps) {
    const [isCollapsed, setIsCollapsed] = useState(false);
    const disabled = isLoading || isRunning;
    const visibleStatus: AnalysisBadgeStatus = isRunning ? "running" : analysis?.status ?? postStatus;

    return (
        <section className="space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="min-w-0">
                    <h2 className="text-lg font-bold text-stone-950">AI 프로젝트 리뷰 리포트</h2>
                    <div className="mt-1">
                        <AnalysisStatusBadge status={visibleStatus} />
                    </div>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                    <RunButton disabled={disabled} isRunning={isRunning} onRun={onRun} />
                    <button
                        type="button"
                        aria-expanded={!isCollapsed}
                        onClick={() => setIsCollapsed((prev) => !prev)}
                        className="rounded border border-stone-300 px-4 py-2 text-sm font-semibold text-stone-700 hover:bg-stone-100"
                    >
                        {isCollapsed ? "리포트 펼치기" : "리포트 접기"}
                    </button>
                </div>
            </div>

            {isCollapsed ? (
                <section className="rounded border border-stone-200 bg-white p-4">
                    <p className="text-sm leading-6 text-stone-600">
                        리포트가 접혀 있습니다.
                    </p>
                </section>
            ) : (
                <>
                    {isLoading ? (
                        <section className="rounded border border-stone-200 bg-white p-4 text-sm text-stone-600">
                            최신 리포트를 확인하는 중...
                        </section>
                    ) : null}

                    {error ? (
                        <section className="rounded border border-amber-200 bg-amber-50 p-4 text-sm leading-6 text-amber-900">
                            {error}
                        </section>
                    ) : null}

                    {!isLoading && !analysis ? (
                        <section className="rounded border border-stone-200 bg-white p-4">
                            <p className="text-sm leading-6 text-stone-600">
                                {isRunning
                                    ? "AI 프로젝트 리뷰 리포트를 생성하는 중입니다. 완료되면 이 영역에 결과가 표시됩니다."
                                    : "아직 저장된 AI 프로젝트 리뷰 리포트가 없습니다. 배포 URL과 프로젝트 설명을 기준으로 첫 리뷰를 실행할 수 있습니다."}
                            </p>
                        </section>
                    ) : null}

                    {analysis ? (
                        <div className="grid gap-4 lg:grid-cols-[minmax(14rem,18rem)_minmax(0,1fr)_minmax(11rem,14rem)] lg:items-start">
                            <aside
                                id="report-evidence"
                                className="scroll-mt-4 lg:sticky lg:top-4 lg:max-h-[80vh] lg:overflow-auto"
                            >
                                <EvidenceCard analysis={analysis} />
                            </aside>

                            <div className="space-y-3">
                                <div id="report-status" className="scroll-mt-4">
                                    <StatusCard analysis={analysis} />
                                </div>
                                <div id="report-summary" className="scroll-mt-4">
                                    <ReviewSummaryCard summary={analysis.report.summary} />
                                </div>
                                <div id="report-service" className="scroll-mt-4">
                                    <ServiceUnderstandingCard service={analysis.report.service_understanding} />
                                </div>
                                <div id="report-diagnosis" className="scroll-mt-4">
                                    <DiagnosisCard diagnosis={analysis.report.diagnosis} />
                                </div>
                                <div id="report-improvement-prompt" className="scroll-mt-4">
                                    <ImprovementPromptCard post={post} analysis={analysis} />
                                </div>
                                <div id="report-similar" className="scroll-mt-4">
                                    <SimilarProjectsCard sources={analysis.report.evidence.rag_sources} />
                                </div>
                            </div>

                            <ReportToc />
                        </div>
                    ) : null}
                </>
            )}
        </section>
    );
}

export default AnalysisReport;
