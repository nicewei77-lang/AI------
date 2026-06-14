// ⚠️ [코치 작성 — 9단계 재드릴 대상] 모든 API 호출이 거치는 얇은 fetch 래퍼.
// axios가 자동으로 해주는 일(baseURL·JSON 직렬화·토큰 첨부·에러 변환)을
// 여기서 손으로 펼쳐서 "네트워크 호출의 본질"이 보이게 한다.

const BASE_URL = "http://localhost:8000"; // 백엔드 주소(CORS 허용됨). 실무에선 import.meta.env.VITE_API_URL

interface ApiOptions {
    method?: string;
    body?: unknown; // JSON으로 보낼 객체
    form?: Record<string, string>; // x-www-form-urlencoded로 보낼 값(OAuth2 로그인용)
}

export class ApiError extends Error {
    status: number;
    detail?: string;

    constructor(message: string, status: number, detail?: string) {
        super(message);
        this.name = "ApiError";
        Object.setPrototypeOf(this, ApiError.prototype);
        this.status = status;
        this.detail = detail;
    }
}

export async function api<T>(path: string, options: ApiOptions = {}): Promise<T> {
    const headers: Record<string, string> = {};

    // 1) 로그인 토큰이 있으면 모든 요청 헤더에 자동으로 붙인다 (Bearer 인증)
    const token = localStorage.getItem("token");
    if (token) headers["Authorization"] = `Bearer ${token}`;

    // 2) 보낼 본문을 인코딩 — 폼이면 폼 인코딩, 아니면 객체를 JSON 문자열로
    let body: BodyInit | undefined;
    if (options.form) {
        headers["Content-Type"] = "application/x-www-form-urlencoded";
        body = new URLSearchParams(options.form).toString();
    } else if (options.body !== undefined) {
        headers["Content-Type"] = "application/json";
        body = JSON.stringify(options.body);
    }

    // 3) 실제 네트워크 왕복 — 여기서 브라우저가 백엔드로 HTTP 요청을 보낸다
    const res = await fetch(BASE_URL + path, {
        method: options.method ?? "GET",
        headers,
        body,
    });

    // 4) fetch는 4xx/5xx에도 에러를 "던지지 않는다" → 직접 status를 확인해 던진다
    //    (axios는 이 단계를 자동으로 해줌 — fetch의 가장 헷갈리는 지점)
    if (!res.ok) {
        const detail = (await res.json().catch(() => ({}))) as { detail?: string };
        throw new ApiError(detail.detail ?? `요청 실패 (${res.status})`, res.status, detail.detail);
    }

    // 5) 응답 본문(스트림)을 JSON으로 파싱해 돌려준다
    return res.json() as Promise<T>;
}
