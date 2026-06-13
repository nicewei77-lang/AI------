// Day 1 드릴에서 직접 작성합니다.
// Post, NewPost, Tag, ExcuseContext, Verdict를 채워 넣으세요.

// export: 다른 파일들이 이 type을 import해서 쓸 수 있도록 함
// type 만들기: type ID = string;

/* 현재 판정 상태 타입 */
export type Verdict = "유죄" | "무죄" | "보류";

// interface: 이 data는 이런 모양이어야 한다를 정의. 주로 여러 필드를 가진 객체의 모양을 정의할 때 씀.
// type과 비슷하지만 나중에 다시 선언해서 필드를 추가할 수 있다.(declaration merging)
/* 
interface User {
  name: string;
  age: number;
}
*/

/* 변명 판정을 위해 글에서 추출할 메타데이터 타입.*/
export interface ExcuseContext {
    date: string;
    location: string;
    time: string;
    route: string | undefined;
}

/* 
1. 타입 합성(Type Composition)
전에 선언한 타입을 다른 타입의 필드로 쓰는 것

2. 배열 타입 선언
같은 타입 데이터가 여러 개 들어갈 때 name: type[]; 방식의 배열으로 선언

3. 타입은 화면에 보이는 것? vs 포함된 정보 전체
정답은 포함된 정보 전체. Post는 이 데이터가 시스템 안에서 존재하는 모양을 정의한다. 화면은 그것을 일부만 보여줄
수도 있고, 가공해서 보여줄 수도 있다. data type과 화면, 둘은 별개의 layer.

4. Type과 Component
타입은 데이터가 화면에 어떻게 그려질지(색깔, 버튼 등)은 모른다. 실행 시점에 사라지고 코드 작성 중에 쓰이는 검사
도구일 뿐이다. 쓰이는 정보 전체가 풍족하게 들어간다.
컴포넌트는 데이터를 화면으로 바꾸는 함수이다. post라는 Post type 데이터를 받아서 화면 조각을 돌려준다.
타입에서 필요한 정보만 원하는 형태로 노출한다.

5. type 선언을 안해도 되는가?
가능하다. type을 안 적으면 any로 취급하고 넘어간다. 타입은 타이핑할 때 자동완성, 오타 표시, 명세서 역할을 해준다.
코드 규모가 커질수록 타입은 필수적.

6. .h 파일과의 비교
C 헤더처럼 "본체와 분리된, 컴파일 타임에 검사되는 약속"이라는 점은 같다.
다른 점: TS 타입은 빌드 후 흔적 없이 사라지고(헤더는 링킹돼 남음), 유니온/옵셔널처럼 표현력이 훨씬 풍부하다.
*/

/* 변명 게시글 타입. */
export interface Post {
    id: string;
    authorName: string;
    title: string;
    tags: Tag[];
    excuseText: string;
    context: ExcuseContext;
    verdict?: Verdict;
    credibility?: number;
    score: number;
    myVote: -1 | 0 | 1;
    commentCount: number;
    createdAt: string;
}

/* 변명하는 상황의 유형을 분류한다. */
export interface Tag {
    id: string; // 태그 고유 식별자
    label: string; // 화면에 보여줄 이름
}

/*
NewPost = "Post에서 서버/AI가 채우는 필드를 뺀 모양" (= 사용자가 직접 입력하는 것만)
    - 기준1: 필드 이름은 Post와 똑같이. (폼이 보낸 데이터가 그대로 저장돼 Post가 되므로)
    - 기준2: id/createdAt(서버 발급), verdict/credibility(AI 판정)는 사용자가 안 적으니 제외.
*/

/* 글 작성 페이지에 필요한 정보. */
export interface NewPost {
    title: string;
    tags: Tag[];
    excuseText: string;
    context: ExcuseContext;
}

/* 댓글 타입. post 상세 페이지에서 댓글 목록/좋아요 상태를 그릴 때 쓴다. */
export interface Comment {
    id: string;
    body: string;
    authorId: number;
    authorName: string;
    createdAt: string;
    likeCount: number;
    myLike: boolean;
}
