// Day 1-2 드릴에서 직접 작성합니다.
// MOCK_POSTS, 필요하다면 MOCK_TAGS를 여기에 정의하세요.

/* Post type을 import 한다. */
import type {Post} from "../types/post";

/* post 여러개를 저장한다 */
export const MOCK_POSTS: Post[] = [
    {
        id: "p1",
        title: "지하철이 멈췄어요",
        excuseText: "2호선이 신도림에서 20분간 정차했습니다.",
        context: {
            date: "2026-06-23",
            location: "둔전역",
            time: "23:00",
            route: "정글에서 둔전역"
         
        },
        tags: [{id: "t1", label: "지각"}],
        createdAt: "2026-06-24T09:30:00",
    },

    {
        id: "p2",
        title: "여친과 싸웠어요",
        excuseText: "에버라인이 폭발했습니다.",
        context: {
            date: "2026-04-23",
            location: "중앙시장역",
            time: "25:00",
            route: "역 근처"
         
        },
        tags: [{id: "t2", label: "지각"}],
        verdict: "무죄",
        credibility: 32,
        createdAt: "2026-06-28T22:30:10"
    },
    
    {
        id: "p3",
        title: "이거 ㅈ된거 맞냐?",
        excuseText: "첫 출근 못함. 오마이갓오마이갓오마이갓오마이갓오마이갓오마이갓오마이갓오마이갓오마이갓오마이갓오마이갓오마이갓오마이갓오마이갓오마이갓오마이갓오마이갓오마이갓오마이갓오마이갓오마이갓오마이갓오마이갓오마이갓오마이갓오마이갓오마이갓오마이갓오마이갓오마이갓오마이갓오마이갓오마이갓오마이갓오마이갓오마이갓오마이갓오마이갓오마이갓오마이갓오마이갓오마이갓오마이갓오마이갓오마이갓오마이갓오마이갓오마이갓",
        context: {
            date: "2026-04-23",
            location: "중앙시장역",
            time: "25:00",
            route: "역 근처",
            
        },
        tags: [{id: "t3", label: "결근"}],
        verdict: "유죄", 
        createdAt: "2026-06-28T22:30:10",
    }
];
