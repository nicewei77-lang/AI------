import type {ActionEffort, Diagnosis, EvidenceKind, Severity} from "../../types/analysis";

interface DiagnosisCardProps {
    diagnosis: Diagnosis;
}

const EVIDENCE_LABELS: Record<EvidenceKind, string> = {
    post_body: "게시글",
    mcp_site: "사이트",
    deploy_status: "배포 확인",
    github_readme: "GitHub README",
    site_context: "사이트 컨텍스트",
    rendered_site: "브라우저 렌더링",
    screenshot: "화면 캡처",
    lighthouse: "Lighthouse",
    inferred: "추정",
    rag: "RAG",
};

const SEVERITY_LABELS: Record<Severity, string> = {
    low: "낮음",
    medium: "중간",
    high: "높음",
};

const EFFORT_LABELS: Record<ActionEffort, string> = {
    low: "낮음",
    medium: "중간",
    high: "높음",
};

function EmptyLine({children}: {children: string}) {
    return <p className="py-2 text-sm text-stone-500">{children}</p>;
}

function EvidencePill({kind}: {kind: EvidenceKind}) {
    return (
        <span className="rounded-full bg-stone-100 px-2 py-0.5 text-xs font-semibold text-stone-600">
            {EVIDENCE_LABELS[kind]}
        </span>
    );
}

function EvidenceRefPill({refId}: {refId: string}) {
    return (
        <span className="rounded-full bg-indigo-50 px-2 py-0.5 text-xs font-semibold text-indigo-800">
            근거 {refId}
        </span>
    );
}

function DiagnosisCard({diagnosis}: DiagnosisCardProps) {
    return (
        <section className="rounded border border-stone-200 bg-white p-4">
            <h3 className="mb-4 text-base font-bold text-stone-950">AI 해석/리스크</h3>

            <div className="space-y-5">
                <div>
                    <h4 className="mb-2 text-sm font-bold text-stone-800">강점</h4>
                    {diagnosis.strengths.length === 0 ? (
                        <EmptyLine>아직 강점 진단 항목이 없습니다.</EmptyLine>
                    ) : (
                        <ul className="divide-y divide-stone-100">
                            {diagnosis.strengths.map((item) => (
                                <li key={`${item.title}-${item.evidence_kind}`} className="py-3">
                                    <div className="mb-1 flex flex-wrap items-center gap-2">
                                        <strong className="break-words text-sm text-stone-950">
                                            {item.title}
                                        </strong>
                                        <EvidencePill kind={item.evidence_kind} />
                                    </div>
                                    <p className="break-words text-sm leading-6 text-stone-700">
                                        {item.reason}
                                    </p>
                                </li>
                            ))}
                        </ul>
                    )}
                </div>

                <div>
                    <h4 className="mb-2 text-sm font-bold text-stone-800">리스크</h4>
                    {diagnosis.weaknesses.length === 0 ? (
                        <EmptyLine>아직 리스크 해석 항목이 없습니다.</EmptyLine>
                    ) : (
                        <ul className="divide-y divide-stone-100">
                            {diagnosis.weaknesses.map((item) => (
                                <li key={`${item.title}-${item.severity}`} className="py-3">
                                    <div className="mb-1 flex flex-wrap items-center gap-2">
                                        <strong className="break-words text-sm text-stone-950">
                                            {item.title}
                                        </strong>
                                        <span className="rounded-full bg-amber-50 px-2 py-0.5 text-xs font-semibold text-amber-800">
                                            {SEVERITY_LABELS[item.severity]}
                                        </span>
                                        <EvidencePill kind={item.evidence_kind} />
                                    </div>
                                    <p className="break-words text-sm leading-6 text-stone-700">
                                        {item.reason}
                                    </p>
                                </li>
                            ))}
                        </ul>
                    )}
                </div>

                <div>
                    <h4 className="mb-2 text-sm font-bold text-stone-800">우선 개선 액션</h4>
                    {diagnosis.improvement_plan.length === 0 ? (
                        <EmptyLine>아직 우선 개선 액션이 없습니다.</EmptyLine>
                    ) : (
                        <ol className="divide-y divide-stone-100">
                            {diagnosis.improvement_plan.map((item) => (
                                <li key={`${item.priority}-${item.action}`} className="py-3">
                                    <div className="mb-1 flex flex-wrap items-center gap-2">
                                        <span className="rounded-full bg-stone-900 px-2 py-0.5 text-xs font-bold text-white">
                                            {item.priority}
                                        </span>
                                        <strong className="break-words text-sm text-stone-950">
                                            {item.action}
                                        </strong>
                                        <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-semibold text-emerald-800">
                                            영향 {EFFORT_LABELS[item.impact ?? "medium"]}
                                        </span>
                                        <span className="rounded-full bg-sky-50 px-2 py-0.5 text-xs font-semibold text-sky-800">
                                            난이도 {EFFORT_LABELS[item.difficulty ?? "medium"]}
                                        </span>
                                    </div>
                                    <p className="break-words text-sm leading-6 text-stone-700">
                                        {item.expected_effect}
                                    </p>
                                    {(item.evidence_refs ?? [item.based_on]).length > 0 ? (
                                        <div className="mt-2 flex flex-wrap gap-2">
                                            {(item.evidence_refs?.length ? item.evidence_refs : [item.based_on]).map((refId) => (
                                                <EvidenceRefPill key={`${item.action}-${refId}`} refId={refId} />
                                            ))}
                                        </div>
                                    ) : null}
                                </li>
                            ))}
                        </ol>
                    )}
                </div>
            </div>
        </section>
    );
}

export default DiagnosisCard;
