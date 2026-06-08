// Day 1-2 드릴에서 직접 작성합니다.
// 목록 화면, 검색 상태, mock fetch 연결을 구현하세요.

// 데이터와 부품 컴포넌트를 불러온다.
import {useState, useEffect} from "react";
import PostList from "../components/PostList";
import {fetchPosts} from "../api/posts";
import type {Post} from "../types/post";

// 실제 화면을 그리는 함수를 정의한다.
function PostListPage() {
    // 기억 칸 3개: 데이터 / 로딩여부 / 에러메세지
    const [posts, setPosts] = useState<Post[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // 첫 화면이 뜰 때 한 번만 데이터 로드
    useEffect(() => {
        async function load() {
            try {
                const data = await fetchPosts();
                setPosts(data.items);
            } catch {
                setError("목록을 불러오지 못했습니다.");
            } finally {
                setLoading(false);
            }
        }
        load();
    }, []);

    // 세 갈래 화면
    if (loading) return <p className="p-8">불러오는 중...</p>;
    if (error) return <p className="p-9 text-red-600">{error}</p>;

    return (
        <div className="mx-auto max-w-2xl px-4 py-8">
            <h1 className="mb-4 text-2xl font-bold">변명 게시판</h1>
            <PostList posts={posts}/>
        </div>
    );
}

export default PostListPage;