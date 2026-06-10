// ⚠️ [임시 채움 — 코치] 9단계 복습 때 이 파일 전체를 지우고 아래 원래 스텁으로 되돌린 뒤 직접 작성하세요.
//   원래 스텁:  export {}
//   (되돌리기 목록은 DOCS/진도_체크포인트.md "임시 채움 되돌리기" 참고)

import {createContext, useContext, useState} from "react";
import type {ReactNode} from "react";
import {login as loginApi} from "../api/auth";

// Context로 공유할 값의 모양
interface AuthContextValue {
    isLoggedIn: boolean;
    login: (email: string, password: string) => Promise<void>;
    logout: () => void;
}

// 전역 로그인 상태를 담는 Context (Provider 밖에서 쓰면 null)
const AuthContext = createContext<AuthContextValue | null>(null);

// 앱 전체를 감싸 로그인 상태를 공급하는 Provider
export function AuthProvider({children}: {children: ReactNode}) {
    const [token, setToken] = useState<string | null>(null);

    async function login(email: string, password: string) {
        const res = await loginApi(email, password);
        setToken(res.token);
    }

    function logout() {
        setToken(null);
    }

    return (
        <AuthContext.Provider value={{isLoggedIn: token !== null, login, logout}}>
            {children}
        </AuthContext.Provider>
    );
}

// 소비 측이 쓰는 훅 (Provider 밖에서 호출하면 에러로 잡아줌)
// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error("useAuth는 AuthProvider 안에서만 쓸 수 있습니다.");
    return ctx;
}
