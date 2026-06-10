# ALIBAI 프론트 학습 단계별 가이드

이 문서는 현재 `frontend/` 작업 트리를 기준으로,  
**빈 파일을 어떤 순서로 직접 채워 나갈지** 안내합니다.

중요:

- `frontend/`는 학습용 작업 트리입니다.
- `reference/frontend-complete/`는 비교용 완성본입니다.
- 완성본을 먼저 읽지 말고, 먼저 직접 타이핑해 보세요.

---

## 0. 시작 전

### 목표
- 이번 주에는 기본 게시판 프론트엔드 감각을 익힙니다.
- 목표는 “앱 완성”보다 “직접 쳐서 React 기본기를 익히기”입니다.

### 실행

```bash
cd frontend
npm run dev
```

### P0에서 이미 되어 있는 것
- Vite 실행 가능
- Tailwind 연결 완료
- BrowserRouter 연결 완료
- 폴더/파일 골격 생성 완료

### 아직 직접 해야 하는 것
- 타입 정의
- mock 데이터
- mock API
- 카드/목록 컴포넌트
- 폼
- 페이지
- Context
- ProtectedRoute

---

## 1. 1단계: P0 확인

### 볼 파일
- `frontend/src/main.tsx`
- `frontend/src/App.tsx`
- `frontend/src/index.css`
- `frontend/vite.config.ts`

### 여기서 확인할 것
- `main.tsx`에 `BrowserRouter`가 들어 있는가
- `index.css`에 `@import "tailwindcss";`가 들어 있는가
- `vite.config.ts`에 Tailwind 플러그인이 연결되어 있는가
- 화면이 뜨는가

### 완료 기준
- `npm run dev`가 실행된다.
- 브라우저에서 P0 안내 화면이 보인다.

---

## 2. 2단계: Day 1 타입부터 직접 작성

### 먼저 채울 파일
- `frontend/src/types/post.ts`

### 여기서 직접 만들 것
- `Verdict`
- `ExcuseContext`
- `Tag`
- `Post`
- `NewPost`

### 체크 질문
- 어떤 필드가 필수인가?
- 어떤 필드가 옵셔널인가?
- `Post`와 `NewPost` 차이는 무엇인가?

### 완료 기준
- 타입 파일이 비어 있지 않고, 직접 손으로 작성되었다.

---

## 3. 3단계: Day 1 목록용 데이터 준비

### 다음 파일
- `frontend/src/api/mockData.ts`

### 여기서 직접 만들 것
- `MOCK_POSTS`
- 필요하면 `MOCK_TAGS`

### 목적
- 실제 백엔드 없이 목록 렌더링에 쓸 재료를 먼저 만든다.

### 완료 기준
- 게시글 3~4개 정도의 mock 데이터가 준비된다.

---

## 4. 4단계: Day 1 컴포넌트 드릴

### 다음 파일
- `frontend/src/components/PostCard.tsx`
- `frontend/src/components/PostList.tsx`

### 순서
1. `PostCard`에 props 받아 표시
2. `PostList`에서 `map()`으로 카드 렌더링
3. `key` 붙이기

### 완료 기준
- 카드 1개를 props로 렌더링할 수 있다.
- 배열을 목록으로 렌더링할 수 있다.

---

## 5. 5단계: Day 1 페이지 조립

### 다음 파일
- `frontend/src/pages/PostListPage.tsx`

### 여기서 할 일
- 처음에는 `useEffect` 없이 mock 배열을 바로 렌더링해도 괜찮다.
- `PostList`에 데이터를 넘겨 목록 화면부터 만든다.

### 완료 기준
- 목록 화면이 뜬다.

---

## 6. 6단계: Day 2 mock API 작성

### 다음 파일
- `frontend/src/api/posts.ts`

### 여기서 직접 만들 것
- `fetchPosts(params?)`
- `fetchPostById(id)`
- `createPost(input)`

### 중요한 규칙
- 검색/태그/페이징 로직은 **페이지가 아니라 이 함수 안**에 둔다.
- 다음 주에 함수 본문만 axios로 바꿀 수 있어야 한다.

### 완료 기준
- 비동기 mock 함수가 동작한다.

---

## 7. 7단계: Day 2 useEffect와 상세 페이지

### 다음 파일
- `frontend/src/pages/PostListPage.tsx`
- `frontend/src/pages/PostDetailPage.tsx`

### 여기서 할 일
- 목록 페이지에서 `fetchPosts()` 호출
- 상세 페이지에서 `useParams()` + `fetchPostById()` 연결
- `loading`, `error` 상태 연습

### 완료 기준
- 목록과 상세 페이지가 mock API로 동작한다.

---

## 8. 8단계: Day 2 폼 드릴

### 다음 파일
- `frontend/src/components/ExcuseForm.tsx`
- `frontend/src/pages/LoginPage.tsx`

### 여기서 할 일
- `useState`로 입력값 제어
- `onChange`, `onSubmit`, `preventDefault()` 연습
- controlled form 감각 익히기

### 완료 기준
- 로그인 폼과 변명 작성 폼이 state와 연결된다.

---

## 9. 9단계: Day 3 Context와 보호 라우트

### 다음 파일
- `frontend/src/context/AuthContext.tsx`
- `frontend/src/components/ProtectedRoute.tsx`
- `frontend/src/pages/PostCreatePage.tsx`
- `frontend/src/api/auth.ts`

### 여기서 할 일
- mock login 함수 만들기
- Context로 로그인 상태 공유하기
- 비로그인 상태에서 `/new` 막기
- 작성 페이지를 보호 페이지로 연결하기

### 완료 기준
- 로그인 상태가 전역으로 공유된다.
- `/new` 접근이 로그인 여부에 따라 달라진다.

---

## 10. 언제 reference를 보나

`reference/frontend-complete/`는 아래 순서로만 보세요.

1. 먼저 직접 구현해 본다.
2. 막힌 지점을 질문하거나 힌트를 받는다.
3. 그래도 비교가 필요할 때만 reference를 연다.

즉, reference는 **출발점이 아니라 마지막 비교본**입니다.

---

## 11. 지금 하지 말 것

- 처음부터 `reference/frontend-complete/` 읽기
- axios 붙이기
- JWT 진짜 구현
- Redux/Zustand 추가
- 테스트부터 만들기
- 디자인에 오래 머무르기

---

## 12. 추천 하루 순서

### Day 1
- P0 확인
- 타입 작성
- mock 데이터 작성
- PostCard / PostList / PostListPage

### Day 2
- mock API 작성
- useEffect 연결
- 상세 페이지
- 로그인 폼 / 작성 폼

### Day 3
- Context
- ProtectedRoute
- 작성 페이지 마무리
- 필요하면 reference와 비교

---

## 13. 한 줄 요약

이번에는 완성본을 읽는 게 아니라  
`frontend/`의 빈 파일을 **직접 채우는 것**이 학습의 본체입니다.
