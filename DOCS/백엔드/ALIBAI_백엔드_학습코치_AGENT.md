# ALIBAI 백엔드 — AI 학습 코치 지침서

> 이 파일은 **VS Code의 AI 에이전트(Claude Code / Codex 등)** 가 읽고 학습자를 **코칭**하기 위한 백엔드 단계 상세 문서다.
> **1차 공통 계약은 `AGENTS.md`다.** 이 문서는 그 위에 백엔드 범위·세션·델타를 더한다(계약 환기와 출처는 §0).
> 진도는 `진도_체크포인트.md`에서 추적한다(매 세션 시작 시 읽고, 끝에 갱신).

---

## 0. 에이전트에게 — 코칭 계약 (가장 중요)

**코칭 계약 본문(역할·응답 형식·설명 원칙=4종 불변식·진행 방식·절대 규칙)은 `AGENTS.md`를 단일 출처로 그대로 적용한다 — 여기 복제하지 않는다.** (더 상세한 예시·세션 교훈은 프론트 지침서 §0·§7.) 이 문서는 그 위에 **백엔드 델타**만 더한다:

### 백엔드 델타 (프론트와 달라지는 점)

- **검증은 "정답본 디프"가 아니라 "실행·`curl`·`/docs`·`pytest`로 직접 확인"이 본체다.** 백엔드는 돌려보면 200/401/404가 즉시 나온다. 막혔는지 여부도 "서버가 뜨나, 엔드포인트가 응답하나"로 객관 판정한다.
- **사전 스텁·정답본(reference)이 없다.** 프론트는 빈 스텁(`export {}`)이 깔려 있었지만, 백엔드는 **세션마다 파일을 처음부터 만든다.** 정답이 필요하면 코치가 요청 시 세션별 스니펫으로 준다.
- **깊이 가드: SQLAlchemy/Pydantic/asyncio 내부를 깊게 파지 않는다.** 모델 정의·요청/응답 스키마·`async`로 소비하는 수준까지만. (프론트의 "TS 제네릭 금지"에 대응.)
- **추상 개념은 "실제 DB/HTTP에서 무슨 일이 일어나나"로 직관화한다.** 브라우저 예시 대신 — 쿼리 로그(실제로 나가는 SQL), 응답 상태코드, JWT 페이로드의 실제 모양(`{"sub": "...", "exp": ...}`), 트랜잭션이 깨졌을 때 롤백되는 장면 등.
- **이번 범위(§2) 밖 = AI 3종(RAG/MCP/Agent).** 질문받으면 개념 1~2문장 후 "그건 다음 AI 단계"로 복귀.

**응답 형식**은 `AGENTS.md` §응답 형식을 따른다(여기 재인쇄하지 않음).

---

## 1. 학습자 프로필 & 맥락

- **수준:** AI 도움으로 Flask/Python 기반 간단한 웹 서비스를 만들어본 경험. **HTTP·라우팅·폼·기본 SQL 감각은 있음.** FastAPI·async·ORM(SQLAlchemy)·JWT·데이터 모델링은 거의 처음.
- **프로젝트:** `ALIBAI — 변명 검증소` 백엔드. 프론트(React)가 쓰던 mock(`api/*.ts`)을 떠받칠 **진짜 서버**.
- **이번 단계 목표:** **순수 포럼 API + 인증 + DB까지.** AI 3종(RAG/MCP/Agent)은 **다음 단계로 분리**(§8). 단, 과제 최종엔 셋 다 동작이 필수.
- **가용 시간:** **2.5일 전부가 백엔드**(B0~B4). AI 3종(RAG/MCP/Agent)은 이 2.5일이 끝난 *다음*의 별도 분량(§8)이다 — 이 2.5일을 AI와 나눠 쓰지 않는다.
- **학습 철학:** 바텀업. **기본 개념 → 직결 코드 스니펫 반복 타이핑 → 손에 익히기.** (프론트와 동일.)

---

## 2. 이번 단계 범위 (Scope Guardrails)

