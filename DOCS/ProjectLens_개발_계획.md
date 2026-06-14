# ProjectLens 개발 계획 — 마일스톤 & 구현 디테일

> ALIBAI(변명 게시판) → ProjectLens(AI 프로젝트 리뷰 게시판) 전환의 **실행 계획서**. 기획은 `DOCS/ProjectLens_Planning.md`, 현행 규범은 루트 `AGENTS.md`. 이 문서는 "무엇을 어떤 순서로, 어떤 파일을 어떻게 고쳐서 만드는가"에 집중한다.
> 모드: **제품 우선·탑다운.** 드릴 폐기. 4키워드(게시판·RAG·MCP·Agent) 전부 "동작"시키되, 깊은 퀄리티는 **히어로 = AI 진단 리포트**(MCP fetch → Agent → 구조화 카드) 하나에 몰아준다.
> 확정 결정: **LLM 스택 = OpenAI Agents SDK + Responses API + gpt-5.5** / **MCP = local/private** / **마이그레이션 = 클린 정리**(`excuse_text`→`body`, `verdict`·`credibility` 드롭) / **분석 = 동기(P0)** / **RAG = cosine 단독(초기)**.
> 현재 체크포인트(2026-06-15): **M3 리포트 카드 UI 완료**. 다음 실행은 **M4 = RAG + Agent Function Calling 보강**부터 재개한다.

---

## 0. 전환 개요 & 자산 인벤토리

피벗이 아니라 "골격 유지 + AI 절반 신축"이다. 기존 게시판 CRUD·인증·댓글·투표는 구조적으로 살아남고, AI 계층(ai/rag/mcp)은 통째로 신규다.

| 버킷 | 대상 | 비용 |
|---|---|---|
| **재사용 100%** | 인증 `backend/app/auth/`·`routers/auth.py`, 댓글 `repositories/comments.py`, 투표 `repositories/votes.py`(`target_type` 다형), 유저·태그, `db.py`(async), `config.py`, `limiter.py` | ~0 |
| **수정** | posts 계층: `models.py:27-45`, `schemas.py`(PostCreate/PostOut), `repositories/posts.py`, `services/posts.py`, 프론트 `types/post.ts`·`api/posts.ts`(`toPost` 어댑터)·`ExcuseForm.tsx`·`PostDetailPage.tsx`·`PostCard.tsx` | 중 |
| **신규** | `backend/app/ai/`, `rag/`, `mcp_client/`, 별도 `mcp-server/`, `services/analysis_service.py`, `routers/analysis.py`, 프론트 `components/analysis/*`·`api/analysis.ts`·`types/analysis.ts` | 대(비용의 대부분) |

**인프라 호재(탐색 확정):**
- `docker-compose.yml`가 이미 `pgvector/pgvector:pg16`(컨테이너 `alibai-db`) → 이미지 교체 불필요, `CREATE EXTENSION vector`만.
- 백엔드 완전 async(`asyncpg`, `AsyncSession`) → AI 러너에 적합.
- 프론트는 axios 아닌 커스텀 fetch 래퍼(`api/http.ts`, base `http://localhost:8000`) + `RawPost`→`Post` 어댑터(`toPost`).

**진행 원칙(순서):** `작동 성공(내 시드 3~5개)` → `데이터 수집(부트캠프 개방)` → `퀄리티(실패모드 먼저)`. 깨진 사이트엔 아무도 안 올린다 — 동작 증명이 개방보다 앞.

**OpenAI 런타임 원칙:** 기본 분석 모델은 `gpt-5.5`, 기본 `reasoning.effort=medium`. Responses API/Agents SDK를 쓰고, Chat Completions를 새 분석 파이프라인 기본값으로 삼지 않는다. Pydantic Structured Outputs가 출력 schema의 단일 출처다.

**MCP 제품 결정:** ProjectLens MVP의 MCP는 OpenAI hosted/remote MCP가 아니라 백엔드가 직접 연결하는 **local/private MCP**다. 사용자 경험은 “URL 입력 → 분석 버튼 → 카드 표시”로 숨기고, URL fetch 보안·실패 메시지·로그 저장은 Backend가 소유한다.

---

## 1. 마일스톤 (우선순위 순 — MVP 척추)

각 마일스톤은 **목표 / 작업(파일) / 검증(동작이 곧 진도)** 으로 적는다. 검증을 통과해야 다음으로 간다.

