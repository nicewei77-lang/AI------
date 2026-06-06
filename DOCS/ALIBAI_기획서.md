# ALIBAI — 변명 검증소

> **AI 변명 재판소 (The Excuse Tribunal)**
> 모든 변명은 무죄로 추정된다. 단, AI가 반증을 찾기 전까지만.

**과목:** AI로 진화하기 — AI 응용 기술을 활용한 게시판 구현 (개인 과제)
**한 줄 정의:** 사용자가 변명을 제출하면, 게시판이 **과거 전과(RAG)** 와 **객관적 증거(MCP)** 를 조회해 **판사(Agent)** 가 신뢰도를 판정하고, 유죄 시 더 나은 변명까지 선고해 주는 Q&A 게시판.

---

## 0. 왜 이 프로젝트인가 (기획 의도)

게시판의 본질은 **글이 쌓이고(축적), 묻고 답하며(스레드), 집단의 지식이 모이는(집단지성)** 비동기 공간이다. ALIBAI는 이 본질을 농담으로 비틀되, 그 농담이 RAG·MCP·Agent 세 기술을 *억지 없이* 요구하도록 설계했다.

- **변명은 반복된다.** "차 막혔어요", "아파서요", "메일 못 봤어요"는 인류 공통의 클리셰다. → 누적될수록 **RAG**가 똑똑해지는 플라이휠.
- **변명은 검증 가능하다.** 날씨·교통·뉴스는 실제로 조회되는 객관 데이터다. → **MCP**가 장식이 아니라 *판결의 증거*가 된다.
- **변명은 판정과 반론이 필요하다.** → **Agent**가 추론 루프로 판결하고, 유죄면 항소용 변명을 생성한다.

즉, 유머는 표면이고 그 아래 구조는 진지하다. 이 문서는 그 진지한 부분을 명세한다.

### 통일 메타포: 법정

| 법정 요소 | 시스템 구성요소 | 기술 |
|---|---|---|
| 피고인의 진술(변명) | 게시물 본문 | 게시판 CRUD |
| 전과 조회 | 유사 변명 검색 / 중복 적발 | **RAG** |
| 증거 수집 | 날씨·교통·뉴스 사실 확인 | **MCP** |
| 판사 | 판정 + 항소 변명 생성 | **Agent** |
| 판례집 | 누적되는 변명·판결 코퍼스 | 게시판 = Vector Store |
| 배심원 | 다른 사용자의 댓글·투표 | 댓글/태그 |

---

## 1. 핵심 사용자 시나리오 (End-to-End)

> 한 번의 흐름 안에 RAG·MCP·Agent가 각자 다른 일을 한다. 겹치지 않는다.

```
1. 피고인 등판
   사용자가 변명을 제출한다.
   "오늘 폭우 때문에 지하철이 지연돼서 9시 회의에 늦었습니다." (2026-06-05, 강남)

2. 전과 조회 — RAG
   과거 변명 코퍼스에서 의미 유사 검색.
   → "폭우/지하철 지연" 변명을 이미 3번 사용 (#41, #58, #77)
   → 판결 요약: 이 사용자의 '날씨 핑계' 누적 4회

3. 증거 수집 — Agent가 도구 선택 → MCP 호출
   Agent: "날씨 + 교통 검증이 필요하다" 판단 (function calling)
   → check_weather("2026-06-05", "강남")  → 맑음, 강수량 0mm
   → check_traffic("2026-06-05", "08:30", "지하철 2호선") → 정상 운행, 지연 기록 없음

4. 판결 — Agent
   증거(날씨 불일치 + 지연 없음) + 전과(상습 날씨핑계)를 종합.
   판정: 유죄 (신뢰도 12%)
   "기상청 기록상 당일 강남 강수량은 0mm이며 2호선 지연 기록이 없습니다.
    또한 본 법정은 귀하의 4번째 날씨 핑계임을 적시합니다."

5. 선고 후 변호 — Agent
   "항소를 원하시면 다음 변명을 권합니다(증거와 모순되지 않음):
    '집 엘리베이터 점검으로 출발이 지연됐습니다' — 검증 불가 영역이라 안전합니다."

6. 판례 축적
   이 변명·증거·판결이 코퍼스에 적재 → 다음 사건의 RAG가 더 똑똑해짐.
```

