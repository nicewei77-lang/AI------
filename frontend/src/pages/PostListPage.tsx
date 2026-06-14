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
                <div className="mx-auto flex max-w-5xl items-center gap-3 px-4 py-3">
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

            <main className="mx-auto max-w-3xl px-4 py-5">
                {loading ? <p className="rounded border border-stone-200 bg-white p-4">불러오는 중...</p> : null}
                {error ? <p className="rounded border border-red-200 bg-red-50 p-4 text-red-700">{error}</p> : null}
                {!loading && !error && posts.length === 0 ? (
                    <p className="rounded border border-stone-200 bg-white p-6 text-center text-stone-500">
                        표시할 게시글이 없습니다.
                    </p>
                ) : null}
                {!loading && !error ? <PostList posts={posts}/> : null}
            </main>
        </div>
    );
}

export default PostListPage;
