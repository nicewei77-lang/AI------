// Day 2 드릴에서 직접 작성합니다.
// fetchPosts, fetchPostById, createPost를 mock API 형태로 구현하세요.

import type {Post} from "../types/post";
import {MOCK_POSTS} from "./mockData";

/* post 목록을 가져오는 함수 */
export async function fetchPosts(
    params?: {q?: string; tag?: string; cursor?: string}
): Promise<{items: Post[]; nextCursor?: string}> {
    // 서버 반환 시간을 모의로 구현한다.
    await new Promise((resolve) => setTimeout(resolve, 300));
    // result를 임의 데이터로 초기화한다.
    let result = MOCK_POSTS;
    // 쿼리로 post의 title을 검사하여 filter한다.
    if (params?.q) {
        result = result.filter(
            (post) => post.title.includes(params.q!)
        );
    }
    // 반환 타입에 맞추어 값을 반환한다.
    return {items: result, nextCursor: undefined};
}




    