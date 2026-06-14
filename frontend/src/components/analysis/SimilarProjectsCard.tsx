import type {RagSource} from "../../types/analysis";

interface SimilarProjectsCardProps {
    sources: RagSource[];
}

function SimilarProjectsCard({sources}: SimilarProjectsCardProps) {
    return (
        <section className="rounded border border-stone-200 bg-white p-4">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                <h3 className="text-base font-bold text-stone-950">유사 프로젝트</h3>
                {sources.length > 0 ? (
                    <span className="rounded-full bg-stone-100 px-2 py-1 text-xs font-semibold text-stone-600">
                        {sources.length}개
                    </span>
                ) : null}
            </div>

            {sources.length === 0 ? (
                <p className="rounded border border-stone-200 bg-stone-50 p-3 text-sm leading-6 text-stone-600">
                    비슷한 게시물이 아직 충분하지 않습니다.
                </p>
            ) : (
                <ul className="divide-y divide-stone-100">
                    {sources.map((source) => {
                        const similarity =
                            typeof source.similarity === "number"
                                ? `${Math.round(source.similarity * 100)}%`
                                : null;
                        return (
                            <li
                                key={`${source.source_id ?? source.title}-${source.title}`}
                                className="py-3"
                            >
                                <div className="mb-1 flex flex-wrap items-center gap-2">
                                    <strong className="break-words text-sm text-stone-950">
                                        {source.title}
                                    </strong>
                                    {similarity ? (
                                        <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-semibold text-emerald-800">
                                            {similarity}
                                        </span>
                                    ) : null}
                                </div>
                                {source.summary ? (
                                    <p className="break-words text-sm leading-6 text-stone-700">
                                        {source.summary}
                                    </p>
                                ) : null}
                            </li>
                        );
                    })}
                </ul>
            )}
        </section>
    );
}

export default SimilarProjectsCard;
