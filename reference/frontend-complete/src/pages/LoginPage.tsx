import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/useAuth'

function LoginPage() {
  const navigate = useNavigate()
  const { isLoggedIn, login } = useAuth()
  const [email, setEmail] = useState('student@alibai.dev')
  const [password, setPassword] = useState('1234')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSubmitting(true)

    try {
      await login(email, password)
      setError(null)
      navigate('/new')
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : '로그인에 실패했습니다.',
      )
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section className="mx-auto max-w-xl space-y-6 rounded-[2rem] border border-stone-200 bg-white p-6 shadow-[0_18px_40px_-30px_rgba(120,53,15,0.45)]">
      <div className="space-y-3">
        <p className="text-xs font-semibold uppercase tracking-[0.35em] text-orange-700">
          Auth Context
        </p>
        <h2 className="font-serif text-3xl text-stone-950">로그인 연습 페이지</h2>
        <p className="text-sm leading-6 text-stone-600">
          이번 주에는 진짜 JWT 대신 가짜 토큰만 발급합니다. 로그인하면
          Context에 상태를 올리고 보호된 작성 페이지로 이동합니다.
        </p>
      </div>

      {isLoggedIn ? (
        <div className="rounded-[1.5rem] bg-emerald-50 p-4 text-sm text-emerald-800">
          이미 로그인된 상태입니다. 바로
          <Link to="/new" className="mx-1 font-semibold underline">
            작성 페이지
          </Link>
          로 이동해도 됩니다.
        </div>
      ) : null}

      <form onSubmit={handleSubmit} className="space-y-4">
        <label className="block space-y-2 text-sm font-medium text-stone-700">
          이메일
          <input
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            className="w-full rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 outline-none transition focus:border-orange-400 focus:bg-white"
          />
        </label>

        <label className="block space-y-2 text-sm font-medium text-stone-700">
          비밀번호
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            className="w-full rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 outline-none transition focus:border-orange-400 focus:bg-white"
          />
        </label>

        {error ? (
          <p className="rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </p>
        ) : null}

        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-full bg-stone-950 px-5 py-3 text-sm font-semibold text-white transition hover:bg-orange-700 disabled:cursor-not-allowed disabled:bg-stone-400"
        >
          {submitting ? '로그인 중...' : '가짜 로그인하기'}
        </button>
      </form>
    </section>
  )
}

export default LoginPage
