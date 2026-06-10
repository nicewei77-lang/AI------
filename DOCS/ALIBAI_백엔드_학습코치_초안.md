# ALIBAI 백엔드 — 학습코치 커리큘럼 (초안 / 큰 그림)

> 상태: **초안.** 이번 범위는 **백엔드(순수 포럼 API + 인프라)까지**. AI 3종(RAG·MCP·Agent)은 **별도로 나중에 계획**한다(아래 §6).
> 짝 문서: 프론트 = `ALIBAI_프론트_학습코치_AGENT.md`, 기획서 = `ALIBAI_기획서.md`, 진도 = `진도_체크포인트.md`.
> 코칭 계약(개념→드릴, 빈칸 중심, 정답 통째 금지, 오리엔테이션 먼저)은 프론트 지침서 §0과 동일하게 적용한다.

---

## 0. 지금 어디인가 (오리엔테이션)

- **완료:** 프론트(React/TS) — 타입·mock API·목록/상세·라우팅까지 직접. 폼/Context는 코치 임시 채움(보충 예정).
- **이번:** 백엔드 = **프론트의 mock(`api/*.ts`)을 실제로 떠받칠 진짜 서버**를 바텀업으로 직접 구현. **순수 포럼 API + 인증 + 인프라까지.**
- **이번엔 안 함:** AI 3종(RAG·MCP·Agent)은 이 초안에서 빼고, 백엔드 토대가 선 뒤 §6에 따라 따로 계획한다. (단, 과제 최종에는 **셋 다 동작이 필수**다.)
- **분량:** 2.5일 중 이 초안은 **백엔드 토대(≈ Day1 풀 + Day2 오전)** 를 다룬다. 남는 분량은 AI 단계용으로 비워 둔다. 프론트처럼 "필수로 쳐볼 것 + 알아야 할 것"으로 세션을 쌓는다.

---

## 1. 무엇을 만드나 — 투표형 포럼 (Reddit-lite)

게시판을 Reddit 결로 가되, 이번엔 **평면 댓글 + 투표/점수**까지만 만든다. (중첩 스레드·서브포럼은 제외 — §1 끝 참고.)

핵심 특징 2가지를 데이터 모델에 반영:

1. **투표/점수** — 글·댓글에 up/down. `votes` 테이블 + 점수 집계 → new/top 정렬. (Reddit의 핵심 차별점)
2. **태그 분류** — 변명 유형(지각/결근/미답장…)을 `tags`(N:M)로. 서브포럼 대용.

댓글은 **평면(1단계)** — `comments`가 글에 1:N로 붙고, 댓글의 댓글(스레드)은 안 한다. ALIBAI 메타포: 투표 = "배심원 평결", (나중에) AI 판결도 댓글(`is_ai=true`)로 부착.

> **이번 제외(범위 밖):** 중첩 스레드 댓글(`parent_id` 자기참조), 서브포럼/커뮤니티(`communities`). 필요해지면 그때 보강한다.

### 데이터 모델 (기획서 §6 기반 + 투표 보강)

기획서 §6 테이블 중 **이번에 만들 것**: `users`, `posts`, `comments`(평면), `tags`, `post_tags`, 그리고 신규 `votes`.
(`excuse_embeddings`·`verifications`는 AI 단계로 미룬다. `posts`의 `verdict/credibility/counsel_excuse`도 컬럼만 두거나 AI 때 추가.)

```text
votes : id, user_id FK, target_type('post'|'comment'), target_id, value SMALLINT(-1|+1),
        UNIQUE(user_id, target_type, target_id)        -- 1인 1표 (멱등성)
comments : 기획서 §6 그대로(평면). parent_id 안 둠.
```

관계 정리(ERD 연습 소재): users—posts(1:N), posts—comments(1:N), posts—tags(N:M, post_tags), users—votes(1:N), posts/comments—votes(다형 1:N).

---

## 2. 범위 가드레일 — 키워드 분류 (드릴 / 개념만 / 다음 단계)

> 사용자가 준 필수 키워드 목록을 ALIBAI **백엔드(이번 범위)** 기준으로 분류.

