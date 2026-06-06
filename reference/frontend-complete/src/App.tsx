import { Link, Route, Routes } from 'react-router-dom'
import ProtectedRoute from './components/ProtectedRoute'
import { useAuth } from './context/useAuth'
import LoginPage from './pages/LoginPage'
import PostCreatePage from './pages/PostCreatePage'
import PostDetailPage from './pages/PostDetailPage'
import PostListPage from './pages/PostListPage'

function App() {
  const { isLoggedIn, logout } = useAuth()

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,#fff4d9_0%,#fff9ef_45%,#f8efe6_100%)] text-stone-900">
      <div className="mx-auto flex min-h-screen max-w-6xl flex-col px-4 py-6 sm:px-6 lg:px-8">
        <header className="mb-8 rounded-[2rem] border border-stone-200/70 bg-white/90 p-6 shadow-[0_24px_80px_-48px_rgba(120,53,15,0.55)] backdrop-blur">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div className="space-y-3">
              <p className="text-xs font-semibold uppercase tracking-[0.35em] text-orange-700">
                ALIBAI Front Lab
              </p>
              <div className="space-y-2">
                <h1 className="font-serif text-4xl leading-tight text-stone-950 sm:text-5xl">
                  변명 검증소 프론트엔드 학습 환경
                </h1>
                <p className="max-w-2xl text-sm leading-6 text-stone-600 sm:text-base">
                  React, TypeScript, mock API, Context, 라우팅을 단계적으로
                  연습할 수 있게 기본 뼈대를 먼저 세팅해 둔 상태입니다.
                </p>
              </div>
            </div>

            <nav className="flex flex-wrap items-center gap-2 text-sm font-medium">
              <Link
                to="/"
                className="rounded-full border border-stone-200 bg-stone-50 px-4 py-2 text-stone-700 transition hover:border-orange-300 hover:bg-orange-50 hover:text-orange-800"
              >
                사건 목록
              </Link>
              <Link
                to="/new"
                className="rounded-full border border-stone-200 bg-stone-50 px-4 py-2 text-stone-700 transition hover:border-orange-300 hover:bg-orange-50 hover:text-orange-800"
              >
                새 변명 작성
              </Link>
              {isLoggedIn ? (
                <button
                  type="button"
                  onClick={logout}
                  className="rounded-full bg-stone-950 px-4 py-2 text-white transition hover:bg-orange-700"
                >
                  로그아웃
                </button>
              ) : (
                <Link
                  to="/login"
                  className="rounded-full bg-stone-950 px-4 py-2 text-white transition hover:bg-orange-700"
                >
                  로그인
                </Link>
              )}
            </nav>
          </div>
        </header>

        <main className="flex-1">
          <Routes>
            <Route path="/" element={<PostListPage />} />
            <Route path="/posts/:id" element={<PostDetailPage />} />
            <Route
              path="/new"
              element={
                <ProtectedRoute>
                  <PostCreatePage />
                </ProtectedRoute>
              }
            />
            <Route path="/login" element={<LoginPage />} />
          </Routes>
        </main>
      </div>
    </div>
  )
}

export default App
