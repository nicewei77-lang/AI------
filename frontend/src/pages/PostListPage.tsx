// Day 1-2 드릴에서 직접 작성합니다.
// 목록 화면, 검색 상태, mock fetch 연결을 구현하세요.

// 데이터와 부품 컴포넌트를 불러온다.
import {useState, useEffect, useCallback} from "react";
import type {FormEvent} from "react";
import {Link} from "react-router-dom";
import PostList from "../components/PostList";
import {fetchPosts} from "../api/posts";
import type {Post} from "../types/post";
import {useAuth} from "../context/AuthContext";

const CAPABILITY_BADGES = [
    "Powered by OpenAI GPT-5.5",
    "MCP Tools",
    "RAG Search",
    "Structured Review",
];

const PREVIEW_EVIDENCE = ["사이트 개요", "GitHub README", "화면 품질", "Lighthouse summary"];
const PREVIEW_OUTPUTS = ["서비스 이해", "강점", "리스크", "개선 액션"];

const REVIEW_FLOW = [
    {
        icon: "📝",
        title: "프로젝트 게시글",
        body: "URL, GitHub, 작성자 설명을 하나의 리뷰 요청으로 묶습니다.",
        accent: "border-orange-200 bg-orange-50 text-orange-900",
    },
    {
        icon: "🔎",
        title: "RAG Search",
        body: "게시판에 쌓인 유사 프로젝트와 기존 리뷰 근거를 검색합니다.",
        accent: "border-emerald-200 bg-emerald-50 text-emerald-900",
    },
    {
        icon: "🛠️",
        title: "MCP Tools",
        body: "사이트, README, 렌더링 화면, Lighthouse 요약을 안전하게 확인합니다.",
        accent: "border-sky-200 bg-sky-50 text-sky-900",
    },
    {
        icon: "🧠",
        title: "ProjectLens Agent",
        body: "OpenAI GPT-5.5가 근거를 비교하고 리뷰 구조를 결정합니다.",
        accent: "border-indigo-200 bg-indigo-50 text-indigo-900",
    },
    {
        icon: "🧩",
        title: "Structured Output",
        body: "서비스 이해, 강점, 리스크, 개선 액션을 카드 데이터로 만듭니다.",
        accent: "border-pink-200 bg-pink-50 text-pink-900",
    },
    {
        icon: "💾",
        title: "리뷰 카드 저장",
        body: "검증 가능한 AI 리뷰를 게시글 상세 화면에 저장하고 보여줍니다.",
        accent: "border-stone-200 bg-white text-stone-900",
    },
];

function OpenAIBadge() {
    return (
        <div className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/10 px-3 py-2 text-sm font-semibold text-white shadow-sm">
            <span className="rounded-full bg-white px-2 py-1 text-xs font-black text-stone-950">
                OpenAI
            </span>
            <span className="whitespace-nowrap">GPT-5.5 기반</span>
        </div>
    );
}

