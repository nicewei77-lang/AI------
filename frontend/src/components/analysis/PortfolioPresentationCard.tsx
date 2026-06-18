import {useMemo, useState} from "react";
import type {
    ExpectedQuestion,
    PortfolioDraft,
    PortfolioTranslation,
    PresentationDraft,
} from "../../types/analysis";

interface PortfolioPresentationCardProps {
    portfolio: PortfolioDraft;
    presentation: PresentationDraft;
    translation?: PortfolioTranslation;
}

type CopyState = "idle" | "copied" | "failed";

const EMPTY_TRANSLATION: PortfolioTranslation = {
    portfolio_sentence: {text: "", source_finding_ids: []},
    presentation_flow: {steps: [], source_finding_ids: []},
    expected_questions: [],
};

function hasPortfolioContent(portfolio: PortfolioDraft) {
    return [
        portfolio.headline,
        portfolio.problem,
        portfolio.solution,
        portfolio.impact,
        ...portfolio.tech_highlights,
        ...portfolio.proof_points,
        ...portfolio.limitations,
    ].some((item) => item.trim().length > 0);
}

function hasPresentationContent(presentation: PresentationDraft) {
    return [
        presentation.opening,
        presentation.closing,
        ...presentation.key_points,
        ...presentation.demo_flow,
        ...presentation.risks_or_next_steps,
    ].some((item) => item.trim().length > 0);
}

function hasTranslationContent(translation: PortfolioTranslation) {
    return (
        translation.portfolio_sentence.text.trim().length > 0 ||
        translation.presentation_flow.steps.some((item) => item.trim().length > 0) ||
        translation.expected_questions.some((item) => item.question.trim().length > 0)
    );
}

function lines(title: string, items: string[]) {
    const clean = items.filter((item) => item.trim());
    if (clean.length === 0) return "";
    return [`${title}`, ...clean.map((item) => `- ${item}`)].join("\n");
}

function toCopyText(
    portfolio: PortfolioDraft,
    presentation: PresentationDraft,
    translation: PortfolioTranslation,
) {
    return [
        "[포트폴리오 문장]",
        portfolio.headline,
        portfolio.problem ? `문제: ${portfolio.problem}` : "",
        portfolio.solution ? `해결: ${portfolio.solution}` : "",
        portfolio.impact ? `효과: ${portfolio.impact}` : "",
        lines("기술 포인트", portfolio.tech_highlights),
        lines("근거", portfolio.proof_points),
        lines("주의할 한계", portfolio.limitations),
        "",
        "[발표 요약]",
        presentation.opening,
        lines("핵심 포인트", presentation.key_points),
        lines("데모 흐름", presentation.demo_flow),
        lines("리스크/다음 단계", presentation.risks_or_next_steps),
        presentation.closing,
        "",
        "[근거 연결 번역]",
        translation.portfolio_sentence.text,
        lines("포트폴리오 근거 ID", translation.portfolio_sentence.source_finding_ids),
        lines("발표 흐름", translation.presentation_flow.steps),
        lines("발표 흐름 근거 ID", translation.presentation_flow.source_finding_ids),
        lines(
            "예상 질문",
            translation.expected_questions.map((item) =>
                `${item.question} - ${item.why_this_question} (${item.source_finding_ids.join(", ")})`,
            ),
        ),
    ]
        .filter((item) => item.trim())
        .join("\n");
}

function BulletList({items}: {items: string[]}) {
    const clean = items.filter((item) => item.trim());
    if (clean.length === 0) return null;
    return (
        <ul className="space-y-1 text-sm leading-6 text-stone-700">
            {clean.map((item) => (
                <li key={item} className="break-words">
                    {item}
                </li>
            ))}
        </ul>
    );
}

function SectionText({label, value}: {label: string; value: string}) {
    if (!value.trim()) return null;
    return (
        <div>
            <h4 className="mb-1 text-xs font-bold uppercase tracking-wide text-stone-500">
                {label}
            </h4>
            <p className="break-words text-sm leading-6 text-stone-700">{value}</p>
        </div>
    );
}

function SourceIdList({ids}: {ids: string[]}) {
    const clean = ids.filter((item) => item.trim());
    if (clean.length === 0) return null;

    return (
        <div className="mt-2 flex flex-wrap gap-2">
            {clean.map((id) => (
                <span
                    key={id}
                    className="rounded-full bg-indigo-50 px-2 py-0.5 text-xs font-semibold text-indigo-800"
                >
                    근거 {id}
                </span>
            ))}
        </div>
    );
}

function ExpectedQuestionList({items}: {items: ExpectedQuestion[]}) {
    const clean = items.filter((item) => item.question.trim());
    if (clean.length === 0) return null;

    return (
        <div className="space-y-2">
            <h5 className="text-xs font-bold uppercase tracking-wide text-stone-500">
                예상 질문
            </h5>
            <ul className="space-y-3">
                {clean.map((item) => (
                    <li key={item.question}>
                        <strong className="break-words text-sm text-stone-950">
                            {item.question}
                        </strong>
                        {item.why_this_question.trim() ? (
                            <p className="mt-1 break-words text-sm leading-6 text-stone-700">
                                {item.why_this_question}
                            </p>
                        ) : null}
                        <SourceIdList ids={item.source_finding_ids} />
                    </li>
                ))}
            </ul>
        </div>
    );
}

