// Day 2 드릴에서 직접 작성합니다.
// fetchPosts, fetchPostById, createPost를 mock API 형태로 구현하세요.

import type {Post} from "../types/post";
import {MOCK_POSTS} from "./mockData";

/* post 목록을 가져오는 함수 */
export async function fetchPosts(
    params?: {q?: string; tagId?: string; cursor?: string}
): Promise<{items: Post[]; nextCursor?: string}> {
    // 서버 반환 시간을 모의로 구현한다.
    await new Promise((resolve) => setTimeout(resolve, 300));
    // result를 임의 데이터로 초기화한다.
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
export async function fetchPostById(id: string): Promise<(item: Post)> {
    await new Promise((resolve) => setTimeout(resolve, 300));

    const found = MOCK_POSTS.find((post) => post.id === id);

    if (!found) {
        throw new Error("글을 찾을 수 없습니다.: " + id);
    }

    return (item: found);
}





    // tag filter