> 기획서·스펙은 고정 계약이 아니라 학습자와 함께 다듬는 대상이다. 모순·중복을 발견하면 코드와 문서(기획서·이 지침서)를 함께 갱신한다. 단, **프론트 mock 시그니처 / 기획서 §7 REST 계약과 API 모양을 맞춘다**(프론트가 본문만 axios로 바꿔 붙도록).

**🟢 직접 손으로 칠 것 (drill 대상)**

- Python (타입 힌트, OOP=모델·서비스 클래스, 예외 처리)
- FastAPI (라우터, 의존성 주입 `Depends`, 자동 문서 `/docs`)
- 레이어드 아키텍처 — `router → service → repository → model/schema`
- PostgreSQL / SQL (CREATE TABLE, SELECT/INSERT/UPDATE/DELETE, Join)
- 데이터 모델링 — ERD(1:N / N:M / 다형), 정규화, PK / FK / UNIQUE / Index
- SQLAlchemy (모델 정의, 관계, 쿼리)
- transaction (투표 토글·다중 행 갱신을 원자적으로)
- REST / api design — 상태코드(201/400/404/409/422/500), 페이징(cursor), 검색·태그 필터, 정렬, 투표
- 멱등성 (투표 1인 1표 = UNIQUE)
- JWT 인증 (해싱, 발급/검증, `Depends` 가드로 보호 라우트)
- CORS (프론트 연동), rate limit (최소 — 로그인 brute-force 방어)
- async/await (FastAPI + asyncpg, "소비" 수준)

**🟡 개념만 (질문받으면 1~2문장 후 복귀)**

- Session vs JWT ("왜 JWT를 골랐나" 대조)
- OAuth2 (`OAuth2PasswordBearer` 형태만, 소셜로그인 실구현 X)
- CSRF / HTTPS (SPA+JWT에서 결, 배포 시)
- 캐싱 ("트래픽 방어=rate limit, 캐시=비싼 호출 절감" 차이만 — 캐시 본체는 AI 단계 MCP)
- MVC ("FastAPI는 MVC보다 레이어드" 한 줄), functional programming (컴프리헨션 수준)
- logging (마무리에 간단히), testing/pytest (stretch)

**🟠 다음(AI) 단계로 미룸 — §8**

- RAG(임베딩·pgvector), MCP(외부 API·JSON-RPC·API키 격리), Agent(LangGraph·function calling)
- 그때 자연히 등장: 임베딩 적재 transaction, 재시도/타임아웃, Job Queue/Redis 캐시, SSE

**🔴 범위 제외**

- GraphQL (REST로 충분), WebSocket (실시간 양방향 기능 없음)

**핵심 원칙: 검색/태그/페이징/정렬 로직은 router가 아니라 repository(쿼리) "내부"에 둔다.** 라우터는 파라미터만 받아 넘긴다. (프론트의 "필터링은 mock 함수 내부" 원칙의 백엔드판.)

### 프론트 ↔ 백엔드 계약 (필드명·쿼리 — 다음 세션 전 못박기)

프론트가 "본문만 axios로 교체"해서 붙으려면 **JSON 모양**이 정확히 맞아야 한다.