### 🟢 직접 손으로 칠 것 (이번 백엔드 핵심 경로)

| 키워드 | 어디에 녹나 |
|---|---|
| Python / OOP / error handling | 백엔드 전반 (모델·서비스 클래스, 예외 처리) |
| REST / api design / HTTP 3xx·4xx·5xx | 게시판 CRUD·검색·투표 엔드포인트, 상태코드·에러 응답 |
| PostgreSQL / SQL / CRUD | 모든 데이터 접근 |
| Join inner/outer | 글+작성자+점수+태그 묶어 조회 |
| PK / FK / Index | 스키마 설계, 검색·정렬 성능 |
| ERD 1:1 / 1:N / N:M | §1 관계 (posts—comments 1:N, post_tags N:M, votes 다형) |
| data modeling / normalization | 스키마 설계 세션(B2) |
| transaction | 투표 토글, 다중 행 갱신을 원자적으로 (B2/B3) |
| JWT | 회원가입/로그인/보호 라우트 (B4) |
| Async | FastAPI async + asyncpg (전반) |
| CORS | 프론트(Vite) ↔ 백엔드 연동 (B4) |
| configuration | `config.py` + `.env` (B1) |
| Layered architecture | routers / services / repository 계층 분리 (B1~) |
| 멱등성 | 투표(1인 1표) (B3) |

### 🟡 개념만 (1~2문장 + 왜 쓰는지, 깊이 안 팜 / 일부 stretch)

| 키워드 | 다루는 방식 |
|---|---|
| Session (vs JWT) | "왜 JWT를 골랐나" 대조로만 (B4) |
| OAuth2 | FastAPI `OAuth2PasswordBearer` 형태만 빌려 씀, 소셜로그인 실구현 X |
| CSRF / Rate limit / HTTPS | SPA+JWT에서 결, 외부호출 보호, 배포 시 — 각 1~2문장 (B4) |
| functional programming | 파이썬 컴프리헨션·순수함수 수준에서 자연스럽게, 별도 학습 X |
| MVC | "FastAPI는 MVC보다 레이어드" 한 줄 대조 (B1) |
| logging | 운영 마무리에서 간단히 (B4 끝/stretch) |
| testing / test framework | pytest 최소 1~2개 (stretch) |

### 🟠 다음(AI) 단계로 미룸 — §6에서 계획

`transaction`(임베딩 적재), `재시도`/`타임아웃`(MCP·LLM), `Job Queue`/`Redis`(임베딩 큐·캐시), `SSE`(판결 스트리밍) → **RAG·MCP·Agent를 붙일 때** 자연스럽게 등장. 이번 백엔드에선 자리만 비워 둔다.

### 🔴 범위 제외

| 키워드 | 이유 |
|---|---|
| GraphQL | REST로 충분, 학습 분량 과다 |
| WebSocket | 실시간 양방향 필요 기능 없음 (필요하면 나중에 SSE 단방향) |

---

## 3. 백엔드 세션 골격 (바텀업)

> 각 세션: **목표 → 손으로 칠 것(drill) → 개념만(know) → 산출물 → 완료 기준.**
> 프론트와 동일하게 개념 먼저, 빈칸 드릴, 정답 통째 금지.

### B1. 환경·설정·골격
- 목표: FastAPI가 뜨고 `/health`가 응답. 계층 구조의 의미를 잡는다.
- 손으로: `uvicorn`으로 `main.py` 띄우기, `config.py`(pydantic-settings로 `.env` 로딩), `/health` 라우트, `docker compose up`으로 Postgres 띄우기, DB 연결(asyncpg/SQLAlchemy).
- 개념만: 레이어드 아키텍처(router→service→repository→model/schema)가 왜 필요한가, MVC와의 차이, async/await가 서버에서 의미하는 것.
- 산출물: `backend/app/{main,config,db}.py` 골격 + DB 컨테이너.
- 키워드: Python, configuration, Layered architecture, Async.