### M0 · 데이터 계층 마이그레이션 — [P0, 모든 것의 전제]

**목표:** 변명 스키마를 프로젝트 스키마로 클린 전환하고 AI 저장소 테이블을 만든다.

**작업:**
- DB `backend/db/schema.sql`:
  ```sql
  -- posts 클린 정리
  ALTER TABLE posts RENAME COLUMN excuse_text TO body;
  ALTER TABLE posts DROP COLUMN verdict, DROP COLUMN credibility, DROP COLUMN context;
  ALTER TABLE posts
    ADD COLUMN post_type        TEXT  NOT NULL DEFAULT 'project',  -- project | idea(후순위)
    ADD COLUMN service_url       TEXT,
    ADD COLUMN github_url        TEXT,
    ADD COLUMN one_liner         TEXT,
    ADD COLUMN target_user       TEXT,
    ADD COLUMN tech_stack        TEXT[],
    ADD COLUMN analysis_status   TEXT  NOT NULL DEFAULT 'not_started', -- not_started|running|completed|failed|need_more_info
    ADD COLUMN ai_summary        TEXT;
  ALTER TABLE posts ADD CONSTRAINT posts_post_type_check
    CHECK (post_type IN ('project', 'idea'));
  ALTER TABLE posts ADD CONSTRAINT posts_analysis_status_check
    CHECK (analysis_status IN ('not_started', 'running', 'completed', 'failed', 'need_more_info'));

  -- AI 저장소
  CREATE EXTENSION IF NOT EXISTS vector;
  CREATE TABLE ai_reports (
    id BIGSERIAL PRIMARY KEY,
    post_id BIGINT REFERENCES posts(id) ON DELETE CASCADE,
    status TEXT NOT NULL CHECK (status IN ('completed', 'need_more_info', 'failed', 'refused')),
    report_type TEXT DEFAULT 'full_analysis',
    model TEXT,
    reasoning_effort TEXT,
    response_id TEXT,
    trace_id TEXT,
    usage JSONB,
    input_snapshot JSONB,
    report JSONB,
    error JSONB,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
  );
  CREATE TABLE mcp_evidences (
    id BIGSERIAL PRIMARY KEY,
    post_id BIGINT REFERENCES posts(id) ON DELETE CASCADE,
    report_id BIGINT REFERENCES ai_reports(id) ON DELETE SET NULL,
    tool_name TEXT NOT NULL,
    arguments JSONB, result JSONB,
    success BOOLEAN DEFAULT true, error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
  );
  CREATE TABLE embeddings (
    id BIGSERIAL PRIMARY KEY,
    source_type TEXT NOT NULL,   -- post | ai_report | comment | template
    source_id BIGINT NOT NULL,
    embedding vector(1536),      -- text-embedding-3-small
    embedding_model TEXT NOT NULL DEFAULT 'text-embedding-3-small',
    dimensions INT NOT NULL DEFAULT 1536,
    content_text TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
  );
  CREATE INDEX embeddings_vec_idx ON embeddings USING ivfflat (embedding vector_cosine_ops);
  ```
  > `analysis_jobs`는 **컷**(동기 MVP). 기존 변명 데이터는 데모/학습용이라 버려도 무방.
- 모델 `backend/app/models.py`: `Post`에서 `excuse_text`/`verdict`/`credibility`/`context` 제거, 위 신규 컬럼 추가(`tech_stack`은 `ARRAY(Text)`). 신규 ORM `AiReport`·`McpEvidence`·`Embedding` 추가(또는 raw SQL 조회로 시작).
- 스키마 `backend/app/schemas.py`: `PostCreate`에 `service_url(serviceUrl)`·`github_url(githubUrl)`·`one_liner(oneLiner)`·`post_type(postType)`·`target_user`·`tech_stack(techStack)` 추가, `excuse_text`→`body`. `PostOut`에 `ai_summary(aiSummary)`·`analysis_status(analysisStatus)`·`one_liner` 추가, `verdict`/`credibility` 제거.
- 리포지토리 `backend/app/repositories/posts.py`: `create_post` insert에 신규 필드 매핑(`repositories/posts.py:92-112`), `list_posts`에 `post_type` 선택 필터(`:37-89`). 검색/페이징 로직은 그대로 유효.
- 서비스 `backend/app/services/posts.py`: `create`가 신규 필드를 받아 넘기도록 확장.
- 의존성 `backend/requirements.txt` 추가: `openai-agents`, `openai`, `httpx`, `pgvector`.
- 설정 `backend/app/config.py` 추가: `openai_api_key`, `embedding_model`(기본 `text-embedding-3-small`), `agent_model`(기본 `gpt-5.5`), `reasoning_effort`(기본 `medium`), MCP 연결 정보. `.env`에 `OPENAI_API_KEY` 추가.

