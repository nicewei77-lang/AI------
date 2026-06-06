import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { createPost } from '../api/posts'
import ExcuseForm from '../components/ExcuseForm'
import type { NewPost } from '../types/post'

function PostCreatePage() {
  const navigate = useNavigate()
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(input: NewPost) {
    setSubmitting(true)

    try {
      const post = await createPost(input)
      setError(null)
      navigate(`/posts/${post.id}`)
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : '게시글을 저장하지 못했습니다.',
      )
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section className="space-y-6">
      <div className="rounded-[2rem] border border-stone-200 bg-white/90 p-6 shadow-[0_18px_40px_-30px_rgba(120,53,15,0.45)]">
        <p className="text-xs font-semibold uppercase tracking-[0.35em] text-orange-700">
          Protected Route
        </p>
        <h2 className="mt-3 font-serif text-3xl text-stone-950">
          새 변명 작성
        </h2>
        <p className="mt-2 text-sm leading-6 text-stone-600">
          이 페이지는 로그인해야만 접근할 수 있습니다. 제출하면 mock API에
          저장한 뒤 상세 페이지로 이동합니다.
        </p>
      </div>

      {error ? (
        <div className="rounded-[1.75rem] bg-red-50 p-5 text-sm text-red-700">
          {error}
        </div>
      ) : null}

      <ExcuseForm onSubmit={handleSubmit} submitting={submitting} />
    </section>
  )
}

export default PostCreatePage
