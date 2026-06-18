// Day 2 드릴에서 직접 작성합니다.
// useParams와 fetchPostById를 이용해 상세 화면을 구현하세요.
import {useState, useEffect} from "react";
import type {FormEvent} from "react";
import {useNavigate, useParams} from "react-router-dom";
import {fetchAnalysisStatus, fetchLatestAnalysis, startAnalysisJob} from "../api/analysis";
import {createComment, fetchComments, toggleCommentLike} from "../api/comments";
import {fetchPostById, votePost} from "../api/posts";
import AnalysisReport from "../components/analysis/AnalysisReport";
import AnalysisStatusBadge from "../components/analysis/AnalysisStatusBadge";
import {useAuth} from "../context/AuthContext";
import type {AnalysisResponse} from "../types/analysis";
import type {Comment, Post} from "../types/post";

type PageMessage = {
    text: string;
    kind: "success" | "error" | "info";
};

const ANALYSIS_POLL_INTERVAL_MS = 2500;
const ANALYSIS_POLL_MAX_ATTEMPTS = 120;

function sleep(ms: number) {
    return new Promise((resolve) => window.setTimeout(resolve, ms));
}

function PostDetailPage() {
    const {id} = useParams();
    const navigate = useNavigate();
    const {isLoggedIn} = useAuth();
    const [post, setPost] = useState<Post | null>(null);
    const [comments, setComments] = useState<Comment[]>([]);
    const [commentBody, setCommentBody] = useState("");
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [message, setMessage] = useState<PageMessage | null>(null);
    const [commentSubmitting, setCommentSubmitting] = useState(false);
    const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
    const [analysisLoading, setAnalysisLoading] = useState(true);
    const [analysisRunning, setAnalysisRunning] = useState(false);
    const [analysisError, setAnalysisError] = useState<string | null>(null);

    function handleBack() {
        navigate("/", {replace: true});
    }

    const backButton = (
        <button
            type="button"
            onClick={handleBack}
            className="rounded-full border border-stone-300 px-3 py-2 text-sm font-semibold text-stone-700 hover:bg-stone-100"
        >
            뒤로
        </button>
    );

    useEffect(() => {
        if (!id) return;

        let cancelled = false;

        async function load() {
            setLoading(true);
            setAnalysisLoading(true);
            setAnalysis(null);
            setAnalysisError(null);
            try {
                const [postData, commentData] = await Promise.all([
                    fetchPostById(id!),
                    fetchComments(id!),
                ]);
                if (!cancelled) {
                    setPost(postData);
                    setComments(commentData);
                    setError(null);
                }
            } catch (err) {
                if (!cancelled) {
                    setError(err instanceof Error ? err.message : "글을 불러오지 못했습니다");
                    setAnalysisLoading(false);
                }
                return;
            } finally {
                if (!cancelled) setLoading(false);
            }

            try {
                const latest = await fetchLatestAnalysis(id!);
                if (!cancelled) {
                    setAnalysis(latest);
                    setAnalysisError(null);
                }
            } catch (err) {
                if (!cancelled) {
                    setAnalysisError(
                        err instanceof Error
                            ? err.message
                            : "최신 AI 리포트를 확인하지 못했습니다.",
                    );
                }
            } finally {
                if (!cancelled) setAnalysisLoading(false);
            }
        }
        void load();

        return () => {
            cancelled = true;
        };
    }, [id]);

    async function handleRunAnalysis() {
        if (!post) return;

        setAnalysisRunning(true);
        setAnalysisError(null);
        setMessage(null);
        setPost({...post, analysisStatus: "running"});

        try {
            const started = await startAnalysisJob(post.id);
            setPost((prev) => (prev ? {...prev, analysisStatus: started.status} : prev));

            let finalStatus = started.status;
            for (let attempt = 0; attempt < ANALYSIS_POLL_MAX_ATTEMPTS; attempt += 1) {
                if (finalStatus !== "running") break;
                await sleep(ANALYSIS_POLL_INTERVAL_MS);
                const next = await fetchAnalysisStatus(post.id);
                finalStatus = next.status;
                setPost((prev) => (prev ? {...prev, analysisStatus: next.status} : prev));
            }

            if (finalStatus === "running") {
                throw new Error("AI 분석이 예상보다 오래 걸리고 있습니다. 잠시 후 다시 확인해주세요.");
            }

            const [refreshedPost, latest] = await Promise.all([fetchPostById(post.id), fetchLatestAnalysis(post.id)]);
            setPost(refreshedPost);
            setAnalysis(latest);
            if (!latest) {
                throw new Error("AI 분석 작업은 종료되었지만 저장된 리포트를 찾지 못했습니다.");
            }
            setMessage({
                text:
                    latest.status === "completed"
                        ? "AI 프로젝트 리뷰가 완료되었습니다."
                        : "AI 프로젝트 리뷰 결과가 저장되었습니다.",
                kind: latest.status === "failed" || latest.status === "refused" ? "info" : "success",
            });
        } catch (err) {
            const text = err instanceof Error ? err.message : "AI 프로젝트 리뷰 요청을 완료하지 못했습니다.";
            setAnalysisError(text);
            setMessage({text, kind: "error"});
            try {
                const refreshedPost = await fetchPostById(post.id);
                setPost(refreshedPost);
            } catch {
                setPost((prev) => (prev ? {...prev, analysisStatus: "failed"} : prev));
            }
        } finally {
            setAnalysisRunning(false);
        }
    }

    async function handleVote(value: 1 | -1) {
        if (!post) return;
        if (!isLoggedIn) {
            setMessage({text: "로그인 후 투표할 수 있습니다.", kind: "info"});
            return;
        }
        try {
            const next = await votePost(post.id, value);
            setPost({...post, score: next.score, myVote: next.myVote});
            setMessage(null);
        } catch (err) {
            setMessage({
                text: err instanceof Error ? err.message : "투표에 실패했습니다.",
                kind: "error",
            });
        }
    }

    async function handleShare() {
        try {
            await navigator.clipboard.writeText(window.location.href);
            setMessage({text: "링크를 복사했습니다.", kind: "success"});
        } catch {
            setMessage({text: "주소를 복사하지 못했습니다.", kind: "error"});
        }
    }

    async function handleCommentSubmit(e: FormEvent) {
        e.preventDefault();
        if (!id) return;
        const body = commentBody.trim();
        if (!body) return;
        if (!isLoggedIn) {
            setMessage({text: "로그인 후 댓글을 작성할 수 있습니다.", kind: "info"});
            return;
        }

        setCommentSubmitting(true);
        setMessage(null);
        try {
            const created = await createComment(id, body);
            setComments((prev) => [...prev, created]);
            setCommentBody("");
        } catch (err) {
            setMessage({
                text: err instanceof Error ? err.message : "댓글 작성에 실패했습니다.",
                kind: "error",
            });
        } finally {
            setCommentSubmitting(false);
        }
    }

    async function handleCommentLike(commentId: string) {
        if (!isLoggedIn) {
            setMessage({text: "로그인 후 댓글 좋아요를 누를 수 있습니다.", kind: "info"});
            return;
        }
        try {
            const next = await toggleCommentLike(commentId);
            setComments((prev) =>
                prev.map((comment) =>
                    comment.id === commentId
                        ? {...comment, likeCount: next.likeCount, myLike: next.myLike}
                        : comment,
                ),
            );
            setMessage(null);
        } catch (err) {
            setMessage({
                text: err instanceof Error ? err.message : "댓글 좋아요에 실패했습니다.",
                kind: "error",
            });
        }
    }

    if (loading) {
        if (!id) {
            return (
                <div className="mx-auto max-w-3xl px-4 py-8">
                    {backButton}
                    <p className="mt-6 rounded border border-red-200 bg-red-50 p-4 text-red-700">
                        글 ID가 없습니다.
                    </p>
                </div>
            );
        }

        return (
            <div className="mx-auto max-w-3xl px-4 py-8">
                {backButton}
                <p className="mt-6 rounded border border-stone-200 bg-white p-4">불러오는 중...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="mx-auto max-w-3xl px-4 py-8">
                {backButton}
                <p className="mt-6 rounded border border-red-200 bg-red-50 p-4 text-red-700">{error}</p>
            </div>
        );
    }

    if (!post) return null;

    return (
        <main className="min-h-screen bg-stone-50 px-4 py-6 text-stone-950">
            <div className="mx-auto max-w-7xl space-y-4">
                <div className="mx-auto max-w-3xl">{backButton}</div>

                <article className="mx-auto max-w-3xl rounded border border-stone-200 bg-white p-5">
                    <div className="mb-3 flex flex-wrap items-center gap-2 text-xs text-stone-500">
                        <span>@{post.authorName}</span>
                        <span>·</span>
                        <time>{new Date(post.createdAt).toLocaleString()}</time>
                        <AnalysisStatusBadge status={post.analysisStatus} />
                    </div>
                    <h1 className="mb-4 text-2xl font-bold leading-tight">{post.title}</h1>
                    {post.oneLiner ? (
                        <p className="mb-4 text-base font-semibold text-stone-800">{post.oneLiner}</p>
                    ) : null}

                    <div className="mb-4 grid gap-2 rounded border border-stone-200 bg-stone-50 p-3 text-sm text-stone-700">
                        <div>
                            <span className="font-semibold">분석 상태</span>{" "}
                            <AnalysisStatusBadge status={post.analysisStatus} />
                        </div>
                        {post.serviceUrl ? (
                            <a
                                className="font-semibold text-orange-700 hover:underline"
                                href={post.serviceUrl}
                                target="_blank"
                                rel="noreferrer"
                            >
                                서비스 URL
                            </a>
                        ) : null}
                        {post.githubUrl ? (
                            <a
                                className="font-semibold text-orange-700 hover:underline"
                                href={post.githubUrl}
                                target="_blank"
                                rel="noreferrer"
                            >
                                GitHub URL
                            </a>
                        ) : null}
                        {post.targetUser ? (
                            <div>
                                <span className="font-semibold">타깃 사용자</span> {post.targetUser}
                            </div>
                        ) : null}
                        {post.techStack.length > 0 ? (
                            <div className="flex flex-wrap gap-2">
                                {post.techStack.map((tech) => (
                                    <span key={tech} className="rounded-full bg-white px-2 py-1 text-xs">
                                        {tech}
                                    </span>
                                ))}
                            </div>
                        ) : null}
                    </div>

                    {post.aiSummary ? (
                        <p className="mb-4 rounded border border-stone-200 bg-stone-50 p-3 text-sm text-stone-700">
                            {post.aiSummary}
                        </p>
                    ) : null}
                </article>

                <AnalysisReport
                    analysis={analysis}
                    post={post}
                    postStatus={post.analysisStatus}
                    isLoading={analysisLoading}
                    isRunning={analysisRunning}
                    error={analysisError}
                    onRun={() => void handleRunAnalysis()}
                />

                <section className="mx-auto max-w-3xl rounded border border-stone-200 bg-white p-5">
                    <p className="whitespace-pre-wrap leading-7 text-stone-800">{post.body}</p>

                    <div className="mt-5 flex flex-wrap gap-2">
                        {post.tags.map((tag) => (
                            <span
                                key={tag.id}
                                className="rounded-full bg-stone-100 px-2 py-1 text-xs font-medium text-stone-600"
                            >
                                #{tag.label}
                            </span>
                        ))}
                    </div>

                    <div className="mt-5 flex flex-wrap items-center gap-2 border-t border-stone-200 pt-4">
                        <button
                            type="button"
                            onClick={() => void handleVote(1)}
                            className={`rounded-full px-3 py-1 text-sm font-semibold ${
                                post.myVote === 1
                                    ? "bg-orange-600 text-white"
                                    : "bg-stone-100 text-stone-700 hover:bg-stone-200"
                            }`}
                        >
                            ▲
                        </button>
                        <span className="rounded-full bg-white px-3 py-1 text-sm font-bold text-stone-800">
                            {post.score}
                        </span>
                        <button
                            type="button"
                            onClick={() => void handleVote(-1)}
                            className={`rounded-full px-3 py-1 text-sm font-semibold ${
                                post.myVote === -1
                                    ? "bg-blue-700 text-white"
                                    : "bg-stone-100 text-stone-700 hover:bg-stone-200"
                            }`}
                        >
                            ▼
                        </button>
                        <button
                            type="button"
                            onClick={() => void handleShare()}
                            className="rounded-full bg-stone-100 px-3 py-1 text-sm font-semibold text-stone-700 hover:bg-stone-200"
                        >
                            공유
                        </button>
                    </div>
                </section>

                {message ? (
                    <p
                        className={`mx-auto max-w-3xl rounded border p-3 text-sm ${
                            message.kind === "success"
                                ? "border-emerald-200 bg-emerald-50 text-emerald-800"
                                : message.kind === "error"
                                  ? "border-red-200 bg-red-50 text-red-700"
                                  : "border-stone-200 bg-white text-stone-700"
                        }`}
                    >
                        {message.text}
                    </p>
                ) : null}

                <section className="mx-auto max-w-3xl rounded border border-stone-200 bg-white p-5">
                    <h2 className="mb-4 text-lg font-bold">댓글</h2>
                    {isLoggedIn ? (
                        <form onSubmit={handleCommentSubmit} className="mb-5 space-y-3">
                            <textarea
                                className="min-h-24 w-full rounded border border-stone-300 p-3 text-sm outline-none focus:border-orange-400"
                                placeholder="댓글을 입력하세요"
                                value={commentBody}
                                onChange={(e) => setCommentBody(e.target.value)}
                            />
                            <button
                                type="submit"
                                disabled={commentSubmitting || commentBody.trim().length === 0}
                                className="rounded-full bg-stone-900 px-4 py-2 text-sm font-semibold text-white hover:bg-stone-700 disabled:cursor-not-allowed disabled:bg-stone-300"
                            >
                                댓글 작성
                            </button>
                        </form>
                    ) : (
                        <p className="mb-5 rounded bg-stone-100 p-3 text-sm text-stone-600">
                            로그인하면 댓글을 작성하고 좋아요를 누를 수 있습니다.
                        </p>
                    )}

                    <div className="divide-y divide-stone-200">
                        {comments.length === 0 ? (
                            <p className="py-6 text-center text-sm text-stone-500">
                                아직 댓글이 없습니다.
                            </p>
                        ) : (
                            comments.map((comment) => (
                                <article key={comment.id} className="py-4">
                                    <div className="mb-2 flex flex-wrap items-center gap-2 text-xs text-stone-500">
                                        <span>@{comment.authorName}</span>
                                        <span>·</span>
                                        <time>{new Date(comment.createdAt).toLocaleString()}</time>
                                    </div>
                                    <p className="mb-3 whitespace-pre-wrap text-sm leading-6 text-stone-800">
                                        {comment.body}
                                    </p>
                                    <button
                                        type="button"
                                        onClick={() => void handleCommentLike(comment.id)}
                                        className={`rounded-full px-3 py-1 text-sm font-semibold ${
                                            comment.myLike
                                                ? "bg-orange-600 text-white"
                                                : "bg-stone-100 text-stone-700 hover:bg-stone-200"
                                        }`}
                                    >
                                        좋아요 {comment.likeCount}
                                    </button>
                                </article>
                            ))
                        )}
                    </div>
                </section>
            </div>
        </main>
    );
}

export default PostDetailPage;