---

## 2. 기능 명세

### 2.1 기본 게시판 기능 (과제 필수)

| 기능 | 설명 | 비고 |
|---|---|---|
| 회원가입 / 로그인 | 이메일 + 비밀번호, JWT 인증 | 피고인 등록 |
| 게시물 CRUD | 변명(=사건) 작성/조회/수정/삭제 | 본문 + 상황 메타데이터(날짜·장소·경로) |
| 댓글 | 다른 사용자의 의견 = 배심원 평결 | AI 판결도 댓글 형태로 부착 |
| 태그 | 변명 유형 분류 (지각/결석/미답장/마감) | 일부 자동 태깅(Agent) |
| 페이징 | 사건 목록 페이지네이션 | cursor 또는 offset |
| 검색 | 키워드 검색 + (확장) 의미 검색 | 의미 검색은 RAG 재사용 |

### 2.2 AI 활용 기능 (과제 필수)

| 기능 | 기술 | 산출물 |
|---|---|---|
| **전과/중복 적발** | RAG | "그 변명 #41에서 이미 사용", 변명 패턴 통계 |
| **알리바이 검증** | MCP | 날씨·교통·뉴스 기반 객관 증거 |
| **판결 + 항소 변명 생성** | Agent | 신뢰도 점수, 판결문, 대체 변명 |

---

## 3. 시스템 아키텍처

```
┌──────────────┐      HTTPS/JSON       ┌─────────────────────────────┐
│  React (Vite)│  ───────────────────▶ │   FastAPI Backend           │
│  법정 UI     │ ◀───────────────────  │   (Host / Orchestrator)     │
└──────────────┘                       │                             │
                                       │  ├─ Auth (JWT)              │
                                       │  ├─ Board CRUD/Comment/Tag  │
                                       │  ├─ RAG 모듈 (전과 조회)    │
                                       │  └─ Agent (LangGraph 판사)  │
                                       └───────┬───────────┬─────────┘
                                               │           │
                            JSON-RPC (MCP)     │           │  SQL
                                               ▼           ▼
                                   ┌────────────────┐  ┌──────────────────────┐
                                   │ 알리바이 검증   │  │ PostgreSQL + pgvector │
                                   │ MCP Server      │  │  - users / posts      │
                                   │  ├ check_weather│  │  - comments / tags    │
                                   │  ├ check_traffic│  │  - verifications      │
                                   │  └ check_news   │  │  - embeddings(vector) │
                                   └───────┬────────┘  └──────────────────────┘
                                           │ REST (API Key는 서버 내부 보관)
                                           ▼
                                 [ 날씨 API / 교통 API / 뉴스 API ]
```

핵심 분리 원칙(노션 정리본 기준):
- **Host = FastAPI**: 사용자 대화, LLM 호출, 도구 사용 판단, 권한 관리.
- **MCP Client**: FastAPI 안에서 MCP Server와 JSON-RPC 세션을 여는 연결 모듈.
- **MCP Server**: 외부 API를 감싸 tool로 노출. **API 키는 여기에만 존재**.
- **LLM(상용)**: 판단(어떤 도구·어떤 인자)만 담당. 실제 호출은 Client/Server가 수행.

---

## 4. 기술 스택 & 선정 근거

