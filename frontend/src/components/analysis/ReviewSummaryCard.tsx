import type {ReviewSummary} from "../../types/analysis";

interface ReviewSummaryCardProps {
    summary: ReviewSummary;
}

function hasItems(items: string[]) {
    return items.some((item) => item.trim().length > 0);
}

function SummaryList({title, items}: {title: string; items: string[]}) {
    const clean = items.filter((item) => item.trim());
    if (clean.length === 0) return null;

    return (
        <div className="space-y-2">
            <h4 className="text-xs font-bold uppercase tracking-wide text-stone-500">{title}</h4>
            <ul className="space-y-1 text-sm leading-6 text-stone-700">
                {clean.slice(0, 4).map((item) => (
                    <li key={item} className="break-words">
                        {item}
                    </li>
                ))}
            </ul>
        </div>
    );
}

function ReviewSummaryCard({summary}: ReviewSummaryCardProps) {
    const hasContent =
        summary.one_line_review.trim().length > 0 ||
        hasItems(summary.strongest_signals) ||
        hasItems(summary.main_risks) ||
        hasItems(summary.priority_actions);

    return (
        <section className="rounded border border-stone-200 bg-white p-4">
            <h3 className="mb-2 text-base font-bold text-stone-950">요약</h3>
            {!hasContent ? (
                <p className="text-sm leading-6 text-stone-500">
                    리포트 요약이 아직 없습니다. 확인된 근거가 쌓이면 강점, 리스크, 우선 액션이 이곳에 표시됩니다.
                </p>
            ) : (
                <div className="space-y-4">
                    {summary.one_line_review.trim() ? (
                        <p className="break-words text-sm font-semibold leading-6 text-stone-900">
                            {summary.one_line_review}
                        </p>
                    ) : null}
                    <div className="grid gap-4 md:grid-cols-3">
                        <SummaryList title="강한 신호" items={summary.strongest_signals} />
                        <SummaryList title="주요 리스크" items={summary.main_risks} />
                        <SummaryList title="우선 개선 액션" items={summary.priority_actions} />
                    </div>
                </div>
            )}
        </section>
    );
}

export default ReviewSummaryCard;
