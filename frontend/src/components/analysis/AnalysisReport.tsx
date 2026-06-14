import type {
    AnalysisBadgeStatus,
    AnalysisLatestResponse,
    AnalysisResponse,
    McpSource,
    ReportStatus,
} from "../../types/analysis";
import AnalysisStatusBadge from "./AnalysisStatusBadge";
import DiagnosisCard from "./DiagnosisCard";
import ServiceUnderstandingCard from "./ServiceUnderstandingCard";

interface AnalysisReportProps {
    analysis: AnalysisResponse | null;
    postStatus: AnalysisBadgeStatus;
    isLoading: boolean;
    isRunning: boolean;
    error: string | null;
    onRun: () => void;
}

const REPORT_STATUS_COPY: Record<ReportStatus, {title: string; body: string}> = {
    completed: {
        title: "분석 완료",
        body: "서비스 이해와 진단 결과를 카드로 정리했습니다.",
    },
    need_more_info: {
        title: "정보가 더 필요합니다",
        body: "AI가 진단을 만들기 전에 보강해야 할 입력이 있습니다.",
    },
    failed: {
        title: "분석을 완료하지 못했습니다",
        body: "사이트 수집 또는 모델 실행 중 문제가 생겼습니다.",
    },
    refused: {
        title: "분석이 거절되었습니다",
        body: "모델 안전 정책상 이 입력에 대한 분석을 제공하지 못했습니다.",
    },
};

function hasLatestMetadata(analysis: AnalysisResponse): analysis is AnalysisLatestResponse {
    return "createdAt" in analysis;
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
                <p className="mb-3 break-words rounded border border-red-100 bg-red-50 p-3 text-sm text-red-700">
                    {status.error}
                </p>
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
    return (
        <li className="py-3">
            <div className="mb-1 flex flex-wrap items-center gap-2">
                <strong className="break-words text-sm text-stone-950">{source.tool_name}</strong>
                <span
                    className={`rounded-full px-2 py-0.5 text-xs font-semibold ${
                        source.success
                            ? "bg-emerald-50 text-emerald-800"
                            : "bg-red-50 text-red-700"
                    }`}
                >
                    {source.success ? "성공" : "실패"}
                </span>
                {source.status_code ? (
                    <span className="rounded-full bg-stone-100 px-2 py-0.5 text-xs font-semibold text-stone-600">
                        HTTP {source.status_code}
                    </span>
                ) : null}
            </div>
            <p className="break-words text-sm leading-6 text-stone-700">{source.summary}</p>
            {source.url || source.final_url ? (
                <p className="mt-1 break-all text-xs text-stone-500">
                    {source.final_url ?? source.url}
                </p>
            ) : null}
            {source.error_message ? (
                <p className="mt-2 break-words text-xs text-red-700">{source.error_message}</p>
            ) : null}
        </li>
    );
}

function EvidenceCard({analysis}: {analysis: AnalysisResponse}) {
    const mcpSources = analysis.report.evidence.mcp_sources;
    const ragSources = analysis.report.evidence.rag_sources;

    return (
        <section className="rounded border border-stone-200 bg-white p-4">
            <h3 className="mb-3 text-base font-bold text-stone-950">근거</h3>
            {mcpSources.length === 0 && ragSources.length === 0 ? (
                <p className="text-sm text-stone-500">저장된 근거 데이터가 없습니다.</p>
            ) : null}
            {mcpSources.length > 0 ? (
                <div>
                    <h4 className="mb-1 text-xs font-bold uppercase tracking-wide text-stone-500">
                        MCP 수집
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
                        RAG 근거
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
    postStatus,
    isLoading,
    isRunning,
    error,
    onRun,
}: AnalysisReportProps) {
    const disabled = isLoading || isRunning;
    const visibleStatus: AnalysisBadgeStatus = isRunning ? "running" : analysis?.status ?? postStatus;

    return (
        <section className="space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="min-w-0">
                    <h2 className="text-lg font-bold text-stone-950">AI 진단 리포트</h2>
                    <div className="mt-1">
                        <AnalysisStatusBadge status={visibleStatus} />
                    </div>
                </div>
                <RunButton disabled={disabled} isRunning={isRunning} onRun={onRun} />
            </div>

            {isLoading ? (
                <section className="rounded border border-stone-200 bg-white p-4 text-sm text-stone-600">
                    최신 리포트를 확인하는 중...
                </section>
            ) : null}

            {error ? (
                <section className="rounded border border-red-200 bg-red-50 p-4 text-sm text-red-700">
                    {error}
                </section>
            ) : null}

            {!isLoading && !analysis ? (
                <section className="rounded border border-stone-200 bg-white p-4">
                    <p className="text-sm leading-6 text-stone-600">
                        아직 저장된 AI 진단 리포트가 없습니다. 배포 URL과 프로젝트 설명을 기준으로
                        첫 분석을 실행할 수 있습니다.
                    </p>
                </section>
            ) : null}

            {analysis ? (
                <>
                    <StatusCard analysis={analysis} />
                    <ServiceUnderstandingCard service={analysis.report.service_understanding} />
                    <DiagnosisCard diagnosis={analysis.report.diagnosis} />
                    <EvidenceCard analysis={analysis} />
                </>
            ) : null}
        </section>
    );
}

export default AnalysisReport;