| 레이어 | 선택 | 근거 |
|---|---|---|
| 프론트엔드 | **React (Vite) + TypeScript** | 과제 필수. Vite로 가벼운 셋업 |
| 백엔드 | **FastAPI (Python)** | 과제 선택지 중 택1. LangGraph·pgvector·MCP SDK와 같은 Python 생태계로 통일 → 솔로 개발 마찰 최소 |
| DB | **PostgreSQL 16 + pgvector** | 과제 선택지. **게시판 데이터와 벡터를 DB 하나로** 처리 → 인프라 최소 |
| LLM | **상용 (OpenAI GPT-4o-mini 또는 Anthropic Claude)** | function calling 지원, 저비용 |
| 임베딩 | **OpenAI text-embedding-3-small** | 한국어 처리 양호, 1536차원, 저렴. (대안: 다국어 오픈 임베딩) |
| Vector DB | **pgvector** | 위 PostgreSQL에 확장으로 포함 |
| RAG 프레임워크 | **LangChain (얇게)** 또는 직접 구현 | 변명은 짧아 chunking 불필요 → 거의 직접 구현 수준으로도 충분. 과제 체크용으로 LangChain retriever만 사용 |
| Agent | **LangGraph** | 과제 권장. 상태(state) 기반 추론 루프, recursion limit으로 무한루프 방지 |
| MCP 서버 | **Python MCP SDK (FastMCP)** | JSON-RPC 기본 제공, tool 정의 간결 |
| 인증 | **JWT (python-jose) + passlib(bcrypt)** | 표준적 |
| 컨테이너 | **Docker Compose (Postgres)** | DB만 컨테이너로, 앱은 로컬 실행해도 무방 |

---

## 5. AI 기술 상세 설계

### 5.1 RAG — 전과 조회 / 중복 적발

**데이터 소스:** 외부 문서가 아니라 **게시판에 누적되는 변명 글 자체**. (Data Store = 판례집)

**파이프라인**
```
변명 등록
 → 변명 본문 + 상황 메타를 임베딩 (text-embedding-3-small)
 → pgvector의 excuse_embeddings 테이블에 저장
 ─────────────────────────────────────────────
새 변명 판정 시
 → 새 변명 임베딩
 → 코사인 유사도 Top-k 검색 (같은 작성자 가중치 ↑)
 → 유사도 임계값 초과 시 "중복/상습" 플래그
```

**노션 RAG 정리본의 안전장치를 그대로 차용** (유머 게시판이지만 정교함은 여기서 드러난다):
1. **문서 우선 규칙**: 판결문은 검색된 전과/증거만 근거로 작성. 추측 금지.
2. **인용 강제**: 모든 판결 주장 뒤에 근거 글 번호([#41]) 또는 증거 출처(기상청) 부착.
3. **관련성 점수**: 유사 전과가 임계값 미만이면 "전과 없음"으로 처리(허위 기소 방지).
4. **충돌 감지**: 증거 간 모순(날씨 API A vs B) 시 최신/신뢰 출처 우선 명시.

> 신뢰성 공식(노션 차용): **검색 품질 × 증거 품질 × 프롬프트 설계 × 모델의 지시 준수 × 검증 장치**

### 5.2 MCP — 알리바이 검증 서버

**과제 요건 매핑**
- ✅ MCP Server 직접 구현 (서버 1개)
- ✅ JSON-RPC 기반 요청/응답 (MCP SDK 기본)
- ✅ 최소 1개 이상 실제 외부 서비스 연동 (날씨 → 뉴스 → 교통 순으로 확장)
- ✅ API Key / 권한 관리 전략 포함

**노출 도구(Tools)**

| Tool | 입력 | 출력 | 감싸는 외부 서비스 |
|---|---|---|---|
| `check_weather` | `date`, `location` | `{condition, precip_mm, supports_excuse}` | 날씨 API |
| `check_traffic` | `date`, `time`, `route` | `{congested, incident, supports_excuse}` | 교통/대중교통 API |
| `check_news` | `date`, `keyword` | `{found, headline, source, supports_excuse}` | 뉴스 API |

각 tool은 외부 API 응답을 **"변명을 뒷받침하는가(boolean) + 근거"** 형태로 가공해 반환한다(AI-friendly interface).

**JSON-RPC 호출 예시**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "check_weather",
    "arguments": { "date": "2026-06-05", "location": "강남" }
  },
  "id": 7
}
```

**API Key / 권한 관리 전략 (과제 채점 포인트)**
- 모든 외부 API 키는 **MCP 서버의 `.env`에만** 존재. LLM·프론트·게시판 DB 어디에도 노출 금지.
- LLM은 "어떤 검증을 할지"만 판단 → 실제 키를 들고 호출하는 건 서버.
- 동일 (날짜+지역) 조회는 **캐싱**(중복 과금/호출 방지).
- tool별 **rate limit** + 호출 실패 시 graceful degradation.
- 모든 검증 호출을 `verifications` 테이블에 **감사 로그**로 적재(누가·언제·무엇을 검증했는지).

### 5.3 Agent — 판사

**구조:** LangGraph 상태 그래프. ReAct 변형(생각 → 도구 → 관찰 → 판결).

**State 정의(요지)**
```
ExcuseCase = {
  excuse_text, context(date/location/route),
  prior_records[],        # RAG 결과
  evidences[],            # MCP 결과
  step_count,             # 무한루프 방지
  verdict, credibility, counsel_excuse
}
```

**노드(흐름)**
```
classify        변명 유형 분류 → 필요한 검증 종류 결정
   ↓
