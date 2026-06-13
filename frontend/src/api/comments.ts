import type {Comment} from "../types/post";
import {api} from "./http";

interface RawComment {
    id: number;
    body: string;
    authorId: number;
    authorName: string;
    createdAt: string;
    likeCount: number;
    myLike: boolean;
}

function toComment(raw: RawComment): Comment {
    return {
        id: String(raw.id),
        body: raw.body,
        authorId: raw.authorId,
        authorName: raw.authorName,
        createdAt: raw.createdAt,
        likeCount: raw.likeCount,
        myLike: raw.myLike,
    };
}

export async function fetchComments(postId: string): Promise<Comment[]> {
    const data = await api<RawComment[]>(`/posts/${postId}/comments`);
    return data.map(toComment);
}

export async function createComment(
    postId: string,
    body: string,
): Promise<Comment> {
    const data = await api<RawComment>(`/posts/${postId}/comments`, {
        method: "POST",
        body: {body},
    });
    return toComment(data);
}

export async function toggleCommentLike(
    commentId: string,
): Promise<{likeCount: number; myLike: boolean}> {
    return api<{likeCount: number; myLike: boolean}>(`/comments/${commentId}/like`, {
        method: "POST",
    });
}
