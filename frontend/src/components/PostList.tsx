// Day 1 드릴에서 직접 작성합니다.
// posts 배열을 map으로 렌더링하는 목록 컴포넌트를 만드세요.
import type {Post} from "../types/post"; // 데이터 타입
import PostCard from "./PostCard"; // 카드 컴포넌트 (default export였음)


// 이 컴포넌트가 받을 props인 Post 배열
interface PostListProps {
    posts: Post[];
}

function PostList({posts}: PostListProps) {
    return (
        <div className="overflow-hidden rounded border border-stone-200 bg-white">
            {posts.map((post) => (<PostCard key={post.id} post={post}/>))}
        </div>
    );
}

export default PostList;
