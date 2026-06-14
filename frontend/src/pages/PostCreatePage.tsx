// ⚠️ [임시 채움 — 코치] 9단계 복습 때 이 파일 전체를 지우고 아래 원래 스텁으로 되돌린 뒤 직접 작성하세요.
//   원래 스텁:  export {}
//   (되돌리기 목록은 DOCS/진도_체크포인트.md "임시 채움 되돌리기" 참고)

import {useNavigate} from "react-router-dom";
import {useState} from "react";
import ProjectForm from "../components/ProjectForm";
import {createPost} from "../api/posts";
import type {NewPost} from "../types/post";

function PostCreatePage() {
    const navigate = useNavigate();
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    async function handleCreate(input: NewPost) {
        setSubmitting(true);
        setError(null);
        try {
            const created = await createPost(input);
            navigate(`/posts/${created.id}`);
        } catch (err) {
            setError(err instanceof Error ? err.message : "프로젝트 등록에 실패했습니다.");
        } finally {
            setSubmitting(false);
        }
    }

    return (
        <main className="min-h-screen bg-stone-50 px-4 py-8 text-stone-950">
            <div className="mx-auto max-w-2xl rounded border border-stone-200 bg-white p-5">
                <h1 className="mb-4 text-2xl font-bold">프로젝트 등록</h1>
                {error ? (
                    <p className="mb-4 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                        {error}
                    </p>
                ) : null}
                <ProjectForm onSubmit={handleCreate} submitting={submitting} />
            </div>
        </main>
    );
}

export default PostCreatePage;