retrieve(RAG)   전과/중복 조회
   ↓
gather_evidence 필요한 MCP tool을 function calling으로 호출 (0~3개)
   ↓
judge           증거 + 전과 종합 → 신뢰도 점수 + 판결문 (인용 강제)
   ↓
counsel         유죄(임계값 미만)면 증거와 모순되지 않는 대체 변명 생성
   ↓
END
```

**무한 루프 방지 / 예외처리 (과제 필수)**
- LangGraph `recursion_limit` 설정 + state의 `step_count` 상한.
- MCP tool **timeout** → 해당 증거는 "확인 불가"로 처리하고 **무죄 추정** 쪽으로 가중(증거 없음을 유죄 근거로 쓰지 않음).
- 외부 API 4xx/5xx → fallback 메시지("증거 수집 실패, 본 건은 증거 불충분으로 판단").
- LLM 출력 파싱 실패 → 1회 재시도 후 안전 기본값.

**판정 점수(신뢰도) 산식 — 농담이되 결정론적으로**
```
credibility (0~100)
 = base 50
   + Σ(증거 일치 시 +가중치 / 불일치 시 -가중치)
   - 전과_패널티(동일 유형 변명 누적 횟수 × k)
 → clamp(0, 100)

판정: credibility ≥ 60 → 무죄(인정)
      40 ≤ credibility < 60 → 보류(추가 소명 요청)
      credibility < 40 → 유죄(기각) + counsel 노드 진입
```

---

## 6. 데이터 모델 (PostgreSQL)

```sql
-- 사용자(피고인)
CREATE TABLE users (
  id            BIGSERIAL PRIMARY KEY,
  email         TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  nickname      TEXT NOT NULL,
  created_at    TIMESTAMPTZ DEFAULT now()
);

-- 변명(사건)
CREATE TABLE posts (
  id            BIGSERIAL PRIMARY KEY,
  author_id     BIGINT REFERENCES users(id) ON DELETE CASCADE,
  situation     TEXT,                         -- 지각/결석/미답장/마감 ...
  excuse_text   TEXT NOT NULL,
  context       JSONB,                        -- {date, location, route, time}
  verdict       TEXT,                         -- 무죄/보류/유죄
  credibility   INT,                          -- 0~100
  counsel_excuse TEXT,                         -- 항소용 대체 변명
  created_at    TIMESTAMPTZ DEFAULT now()
);

-- 변명 임베딩 (전과 조회용)
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE excuse_embeddings (
  post_id   BIGINT PRIMARY KEY REFERENCES posts(id) ON DELETE CASCADE,
  embedding vector(1536)
);
CREATE INDEX ON excuse_embeddings USING ivfflat (embedding vector_cosine_ops);