function TranslationBlock({translation}: {translation: PortfolioTranslation}) {
    if (!hasTranslationContent(translation)) return null;

    return (
        <div className="mt-5 border-t border-stone-200 pt-4">
            <h4 className="mb-3 text-sm font-bold text-stone-800">근거 연결 번역</h4>
            <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-4">
                    {translation.portfolio_sentence.text.trim() ? (
                        <div>
                            <h5 className="mb-1 text-xs font-bold uppercase tracking-wide text-stone-500">
                                포트폴리오 문장
                            </h5>
                            <p className="break-words text-sm leading-6 text-stone-700">
                                {translation.portfolio_sentence.text}
                            </p>
                            <SourceIdList ids={translation.portfolio_sentence.source_finding_ids} />
                        </div>
                    ) : null}
                    {translation.presentation_flow.steps.some((item) => item.trim()) ? (
                        <div>
                            <h5 className="mb-1 text-xs font-bold uppercase tracking-wide text-stone-500">
                                발표 흐름
                            </h5>
                            <BulletList items={translation.presentation_flow.steps} />
                            <SourceIdList ids={translation.presentation_flow.source_finding_ids} />
                        </div>
                    ) : null}
                </div>
                <ExpectedQuestionList items={translation.expected_questions} />
            </div>
        </div>
    );
}

function CopyButton({text}: {text: string}) {
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

    const label = state === "copied" ? "복사됨" : state === "failed" ? "실패" : "복사";

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

function PortfolioPresentationCard({
    portfolio,
    presentation,
    translation,
}: PortfolioPresentationCardProps) {
    const safeTranslation = translation ?? EMPTY_TRANSLATION;
    const hasContent =
        hasPortfolioContent(portfolio) ||
        hasPresentationContent(presentation) ||
        hasTranslationContent(safeTranslation);
    const copyText = useMemo(
        () => toCopyText(portfolio, presentation, safeTranslation),
        [portfolio, presentation, safeTranslation],
    );

    return (
        <section className="rounded border border-stone-200 bg-white p-4">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
                <h3 className="text-base font-bold text-stone-950">포트폴리오/발표 번역</h3>
                {hasContent ? <CopyButton text={copyText} /> : null}
            </div>

            {!hasContent ? (
                <p className="rounded border border-stone-200 bg-stone-50 p-3 text-sm leading-6 text-stone-600">
                    저장된 포트폴리오/발표 번역이 없습니다. 현재 리포트는 확인된 근거와 개선 액션 중심으로 표시됩니다.
                </p>
            ) : (
                <div className="grid gap-5 md:grid-cols-2">
                    <div className="space-y-4">
                        <h4 className="text-sm font-bold text-stone-800">포트폴리오 문장</h4>
                        <SectionText label="헤드라인" value={portfolio.headline} />
                        <SectionText label="문제" value={portfolio.problem} />
                        <SectionText label="해결" value={portfolio.solution} />
                        <SectionText label="효과" value={portfolio.impact} />
                        <div>
                            <h5 className="mb-1 text-xs font-bold uppercase tracking-wide text-stone-500">
                                기술 포인트
                            </h5>
                            <BulletList items={portfolio.tech_highlights} />
                        </div>
                        <div>
                            <h5 className="mb-1 text-xs font-bold uppercase tracking-wide text-stone-500">
                                근거와 한계
                            </h5>
                            <BulletList items={[...portfolio.proof_points, ...portfolio.limitations]} />
                        </div>
                    </div>

                    <div className="space-y-4">
                        <h4 className="text-sm font-bold text-stone-800">발표 요약</h4>
                        <SectionText label="오프닝" value={presentation.opening} />
                        <div>
                            <h5 className="mb-1 text-xs font-bold uppercase tracking-wide text-stone-500">
                                핵심 포인트
                            </h5>
                            <BulletList items={presentation.key_points} />
                        </div>
                        <div>
                            <h5 className="mb-1 text-xs font-bold uppercase tracking-wide text-stone-500">
                                데모 흐름
                            </h5>
                            <BulletList items={presentation.demo_flow} />
                        </div>
                        <div>
                            <h5 className="mb-1 text-xs font-bold uppercase tracking-wide text-stone-500">
                                다음 단계
                            </h5>
                            <BulletList items={presentation.risks_or_next_steps} />
                        </div>
                        <SectionText label="클로징" value={presentation.closing} />
                    </div>
                </div>
            )}
            {hasContent ? <TranslationBlock translation={safeTranslation} /> : null}
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
    textArea.style.left = "-9999px";
    textArea.style.top = "0";
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    try {
        return document.execCommand("copy");
    } finally {
        document.body.removeChild(textArea);
    }
}

export default PortfolioPresentationCard;