function ServiceHero() {
    return (
        <section className="overflow-hidden rounded-lg border border-stone-800 bg-stone-950 text-white shadow-[0_18px_45px_-30px_rgba(28,25,23,0.65)]">
            <div className="grid gap-6 px-5 py-7 md:px-7 lg:grid-cols-[minmax(0,1fr)_360px] lg:items-center">
                <div className="min-w-0">
                    <div className="mb-4 flex flex-wrap items-center gap-2">
                        <span className="rounded-full bg-orange-500 px-3 py-1 text-xs font-bold uppercase tracking-wide text-white">
                            AI Project Review
                        </span>
                        <OpenAIBadge />
                    </div>
                    <p className="mb-3 text-sm font-bold uppercase tracking-wide text-orange-200">
                        ProjectLens
                    </p>
                    <h1 className="max-w-3xl text-3xl font-black leading-tight text-white md:text-5xl">
                        프로젝트를 올리면, AI가 근거를 읽고 리뷰를 남깁니다.
                    </h1>
                    <p className="mt-4 max-w-2xl text-base leading-7 text-stone-200 md:text-lg">
                        ProjectLens는 URL, GitHub README, 화면 품질, 유사 프로젝트 데이터를 바탕으로
                        서비스 이해, 강점, 리스크, 개선 액션을 구조화된 리뷰 카드로 정리합니다.
                    </p>
                    <div className="mt-6 flex flex-wrap gap-2">
                        {CAPABILITY_BADGES.map((badge) => (
                            <span
                                key={badge}
                                className="rounded-full border border-white/15 bg-white/10 px-3 py-1.5 text-xs font-semibold text-stone-100"
                            >
                                {badge}
                            </span>
                        ))}
                    </div>
                    <div className="mt-7 flex flex-wrap items-center gap-3">
                        <Link
                            to="/new"
                            className="rounded-full bg-orange-500 px-5 py-3 text-sm font-bold text-white hover:bg-orange-600"
                        >
                            새 프로젝트 등록
                        </Link>
                        <a
                            href="#latest-reviews"
                            className="rounded-full border border-white/20 px-5 py-3 text-sm font-bold text-white hover:bg-white/10"
                        >
                            최신 리뷰 보기
                        </a>
                    </div>
                </div>

                <aside className="rounded-lg border border-white/15 bg-white p-4 text-stone-950 shadow-[0_18px_40px_-28px_rgba(0,0,0,0.8)]">
                    <div className="mb-4 flex items-center justify-between gap-3">
                        <div>
                            <p className="text-xs font-bold uppercase tracking-wide text-stone-500">
                                Review Preview
                            </p>
                            <h2 className="mt-1 text-lg font-black leading-snug">
                                근거 기반 AI 리뷰 카드
                            </h2>
                        </div>
                        <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-bold text-emerald-800">
                            completed
                        </span>
                    </div>
                    <div className="space-y-4">
                        <PreviewBlock title="확인된 근거" items={PREVIEW_EVIDENCE} />
                        <PreviewBlock title="AI 리뷰" items={PREVIEW_OUTPUTS} />
                        <div className="rounded border border-stone-200 bg-stone-50 p-3">
                            <h3 className="text-xs font-bold uppercase tracking-wide text-stone-500">
                                분석 범위
                            </h3>
                            <p className="mt-2 text-sm leading-6 text-stone-700">
                                확인한 것과 확인하지 못한 것을 분리해, 없는 기능을 지어내지 않습니다.
                            </p>
                        </div>
                    </div>
                </aside>
            </div>
        </section>
    );
}

function PreviewBlock({title, items}: {title: string; items: string[]}) {
    return (
        <div className="rounded border border-stone-200 bg-white p-3">
            <h3 className="text-xs font-bold uppercase tracking-wide text-stone-500">
                {title}
            </h3>
            <div className="mt-2 flex flex-wrap gap-2">
                {items.map((item) => (
                    <span
                        key={item}
                        className="rounded-full bg-stone-100 px-2 py-1 text-xs font-semibold text-stone-700"
                    >
                        {item}
                    </span>
                ))}
            </div>
        </div>
    );
}

function ReviewFlowDiagram() {
    return (
        <section className="space-y-4">
            <div className="flex flex-wrap items-end justify-between gap-3">
                <div>
                    <p className="text-sm font-bold uppercase tracking-wide text-orange-600">
                        Agent Pipeline
                    </p>
                    <h2 className="mt-1 text-2xl font-black text-stone-950">
                        AI 리뷰는 이렇게 생성됩니다
                    </h2>
                </div>
                <p className="max-w-2xl text-sm leading-6 text-stone-600">
                    Agent는 게시글만 읽지 않습니다. 제출된 URL과 GitHub를 안전하게 확인하고,
                    게시판에 쌓인 유사 프로젝트를 함께 참고한 뒤, 검증 가능한 리뷰 카드로 저장합니다.
                </p>
            </div>
            <div className="grid gap-3 lg:grid-cols-6">
                {REVIEW_FLOW.map((step, index) => (
                    <article
                        key={step.title}
                        className={`relative rounded-lg border p-4 ${step.accent}`}
                    >
                        {index > 0 ? (
                            <span className="absolute -left-3 top-1/2 hidden -translate-y-1/2 rounded-full border border-stone-200 bg-white px-1.5 py-0.5 text-xs font-black text-stone-500 lg:block">
                                →
                            </span>
                        ) : null}
                        <div className="mb-4 flex items-center gap-3">
                            <span className="inline-flex h-9 w-9 items-center justify-center rounded-full bg-white/90 text-lg shadow-sm">
                                {step.icon}
                            </span>
                            <span className="inline-flex h-7 w-7 items-center justify-center rounded-full bg-white/80 text-xs font-black text-stone-900">
                                {index + 1}
                            </span>
                        </div>
                        <h3 className="text-sm font-black">{step.title}</h3>
                        <p className="mt-2 text-sm leading-6">{step.body}</p>
                    </article>
                ))}
            </div>
        </section>
    );
}