- **JSON 필드 = 프론트 camelCase, DB/ORM 내부 = snake_case.** Pydantic alias로 잇는다: `excuseText ↔ excuse_text`, `createdAt ↔ created_at`. (스키마에 `Field(alias=...)` + `populate_by_name=True`, 응답은 FastAPI `response_model_by_alias=True` 또는 `model_dump(by_alias=True)`로 camelCase 출력.)
- **태그 ID 계약:** 외부 API의 `Tag.id`는 프론트가 쓰는 문자열 id(slug, 예: `"t1"`)이고, DB 내부 FK는 `tags.id` 숫자 PK다. DB에는 `tags.slug TEXT UNIQUE`를 두고, repository가 `?tag=t1` / `tagIds:["t1"]`를 `tags.slug`로 찾아 숫자 `tags.id`로 변환한다.
- **목록 쿼리:** HTTP는 `?q=`, `?tag=`, `?cursor=`. 프론트 `fetchPosts`는 내부 시그니처로 `tagId`를 쓰지만 본문에서 `tag`로 변환해 보낸다 → **백엔드는 `tag`를 받는다**(체크포인트 2026-06-08 설계 로그).
- **생성 입력:** 프론트 보충/axios 전환 때 `NewPost.tags: Tag[]`는 `tagIds: string[]`로 정리하거나, 함수 본문에서 `tags.map(t => t.id)`로 변환한다. 백엔드 스키마는 내부 필드명 `tag_ids`, 외부 JSON alias `tagIds`, 값은 문자열 slug 배열.
- **반환 모양:** 목록 `{ items: Post[], nextCursor? }`, 상세 `Post`. 프론트 `types/post.ts` 키와 일치해야 한다.
- **투표 점수:** `score`는 합산 단일 정수(net = up − down). 응답 `Post`에 포함한다. 현재 프론트 `Post` 타입에는 아직 없으므로 B4 axios 전환/투표 UI 보충 때 `score`를 추가하고 mock 기본값도 맞춘다.
- **투표 API 계약:** `POST /posts/{id}/vote` body는 `{ "value": 1 | -1 }`, 응답은 `{ "score": number, "myVote": 1 | -1 | 0 }`. 같은 값을 다시 누르면 취소(`myVote=0`), 반대 값을 누르면 전환한다.

---

## 3. 멘탈 모델 전환 (시작 전 반드시 짚기, 5분)

학습자는 Flask 경험이 있다. 그 위에 얹는다.

- **Flask:** 보통 동기. 뷰 함수가 직접 SQL·템플릿을 다루고, 요청마다 위→아래로 즉시 실행.
- **FastAPI:** ① **타입 기반** — 요청/응답을 Pydantic 스키마로 선언하면 검증·문서가 자동. ② **async** — `async def` 핸들러가 I/O(DB·네트워크)를 기다리는 동안 다른 요청을 처리. ③ **레이어드** — 뷰가 다 하지 않고 `router(입출력) → service(규칙) → repository(DB)`로 책임을 쪼갬. ④ **의존성 주입** — `Depends`로 "로그인 유저", "DB 세션"을 핸들러에 주입.
- **ORM 전환:** 직접 SQL 문자열 대신 SQLAlchemy 모델/쿼리로 다룬다. (단, B2에서 SQL을 한 번 직접 쳐 본 뒤 ORM으로 옮겨, 둘의 대응을 눈으로 본다.)
- 핵심 질문: **"이 요청은 어떤 데이터를 받아(스키마) 어느 계층을 거쳐(router→service→repo) 무엇을 반환하나(응답 스키마)?"**

→ 학습자가 "Flask 뷰가 다 하던 일을 FastAPI에선 어떻게 쪼개나"를 자기 말로 설명하게 한 뒤 진행.

---

## 4. 환경 세팅 (Phase B0)

에이전트는 명령 단위로 안내하고 각 명령이 뭘 하는지 한 줄로 설명한다. **이 단계의 인프라/설정 파일(`docker-compose.yml`, `requirements.txt`, venv)은 코치가 직접 만들어줘도 된다.**

```bash
# 0) DB — Docker로 PostgreSQL (pgvector 이미지: 다음 AI 단계 대비)
docker compose up -d                      # docker-compose.yml은 기획서 §8.3 기반

# 1) 백엔드 폴더 + 가상환경 (모노레포: frontend/ 옆에 backend/)
cd backend
python -m venv .venv && source .venv/bin/activate

# 2) 의존성 — 코치가 requirements.txt를 만들어 주고, 설치는 항상 -r로 통일
#    requirements.txt 내용: fastapi  uvicorn[standard]  sqlalchemy  asyncpg
#                           pydantic-settings  python-jose  passlib[bcrypt]  slowapi
pip install -r requirements.txt

# 3) 개발 서버
uvicorn app.main:app --reload
```

**확인용 폴더 구조 (기획서 §8.1 backend/ 기준, 이번 단계 버전 — 폴더 인덱스 겸용)**

