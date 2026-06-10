// ⚠️ [임시 채움 — 코치] 9단계 복습 때 이 파일 전체를 지우고 아래 원래 스텁으로 되돌린 뒤 직접 작성하세요.
//   원래 스텁:  export {}
//   (되돌리기 목록은 DOCS/진도_체크포인트.md "임시 채움 되돌리기" 참고)

import {Navigate} from "react-router-dom";
import type {ReactNode} from "react";
import {useAuth} from "../context/AuthContext";

// 비로그인 상태면 /login 으로 돌려보내는 작은 가드
function ProtectedRoute({children}: {children: ReactNode}) {
    const {isLoggedIn} = useAuth();
    if (!isLoggedIn) return <Navigate to="/login" replace />;
    return <>{children}</>;
}

export default ProtectedRoute;