### B2. 데이터 모델링 + PostgreSQL
- 목표: §1 스키마를 ERD로 그리고 테이블로 만든다.
- 손으로: SQL로 직접 `CREATE TABLE`(users/posts/comments/tags/post_tags/votes) 한 번 쳐보기 → 그 다음 SQLAlchemy 모델로 옮기기. PK/FK/UNIQUE/Index 달기. 투표 UNIQUE(1인1표).
- 개념만: 정규화(왜 post_tags로 N:M을 푸나), transaction(ACID 한 문단), 인덱스가 검색/정렬에 주는 영향, Alembic은 "있다" 정도.
- 산출물: `models.py` + 실제 생성된 테이블.
- 키워드: data modeling, normalization, ERD 1:N/N:M, PK/FK/Index, SQL, transaction.

### B3. CRUD + REST 설계 + 투표
- 목표: 인증 없이 글/댓글/태그/투표가 REST로 동작.
- 손으로: Pydantic 스키마(요청/응답 분리) → router → service → repository. `GET /posts`(페이징 cursor + 검색 q + 태그 필터, **로직은 repository 쿼리 안에**), `POST /posts`, `GET /posts/{id}`, 평면 댓글 CRUD, `POST .../vote`(토글 = transaction). Join으로 글+작성자+점수 한 번에.
- 개념만: HTTP 상태코드 매핑(201/400/404/409/500), 멱등성(투표 UNIQUE로 1인1표), 에러 응답 형태(HTTPException), new/top 정렬.
- 산출물: 프론트 mock과 **시그니처가 맞는** 실제 포럼 API.
- 키워드: REST, api design, CRUD, Join, error handling/HTTP, 멱등성, transaction.

### B4. 인증 + 프론트 연동
- 목표: 회원가입/로그인/보호 라우트 + 프론트가 실제로 붙음.
- 손으로: `passlib`으로 비밀번호 해싱, `python-jose`로 JWT 발급·검증, `Depends(get_current_user)` 가드로 글쓰기 보호, CORS 미들웨어(프론트 origin 허용). (프론트 `api/auth.ts`·`api/posts.ts`의 본문을 axios로 교체하는 지점)
- 개념만: Session vs JWT(왜 JWT), OAuth2PasswordBearer 형태, CSRF가 SPA+JWT에서 결이 다른 이유, Rate limit/HTTPS, logging 한 줄.
- 산출물: 로그인 → 토큰 → 보호 엔드포인트. 프론트에서 mock 없이 동작.
- 키워드: JWT, OAuth2(형태만), Session·CSRF·Rate limit·HTTPS(개념), CORS.

---

## 4. 이번 백엔드의 완료 기준 (done)

- 프론트가 mock 대신 이 백엔드를 때려도 목록/상세/작성/로그인/투표가 동작.
- 글/댓글/태그/투표가 REST로 CRUD되고, 검색·태그필터·페이징·정렬이 서버에서 처리됨.
- JWT 로그인 + 보호 라우트 + CORS로 프론트 연동 완료.

---

## 5. 확정 필요 (백엔드 진행 전)

- (참고) Reddit 깊이 = **평면 댓글 + 투표**로 확정. LLM/임베딩 provider·AI 우선순위는 §6(AI 단계 계획) 때 정한다.

---

## 6. 다음 단계 예고 — AI 3종 (별도 계획)

> 백엔드 토대가 서면 RAG·MCP·Agent를 **별도 세션으로 계획**한다. 과제 최종에는 **셋 다 end-to-end 동작이 필수**다(사용자 확정). 이번 초안에선 자리만 비워 둔다.

- **RAG** — 등록 시 임베딩 적재(transaction), pgvector 유사/중복 검색. (`excuse_embeddings`)
- **MCP** — FastMCP 서버 + 외부 API 1개(날씨), JSON-RPC, API키 격리, timeout/재시도/캐시.
- **Agent** — LangGraph 판결 루프(`/trial`), 무한루프 방지, 멱등성. (`verdict/credibility/counsel`)
- AI 계획 착수 시 정할 것: **LLM/임베딩 provider 조합**, 분량 배분, 신뢰성(재시도·타임아웃·로깅) 깊이.
