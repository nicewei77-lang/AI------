import type { Post, Tag } from '../types/post'

export const MOCK_TAGS: Tag[] = [
  { id: 'tag-late', name: '지각' },
  { id: 'tag-work', name: '출근' },
  { id: 'tag-weather', name: '날씨' },
  { id: 'tag-message', name: '미답장' },
]

export const MOCK_POSTS: Post[] = [
  {
    id: '1',
    situation: '지각',
    excuseText: '비가 너무 많이 와서 지하철에서 한참 멈춰 있었어요.',
    context: {
      date: '2026-06-05',
      location: '강남',
      route: '지하철 2호선',
      time: '08:30',
    },
    tags: [MOCK_TAGS[0], MOCK_TAGS[2]],
    verdict: '유죄',
    credibility: 12,
    createdAt: '2026-06-05T08:55:00.000Z',
  },
  {
    id: '2',
    situation: '미답장',
    excuseText: '휴대폰 배터리가 완전히 방전돼서 연락을 못 봤습니다.',
    context: {
      date: '2026-06-04',
      location: '성수',
      time: '21:10',
    },
    tags: [MOCK_TAGS[3]],
    verdict: '보류',
    credibility: 54,
    createdAt: '2026-06-04T21:40:00.000Z',
  },
  {
    id: '3',
    situation: '마감',
    excuseText: '파일은 다 완성했는데 저장 직전에 노트북이 갑자기 재부팅됐어요.',
    context: {
      date: '2026-06-03',
      location: '합정',
      time: '23:20',
    },
    tags: [MOCK_TAGS[1]],
    verdict: '무죄',
    credibility: 78,
    createdAt: '2026-06-03T23:25:00.000Z',
  },
  {
    id: '4',
    situation: '결석',
    excuseText: '아침부터 열이 올라서 병원 다녀오느라 수업에 못 갔어요.',
    context: {
      date: '2026-06-02',
      location: '신촌',
      time: '09:15',
    },
    tags: [MOCK_TAGS[2]],
    createdAt: '2026-06-02T10:05:00.000Z',
  },
]