```
backend/
├── app/
│   ├── main.py          # FastAPI 진입점 (라우터 등록, CORS, /health)
│   ├── config.py        # 환경변수 로딩 (pydantic-settings + .env)
│   ├── db.py            # 엔진/세션 (asyncpg)
│   ├── models.py        # SQLAlchemy ORM 모델 (users/posts/comments/tags/post_tags/votes)
│   ├── schemas.py       # Pydantic 요청/응답 스키마
│   ├── auth/            # 해싱, JWT 발급·검증, get_current_user 의존성
│   └── routers/         # posts, comments, auth, votes
│       └── ...
├── requirements.txt
└── .env                 # DB URL, JWT 시크릿 (외부 노출 비밀값)
```

> AI 단계(§8)에서 `rag/`, `agent/`, `mcp_client/`와 `mcp-server/`가 추가된다. 지금은 자리만 안다.

**폴더 골격 운영(코치):** 각 세션에 필요한 **빈 폴더/디렉터리는 코치가 만든다.** 만든 직후 (1) 왜 이 계층으로 나눴는지(책임 분리), (2) 전체 구조 속 위치, (3) 다음에 학습자가 직접 나눌 때의 **분할 기준**을 설명한다. 기준 요지 — *한 파일 = 한 책임*: "이 코드가 HTTP를 아는가(→router)·규칙을 다루나(→service)·DB를 아는가(→repository)·데이터 모양인가(→models/schemas)." 둘 다 알면 쪼갠다. 같은 종류가 여러 개가 되면 파일 → 폴더로 승격(`routers/posts.py`, `routers/comments.py` …).

**B0 완료 기준:** `uvicorn`으로 서버가 뜨고, `/health`가 200, `/docs`(Swagger UI)가 열리며, DB 컨테이너가 떠 있다.

---

## 5. 단계별 커리큘럼

> 각 블록: **개념(중요도로 분량 조절) → 드릴(빈칸 반복 타이핑) → 수직 슬라이스(그 세션 조각을 ALIBAI 실물로 합치기) → 완료 기준.**
> 드릴은 빈칸 비중으로 레벨 3개. 처음엔 빈칸이 가장 많은 레벨 3을 주고 요청에 따라 조정.

**추천 2.5일 배분 (전부 백엔드):**

- **Day 1:** B0(환경 세팅) → B1(설정·골격) → B2(데이터 모델링) — "돌아가는 빈 서버 + 테이블"까지.
- **Day 2:** B3(CRUD+REST+투표) — 가장 무거운 세션(스키마·계층·검색/태그/페이징/정렬·투표 트랜잭션).
- **Day 2.5 (반나절):** B4(인증 + 프론트 연동) + 마무리(logging, pytest 1~2개는 stretch). 시간이 남으면 정렬/페이징 보강.

(AI 3종은 이 2.5일 이후 §8로 별도 계획.)

> **📖 공식문서 우선(doc-first) 연습:** 각 세션의 `📖 1차 출처`는 코치가 설명을 다 깔기 전에 **학습자가 먼저 읽고 자기 말로 요약**할 챕터다(맵·사용법 = `공식문서_레퍼런스.md`). 코치는 요약을 듣고 빈 곳·오해만 메운 뒤 드릴로 간다. 전 세션을 한 번에 뒤집지 말고 **B4(인증)를 첫 본격 doc-first 트라이얼**로 삼는다 — FastAPI Security 챕터가 자족적이라 "문서만 보고 구현" 성공 경험을 만들기 좋다.

### B1. 환경·설정·골격

- **개념:** FastAPI vs Flask(타입+자동검증+async+자동docs), 레이어드 아키텍처가 왜 필요한가(뷰 비대화 방지), `pydantic-settings`로 `.env` 로딩, ASGI/uvicorn, async/await가 서버에서 의미하는 것.
- **드릴 (config / 진입점):**

  ```python
  # config.py  (Pydantic v2: 세팅은 SettingsConfigDict — B3의 모델 ConfigDict와 짝)
  from pydantic_settings import BaseSettings, SettingsConfigDict

  class Settings(BaseSettings):
      database_url: ___          # 타입 힌트
      jwt_secret: ___
      model_config = SettingsConfigDict(env_file="___")   # ".env"

  settings = Settings()
  ```

  ```python
  # main.py
  from fastapi import FastAPI

  app = ___()                     # FastAPI 인스턴스

  @app.___("/health")            # GET 데코레이터
  async def health():
      return {"status": "ok"}
  ```

