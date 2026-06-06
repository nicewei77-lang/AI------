export type Verdict = '무죄' | '보류' | '유죄'

export type Situation = '지각' | '결석' | '미답장' | '마감'

export interface ExcuseContext {
  date: string
  location?: string
  route?: string
  time?: string
}

export interface Tag {
  id: string
  name: string
}

export interface Post {
  id: string
  situation: Situation
  excuseText: string
  context: ExcuseContext
  tags: Tag[]
  verdict?: Verdict
  credibility?: number
  createdAt: string
}

export interface NewPost {
  situation: Situation
  excuseText: string
  context: ExcuseContext
  tags: Tag[]
}
