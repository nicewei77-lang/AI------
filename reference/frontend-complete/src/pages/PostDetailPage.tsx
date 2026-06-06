import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { fetchPostById } from '../api/posts'
import type { Post } from '../types/post'

function PostDetailPage() {
  const { id } = useParams()
  const postId = id ?? null
  const [post, setPost] = useState<Post | null>(null)
  const [loading, setLoading] = useState(postId !== null)
  const [error, setError] = useState<string | null>(
    postId === null ? '게시글 ID가 없습니다.' : null,
  )

  useEffect(() => {
    if (postId === null) {
      return
    }

    let cancelled = false

    async function loadPost() {
      const validPostId = postId

      if (validPostId === null) {
        return
      }

      setLoading(true)

      try {
        const nextPost = await fetchPostById(validPostId)

        if (!cancelled) {
          setPost(nextPost)
          setError(null)
        }
      } catch (error) {
        if (!cancelled) {
          setError(
            error instanceof Error
              ? error.message
              : '상세 정보를 불러오지 못했습니다.',
          )
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    void loadPost()

    return () => {
      cancelled = true
    }
  }, [postId])

  if (loading) {
    return (
      <div className="rounded-[1.75rem] border border-stone-200 bg-white p-8 text-center text-stone-500">
        사건 상세를 불러오는 중입니다...
      </div>
    )
  }

  if (error || !post) {
    return (
      <div className="space-y-4 rounded-[1.75rem] bg-red-50 p-6 text-red-700">
        <p>{error ?? '게시글을 찾을 수 없습니다.'}</p>
        <Link to="/" className="font-semibold text-red-800 underline">
          목록으로 돌아가기
        </Link>
      </div>
    )
  }

  return (
    <section className="space-y-6 rounded-[2rem] border border-stone-200 bg-white p-6 shadow-[0_18px_40px_-30px_rgba(120,53,15,0.45)]">
      <div className="flex flex-wrap items-center gap-2">
        <span className="rounded-full bg-orange-100 px-3 py-1 text-xs font-semibold text-orange-800">
          {post.situation}
        </span>
        <span className="rounded-full bg-stone-100 px-3 py-1 text-xs font-semibold text-stone-700">
          {post.verdict ?? '재판 전'}
        </span>
        {post.credibility !== undefined ? (
          <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-800">
            신뢰도 {post.credibility}%
          </span>
        ) : null}
      </div>

      <div className="space-y-3">
        <p className="text-sm font-semibold uppercase tracking-[0.25em] text-stone-400">
          Excuse Record
        </p>
        <h2 className="font-serif text-3xl leading-tight text-stone-950">
          {post.excuseText}
        </h2>
      </div>

      <dl className="grid gap-4 rounded-[1.5rem] bg-stone-50 p-5 text-sm text-stone-700 md:grid-cols-2">
        <div>
          <dt className="font-semibold text-stone-900">날짜</dt>
          <dd>{post.context.date}</dd>
        </div>
        <div>
          <dt className="font-semibold text-stone-900">시간</dt>
          <dd>{post.context.time ?? '미입력'}</dd>
        </div>
        <div>
          <dt className="font-semibold text-stone-900">장소</dt>
          <dd>{post.context.location ?? '미입력'}</dd>
        </div>
        <div>
          <dt className="font-semibold text-stone-900">경로</dt>
          <dd>{post.context.route ?? '미입력'}</dd>
        </div>
      </dl>

      <div className="flex flex-wrap gap-2">
        {post.tags.map((tag) => (
          <span
            key={tag.id}
            className="rounded-full border border-stone-200 px-3 py-1 text-xs text-stone-600"
          >
            #{tag.name}
          </span>
        ))}
      </div>

      <Link
        to="/"
        className="inline-flex rounded-full border border-stone-200 px-4 py-2 text-sm font-semibold text-stone-700 transition hover:border-orange-300 hover:text-orange-800"
      >
        목록으로 돌아가기
      </Link>
    </section>
  )
}

export default PostDetailPage
