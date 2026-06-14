// ⚠️ [임시 채움 — 코치] 8단계 복습 때 이 파일 전체를 지우고 아래 원래 스텁으로 되돌린 뒤 직접 작성하세요.
//   원래 스텁:  export {}
//   (되돌리기 목록은 DOCS/진도_체크포인트.md "임시 채움 되돌리기" 참고)

import {useState} from "react";
import type {FormEvent} from "react";
import type {NewPost} from "../types/post";

// 제출 시 부모에게 NewPost를 넘겨주는 콜백 props
interface ExcuseFormProps {
    onSubmit: (input: NewPost) => void;
}

function ExcuseForm({onSubmit}: ExcuseFormProps) {
    const [title, setTitle] = useState("");
    const [body, setBody] = useState("");
    const [oneLiner, setOneLiner] = useState("");
    const [serviceUrl, setServiceUrl] = useState("");
    const [githubUrl, setGithubUrl] = useState("");
    const [targetUser, setTargetUser] = useState("");
    const [techStackText, setTechStackText] = useState("");

    function handleSubmit(e: FormEvent) {
        e.preventDefault();
        const techStack = techStackText
            .split(",")
            .map((item) => item.trim())
            .filter(Boolean);
        onSubmit({
            title: title.trim(),
            body: body.trim(),
            postType: "project",
            serviceUrl: serviceUrl.trim() || undefined,
            githubUrl: githubUrl.trim() || undefined,
            oneLiner: oneLiner.trim() || undefined,
            targetUser: targetUser.trim() || undefined,
            techStack,
            tags: [],
        });
    }

    return (
        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
            <input
                className="rounded border p-2"
                placeholder="제목"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
            />
            <input
                className="rounded border p-2"
                placeholder="한 줄 소개"
                value={oneLiner}
                onChange={(e) => setOneLiner(e.target.value)}
            />
            <input
                className="rounded border p-2"
                placeholder="서비스 URL"
                value={serviceUrl}
                onChange={(e) => setServiceUrl(e.target.value)}
            />
            <input
                className="rounded border p-2"
                placeholder="GitHub URL"
                value={githubUrl}
                onChange={(e) => setGithubUrl(e.target.value)}
            />
            <input
                className="rounded border p-2"
                placeholder="타깃 사용자"
                value={targetUser}
                onChange={(e) => setTargetUser(e.target.value)}
            />
            <input
                className="rounded border p-2"
                placeholder="기술 스택, 쉼표로 구분"
                value={techStackText}
                onChange={(e) => setTechStackText(e.target.value)}
            />
            <textarea
                className="rounded border p-2"
                placeholder="프로젝트 설명"
                value={body}
                onChange={(e) => setBody(e.target.value)}
            />
            <button
                className="rounded bg-black p-2 text-white disabled:cursor-not-allowed disabled:bg-stone-300"
                type="submit"
                disabled={!title.trim() || !body.trim()}
            >
                등록
            </button>
        </form>
    );
}

export default ExcuseForm;
