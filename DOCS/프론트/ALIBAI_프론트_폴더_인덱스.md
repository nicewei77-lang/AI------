# ALIBAI 프론트 폴더 인덱스

이 문서는 현재 프론트 학습 환경의 폴더 역할을 빠르게 파악하기 위한 **인덱스**입니다.  
지금 기준으로:

- `frontend/`는 **학습용 P0 작업 트리**
- `reference/frontend-complete/`는 **비교용 완성본**

상세 학습 순서는 `ALIBAI_프론트_학습_단계별_가이드.md`를 참고합니다.

---

## 1. 전체 구조

```text
AI로 진화하기/
├── agent.md
├── DOCS/
├── frontend/                    # 직접 손으로 채워 넣는 학습용 작업 트리
└── reference/
    ├── README.md
    └── frontend-complete/       # 비교용 완성 예시
```

---

## 2. 어떤 폴더를 어떻게 써야 하나

### `frontend/`
- 이번 주 실제 학습은 **여기서만** 진행합니다.
- 상태는 `P0` 수준입니다.
  - Vite 실행 가능
  - Tailwind 연결 완료
  - BrowserRouter 연결 완료
  - 폴더/파일 골격 생성 완료
  - Day 1~3 드릴 코드는 아직 비어 있음

### `reference/frontend-complete/`
- 예전에 만들어 둔 **완성형 참고본**입니다.
- 먼저 여기부터 읽지 말고, 드릴을 직접 해 본 뒤 비교용으로만 봅니다.

---

## 3. 루트 문서

### `agent.md`
- 에이전트가 따라야 할 최소 운영 규칙입니다.

### `DOCS/ALIBAI_프론트_학습코치_AGENT.md`
- 학습 코칭 원본 기준 문서입니다.
- 역할, 범위 제한, 단계별 철학이 가장 자세히 들어 있습니다.

### `DOCS/ALIBAI_프론트_학습_단계별_가이드.md`
- 지금 이 구조를 기준으로 실제 학습 순서를 안내합니다.

### `DOCS/ALIBAI_기획서.md`
- 프로젝트 전체 목표와 다음 주 백엔드/RAG/MCP/Agent 확장 방향을 설명합니다.

---

## 4. `frontend/` 핵심 파일

### `frontend/package.json`
- 실행 스크립트와 의존성이 있습니다.
- 주로 `npm run dev`, `npm run build`, `npm run lint`를 사용합니다.

### `frontend/vite.config.ts`
- Vite 설정 파일입니다.
- React + Tailwind Vite 플러그인이 연결되어 있습니다.

### `frontend/src/main.tsx`
- 앱 시작점입니다.
- `BrowserRouter`까지만 연결된 상태입니다.

### `frontend/src/App.tsx`
- 지금은 학습용 안내 화면만 들어 있습니다.
- 라우팅/페이지 조립은 나중에 직접 작성해야 합니다.

### `frontend/src/index.css`
- Tailwind import와 최소 전역 스타일만 있습니다.

---

## 5. `frontend/src/` 폴더 의미

### `src/types/`
- TypeScript 타입을 직접 작성하는 자리입니다.
- 시작 파일: `types/post.ts`

### `src/api/`
- mock 데이터를 직접 만들고, mock API 함수를 직접 작성하는 자리입니다.
- 시작 파일:
  - `api/mockData.ts`
  - `api/posts.ts`
  - `api/auth.ts`

### `src/components/`
- 재사용 UI 조각을 직접 만드는 자리입니다.
- 시작 파일:
  - `components/PostCard.tsx`
  - `components/PostList.tsx`
  - `components/ExcuseForm.tsx`
  - `components/ProtectedRoute.tsx`

### `src/pages/`
- 라우팅 대상이 되는 화면 파일입니다.
- 시작 파일:
  - `pages/PostListPage.tsx`
  - `pages/PostDetailPage.tsx`
  - `pages/PostCreatePage.tsx`
  - `pages/LoginPage.tsx`

### `src/context/`
- 로그인 상태를 전역으로 공유하는 흐름을 직접 구현하는 자리입니다.
- 시작 파일:
  - `context/AuthContext.tsx`

---

## 6. 파일 상태 읽는 법

현재 `frontend/src/` 안의 대부분 파일은:

- 아직 구현되지 않았고
- 짧은 안내 주석만 있으며
- `export {}` 정도만 들어 있는 상태입니다.

즉, 이 파일들은 “완성 코드”가 아니라 **직접 채워 넣을 빈 드릴 파일**입니다.

---

## 7. 지금 안 봐도 되는 것

### `frontend/node_modules/`
- 라이브러리 설치 결과물입니다.

### `frontend/src/assets/`
- 기본 스캐폴드 자산입니다.
- 이번 주 핵심 학습 대상은 아닙니다.

### `frontend/src/App.css`
- 현재 import되지 않는 기본 파일입니다.
- 무시해도 됩니다.

### `reference/frontend-complete/dist/`
- 빌드 산출물입니다.
- 읽거나 수정할 필요가 없습니다.

---

## 8. 추천 탐색 순서

1. `frontend/src/main.tsx`
2. `frontend/src/App.tsx`
3. `frontend/src/types/post.ts`
4. `frontend/src/api/mockData.ts`
5. `frontend/src/api/posts.ts`
6. `frontend/src/components/PostCard.tsx`
7. `frontend/src/components/PostList.tsx`
8. `frontend/src/pages/PostListPage.tsx`
9. `frontend/src/components/ExcuseForm.tsx`
10. `frontend/src/pages/LoginPage.tsx`
11. `frontend/src/pages/PostDetailPage.tsx`
12. `frontend/src/context/AuthContext.tsx`
13. `frontend/src/components/ProtectedRoute.tsx`
14. `frontend/src/pages/PostCreatePage.tsx`

---

## 9. 한 줄 요약

- `frontend/`에서 직접 작성한다.
- `reference/frontend-complete/`는 나중에 비교만 한다.
- 지금은 “코드를 읽는 단계”보다 “빈 파일을 직접 채우는 단계”다.
