// Day 2 드릴에서 직접 작성합니다.
// useParams와 fetchPostById를 이용해 상세 화면을 구현하세요.
import {useState, useEffect} from "react";
import {useParams} from "react-router-dom";
import {fetchPostById} from "../api/posts";
import type {Post} from "../types/post";

function postDetailPage() {
    const {id} = useParams();
    const [post, setPost] = useState<Post | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function load() {
            try {const data = await fetchPostById(id!);
            setPost(data);
            } catch {
                setError("글을 불러오지 못했습니다");
            } finally {
                setLoading(false);
            }
        };
    load();
    }, [id]);   

    if (loading) return <p className="p-8">불러오는 중...</p>;
    if (error) return <p className="p-8 text-red-600">{error}</p>;
    if (!post) return null;

    return (
        <div className="mx-auto max-w-2xl px-4 py-8">
            <h1 className="mb-4 text-2xl font-bold">{post.title}</h1>
            <p>{post.excuseText}</p>
        </div>
    );
}

export default postDetailPage;
