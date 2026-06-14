// ⚠️ [코치 작성 — 9단계 재드릴 대상] mock(MOCK_POSTS 배열 읽기) → 실제 백엔드 HTTP 호출로 교체.
//   시그니처는 그대로 유지(컴포넌트는 안 바뀜). 백엔드 JSON ↔ 프론트 Post 변환은 "이 함수 안에서".

import type {AnalysisStatus, Post, NewPost, PostType, Tag} from "../types/post";
import {api} from "./http";

// 백엔드 PostOut(JSON) 모양 — 프론트 Post와 다르다(id는 숫자, score/myVote가 더 있음).
interface RawPost {
    id: number;
    authorName: string;
    title: string;
    body: string;
    postType: PostType;
    serviceUrl: string | null;
    githubUrl: string | null;
    oneLiner: string | null;
    targetUser: string | null;
    techStack: string[] | null;
    analysisStatus: AnalysisStatus;
    aiSummary: string | null;
    createdAt: string;
    score: number;
    myVote: number;
    commentCount: number;
    tags: Tag[];
}

// 백엔드 응답 → 프론트 Post 모양으로 변환(경계에서 1번만 맞춰주면 컴포넌트는 그대로 쓴다)
function toPost(raw: RawPost): Post {
    return {
        id: String(raw.id), // 백엔드 int → 프론트 string
        authorName: raw.authorName,
        title: raw.title,
        tags: raw.tags ?? [],
        body: raw.body,
        postType: raw.postType,
        serviceUrl: raw.serviceUrl ?? undefined,
        githubUrl: raw.githubUrl ?? undefined,
        oneLiner: raw.oneLiner ?? undefined,
        targetUser: raw.targetUser ?? undefined,
        techStack: raw.techStack ?? [],
        analysisStatus: raw.analysisStatus,
        aiSummary: raw.aiSummary ?? undefined,
        score: raw.score,
        myVote: raw.myVote as Post["myVote"],
        commentCount: raw.commentCount,
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
            body: input.body,
            postType: input.postType,
            serviceUrl: input.serviceUrl,
            githubUrl: input.githubUrl,
            oneLiner: input.oneLiner,
            targetUser: input.targetUser,
            techStack: input.techStack,
            tagIds: input.tags.map((t) => t.id), // Tag[] → slug 문자열 배열
        },
    });
    return toPost(raw);
}

/* post 투표: POST /posts/{id}/vote */
export async function votePost(
    postId: string,
    value: 1 | -1,
): Promise<{score: number; myVote: Post["myVote"]}> {
    const data = await api<{score: number; myVote: number}>(`/posts/${postId}/vote`, {
        method: "POST",
        body: {value},
    });
    return {
        score: data.score,
        myVote: data.myVote as Post["myVote"],
    };
}
