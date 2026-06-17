import type {AnalysisBadgeStatus} from "../../types/analysis";

const STATUS_LABELS: Record<AnalysisBadgeStatus, string> = {
    not_started: "미실행",
    running: "분석 중",
    completed: "완료",
    failed: "범위 한계",
    need_more_info: "정보 필요",
    refused: "제공 불가",
};

const STATUS_CLASSES: Record<AnalysisBadgeStatus, string> = {
    not_started: "border-stone-200 bg-stone-100 text-stone-700",
    running: "border-sky-200 bg-sky-50 text-sky-800",
    completed: "border-emerald-200 bg-emerald-50 text-emerald-800",
    failed: "border-amber-200 bg-amber-50 text-amber-800",
    need_more_info: "border-amber-200 bg-amber-50 text-amber-800",
    refused: "border-zinc-300 bg-zinc-100 text-zinc-700",
};

interface AnalysisStatusBadgeProps {
    status: AnalysisBadgeStatus;
    size?: "sm" | "md";
}

function AnalysisStatusBadge({status, size = "sm"}: AnalysisStatusBadgeProps) {
    return (
        <span
            className={`inline-flex max-w-full items-center rounded-full border font-semibold ${
                size === "md" ? "px-3 py-1 text-sm" : "px-2 py-0.5 text-xs"
            } ${STATUS_CLASSES[status]}`}
        >
            {STATUS_LABELS[status]}
        </span>
    );
}

export default AnalysisStatusBadge;