// 실제 화면을 그리는 함수를 정의한다.
function PostListPage() {
    // 기억 칸 3개: 데이터 / 로딩여부 / 에러메세지
    const [posts, setPosts] = useState<Post[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [searchText, setSearchText] = useState("");
    const {isLoggedIn, logout} = useAuth();

    const loadPosts = useCallback(async (
        q: string,
        isCancelled: () => boolean = () => false,
    ) => {
        try {
            const data = await fetchPosts({q: q.trim() || undefined});
            if (!isCancelled()) {
                setPosts(data.items);
            }
        } catch {
            if (!isCancelled()) {
                setError("목록을 불러오지 못했습니다.");
            }
        } finally {
            if (!isCancelled()) {
                setLoading(false);
            }
        }
    }, []);

    // 첫 화면이 뜰 때 한 번만 데이터 로드
    useEffect(() => {
        let cancelled = false;
        const timer = window.setTimeout(() => {
            void loadPosts("", () => cancelled);
        }, 0);

        return () => {
            cancelled = true;
            window.clearTimeout(timer);
        };
    }, [loadPosts]);

    function handleSearch(e: FormEvent) {
        e.preventDefault();
        setLoading(true);
        setError(null);
        void loadPosts(searchText);
    }

    // 세 갈래 화면
    return (
        <div className="min-h-screen bg-stone-50 text-stone-950">
            <header className="sticky top-0 z-10 border-b border-stone-200 bg-white/95 backdrop-blur">
                <div className="mx-auto flex max-w-6xl flex-col gap-3 px-4 py-3 sm:flex-row sm:items-center">
                    <Link to="/" className="shrink-0 text-xl font-black text-orange-600">
                        ProjectLens
                    </Link>
                    <form onSubmit={handleSearch} className="flex min-w-0 flex-1 gap-2">
                        <input
                            className="min-w-0 flex-1 rounded-full border border-stone-200 bg-stone-100 px-4 py-2 text-sm outline-none focus:border-orange-400 focus:bg-white"
                            placeholder="프로젝트 검색"
                            value={searchText}
                            onChange={(e) => setSearchText(e.target.value)}
                        />
                        <button
                            type="submit"
                            className="rounded-full bg-stone-900 px-4 py-2 text-sm font-semibold text-white hover:bg-stone-700"
                        >
                            검색
                        </button>
                    </form>
                    <div className="flex shrink-0 items-center gap-2">
                        {isLoggedIn ? (
                            <>
                                <Link
                                    to="/new"
                                    className="rounded-full border border-stone-300 px-3 py-2 text-sm font-semibold hover:bg-stone-100"
                                >
                                    새 프로젝트
                                </Link>
                                <button
                                    type="button"
                                    onClick={logout}
                                    className="rounded-full bg-orange-600 px-3 py-2 text-sm font-semibold text-white hover:bg-orange-700"
                                >
                                    로그아웃
                                </button>
                            </>
                        ) : (
                            <>
                                <Link
                                    to="/signup"
                                    className="rounded-full border border-stone-300 px-3 py-2 text-sm font-semibold hover:bg-stone-100"
                                >
                                    가입
                                </Link>
                                <Link
                                    to="/login"
                                    className="rounded-full bg-orange-600 px-3 py-2 text-sm font-semibold text-white hover:bg-orange-700"
                                >
                                    로그인
                                </Link>
                            </>
                        )}
                    </div>
                </div>
            </header>

            <main className="mx-auto w-full max-w-6xl space-y-8 px-4 py-6">
                <ServiceHero />
                <ReviewFlowDiagram />

                <section id="latest-reviews" className="mx-auto w-full max-w-3xl space-y-4">
                    <div>
                        <p className="text-sm font-bold uppercase tracking-wide text-orange-600">
                            Community Reviews
                        </p>
                        <h2 className="mt-1 text-2xl font-black text-stone-950">
                            최신 프로젝트 리뷰
                        </h2>
                    </div>
                    {loading ? <p className="rounded border border-stone-200 bg-white p-4">불러오는 중...</p> : null}
                    {error ? <p className="rounded border border-red-200 bg-red-50 p-4 text-red-700">{error}</p> : null}
                    {!loading && !error && posts.length === 0 ? (
                        <p className="rounded border border-stone-200 bg-white p-6 text-center text-stone-500">
                            표시할 게시글이 없습니다.
                        </p>
                    ) : null}
                    {!loading && !error ? <PostList posts={posts}/> : null}
                </section>
            </main>
        </div>
    );
}

export default PostListPage;