-- 댓글(배심원 + AI 판결)
CREATE TABLE comments (
  id         BIGSERIAL PRIMARY KEY,
  post_id    BIGINT REFERENCES posts(id) ON DELETE CASCADE,
  author_id  BIGINT REFERENCES users(id),  -- AI 판결은 NULL + is_ai
  is_ai      BOOLEAN DEFAULT false,
  body       TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 태그
CREATE TABLE tags (
  id   BIGSERIAL PRIMARY KEY,
  name TEXT UNIQUE NOT NULL
);
CREATE TABLE post_tags (
  post_id BIGINT REFERENCES posts(id) ON DELETE CASCADE,
  tag_id  BIGINT REFERENCES tags(id) ON DELETE CASCADE,
  PRIMARY KEY (post_id, tag_id)
);

-- MCP 검증 감사 로그
CREATE TABLE verifications (
  id            BIGSERIAL PRIMARY KEY,
  post_id       BIGINT REFERENCES posts(id) ON DELETE CASCADE,
  tool_name     TEXT,
  arguments     JSONB,
  evidence      JSONB,
  supports      BOOLEAN,
  created_at    TIMESTAMPTZ DEFAULT now()
);
```

---

## 7. API 설계 (REST)

| Method | Endpoint | 설명 |
|---|---|---|
| POST | `/auth/signup` | 회원가입 |
| POST | `/auth/login` | 로그인 → JWT |
| GET | `/posts` | 사건 목록 (페이징, `?cursor=`, `?tag=`, `?q=`) |
| POST | `/posts` | 변명 제출 (등록 직후 임베딩 적재) |
| GET | `/posts/{id}` | 사건 상세 (판결·증거 포함) |
| PATCH | `/posts/{id}` | 수정 |
| DELETE | `/posts/{id}` | 삭제 |
| POST | `/posts/{id}/trial` | **재판 시작** → Agent 판정 트리거 |
| GET | `/posts/{id}/comments` | 댓글 목록 |
| POST | `/posts/{id}/comments` | 댓글 작성 |
| GET | `/search?q=` | 키워드 + (확장) 의미 검색 |
| GET | `/stats/me` | 내 변명 패턴 통계 (RAG 집계) |

> `/trial`을 별도 엔드포인트로 둬서 "등록"과 "재판"을 분리 → 데모 시 판정 과정을 명확히 보여줄 수 있다.

---

## 8. 개발 환경 & 폴더 구조

### 8.1 폴더 구조 (모노레포)

```
alibai/
├── README.md
├── docker-compose.yml          # PostgreSQL + pgvector
├── .env.example                # 루트 공통 (참고용)
│
├── frontend/                   # React + Vite + TS
│   ├── src/
│   │   ├── pages/              # 사건목록 / 사건상세 / 작성 / 로그인
│   │   ├── components/         # 판결카드, 증거뱃지, 변명폼
│   │   ├── api/                # axios 클라이언트
│   │   └── types/
│   ├── index.html
│   ├── package.json
│   └── vite.config.ts
│
├── backend/                    # FastAPI (Host / Orchestrator)
│   ├── app/
│   │   ├── main.py             # FastAPI 진입점
│   │   ├── config.py           # 환경변수 로딩
│   │   ├── db.py               # SQLAlchemy / asyncpg
│   │   ├── models.py           # ORM 모델
│   │   ├── schemas.py          # Pydantic 스키마
│   │   ├── auth/               # JWT, 해싱
│   │   ├── routers/            # posts, comments, auth, search, trial
│   │   ├── rag/                # 임베딩, pgvector 검색, 전과 조회
│   │   ├── agent/              # LangGraph 그래프(판사), 프롬프트
│   │   └── mcp_client/         # MCP 서버와 JSON-RPC 세션
│   ├── requirements.txt
│   └── .env                    # 백엔드 비밀값 (LLM 키, DB URL, JWT 시크릿)
│
└── mcp-server/                 # 알리바이 검증 MCP Server
    ├── server.py               # FastMCP, tool 3종 정의
    ├── tools/
    │   ├── weather.py          # 날씨 API 래퍼
    │   ├── traffic.py          # 교통 API 래퍼
    │   └── news.py             # 뉴스 API 래퍼
    ├── cache.py                # (날짜+지역) 캐싱
    ├── requirements.txt
    └── .env                    # ★ 외부 API 키는 오직 여기 ★
```

### 8.2 환경 변수

```ini
# mcp-server/.env  ── 외부 API 키는 여기에만!
WEATHER_API_KEY=____
NEWS_API_KEY=____
TRAFFIC_API_KEY=____

# backend/.env
DATABASE_URL=postgresql+asyncpg://alibai:alibai@localhost:5432/alibai
OPENAI_API_KEY=____            # 또는 ANTHROPIC_API_KEY
EMBEDDING_MODEL=text-embedding-3-small
JWT_SECRET=____
MCP_SERVER_URL=http://localhost:8765   # 또는 stdio
```

### 8.3 docker-compose (DB)

```yaml
services:
  db:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: alibai
      POSTGRES_PASSWORD: alibai
      POSTGRES_DB: alibai
    ports: ["5432:5432"]
    volumes: ["pgdata:/var/lib/postgresql/data"]
volumes:
  pgdata:
```

### 8.4 셋업 명령

```bash
# 0. DB
docker compose up -d

# 1. 백엔드
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt        # fastapi uvicorn sqlalchemy asyncpg
                                        # pgvector langgraph langchain openai
                                        # python-jose passlib[bcrypt] httpx
uvicorn app.main:app --reload

# 2. MCP 서버
cd ../mcp-server
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt        # mcp(fastmcp) httpx python-dotenv
python server.py

# 3. 프론트엔드
cd ../frontend
npm install                            # react react-dom axios + vite
npm run dev
```

---

## 9. 구현 로드맵 (마일스톤)

> 작게 시작해 단계마다 동작하는 것을 보장한다. 외부 API는 **날씨 하나**로 MVP를 먼저 돌린다.

| 단계 | 목표 | 산출물 |
|---|---|---|
| **P0** | 환경 세팅 | docker DB, 3개 repo 골격, .env, 헬스체크 |
| **P1** | 순수 게시판 | 회원가입/로그인, 변명 CRUD, 댓글, 태그, 페이징, 키워드 검색 |
| **P2** | RAG | 등록 시 임베딩 적재, 전과/중복 검색, 패턴 통계 `/stats/me` |
| **P3** | MCP(날씨) + 판결 | `check_weather` tool, MCP Client 연결, judge 노드로 판정 |
| **P4** | Agent 고도화 | LangGraph state·재생성(counsel), 무한루프/예외처리, 뉴스·교통 tool 추가 |
| **P5** | 데모 & 제출 | 시드 변명 20건, 스크린샷, README 작성 |

---

## 10. 리스크 & 한계 (정직하게)

- **콜드스타트:** 초기 판례집이 비어 RAG가 빈약 → MVP 단계에선 MCP(증거) 비중이 큼. 시드 데이터 + 본인 사용으로 플라이휠 가동. *(이 한계 자체가 README 회고의 좋은 소재)*
- **외부 API 무료 티어:** 호출 한도·한국 데이터 커버리지 제약 가능. 캐싱 + 날씨 우선 전략으로 완화.
- **오판(false verdict):** 증거 불충분을 유죄 근거로 쓰지 않도록 "무죄 추정" 가중. 사용자에게 **재심 청구**(재판 재실행) 제공.
- **한국어 임베딩 품질:** 짧은 변명 문장의 유사도 정확도 점검 필요. 임계값 튜닝 또는 임베딩 모델 교체로 대응.
- **개인정보:** 변명에 들어갈 수 있는 위치·일정은 장기 저장 범위를 최소화(노션 Agent 정리본의 memory 주의사항 준수).

---

## 11. 제출물(README) 매핑

과제 README 6항목이 이 기획서로 거의 자동 충족된다.

| README 항목 | 본 문서 대응 |
|---|---|
| 1. 프로젝트 개요 | §0, §1 |
| 2. 주요 구현 기능 | §2 |
| 3. 전체 아키텍처 구조 | §3, §6, §7, §8 |
| 4. RAG 기능·기술·구조 | §5.1 |
| 4. MCP 기능·기술·구조 | §5.2 |
| 4. Agent 기능·기술·구조 | §5.3 |
| 5. 데모 (스크린샷 1+) | P5 산출물 |
| 6. 회고·한계·개선 | §10 |

---

## 부록 A. 톤 가이드 — "유머러스함과 대비되는 정교함"

- **표면(UI·문구)은 웃기게:** 판결문, "무죄 추정", "항소", "전과 4범" 같은 법정 카피.
- **내부(엔지니어링)는 진지하게:** 인용 강제, 충돌 감지, 무죄 추정 가중, 감사 로그, 무한루프 방지.
- 농담이 기능을 가리지 않게: 판정 근거(증거 출처·전과 글 번호)는 **항상 명시**한다. 웃기지만 검증 가능해야 한다.

> *"본 법정은 귀하의 변명을 사랑합니다. 다만 믿지는 않습니다."*
