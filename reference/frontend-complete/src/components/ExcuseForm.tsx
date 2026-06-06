import { useState, type FormEvent } from 'react'
import type { NewPost, Situation } from '../types/post'

const situationOptions: Situation[] = ['지각', '결석', '미답장', '마감']

interface ExcuseFormProps {
  onSubmit: (input: NewPost) => Promise<void> | void
  submitting?: boolean
}

function ExcuseForm({ onSubmit, submitting = false }: ExcuseFormProps) {
  const [situation, setSituation] = useState<Situation>('지각')
  const [excuseText, setExcuseText] = useState('')
  const [date, setDate] = useState('2026-06-07')
  const [location, setLocation] = useState('강남')
  const [route, setRoute] = useState('지하철 2호선')
  const [time, setTime] = useState('09:00')
  const [tagInput, setTagInput] = useState('지각,출근')
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    if (!excuseText.trim()) {
      setError('변명 본문을 먼저 적어 주세요.')
      return
    }

    const tags = tagInput
      .split(',')
      .map((tag) => tag.trim())
      .filter(Boolean)
      .map((tag, index) => ({
        id: `tag-${Date.now()}-${index}`,
        name: tag,
      }))

    setError(null)

    await onSubmit({
      situation,
      excuseText: excuseText.trim(),
      context: {
        date,
        location: location.trim() || undefined,
        route: route.trim() || undefined,
        time: time.trim() || undefined,
      },
      tags,
    })
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-5 rounded-[2rem] border border-stone-200 bg-white p-6 shadow-[0_18px_40px_-30px_rgba(120,53,15,0.45)]"
    >
      <div className="grid gap-5 md:grid-cols-2">
        <label className="space-y-2 text-sm font-medium text-stone-700">
          상황
          <select
            value={situation}
            onChange={(event) => setSituation(event.target.value as Situation)}
            className="w-full rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 outline-none transition focus:border-orange-400 focus:bg-white"
          >
            {situationOptions.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </label>

        <label className="space-y-2 text-sm font-medium text-stone-700">
          태그
          <input
            value={tagInput}
            onChange={(event) => setTagInput(event.target.value)}
            placeholder="지각,출근"
            className="w-full rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 outline-none transition focus:border-orange-400 focus:bg-white"
          />
        </label>
      </div>

      <label className="block space-y-2 text-sm font-medium text-stone-700">
        변명 본문
        <textarea
          value={excuseText}
          onChange={(event) => setExcuseText(event.target.value)}
          rows={6}
          placeholder="무슨 일이 있었는지 적어 보세요."
          className="w-full rounded-[1.5rem] border border-stone-200 bg-stone-50 px-4 py-3 outline-none transition focus:border-orange-400 focus:bg-white"
        />
      </label>

      <div className="grid gap-5 md:grid-cols-2">
        <label className="space-y-2 text-sm font-medium text-stone-700">
          날짜
          <input
            type="date"
            value={date}
            onChange={(event) => setDate(event.target.value)}
            className="w-full rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 outline-none transition focus:border-orange-400 focus:bg-white"
          />
        </label>

        <label className="space-y-2 text-sm font-medium text-stone-700">
          시간
          <input
            type="time"
            value={time}
            onChange={(event) => setTime(event.target.value)}
            className="w-full rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 outline-none transition focus:border-orange-400 focus:bg-white"
          />
        </label>

        <label className="space-y-2 text-sm font-medium text-stone-700">
          장소
          <input
            value={location}
            onChange={(event) => setLocation(event.target.value)}
            placeholder="강남"
            className="w-full rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 outline-none transition focus:border-orange-400 focus:bg-white"
          />
        </label>

        <label className="space-y-2 text-sm font-medium text-stone-700">
          경로
          <input
            value={route}
            onChange={(event) => setRoute(event.target.value)}
            placeholder="지하철 2호선"
            className="w-full rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 outline-none transition focus:border-orange-400 focus:bg-white"
          />
        </label>
      </div>

      {error ? (
        <p className="rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </p>
      ) : null}

      <button
        type="submit"
        disabled={submitting}
        className="rounded-full bg-stone-950 px-5 py-3 text-sm font-semibold text-white transition hover:bg-orange-700 disabled:cursor-not-allowed disabled:bg-stone-400"
      >
        {submitting ? '제출 중...' : 'mock API로 제출하기'}
      </button>
    </form>
  )
}

export default ExcuseForm