- **수직 슬라이스 ①:** `uvicorn app.main:app --reload`로 띄워 `/health` 200 + `/docs` 확인. `db.py`로 DB 연결 한 줄 확인.
- **완료 기준:** 서버 기동, `/health` 응답, DB 연결 성공. "router→service→repository가 왜 필요한가"를 자기 말로 설명.
- **키워드:** Python, configuration, Layered architecture, Async.
- **📖 1차 출처:** FastAPI *Tutorial → First Steps* + *Settings and Environment Variables*. (배경) MDN HTTP 개요.

### B2. 데이터 모델링 + PostgreSQL

- **개념:** ERD(users—posts 1:N, posts—comments 1:N, post_tags N:M, votes 다형 1:N), 정규화(왜 태그를 post_tags로 분리하나), API용 slug와 DB용 PK를 분리하는 이유, PK/FK/UNIQUE/Index, transaction(ACID 한 문단), SQLAlchemy 선언형 모델·관계.
- **드릴 1 (SQL 직접):**

  ```sql
  CREATE TABLE posts (
    id        BIGSERIAL ___ KEY,                  -- PRIMARY
    author_id BIGINT ___ users(id) ON DELETE CASCADE,  -- REFERENCES (FK)
    title     TEXT NOT NULL,
    excuse_text TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
  );

  CREATE TABLE tags (
    id   BIGSERIAL PRIMARY KEY,
    slug TEXT ___ NOT NULL,                       -- UNIQUE, API Tag.id로 노출(t1 등)
    name TEXT UNIQUE NOT NULL
  );

  CREATE TABLE post_tags (
    post_id BIGINT REFERENCES posts(id) ON DELETE CASCADE,
    tag_id  BIGINT REFERENCES tags(id)  ON DELETE CASCADE,
    ___ KEY (post_id, tag_id)                     -- 복합 PRIMARY (N:M)
  );

  CREATE TABLE votes (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    target_type TEXT, target_id BIGINT,
    value SMALLINT,                               -- +1 / -1
    ___ (user_id, target_type, target_id)        -- UNIQUE (1인 1표)
  );
  ```

  - ⚠️ **`users`(기획서 §6 그대로)·`comments`(평면, `post_id` FK)도 같이 만든다 — `users`는 posts/votes의 FK 대상이라 먼저.** 위 4개는 예시고, 이 둘은 같은 방식으로 직접 채운다(완료 기준의 6개 테이블).
- **드릴 2 (SQLAlchemy 모델):** 위 SQL을 모델로 옮겨 쓰기(빈칸: `Column`, `ForeignKey`, `relationship`, `UniqueConstraint`).
- **수직 슬라이스 ②:** 모델로 테이블 생성 → DB에 실제로 만들어졌는지 확인(`\dt`).
- **완료 기준:** users/posts/comments/tags/post_tags/votes 테이블 생성. ERD의 1:N/N:M/다형 관계와 "투표 UNIQUE가 왜 1인1표인지"를 설명.
- **키워드:** data modeling, normalization, ERD 1:N/N:M, PK/FK/Index, SQL, transaction.
- **📖 1차 출처:** PostgreSQL *Part I. Tutorial*(1~3장) + *The SQL Language → Joins / Data Definition(제약·인덱스)* + *Transactions*.

### B3. CRUD + REST 설계 + 투표

