function App() {
  return (
    <main className="min-h-screen bg-[linear-gradient(180deg,#fffaf1_0%,#f9f0e6_100%)] px-6 py-12 text-stone-900">
      <div className="mx-auto max-w-4xl rounded-[2rem] border border-stone-200 bg-white/90 p-8 shadow-[0_24px_80px_-48px_rgba(120,53,15,0.45)]">
        <p className="text-xs font-semibold uppercase tracking-[0.35em] text-orange-700">
          P0 Learning Workspace
        </p>
        <h1 className="mt-4 font-serif text-4xl leading-tight text-stone-950">
          ALIBAI 프론트 학습용 기본 세팅
        </h1>
        <p className="mt-4 text-base leading-7 text-stone-600">
          이 `frontend/`는 학습용 작업 트리입니다. 라우터와 Tailwind 연결,
          폴더 골격만 준비되어 있고 Day 1~3 드릴 코드는 비워 둔 상태입니다.
        </p>

        <section className="mt-8 grid gap-4 md:grid-cols-2">
          <div className="rounded-[1.5rem] bg-orange-50 p-5">
            <h2 className="text-lg font-semibold text-stone-900">
              지금 여기서 할 일
            </h2>
            <ul className="mt-3 space-y-2 text-sm leading-6 text-stone-700">
              <li>`src/types/post.ts`부터 직접 타입 작성</li>
              <li>`pages/`, `components/`는 드릴하면서 채우기</li>
              <li>`api/`는 mock 함수 연습용으로 직접 구현</li>
            </ul>
          </div>

          <div className="rounded-[1.5rem] bg-stone-100 p-5">
            <h2 className="text-lg font-semibold text-stone-900">
              참고용 완성본
            </h2>
            <p className="mt-3 text-sm leading-6 text-stone-700">
              이미 만들어 둔 완성 예시는
              `reference/frontend-complete/`에 보관했습니다. 드릴을 먼저 한 뒤
              비교용으로만 보는 것을 권장합니다.
            </p>
          </div>
        </section>
      </div>
    </main>
  )
}

export default App
