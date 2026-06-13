// ⚠️ [코치 작성 — 9단계 재드릴 대상] mock 로그인을 실제 백엔드 호출로 교체.
//   (시그니처 login(email, password) → {token} 은 그대로 유지 → AuthContext는 안 바뀜)

import {api} from "./http";

// 백엔드 POST /auth/login: OAuth2 표준이라 JSON이 아니라 "폼"으로 username/password를 보낸다.
// 응답은 {access_token, token_type}. 받은 토큰을 localStorage에 저장 → 이후 요청에 자동 첨부.
export async function login(
    email: string,
    password: string
): Promise<{token: string}> {
    const data = await api<{access_token: string; token_type: string}>("/auth/login", {
        method: "POST",
        // 백엔드는 username으로 유저를 찾는다 → 입력값을 username 자리에 보낸다.
        // (프론트가 'email'이라 부르는 것과 백엔드 'username'의 이름 정리는 9단계 몫)
        form: {username: email, password},
    });
    localStorage.setItem("token", data.access_token);
    return {token: data.access_token};
}
