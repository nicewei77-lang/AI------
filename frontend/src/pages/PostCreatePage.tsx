// ⚠️ [임시 채움 — 코치] 9단계 복습 때 이 파일 전체를 지우고 아래 원래 스텁으로 되돌린 뒤 직접 작성하세요.
//   원래 스텁:  export {}
//   (되돌리기 목록은 DOCS/진도_체크포인트.md "임시 채움 되돌리기" 참고)

import {useNavigate} from "react-router-dom";
import ExcuseForm from "../components/ExcuseForm";
import {createPost} from "../api/posts";
import type {NewPost} from "../types/post";

function PostCreatePage() {
    const navigate = useNavigate();

    // ExcuseForm이 넘긴 입력을 createPost로 저장하고 상세로 이동
    async function handleCreate(input: NewPost) {
        const created = await createPost(input);
        navigate(`/posts/${created.id}`);
    }

    return (
        <div className="mx-auto max-w-2xl px-4 py-8">
            <h1 className="mb-4 text-2xl font-bold">프로젝트 등록</h1>
            <ExcuseForm onSubmit={handleCreate} />
        </div>
    );
}

export default PostCreatePage;