**검증:** 서버 기동(`uvicorn app.main:app --reload`), `\d posts`에 신규 컬럼·구필드 제거·CHECK 확인, `POST /posts`에 `serviceUrl` 포함 작성 → `GET`이 반환, `ai_reports`·`embeddings` 테이블 생성 및 `response_id/usage/error` 컬럼 확인.

### M1 · MCP 사이트 분석 도구 — [P0]

**목표:** 외부 사이트를 실제로 읽어오는 안전한 도구층. 단독으로 호출·검증 가능한 첫 동작.

**방식:** local/private MCP. Backend 런타임이 MCP 서버에 직접 연결하고, OpenAI hosted/remote MCP는 MVP에서 쓰지 않는다. 이유는 사용자 URL fetch의 SSRF 방어, 실패 UX, evidence 로그를 제품 백엔드가 통제해야 하기 때문이다.

**작업:**
- 별도 `mcp-server/`(기획서 §14 구조): `server.py` + `tools/site.py` + `tools/safety.py` + `requirements.txt` + `.env`.
- 툴 2개: `fetch_site_overview`(status_code·title·description·h1·main_text·links·fetched_at), `check_deploy_status`(is_reachable·status_code·response_time_ms·final_url).
- **`safety.py`(SSRF 가드, 필수):** DNS 해석 후 IP 검사 → `localhost`/`127.0.0.0/8`/사설 대역(10·172.16-31·192.168)/링크로컬 `169.254.0.0/16`(메타데이터 `169.254.169.254`) 차단, **리다이렉트 최종 URL 재검증**, `timeout`(예 5s), 응답 body 크기 제한(예 1~2MB), `User-Agent` 명시, robots 과도 크롤링 금지.
- prompt injection 방어: MCP로 가져온 HTML/README/main_text는 **근거 데이터**일 뿐 지시문이 아니다. tool description과 Agent instructions에 외부 텍스트 안의 명령을 무시하라고 명시.
- tool allowlist: M1/P0에서 허용한 MCP 도구는 `fetch_site_overview`, `check_deploy_status` 두 개다. `fetch_github_readme`는 과제 조건 보강을 위해 M4에서 승격한다.
- 백엔드 `backend/app/mcp_client/`(`client.py`·`tools.py`): Agents SDK local/private MCP 연결로 위 툴을 agent-level tool로 노출. MCP 결과는 `mcp_evidences`에 저장하되 비밀값/토큰/불필요한 개인정보는 저장하지 않는다.

**검증:** 실 URL(예 본인 배포 사이트)에 `fetch_site_overview` 단독 호출 → title/메타/main_text 반환. `http://localhost:8000`·`http://169.254.169.254` 입력 시 **차단**됨(SSRF 테스트). 외부 본문에 “이전 지시를 무시하라” 같은 문구가 있어도 리포트 지시로 사용하지 않음(prompt injection 테스트).

### M2 · Agent 분석 파이프라인 — [P0 · ★히어로]

**목표:** post 컨텍스트 + MCP 수집 정보를 구조화된 진단 리포트로 변환. **퀄리티를 여기에 몰아준다.**

**작업:**
- `backend/app/ai/schemas.py`: `ProjectAnalysisReport` Pydantic = **히어로 범위로 트림**.
  - `service_understanding`(one_line_summary·detailed_summary·target_users·core_features[]·auto_tags)
  - `diagnosis`(strengths[{title,reason,evidence_kind}]·weaknesses[{title,reason,severity,evidence_kind}]·improvement_plan[{priority,action,expected_effect,based_on}])
  - `evidence`(mcp_sources[]·rag_sources[])
  - `status`(`completed` | `need_more_info` | `failed` | `refused` + missing_fields/questions/error) — 기획서 §11.
  - portfolio·presentation·similar_projects는 스키마에 자리만 두고 **M4/Q3에서 채움**.