- **개념:** Pydantic 요청/응답 스키마 분리(왜 입력과 출력을 나누나 — 비밀번호 같은 필드 누출 방지), `router→service→repository` 흐름, HTTP 상태코드 매핑(201 생성/400·422 잘못된 입력/404 없음/409 충돌), `HTTPException`, 페이징(cursor), 검색·태그 필터(쿼리 "내부"), Join, 멱등성(투표 토글).
- **드릴 (라우터/스키마/리포):**

  ```python
  # schemas.py — 외부 JSON은 camelCase, 내부 필드는 snake_case (alias로 연결)
  class PostCreate(BaseModel):
      title: ___
      excuse_text: str = Field(alias="___")        # "excuseText"
      tag_ids: list[str] = Field(default_factory=list, alias="___")  # "tagIds", 값은 태그 slug
      model_config = ConfigDict(populate_by_name=___)   # alias·필드명 둘 다 허용

  class PostOut(BaseModel):   # 부분 골격 — tags/verdict 등은 프론트 Post 키에 맞춰 확장
      id: int
      title: str
      excuse_text: str = Field(alias="excuseText")
      created_at: datetime = Field(alias="___")     # "createdAt"
      score: int                                    # 저장 컬럼 아님 — votes 합산(SUM(value), LEFT JOIN)
      model_config = ConfigDict(from_attributes=___, populate_by_name=True)  # ORM 객체 → 스키마
      # 응답 직렬화 시 response_model_by_alias=True 또는 by_alias=True 로 camelCase JSON 출력

  # routers/posts.py
  @router.post("/posts", status_code=___)        # 201
  async def create_post(body: PostCreate, ...):
      return await service.create(body)

  @router.get("/posts/{post_id}", response_model=PostOut, response_model_by_alias=True)
  async def get_post(post_id: int, ...):
      post = await repo.get(post_id)
      if not post:
          raise HTTPException(status_code=___, detail="not found")   # 404
      return post
  ```

  - 검색/태그/페이징은 `GET /posts`가 `q`/`tag`/`cursor`를 받아 **repository 쿼리 안에서** 처리.
  - `score`는 posts 컬럼이 아니라 **votes를 `LEFT JOIN` + `SUM(value)`로 집계**해 만든다(= "Join" 키워드의 실제 용처).
  - 투표 `POST /posts/{id}/vote`는 body `{value: 1|-1}`. 같은 값 재클릭은 취소, 반대 값은 전환 → **transaction**으로 votes upsert/delete + score 반영.
- **수직 슬라이스 ③:** 글 작성(201) → 목록(검색·태그·페이징·정렬) → 상세(404 처리) → 댓글 → 투표. 전부 `/docs`나 `curl`로 확인.
- **완료 기준:** 프론트 mock과 시그니처가 맞는 포럼 API가 REST로 동작. 상태코드를 의도대로 반환하고, 필터링이 라우터가 아니라 repository에 있다.
- **키워드:** REST, api design, CRUD, Join, error handling/HTTP, 멱등성, transaction.
- **📖 1차 출처:** FastAPI *Request Body / Response Model / Handling Errors / Dependencies*. (배경) MDN HTTP *Response status codes*.

### B4. 인증 + 프론트 연동

- **개념:** 해싱(bcrypt, salt, **왜 평문 저장 금지**), JWT 구조(`header.payload.signature`, 서명·검증, stateless = 서버가 세션을 안 들고 있음), `Depends`로 `get_current_user` 가드, `OAuth2PasswordBearer` 형태, CORS(왜 필요 — 다른 origin인 프론트의 요청 허용, preflight), rate limit(최소).
- **드릴 (해싱/토큰/가드):**

  ```python
  # auth/security.py
  def hash_password(pw: str) -> str:
      return pwd_context.___(pw)                  # hash

  def verify_password(pw: str, hashed: str) -> bool:
      return pwd_context.___(pw, hashed)          # verify

  def create_access_token(sub: str) -> str:
      payload = {"sub": sub, "exp": ___}          # 만료시각
      return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")

  # auth/deps.py
  async def get_current_user(token: str = Depends(oauth2_scheme)):
      payload = jwt.___(token, settings.jwt_secret, algorithms=["HS256"])  # decode
      ...  # sub로 유저 조회, 실패 시 401
  ```

  - `main.py`에 CORS 미들웨어(프론트 origin 허용), 로그인 라우트에 slowapi rate limit.
  - `POST /posts`를 `Depends(get_current_user)`로 보호.
