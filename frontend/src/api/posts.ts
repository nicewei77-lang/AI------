// ⚠️ [코치 작성 — 9단계 재드릴 대상] mock(MOCK_POSTS 배열 읽기) → 실제 백엔드 HTTP 호출로 교체.
//   시그니처는 그대로 유지(컴포넌트는 안 바뀜). 백엔드 JSON ↔ 프론트 Post 변환은 "이 함수 안에서".

import type {Post, NewPost, Tag, ExcuseContext} from "../types/post";
import {api} from "./http";

// 백엔드 PostOut(JSON) 모양 — 프론트 Post와 다르다(id는 숫자, score/myVote가 더 있음).
interface RawPost {
    id: number;
    title: string;
    excuseText: string;
    createdAt: string;
    score: number;
    myVote: number;
    verdict: string | null;
    credibility: number | null;
    context: ExcuseContext | null;
    tags: Tag[];
}

// 백엔드 응답 → 프론트 Post 모양으로 변환(경계에서 1번만 맞춰주면 컴포넌트는 그대로 쓴다)
function toPost(raw: RawPost): Post {
    return {
        id: String(raw.id), // 백엔드 int → 프론트 string
        title: raw.title,
        tags: raw.tags ?? [],
        excuseText: raw.excuseText,
        context: raw.context ?? {date: "", location: "", time: "", route: undefined},
        verdict: (raw.verdict ?? undefined) as Post["verdict"],
        credibility: raw.credibility ?? undefined,
        createdAt: raw.createdAt,
    };
}

/* post 목록: GET /posts?q=&tag=&cursor= */
export async function fetchPosts(
    params?: {q?: string; tagId?: string; cursor?: string}
): Promise<{items: Post[]; nextCursor?: string}> {
    const qs = new URLSearchParams();
    if (params?.q) qs.set("q", params.q);
    if (params?.tagId) qs.set("tag", params.tagId); // 프론트 tagId → 백엔드 tag
    if (params?.cursor) qs.set("cursor", params.cursor);
    const query = qs.toString() ? `?${qs.toString()}` : "";

    const data = await api<{items: RawPost[]; nextCursor: string | null}>(`/posts${query}`);
    return {
        items: data.items.map(toPost),
        nextCursor: data.nextCursor ?? undefined,
    };
}

/* post 한 개: GET /posts/{id} */
export async function fetchPostById(id: string): Promise<Post> {
    const raw = await api<RawPost>(`/posts/${id}`);
    return toPost(raw);
}

/* 새 변명글 제출: POST /posts (로그인 토큰은 http 래퍼가 자동 첨부) */
export async function createPost(input: NewPost): Promise<Post> {
    const raw = await api<RawPost>("/posts", {
        method: "POST",
        body: {
            title: input.title,
            excuseText: input.excuseText,
            tagIds: input.tags.map((t) => t.id), // Tag[] → slug 문자열 배열
            context: input.context,
        },
    });
    return toPost(raw);
}
