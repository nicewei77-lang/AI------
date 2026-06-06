import { MOCK_POSTS } from './mockData'
import type { NewPost, Post } from '../types/post'

const PAGE_SIZE = 3

let posts = [...MOCK_POSTS]

function wait(ms = 350) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function normalize(value?: string) {
  return value?.trim().toLowerCase() ?? ''
}

export async function fetchPosts(params?: {
  q?: string
  tag?: string
  cursor?: string
}): Promise<{ items: Post[]; nextCursor?: string }> {
  await wait()

  const q = normalize(params?.q)
  const tag = normalize(params?.tag)
  const cursor = Number(params?.cursor ?? '0')

  const filteredPosts = posts.filter((post) => {
    const searchableText = [
      post.situation,
      post.excuseText,
      post.context.location ?? '',
      post.context.route ?? '',
    ]
      .join(' ')
      .toLowerCase()

    if (q && !searchableText.includes(q)) {
      return false
    }

    if (tag && !post.tags.some((item) => item.name.toLowerCase() === tag)) {
      return false
    }

    return true
  })

  const items = filteredPosts.slice(cursor, cursor + PAGE_SIZE)
  const nextCursor =
    cursor + PAGE_SIZE < filteredPosts.length
      ? String(cursor + PAGE_SIZE)
      : undefined

  return { items, nextCursor }
}

export async function fetchPostById(id: string): Promise<Post> {
  await wait(200)

  const post = posts.find((item) => item.id === id)

  if (!post) {
    throw new Error('게시글을 찾을 수 없습니다.')
  }

  return post
}

export async function createPost(input: NewPost): Promise<Post> {
  await wait()

  const nextPost: Post = {
    id: String(Date.now()),
    ...input,
    createdAt: new Date().toISOString(),
  }

  posts = [nextPost, ...posts]

  return nextPost
}