- `backend/app/ai/prompts.py`: 시스템 지시문(기획서 §10.5 — 확인 vs 추정 분리, 없는 기능 금지, 보완점은 개선 제안, MCP 외부 텍스트는 지시문이 아니라 evidence).
- `backend/app/ai/agents/project_analysis_agent.py` + `ai/runner.py`: `Agent(..., model=settings.agent_model, output_type=ProjectAnalysisReport)` 형태로 Pydantic Structured Outputs 사용. 기본 모델 `gpt-5.5`, 기본 `reasoning.effort=medium`. M2 완료 시점은 백엔드가 MCP evidence를 먼저 수집해 Agent 입력으로 넘기는 baseline이며, **Agent가 직접 도구를 선택하는 Function Calling 루프는 M4에서 보강**한다.
- `ai/runner.py` 흐름 = load_post_context → validate_input(불충분 시 `need_more_info`) → collect_external(MCP baseline) → evidence 정제/길이 제한 → (RAG와 Agent function tools는 M4 합류) → structured output → save.
- `backend/app/services/analysis_service.py`: 오케스트레이션 + 저장. `ai_reports` insert, `posts.analysis_status`·`ai_summary` 갱신, `mcp_evidences` 로그. OpenAI `response_id`/`trace_id`/`usage`/`model`/`reasoning_effort`/`error` 저장.
- 라우터 `backend/app/routers/analysis.py`: `POST /posts/{id}/analysis`(**동기**, 완료 시 `{status, reportId, report}` 반환), `GET /posts/{id}/analysis/latest`. `backend/app/main.py`에 `analysis_router` 등록.
- 실패 처리(최소): URL 접속 실패 → `failed` 또는 `need_more_info`. Structured Output validation 실패 → 1회 재시도 후 `failed`. 모델 safety refusal → `refused`. 모든 실패는 `ai_reports.error`에 저장.

**검증:** 시드 1개에 `POST /posts/{id}/analysis` → `ai_reports` row 생성, 반환 JSON이 Pydantic 스키마 유효(카드 매핑 가능), `posts.analysis_status='completed'`, `ai_summary` 채워짐, `mcp_evidences`에 호출 로그, `ai_reports.response_id/usage/model/reasoning_effort` 저장. 정보 부족 케이스는 `need_more_info`, 접속 실패는 `failed`, refusal 모의 케이스는 `refused`로 저장.

### M3 · 리포트 카드 UI — [P0 · "작동 성공" 지점]

**목표:** "URL 넣으면 진짜 카드가 뜬다"를 브라우저에서 관통 증명.

**작업:**
- 타입/`api`: 프론트 `types/analysis.ts`(`ProjectAnalysisReport` 미러), `api/analysis.ts`(`runAnalysis`·`fetchLatestReport`). `types/post.ts`·`api/posts.ts`의 `toPost` 어댑터에서 alibi 필드(`verdict`·`credibility`·`excuseText`·`ExcuseContext`) 제거 → `body`·프로젝트 필드·`aiSummary`·`analysisStatus`로 교체. `mockData.ts`도 ProjectLens 모양으로.
- 컴포넌트 `frontend/src/components/analysis/`: `AnalysisReport`(상태머신 분기), `ServiceUnderstandingCard`, `DiagnosisCard`, `AnalysisStatusBadge`(not_started/running/completed/failed/need_more_info/refused).
- 페이지: `PostDetailPage.tsx`에 `[AI 분석 실행]` 버튼 + 리포트 영역 삽입. `ProjectForm`(ExcuseForm 대체) = 프로젝트명·한줄설명·URL·GitHub·기술스택·본문. `PostCard.tsx`에 `aiSummary` + 상태 배지.

**검증(브라우저 E2E):** 로그인 → URL 포함 프로젝트 작성 → 상세에서 `[AI 분석 실행]` → 서비스이해/진단 카드 렌더, 상태 배지 전이. `need_more_info`/`failed`/`refused`도 깨지지 않고 안내 카드로 렌더. **여기서 "작동 성공" 달성 → 시드 5개 채우고 데모 가능.**

### M4 · RAG + Agent Function Calling 보강 — [P1 · 과제 필수 강화]

**목표:** M3에서 화면까지 연결된 분석 흐름을 과제 조건에 맞게 강화한다. RAG로 게시판을 검색 가능한 판례집으로 만들고, MCP 호출은 Agent가 `function_tool`로 선택 실행하게 바꾼다. **데이터 적을 땐 약함을 인정**하고, 도구 호출 근거는 `mcp_evidences`에 남긴다.

