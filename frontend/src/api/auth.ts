// ⚠️ [임시 채움 — 코치] 9단계 복습 때 이 파일 전체를 지우고 아래 원래 스텁으로 되돌린 뒤 직접 작성하세요.
//   원래 스텁:  export {}
//   (되돌리기 목록은 DOCS/진도_체크포인트.md "임시 채움 되돌리기" 참고)

// login(email, password) mock 함수 — 다음 주 본문만 axios로 교체할 부분.
export async function login(
    email: string,
    password: string
): Promise<{token: string}> {
    // 네트워크 지연 흉내
    await new Promise((resolve) => setTimeout(resolve, 300));
    // 가짜 검증: 둘 다 채워져 있으면 통과
    if (!email || !password) {
        throw new Error("이메일과 비밀번호를 입력하세요.");
    }
    // 가짜 토큰 (다음 주 실제 JWT로 교체)
    return {token: "mock-token-" + email};
}
