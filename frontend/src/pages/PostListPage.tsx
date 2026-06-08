// Day 1-2 드릴에서 직접 작성합니다.
// 목록 화면, 검색 상태, mock fetch 연결을 구현하세요.

// 데이터와 부품 컴포넌트를 불러온다.
import PostList from "../components/PostList";
import {MOCK_POSTS} from "../api/mockData";

// 실제 화면을 그리는 함수를 정의한다.
function PostListPage() {
    return (
        <div className="mx-auto max-w-2xl px-4 py-8">
            <h1 className="mb-4 text-2xl font-bold">변명 게시판</h1>
            <PostList posts={MOCK_POSTS}/>
        </div>
    );
}

export default PostListPage;