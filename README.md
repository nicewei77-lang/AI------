# ProjectLens

ProjectLens는 공개된 프로젝트 URL과 GitHub 저장소를 AI가 근거 기반으로 진단하고, 그 결과를 개선 액션과 포트폴리오/발표 문장으로 재사용할 수 있게 정리하는 프로젝트 리뷰 게시판입니다.

- 서비스 URL: https://frontend-wei5.vercel.app
- GitHub URL: https://github.com/nicewei77-lang/AI------
- 백엔드 API 기본값: https://projectlens-api.onrender.com

## 1. 문제 정의

개인 프로젝트나 부트캠프 프로젝트를 만든 개발자는 실제 구현보다 설명에서 더 자주 막힙니다. 배포 URL은 있지만 첫 화면이 무엇을 말하는지, README가 충분한지, 포트폴리오 문장으로 어떤 강점을 잡아야 하는지 판단하기 어렵습니다.

ProjectLens는 프로젝트 작성자가 입력한 설명, 공개 서비스 URL, GitHub README, 유사 프로젝트 데이터를 함께 보고 다음 질문에 답하도록 설계했습니다.

- 이 서비스가 무엇을 하는지 한 문장으로 설명할 수 있는가?
- 공개 화면과 README만 보고 확인 가능한 강점은 무엇인가?
- 확인되지 않은 기능을 지어내지 않고 리스크와 개선 방향을 말할 수 있는가?
- 분석 결과를 발표나 포트폴리오 문장으로 다시 쓸 수 있는가?

## 2. 타깃 사용자

주 사용자는 부트캠프 또는 개인 프로젝트를 만든 개발자입니다. 특히 프로젝트는 완성했지만 서비스 설명, 개선 우선순위, 발표 흐름, 포트폴리오 문장을 정리해야 하는 사람을 대상으로 합니다.

ProjectLens는 코드 품질 감사 도구가 아니라 공개 표면을 바탕으로 한 AI 프로젝트 리뷰 도구입니다. 로그인 뒤 화면, 비공개 코드, 실제 사용자 데이터는 분석 범위에 포함하지 않습니다.

## 3. 핵심 흐름

1. 사용자가 프로젝트 제목, 한 줄 설명, 서비스 URL, GitHub URL, 기술 스택, 본문 설명을 게시글로 등록합니다.
2. 백엔드는 서비스 URL의 배포 상태와 공개 페이지 내용을 안전하게 수집합니다.
3. GitHub URL이 있으면 README와 기본 저장소 메타데이터를 공개 근거로 가져옵니다.
4. RAG 검색으로 게시판에 쌓인 유사 프로젝트와 기존 리포트 근거를 찾습니다.
5. OpenAI Agent가 수집된 근거를 바탕으로 구조화된 AI 리뷰 리포트를 생성합니다.
6. 프론트엔드는 리포트를 채팅 로그가 아니라 카드 UI로 보여주고, 포트폴리오/발표 문장 복사를 지원합니다.

## 4. Agent, RAG, MCP 아키텍처

ProjectLens의 AI 리뷰는 모델 호출 하나로 끝나지 않습니다. 백엔드가 근거 수집, 도구 호출, RAG 검색, 출력 검증, 저장을 오케스트레이션합니다.

```text
Project post
  -> FastAPI analysis API
  -> local/private MCP tools
       - check_deploy_status
       - fetch_site_overview
       - fetch_github_readme
       - fetch_site_context
       - fetch_rendered_site_overview
       - capture_screenshot
       - run_lighthouse_summary
  -> pgvector RAG search
  -> OpenAI Agents SDK + Responses API
  -> Pydantic Structured Output
  -> ai_reports / mcp_evidences / embeddings
  -> React report cards
```

### Backend

- FastAPI async API
- PostgreSQL + pgvector
- SQLAlchemy async session
- OpenAI Agents SDK + Responses API
- Pydantic Structured Outputs
- local/private MCP server

### Frontend

- React + TypeScript + Vite
- 커스텀 fetch wrapper
- 프로젝트 목록/상세/등록 화면
- AI 리포트 카드, 근거 카드, 유사 프로젝트 카드, 포트폴리오/발표 카드

### Data storage

- `posts`: 프로젝트 게시글과 분석 상태
- `ai_reports`: Agent 실행 결과, response/trace/usage/error, structured report JSON
- `mcp_evidences`: MCP 도구 호출 근거와 실패 정보
- `embeddings`: 게시글/리포트 기반 RAG 벡터

## 5. 실행 방법

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

`.env`에는 로컬 DB와 OpenAI 키를 설정합니다. 비밀값은 커밋하지 않습니다.

```bash
docker compose up -d db
python scripts/apply_schema.py
uvicorn app.main:app --reload
```

헬스 체크:

```bash
curl http://localhost:8000/health
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

프로덕션 빌드 확인:

```bash
cd frontend
npm run build
```

### MCP / Lighthouse support

MCP 서버는 백엔드에서 local/private 도구층으로 사용합니다. Lighthouse 요약 도구를 쓰려면 `mcp-server`의 Node 의존성이 필요합니다.

```bash
cd mcp-server
npm install
```

## 6. 공개 근거와 분석 한계

ProjectLens는 공개 근거와 AI 해석을 분리합니다. 외부 사이트나 README에서 가져온 텍스트는 분석 대상 데이터일 뿐, Agent가 따라야 하는 지시문이 아닙니다.

현재 리포트가 근거로 삼을 수 있는 범위:

- 사용자가 작성한 게시글 본문, 한 줄 설명, 타깃 사용자, 기술 스택
- 공개 서비스 URL의 HTTP 상태, 제목, 주요 텍스트, 내부 링크 일부
- GitHub README와 기본 저장소 메타데이터
- 첫 화면 렌더링 결과, 스크린샷 메타데이터, Lighthouse summary
- 게시판에 저장된 유사 프로젝트 RAG 결과

리포트가 단정하지 않는 범위:

- 로그인 뒤 화면이나 비공개 관리자 화면
- 비공개 코드 내부 품질
- 실제 사용자 지표, 매출, 트래픽
- README나 공개 화면에 없는 기능
- Lighthouse 점수를 제품 가치 자체로 해석하는 주장

분석이 실패하거나 근거가 부족하면 `failed` 또는 `need_more_info` 상태로 저장하고, 확인하지 못한 범위를 카드에 표시합니다.

## 7. 검증 명령

대표 검증 흐름은 다음과 같습니다.

```bash
cd backend
.venv/bin/python -m compileall app ../mcp-server
.venv/bin/python scripts/run_projectlens_q1_q5_smoke.py
.venv/bin/python scripts/run_projectlens_mcp_expansion_smoke.py --fail-under-threshold
.venv/bin/python scripts/run_projectlens_quality_eval.py --fail-under-threshold
```

```bash
cd frontend
npm run build
```

공개 리뷰 전에는 다음을 확인합니다.

```bash
curl -s -o /dev/null -w '%{http_code}\n' https://frontend-wei5.vercel.app
curl -s -o /dev/null -w '%{http_code}\n' https://github.com/nicewei77-lang/AI------
```

두 URL 모두 외부에서 `200`으로 접근 가능해야 ProjectLens의 공개 근거 수집 리포트가 정상적으로 의미를 가집니다.