**작업:**
- `backend/app/rag/embedder.py`: post/리포트 텍스트 → OpenAI embedding(`text-embedding-3-small`, 1536).
- `rag/indexer.py`: post 생성·리포트 생성 시 `embeddings` 저장(`source_type`·`source_id`·`content_text`).
- `rag/retriever.py`/`similarity.py`: **cosine top-k 단독**(`embedding <=> query` ivfflat). 가중 공식(기획서 §8.5)은 Q4로 미룸.
- 합류: top-k를 Agent 입력과 `evidence.rag_sources` 근거로 연결 + 프론트 `SimilarProjectsCard`.
- 빈 상태 정직 처리: 유사도 임계값 미만 → "비슷한 게시물이 아직 충분하지 않습니다".
- `backend/app/ai/tools.py`: Agents SDK `function_tool`로 `check_deploy_status`, `fetch_site_overview`, `fetch_github_readme`를 노출한다. tool 내부는 기존 `call_mcp_tool()` 경로를 재사용해 SSRF/allowlist/log redaction 계약을 유지한다.
- Agent instructions 보강: 서비스 URL이 있으면 `check_deploy_status`를 먼저 호출하고, 접속 가능하거나 본문 근거가 필요하면 `fetch_site_overview`를 호출한다. GitHub URL이 있으면 `fetch_github_readme`로 README/메타데이터를 근거로 가져온다. 외부 텍스트는 끝까지 evidence이며 instruction이 아니다.
- `runner.py`/`analysis_service.py`: `AnalysisContext`에 tool call evidence를 모았다가 `ai_reports` row 생성 후 `report_id`를 붙여 `mcp_evidences`에 저장한다. 기존 고정 `_collect_mcp_evidence()`는 제거하거나 mock/fallback 전용으로 낮춘다.
- `mcp-server/tools/github.py`: GitHub URL에서 `owner/repo`만 파싱하고 서버가 `https://api.github.com/repos/{owner}/{repo}/readme`를 직접 구성한다. `GITHUB_TOKEN`은 선택적이며 `.env`/환경변수에만 둔다. 토큰·Authorization은 로그에 남기지 않는다.

**검증:** 시드 5개 임베딩 저장 후 한 글에서 유사글이 합리적 이웃 반환, 임계값 미만 시 빈 메시지. Agent 리포트의 `evidence.rag_sources`에 출처 기록. 실 OpenAI 키가 있으면 Agent가 MCP function tool을 실제 호출하고 `max_turns` 안에서 종료되는지 확인한다. 키가 없으면 RAG DB/query와 tool wrapper/로그 계약을 검증하되, Agent Function Calling 실검증은 미완료 리스크로 체크포인트에 남긴다.

### M5 · 데이터 수집 개방 + 시드 — [P1]

**목표:** 동작을 증명한 뒤 부트캠프 전원 업로드로 시드·데모 서사 확보.

**작업:** 본인이 시드 5개 작성 → 파이프라인 증명 → 개방. 업로드 폼/안내에 **동의 문구 1줄**("등록한 URL·GitHub는 AI 분석과 유사 추천에 사용됩니다"). 순서는 반드시 개방보다 동작이 앞.

**검증:** 외부 사용자 업로드 → 분석 정상, 게시물 누적될수록 유사 추천 품질 상승 체감.

---

## 2. 퀄리티 상승 단계 (작동 성공 후)

> 신기능 추가가 아니라 **완성도**가 목표. 남는 시간은 여기 순서대로.

- **Q1 · 실패 모드 견고화 [최고 ROI]:** 기획서 §20의 5개 — URL 실패 graceful 안내, 사이트 텍스트 빈약 → `body`/README 폴백, RAG 빈 결과, Structured Output validation/refusal 처리, 느린 분석 → loading. *"실제 쓸 만한 퀄리티"를 죽이는 건 AI 성능이 아니라 통합 글루·엣지케이스다.*
- **Q2 · 프롬프트/스키마 튜닝:** "확인된 정보 vs AI 추정" 명시 분리, 보완점 톤(인신공격 금지·실행 가능 제안), 카드별 재생성 버튼(선택).
- **Q3 · 보너스 줍기:** 포폴/발표 카드 — 같은 리포트 재활용이라 **저비용 고가치**. `POST /posts/{id}/portfolio`·`/presentation`, `PortfolioCard`·`PresentationCard` + 복사 버튼. 본인 발표 서사에도 직결.
- **Q4 · RAG 정밀화(데이터 쌓인 뒤):** `semantic*0.65 + tag_overlap*0.15 + vote*0.10 + recency*0.05 + same_type*0.05`(기획서 §8.5). 게시물 20개 미만에선 의미 없으니 데이터 확보 후.
- **Q5 · MCP 확장(선택):** M4의 `fetch_github_readme` 이후에도 가치가 분명할 때만 screenshot/Lighthouse/robots 등 §9.4 후보를 추가한다. 과제 필수 보강은 M4에서 끝내고, Q5는 품질 선택지로 둔다.

