import {useMemo, useState} from "react";
import type {AnalysisResponse, ImprovementAction} from "../../types/analysis";
import type {Post} from "../../types/post";

interface ImprovementPromptCardProps {
    post: Post;
    analysis: AnalysisResponse;
}

type CopyState = "idle" | "copied" | "failed";

const PRIORITY_ORDER: Record<ImprovementAction["priority"], number> = {
    P0: 0,
    P1: 1,
    P2: 2,
};

function cleanText(value?: string | null) {
    return value?.trim() ?? "";
}

function truncateText(value: string, maxLength = 900) {
    const clean = cleanText(value).replace(/\s+/g, " ");
    if (clean.length <= maxLength) return clean;
    return `${clean.slice(0, maxLength).trim()}...`;
}

function section(title: string, lines: string[]) {
    const clean = lines.filter((line) => line.trim().length > 0);
    if (clean.length === 0) return "";
    return [`## ${title}`, ...clean].join("\n");
}

function labeledLine(label: string, value?: string | null) {
    const clean = cleanText(value);
    return clean ? `- ${label}: ${clean}` : "";
}

function listLines(items: string[]) {
    return items
        .map((item) => cleanText(item))
        .filter(Boolean)
        .map((item) => `- ${item}`);
}

function sortActions(actions: ImprovementAction[]) {
    return [...actions].sort((left, right) => {
        const priorityDiff = PRIORITY_ORDER[left.priority] - PRIORITY_ORDER[right.priority];
        if (priorityDiff !== 0) return priorityDiff;
        return left.action.localeCompare(right.action);
    });
}

function actionLines(actions: ImprovementAction[]) {
    const sorted = sortActions(actions);
    if (sorted.length === 0) {
        return ["- 저장된 우선 개선 액션이 없습니다. 먼저 리포트의 리스크와 한계를 확인해 작은 개선 후보를 제안하세요."];
    }

    return sorted.flatMap((item) => [
        `- [${item.priority}] ${item.action}`,
        `  - 기대 효과: ${item.expected_effect}`,
        `  - 영향도/난이도: ${item.impact}/${item.difficulty}`,
        item.evidence_refs.length > 0
            ? `  - 근거 ID: ${item.evidence_refs.join(", ")}`
            : `  - 근거 종류: ${item.based_on}`,
    ]);
}

function evidenceLines(analysis: AnalysisResponse) {
    const findings = analysis.report.evidence.findings ?? [];
    if (findings.length === 0) {
        return ["- 저장된 근거 ID가 없습니다. 리포트의 공개 근거 카드와 현재 코드를 직접 대조하세요."];
    }

    return findings.map((finding) => {
        const source = cleanText(finding.source);
        return `- ${finding.id}: ${finding.title} | 관찰: ${finding.observed}${source ? ` | 출처: ${source}` : ""}`;
    });
}

function limitationLines(analysis: AnalysisResponse) {
    const {limitations} = analysis.report;
    const seen = listLines(limitations.seen);
    const notSeen = listLines(limitations.not_seen);
    const disclaimers = listLines(limitations.disclaimers);

    return [
        seen.length > 0 ? "[확인한 범위]" : "",
        ...seen,
        notSeen.length > 0 ? "[확인하지 못한 범위]" : "",
        ...notSeen,
        disclaimers.length > 0 ? "[읽는 방법]" : "",
        ...disclaimers,
    ];
}

