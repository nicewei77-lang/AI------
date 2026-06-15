import {useMemo, useState} from "react";
import type {PortfolioDraft, PresentationDraft} from "../../types/analysis";

interface PortfolioPresentationCardProps {
    portfolio: PortfolioDraft;
    presentation: PresentationDraft;
}

type CopyState = "idle" | "copied" | "failed";

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

function lines(title: string, items: string[]) {
    const clean = items.filter((item) => item.trim());
    if (clean.length === 0) return "";
    return [`${title}`, ...clean.map((item) => `- ${item}`)].join("\n");
}

function toCopyText(portfolio: PortfolioDraft, presentation: PresentationDraft) {
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
}: PortfolioPresentationCardProps) {
    const hasContent = hasPortfolioContent(portfolio) || hasPresentationContent(presentation);
    const copyText = useMemo(
        () => toCopyText(portfolio, presentation),
        [portfolio, presentation],
    );

    return (
        <section className="rounded border border-stone-200 bg-white p-4">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
                <h3 className="text-base font-bold text-stone-950">포트폴리오/발표</h3>
                {hasContent ? <CopyButton text={copyText} /> : null}
            </div>

            {!hasContent ? (
                <p className="rounded border border-stone-200 bg-stone-50 p-3 text-sm leading-6 text-stone-600">
                    completed 리포트가 생성되면 포트폴리오 문장과 발표 요약이 표시됩니다.
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
