// Day 1-2 드릴에서 직접 작성합니다.
// MOCK_POSTS, 필요하다면 MOCK_TAGS를 여기에 정의하세요.

/* Post type을 import 한다. */
import type {Post} from "../types/post";

/* post 여러개를 저장한다 */
export const MOCK_POSTS: Post[] = [
    {
        id: "p1",
        authorName: "demo",
        title: "부트캠프 회고 모음",
        body: "정글 수료생들이 프로젝트 회고와 개선점을 공유하는 게시판입니다.",
        postType: "project",
        serviceUrl: "https://example.com",
        githubUrl: "https://github.com/example/project-lens-seed",
        oneLiner: "프로젝트 회고를 모아 다음 팀의 시행착오를 줄입니다.",
        targetUser: "부트캠프 수료생",
        techStack: ["React", "FastAPI", "PostgreSQL"],
        analysisStatus: "not_started",
        tags: [{id: "t1", label: "리뷰"}],
        score: 0,
        myVote: 0,
        commentCount: 0,
        createdAt: "2026-06-24T09:30:00",
    },

    {
        id: "p2",
        authorName: "demo",
        title: "스터디 매칭 보드",
        body: "관심 주제와 가능 시간을 기준으로 작은 스터디 그룹을 연결합니다.",
        postType: "project",
        oneLiner: "혼자 공부하는 사람을 작게 묶어주는 매칭 보드입니다.",
        targetUser: "취업 준비 개발자",
        techStack: ["TypeScript", "Supabase"],
        analysisStatus: "need_more_info",
        tags: [{id: "t2", label: "커뮤니티"}],
        score: 0,
        myVote: 0,
        commentCount: 0,
        createdAt: "2026-06-28T22:30:10"
    },
    
    {
        id: "p3",
        authorName: "demo",
        title: "면접 질문 복습 앱",
        body: "기술 면접 질문을 답변 단위로 쪼개고, 복습 주기를 관리합니다.",
        postType: "project",
        oneLiner: "면접 답변을 작은 카드로 반복 연습합니다.",
        targetUser: "주니어 개발자",
        techStack: ["React", "IndexedDB"],
        analysisStatus: "completed",
        aiSummary: "복습 흐름은 명확하지만 실제 답변 품질 피드백 근거가 더 필요합니다.",
        tags: [{id: "t3", label: "학습"}],
        score: 0,
        myVote: 0,
        commentCount: 0,
        createdAt: "2026-06-28T22:30:10",
    }
];
