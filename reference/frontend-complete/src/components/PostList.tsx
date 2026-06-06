import PostCard from './PostCard'
import type { Post } from '../types/post'

function PostList({ posts }: { posts: Post[] }) {
  if (posts.length === 0) {
    return (
      <div className="rounded-[1.75rem] border border-dashed border-stone-300 bg-white/70 p-10 text-center text-stone-500">
        조건에 맞는 사건이 아직 없습니다.
      </div>
    )
  }

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      {posts.map((post) => (
        <PostCard key={post.id} post={post} />
      ))}
    </div>
  )
}

export default PostList
