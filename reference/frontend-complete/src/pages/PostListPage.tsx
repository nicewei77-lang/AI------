import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { MOCK_TAGS } from '../api/mockData'
import { fetchPosts } from '../api/posts'
import PostList from '../components/PostList'
import type { Post } from '../types/post'

function PostListPage() {
  const [posts, setPosts] = useState<Post[]>([])
  const [query, setQuery] = useState('')
  const [tag, setTag] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function loadPosts() {
      setLoading(true)

      try {
        const response = await fetchPosts({
          q: query.trim() || undefined,
          tag: tag || undefined,
        })

        if (!cancelled) {
          setPosts(response.items)
          setError(null)
        }
      } catch (error) {
        if (!cancelled) {
          setError(
            error instanceof Error
              ? error.message
              : '목록을 불러오는 중 오류가 발생했습니다.',
          )
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    void loadPosts()

    return () => {
      cancelled = true
    }
  }, [query, tag])

  return (
    <section className="space-y-6">
      <div className="grid gap-4 rounded-[2rem] border border-stone-200 bg-white/90 p-6 shadow-[0_18px_40px_-32px_rgba(120,53,15,0.4)] lg:grid-cols-[1.4fr_0.8fr_auto] lg:items-end">
        <label className="space-y-2 text-sm font-medium text-stone-700">
          키워드 검색
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="비, 지하철, 방전 같은 단어로 찾아보세요."
            className="w-full rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 outline-none transition focus:border-orange-400 focus:bg-white"
          />
        </label>

        <label className="space-y-2 text-sm font-medium text-stone-700">
          태그 필터
          <select
            value={tag}
            onChange={(event) => setTag(event.target.value)}
            className="w-full rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 outline-none transition focus:border-orange-400 focus:bg-white"
          >
            <option value="">전체 태그</option>
            {MOCK_TAGS.map((item) => (
              <option key={item.id} value={item.name}>
                {item.name}
              </option>
            ))}
          </select>
        </label>

        <Link
          to="/new"
          className="inline-flex items-center justify-center rounded-full bg-stone-950 px-5 py-3 text-sm font-semibold text-white transition hover:bg-orange-700"
        >
          새 사건 작성
        </Link>
      </div>

      <div className="rounded-[2rem] border border-dashed border-orange-200 bg-orange-50/70 p-5 text-sm leading-6 text-orange-900">
        이 화면은 학습용 mock 환경입니다. 검색과 태그 필터는 화면이 아니라
        <code className="mx-1 rounded bg-white px-2 py-1 text-xs">
          api/posts.ts
        </code>
        내부에서 처리되도록 맞춰 두었습니다.
      </div>

      {error ? (
        <div className="rounded-[1.75rem] bg-red-50 p-5 text-sm text-red-700">
          {error}
        </div>
      ) : null}

      {loading ? (
        <div className="rounded-[1.75rem] border border-stone-200 bg-white p-8 text-center text-stone-500">
          사건 목록을 불러오는 중입니다...
        </div>
      ) : (
        <PostList posts={posts} />
      )}
    </section>
  )
}

export default PostListPage
