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
    const [excuseText, setExcuseText] = useState("");

    function handleSubmit(e: FormEvent) {
        e.preventDefault();
        onSubmit({
            title,
            excuseText,
            tags: [],
            context: {date: "", location: "", time: "", route: undefined},
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
            <textarea
                className="rounded border p-2"
                placeholder="변명 내용"
                value={excuseText}
                onChange={(e) => setExcuseText(e.target.value)}
            />
            <button className="rounded bg-black p-2 text-white" type="submit">
                제출
            </button>
        </form>
    );
}

export default ExcuseForm;
