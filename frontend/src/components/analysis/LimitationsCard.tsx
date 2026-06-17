import type {AnalysisLimitations} from "../../types/analysis";

interface LimitationsCardProps {
    limitations: AnalysisLimitations;
}

const DEFAULT_NOT_SEEN = [
    "비공개 코드, 로그인 뒤 화면, 실제 사용자 데이터는 분석 범위에 포함되지 않습니다.",
    "GitHub는 README와 기본 저장소 메타데이터 근거로만 다룹니다.",
    "Lighthouse summary는 공개 데모의 기술 표면 근거이며 프로젝트 가치 점수가 아닙니다.",
];

const DEFAULT_DISCLAIMERS = [
    "이 리포트는 공개 근거를 바탕으로 한 AI 해석이며, 내부 구현 검토나 성과 단정이 아닙니다.",
];

function cleanItems(items: string[]) {
    return items.filter((item) => item.trim());
}

function LimitList({title, items}: {title: string; items: string[]}) {
    const clean = cleanItems(items);
    if (clean.length === 0) return null;

    return (
        <div className="space-y-2">
            <h4 className="text-xs font-bold uppercase tracking-wide text-stone-500">{title}</h4>
            <ul className="space-y-1 text-sm leading-6 text-stone-700">
                {clean.map((item) => (
                    <li key={item} className="break-words">
                        {item}
                    </li>
                ))}
            </ul>
        </div>
    );
}

function LimitationsCard({limitations}: LimitationsCardProps) {
    const seen = cleanItems(limitations.seen);
    const notSeen = cleanItems(limitations.not_seen);
    const disclaimers = cleanItems(limitations.disclaimers);

    return (
        <section className="rounded border border-stone-200 bg-white p-4">
            <h3 className="mb-3 text-base font-bold text-stone-950">분석 범위와 한계</h3>
            <div className="grid gap-4 md:grid-cols-3">
                <LimitList
                    title="확인한 범위"
                    items={seen.length > 0 ? seen : ["게시글에 저장된 프로젝트 설명"]}
                />
                <LimitList
                    title="확인하지 못한 범위"
                    items={notSeen.length > 0 ? notSeen : DEFAULT_NOT_SEEN}
                />
                <LimitList
                    title="읽는 방법"
                    items={disclaimers.length > 0 ? disclaimers : DEFAULT_DISCLAIMERS}
                />
            </div>
        </section>
    );
}

export default LimitationsCard;
