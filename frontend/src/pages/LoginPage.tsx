// ⚠️ [임시 채움 — 코치] 8단계 복습 때 이 파일 전체를 지우고 아래 원래 스텁으로 되돌린 뒤 직접 작성하세요.
//   원래 스텁:  export {}
//   (되돌리기 목록은 DOCS/진도_체크포인트.md "임시 채움 되돌리기" 참고)

import {useState} from "react";
import type {FormEvent} from "react";
import {useNavigate} from "react-router-dom";
import {useAuth} from "../context/AuthContext";

function LoginPage() {
    // 입력값을 state가 소유하는 제어 컴포넌트
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState<string | null>(null);
    const {login} = useAuth();
    const navigate = useNavigate();

    async function handleSubmit(e: FormEvent) {
        e.preventDefault(); // 기본 새로고침 막기
        try {
            await login(email, password);
            navigate("/"); // 성공 시 목록으로
        } catch {
            setError("로그인에 실패했습니다.");
        }
    }

    return (
        <div className="mx-auto max-w-sm px-4 py-8">
            <h1 className="mb-4 text-2xl font-bold">로그인</h1>
            <form onSubmit={handleSubmit} className="flex flex-col gap-3">
                <input
                    className="rounded border p-2"
                    placeholder="이메일"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                />
                <input
                    className="rounded border p-2"
                    type="password"
                    placeholder="비밀번호"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                />
                {error && <p className="text-red-600">{error}</p>}
                <button className="rounded bg-black p-2 text-white" type="submit">
                    로그인
                </button>
            </form>
        </div>
    );
}

export default LoginPage;
