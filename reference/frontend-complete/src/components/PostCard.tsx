import { Link } from 'react-router-dom'
import type { Post } from '../types/post'

function formatDate(date: string) {
  return new Intl.DateTimeFormat('ko-KR', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(date))
}

function PostCard({ post }: { post: Post }) {
  return (
    <article className="rounded-[1.75rem] border border-stone-200 bg-white p-5 shadow-[0_18px_40px_-30px_rgba(120,53,15,0.45)] transition hover:-translate-y-0.5 hover:shadow-[0_24px_56px_-32px_rgba(120,53,15,0.5)]">
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <span className="rounded-full bg-orange-100 px-3 py-1 text-xs font-semibold text-orange-800">
          {post.situation}
        </span>
        {post.verdict ? (
          <span className="rounded-full bg-stone-900 px-3 py-1 text-xs font-semibold text-white">
            {post.verdict}
          </span>
        ) : (
          <span className="rounded-full bg-stone-100 px-3 py-1 text-xs font-semibold text-stone-600">
            재판 전
          </span>
        )}
      </div>

      <p className="mb-4 text-lg font-semibold leading-7 text-stone-900">
        {post.excuseText}
      </p>

      <dl className="grid gap-2 text-sm text-stone-600 sm:grid-cols-2">
        <div>
          <dt className="font-medium text-stone-800">날짜</dt>
          <dd>{post.context.date}</dd>
        </div>
        <div>
          <dt className="font-medium text-stone-800">장소</dt>
          <dd>{post.context.location ?? '미입력'}</dd>
        </div>
      </dl>

      <div className="mt-4 flex flex-wrap gap-2">
        {post.tags.map((tag) => (
          <span
            key={tag.id}
            className="rounded-full border border-stone-200 px-3 py-1 text-xs text-stone-600"
          >
            #{tag.name}
          </span>
        ))}
      </div>

      <div className="mt-5 flex items-center justify-between text-sm">
        <span className="text-stone-500">{formatDate(post.createdAt)}</span>
        <Link
          to={`/posts/${post.id}`}
          className="font-semibold text-orange-700 transition hover:text-orange-900"
        >
          상세 보기
        </Link>
      </div>
    </article>
  )
}

export default PostCard