---

## 3. 컷 리스트 (이번엔 안 한다)

async job + polling(P0 컷, 단 시드 분석이 15초를 자주 넘으면 승격) · 멀티 에이전트 분리 · 시작부터 가중 점수 · Playwright 스크린샷 · Lighthouse · 아이디어 게시판(기획서도 "선택") · 전체 재생성 버튼 · 웹 전체 크롤링 · GitHub Issue 자동 생성 · Slack/Notion 연동.

---

## 4. 결정 로그 & 환경 준비

**확정:**
- LLM 스택 = **OpenAI Agents SDK + Responses API + gpt-5.5**(기획서 §7 일치, MCP 연결 + Structured Outputs).
- 모델 설정 = `agent_model=gpt-5.5`, `reasoning_effort=medium` 기본. 시드 5개로 품질/비용/지연을 보고 조정.
- MCP 방식 = **local/private MCP**. Backend가 연결·필터링·승인/로그·실패 UX를 소유. hosted/remote MCP는 추후 공식 외부 서비스 연동 옵션.
- Agent 도구 호출 = M4부터 Agents SDK `function_tool`이 local/private MCP 호출을 감싼다. 백엔드는 도구 호출 context와 evidence 저장을 소유한다.
- 마이그레이션 = **클린 정리**(`excuse_text`→`body`, `verdict`·`credibility`·`context` 드롭).
- 분석 = **동기**(MVP). RAG = **cosine 단독**(초기), 가중은 Q4.
- 임베딩 = `text-embedding-3-small`(1536).

**환경 준비물:**
- `.env`: `OPENAI_API_KEY`, `AGENT_MODEL=gpt-5.5`, `REASONING_EFFORT=medium`, (필요시) MCP 연결값. 비밀값은 `.env`만 — 커밋 금지.
- DB: `docker compose up -d db`(이미 pgvector 이미지) → `CREATE EXTENSION vector`.
- 설치: `pip install -r backend/requirements.txt`(신규 4종 포함), `mcp-server/requirements.txt`.

**1차 출처:** OpenAI latest model guide(`gpt-5.5`), Agents SDK/Responses API, Agents MCP integration, MCP/connectors safety, Structured Outputs, embeddings guide — 기획서 §7.2 링크. pgvector 연산자(`<=>`), FastAPI 라우팅은 `DOCS/백엔드/공식문서_레퍼런스.md`.

---

## 5. 빠른 체크리스트

```text
M0 [ ] posts 클린 마이그레이션 + ai_reports/mcp_evidences/embeddings + CREATE EXTENSION vector
   [ ] CHECK 제약 + response_id/trace_id/usage/error 컬럼
   [ ] models/schemas/repo/service 갱신, requirements 4종, config+.env(gpt-5.5/medium)
M1 [ ] mcp-server fetch_site_overview + check_deploy_status + SSRF safety
   [ ] local/private backend mcp_client 연결 + tool allowlist + prompt injection 방어
M2 [ ] ProjectAnalysisReport(트림) + prompts + agent/runner + analysis_service
   [ ] POST /posts/{id}/analysis(동기) + Structured Outputs + response/usage/error 저장
   [ ] need_more_info/failed/refused 검증
M3 [ ] types/api/analysis + P0 카드 4종 + ProjectForm + PostDetail/Card 개편 → 브라우저 E2E
M4 [ ] embedder/indexer/retriever(cosine) + SimilarProjectsCard + 빈상태
   [ ] Agent function_tool(check_deploy_status/fetch_site_overview/fetch_github_readme) + evidence 저장
M5 [ ] 시드 5개 → 동작 증명 → 개방(동의 문구)
Q1 [ ] 실패 모드 5종  Q2 [ ] 프롬프트/스키마  Q3 [ ] 포폴/발표  Q4 [ ] RAG 가중  Q5 [ ] 추가 MCP 확장(선택)
```
