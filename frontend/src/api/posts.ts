// Day 2 드릴에서 직접 작성합니다.
// fetchPosts, fetchPostById, createPost를 mock API 형태로 구현하세요.

import type {Post, NewPost} from "../types/post";
import {MOCK_POSTS} from "./mockData";

/* post 목록을 가져오는 함수 */
export async function fetchPosts(
    params?: {q?: string; tagId?: string; cursor?: string}
): Promise<{items: Post[]; nextCursor?: string}> {
    // 네트워크 지연(0.3초)을 흉내 낸다
    await new Promise((resolve) => setTimeout(resolve, 300));
    // result를 전체 원본 데이터로 초기화한다.
    let result = MOCK_POSTS;
    // params이 있다면, 쿼리로 post의 title을 검사하여 filter한다.
    if (params?.q) {
        result = result.filter(
            (post) => post.title.includes(params.q!)
        );
    }
    // tag filter
    if (params?.tagId) {
        result = result.filter(
            (post) => post.tags.some((t) => t.id === params.tagId)
        );
    }
    // 반환 타입에 맞추어 값을 반환한다.
    return {items: result, nextCursor: undefined};
}

/* id를 받아 post 한 개를 가져오는 함수 */
export async function fetchPostById(id: string): Promise<Post> {
    await new Promise((resolve) => setTimeout(resolve, 300));
    // 원본 데이터에서 id가 일치하는 post를 찾아 found에 저장한다.
    const found = MOCK_POSTS.find((post) => post.id === id);
    // 해당하는 id를 가진 post를 찾을 수 없을 경우 에러 메세지와 id를 호출부에 알린다.
    if (!found) {
        throw new Error("글을 찾을 수 없습니다: " + id);
    }

    return found;
}

/* 새 변명글을 제출하는 함수 */
export async function createPost(input: NewPost): Promise<Post> {
    await new Promise((resolve) => setTimeout(resolve, 300));
    // 반환할 Post를 만든다.
    const newPost: Post = {
        ...input,
        id: crypto.randomUUID(),
        createdAt: new Date().toISOString(),
    };
    // 원본 데이터에 새로운 변명글을 추가한다.
    MOCK_POSTS.push(newPost);

    return newPost;
}