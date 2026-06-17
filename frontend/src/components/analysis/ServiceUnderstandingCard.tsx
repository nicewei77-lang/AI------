import type {ServiceUnderstanding} from "../../types/analysis";

interface ServiceUnderstandingCardProps {
    service: ServiceUnderstanding;
}

function FactList({title, items}: {title: string; items: string[]}) {
    if (items.length === 0) return null;

    return (
        <div className="space-y-2">
            <h4 className="text-xs font-bold uppercase tracking-wide text-stone-500">{title}</h4>
            <ul className="space-y-1 text-sm leading-6 text-stone-700">
                {items.map((item) => (
                    <li key={item} className="break-words">
                        {item}
                    </li>
                ))}
            </ul>
        </div>
    );
}

function InsightBlock({title, value}: {title: string; value: string}) {
    if (!value.trim()) return null;

    return (
        <div className="rounded border border-stone-200 bg-stone-50 p-3">
            <h4 className="mb-1 text-xs font-bold uppercase tracking-wide text-stone-500">
                {title}
            </h4>
            <p className="break-words text-sm leading-6 text-stone-700">{value}</p>
        </div>
    );
}

function ServiceUnderstandingCard({service}: ServiceUnderstandingCardProps) {
    return (
        <section className="rounded border border-stone-200 bg-white p-4">
            <div className="mb-3 flex flex-wrap items-start justify-between gap-2">
                <div className="min-w-0">
                    <h3 className="text-base font-bold text-stone-950">서비스 이해와 AI 해석</h3>
                    <p className="mt-1 break-words text-sm font-semibold text-stone-800">
                        {service.one_line_summary}
                    </p>
                </div>
            </div>

            <p className="mb-4 whitespace-pre-wrap break-words text-sm leading-6 text-stone-700">
                {service.detailed_summary}
            </p>

            <div className="mb-4 grid gap-3">
                <InsightBlock title="사이트 구조" value={service.site_structure_summary} />
                <InsightBlock title="서비스 본질" value={service.service_essence} />
                <InsightBlock title="핵심 인사이트" value={service.key_insight} />
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
                <FactList title="타깃 사용자" items={service.target_users} />
                <FactList title="핵심 기능" items={service.core_features} />
                <FactList title="확인된 사실" items={service.confirmed_facts} />
                <FactList title="AI 추정" items={service.inferred_facts} />
            </div>

            {service.auto_tags.length > 0 ? (
                <div className="mt-4 flex flex-wrap gap-2">
                    {service.auto_tags.map((tag) => (
                        <span
                            key={tag}
                            className="max-w-full rounded-full bg-stone-100 px-2 py-1 text-xs font-medium text-stone-600"
                        >
                            #{tag}
                        </span>
                    ))}
                </div>
            ) : null}
        </section>
    );
}

export default ServiceUnderstandingCard;
