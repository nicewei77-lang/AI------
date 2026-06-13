// ⚠️ [코치 작성 — 계획 범위 밖] /signup 빈 화면 대응으로 추가. LoginPage를 본보기로 함.

import {useState} from "react";
import type {FormEvent} from "react";
import {useNavigate, Link} from "react-router-dom";
import {signup} from "../api/auth";

function SignupPage() {
    // 입력값을 state가 소유하는 제어 컴포넌트 (로그인보다 username이 하나 더 있다)
    const [username, setUsername] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState<string | null>(null);
    const navigate = useNavigate();

    async function handleSubmit(e: FormEvent) {
        e.preventDefault(); // 기본 새로고침 막기
        setError(null);
        try {
            await signup(username, email, password);
            navigate("/login"); // 가입 성공 → 로그인 화면으로 (signup은 토큰을 안 줌)
        } catch (err) {
            // http 래퍼가 백엔드 detail(예: "username taken")을 Error.message로 던진다
            setError(err instanceof Error ? err.message : "회원가입에 실패했습니다.");
        }
    }

    return (
        <div className="mx-auto max-w-sm px-4 py-8">
            <h1 className="mb-4 text-2xl font-bold">회원가입</h1>
            <form onSubmit={handleSubmit} className="flex flex-col gap-3">
                <input
                    className="rounded border p-2"
                    placeholder="아이디"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                />
                <input
                    className="rounded border p-2"
                    type="email"
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
                    회원가입
                </button>
            </form>
            <p className="mt-3 text-sm">
                이미 계정이 있나요?{" "}
                <Link className="underline" to="/login">
                    로그인
                </Link>
            </p>
        </div>
    );
}

export default SignupPage;