function buildPrompt(post: Post, analysis: AnalysisResponse) {
    const report = analysis.report;
    const contextLines = [
        labeledLine("프로젝트 제목", post.title),
        labeledLine("한 줄 설명", post.oneLiner),
        labeledLine("서비스 URL", post.serviceUrl),
        labeledLine("GitHub URL", post.githubUrl),
        labeledLine("타깃 사용자", post.targetUser),
        post.techStack.length > 0 ? `- 기술스택: ${post.techStack.join(", ")}` : "",
        labeledLine("AI 요약", post.aiSummary),
        labeledLine("게시글 본문 요약", truncateText(post.body)),
    ];

    return [
        "아래 ProjectLens AI 리뷰 리포트를 근거로 이 프로젝트를 최소 범위로 개선해줘.",
        "",
        section("작업 원칙", [
            "- 리포트에 없는 기능을 지어내지 말고, 현재 코드와 리포트 근거를 먼저 확인한다.",
            "- 새 API, 새 DB migration, 새 외부 도구는 사용자가 명시하지 않는 한 추가하지 않는다.",
            "- P0 -> P1 -> P2 순서로, 실제 코드에서 확인 가능한 개선만 작게 구현한다.",
            "- 공개 근거와 AI 해석을 구분하고, 분석 한계를 넘는 단정은 하지 않는다.",
        ]),
        section("프로젝트 컨텍스트", contextLines),
        section("리포트 요약", [
            labeledLine("한 줄 리뷰", report.summary.one_line_review),
            report.summary.strongest_signals.length > 0 ? "[강한 신호]" : "",
            ...listLines(report.summary.strongest_signals),
            report.summary.main_risks.length > 0 ? "[주요 리스크]" : "",
            ...listLines(report.summary.main_risks),
            report.summary.priority_actions.length > 0 ? "[요약된 우선 액션]" : "",
            ...listLines(report.summary.priority_actions),
        ]),
        section("실행할 개선 액션", actionLines(report.diagnosis.improvement_plan)),
        section("근거", evidenceLines(analysis)),
        section("분석 한계", limitationLines(analysis)),
        section("완료 기준", [
            "- 변경한 파일과 핵심 변경 내용을 요약한다.",
            "- 실행한 검증 명령과 결과를 적는다.",
            "- 구현하지 않은 항목과 남은 리스크를 분리해서 보고한다.",
        ]),
    ]
        .filter((part) => part.trim().length > 0)
        .join("\n\n");
}

function PromptCopyButton({text}: {text: string}) {
    const [state, setState] = useState<CopyState>("idle");

    async function handleCopy() {
        if (await copyToClipboard(text)) {
            setState("copied");
            window.setTimeout(() => setState("idle"), 1400);
            return;
        }
        setState("failed");
        window.setTimeout(() => setState("idle"), 1600);
    }

    const label = state === "copied" ? "복사됨" : state === "failed" ? "실패" : "프롬프트 복사";

    return (
        <button
            type="button"
            onClick={handleCopy}
            className="rounded border border-stone-300 px-3 py-2 text-sm font-semibold text-stone-700 hover:bg-stone-100"
        >
            {label}
        </button>
    );
}

function ImprovementPromptCard({post, analysis}: ImprovementPromptCardProps) {
    const promptText = useMemo(() => buildPrompt(post, analysis), [post, analysis]);

    return (
        <section className="rounded border border-stone-200 bg-white p-4">
            <div className="mb-3 flex flex-wrap items-start justify-between gap-2">
                <div>
                    <h3 className="text-base font-bold text-stone-950">개선 프롬프트</h3>
                    <p className="mt-1 text-sm leading-6 text-stone-600">
                        이 리포트를 코딩 에이전트에게 넘겨 프로젝트 개선 작업을 바로 시작할 수 있게 만든 복사용 지시문입니다.
                    </p>
                </div>
                <PromptCopyButton text={promptText} />
            </div>
            <textarea
                readOnly
                value={promptText}
                className="h-80 w-full resize-y rounded border border-stone-200 bg-stone-50 p-3 font-mono text-xs leading-5 text-stone-800 outline-none"
                aria-label="프로젝트 개선용 에이전트 프롬프트"
            />
        </section>
    );
}

async function copyToClipboard(text: string) {
    if (navigator.clipboard?.writeText) {
        try {
            await navigator.clipboard.writeText(text);
            return true;
        } catch {
            // Fall through to the DOM fallback for browsers that block clipboard writes.
        }
    }

    const textArea = document.createElement("textarea");
    textArea.value = text;
    textArea.setAttribute("readonly", "true");
    textArea.style.position = "fixed";
    textArea.style.left = "0";
    textArea.style.top = "0";
    textArea.style.width = "1px";
    textArea.style.height = "1px";
    textArea.style.opacity = "0";
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    textArea.setSelectionRange(0, text.length);
    try {
        return document.execCommand("copy");
    } finally {
        document.body.removeChild(textArea);
    }
}

export default ImprovementPromptCard;
