// Day 1 드릴에서 직접 작성합니다.
// PostCard props를 받아 게시글 1개를 렌더링하세요.
/* 
컴포넌트는 데이터를 화면 조각으로 바꾸는 함수예요(타입 파일 §4에 적어둔 그 내용). PostCard.tsx는 그중 가장 작은 단위 — Post 1개를 props로 받아 카드 1장을 그리는 함수. 
컴포넌트는 함수. 입력은 데이터, 출력은 화면. 이름은 반드시 대문자로 시작. 소문자면 HTML 태그로 취급됨.
.tsx 확장자: jsx를 쓸 수 있는 ts 파일.
jsx: 함수 안에서 html 같은 걸 return 하는 문법. return <h2>안녕</h2> {}를 쓰면 태그 안에 JS를 끼워넣을 수 있다
html과 다르게 class 대신 className을 쓴다.
4. props (= properties, "속성")
컴포넌트(함수)에 넘기는 입력 인자. 부모가 <PostCard post={...} />처럼 주면, PostCard 함수는 그걸 첫 번째 매개변수 객체로 받아요. props는 읽기 전용 — 안에서 바꾸지 않아요.

5. 구조분해(destructuring)
객체에서 필요한 필드만 꺼내 변수로 바로 받는 문법.


const obj = { post: 1, x: 2 };
const { post } = obj;   // post === 1
그래서 컴포넌트 매개변수에서 function PostCard({ post }: Props) 라고 쓰면, props 객체에서 post만 바로 꺼내 쓰는 거예요.

6. props 타입 지정
이 컴포넌트가 어떤 모양의 props를 받는지 TypeScript로 약속해요. 보통 interface로 정의 — 지난 세션에 배운 그 interface예요.


interface PostCardProps {
  post: Post;   // Post 하나를 받는다
}

*/
// Post 타입을 가져온다.
import type {Post} from "../types/post";
import {Link} from "react-router-dom";

// 이 component가 받을 props의 모양을 약속한다.
interface PostCardProps {
    post: Post;
}
//  article: 독립된 HTML 시멘틱 요소(카드, 포럼 글 등)

// Post 1개를 받아 카드 1장을 그리는 컴포넌트를 정의한다.
function PostCard({post}: PostCardProps) {
    return (
        <article className="rounded border p-4">
            <h2>
                <Link to={`/posts/${post.id}`} className="hover:underline">
                {post.title}
                </Link>
            </h2>
            <p>{post.excuseText}</p>
        </article>    
    );
}

export default PostCard;