- **수직 슬라이스 ④ (전체 흐름):** 회원가입 → 로그인(토큰) → 보호 엔드포인트 호출 → **프론트의 `api/auth.ts`·`api/posts.ts` 본문을 axios로 교체**해 mock 없이 실제 동작.
- **완료 기준:** JWT 로그인 + 보호 라우트 + CORS로 프론트가 붙는다. 비로그인 요청은 401. "JWT가 왜 stateless인지", "비밀번호를 왜 해싱하는지" 설명.
- **키워드:** JWT, OAuth2(형태만), CORS, Rate limit(최소), Session·CSRF·HTTPS(개념).
- **📖 1차 출처 (doc-first 트라이얼):** FastAPI *Security → "OAuth2 with Password (and hashing), Bearer with JWT tokens"* + *CORS (Middleware)*. (배경) MDN HTTP *CORS / Authentication / Cookies(세션)*.

---

## 6. 진행 체크리스트 (에이전트가 매 세션 갱신)

```
[ ] B0  환경 세팅 — uvicorn /health + /docs, Docker Postgres, backend/ 골격
[ ] B1  설정·골격 — config(.env)/main/db, 레이어드 구조 (슬라이스①)
[ ] B2  데이터 모델링 — ERD→SQL→SQLAlchemy 모델, 테이블 생성 (슬라이스②)
[ ] B3  CRUD+REST+투표 — 스키마(camel↔snake alias, tag slug↔DB PK 변환)/라우터/리포, 검색·태그·페이징·투표 body/score (슬라이스③)
[ ] B4  인증+연동 — 해싱/JWT/가드/CORS/rate limit, 프론트 axios 연결 (슬라이스④)
```

각 항목 완료 시 (1) 완료 기준 충족을 학습자와 확인하고, (2) 직전 개념 하나를 **변형 드릴**로 한 번 더 복습시킨 뒤 다음으로 넘어간다.

---

## 7. 에이전트 자가 점검 (응답 전 확인)

일반 점검은 `AGENTS.md`(절대 규칙 · 응답 형식 · 설명 원칙 4종 불변식 · 진행 방식)를 단일 출처로 적용한다 — 여기 재나열하지 않는다. **백엔드 추가 점검:**

1. 검증을 "실행·`curl`·`/docs`"로 안내했는가? (정답본 디프가 아니라 돌려서 확인.)
2. 필터링/페이징/정렬을 **라우터가 아니라 repository(쿼리) 안**에 두게 했는가?
3. 요청/응답 스키마를 분리했는가? (비밀번호 등 민감 필드가 응답에 새지 않게.)
4. 다중 행 변경(투표 토글 등)을 **transaction**으로 묶었는가?
5. 비밀번호를 평문이 아니라 **해싱**해서 다루는가? 비밀값은 `.env`에만?
6. API 시그니처를 기획서 §7 REST 계약 / 프론트 mock과 맞췄는가?
   - 태그는 외부 slug(`Tag.id`) ↔ 내부 숫자 PK로 변환되는가?
   - 투표는 `{value}` 요청과 `{score,myVote}` 응답 계약을 지키는가?
7. 범위 밖(AI: RAG/MCP/Agent)으로 새지 않았는가? → 개념 1~2문장 후 복귀.
8. SQLAlchemy/Pydantic/asyncio 내부를 과하게 깊이 파고 있지 않은가? → 정의·사용 수준까지만.

---

## 8. 다음 단계 예고 — AI 3종 (별도 계획)

백엔드 토대가 서면 RAG·MCP·Agent를 **별도 세션으로 계획**한다. 과제 최종엔 **셋 다 end-to-end 동작이 필수**(사용자 확정). 이번 문서는 자리만 비워 둔다.

- **RAG** — 등록 시 임베딩 적재(transaction), pgvector 유사/중복 검색. (`excuse_embeddings`)
- **MCP** — FastMCP 서버 + 외부 API 1개(날씨), JSON-RPC, API키 격리, timeout/재시도/캐시.
- **Agent** — LangGraph 판결 루프(`/posts/{id}/trial`), function calling, 무한루프 방지, 멱등성. (`verdict/credibility/counsel`)
- 착수 시 정할 것: **LLM/임베딩 provider 조합**, 분량 배분, 신뢰성(재시도·타임아웃·로깅) 깊이.
