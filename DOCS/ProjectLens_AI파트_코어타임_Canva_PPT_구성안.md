# ProjectLens AI 파트 코어타임 Canva PPT 구성안

> 기준 문서: `DOCS/ProjectLens_AI파트_코어타임_설명초안.md`  
> 목적: ProjectLens 서비스 소개가 아니라, 과제의 AI 필수 요구인 RAG, MCP, AI Agent를 이해시키는 발표자료로 변환한다.  
> Canva 제작 원칙: 텍스트를 줄이고, RAG/MCP/Agent 관계와 Agent 루프를 시각자료로 적극 표현한다.

---

## 0. Canva 제작 브리프

### 발표 제목

```text
AI 활용 필수 요구 이해하기
RAG, MCP, Agent를 과제 구현 관점으로 연결하기
```

### 대상

- React/FastAPI 게시판 구현 경험은 있지만 AI 응용 구현은 낯선 부트캠프 팀원
- "무엇을 구현해야 하는지"는 알지만, RAG/MCP/Agent의 구현 디테일을 잡기 어려운 사람
- 발표 이후 직접 구현할 때 어떤 선택지를 봐야 하는지 기준이 필요한 사람

### 핵심 메시지

```text
RAG는 검색,
MCP는 연결,
Agent는 루프다.
```

### 발표 톤

- 개념은 쉽게 말한다.
- 구현 판단은 정확하게 말한다.
- ProjectLens는 예시로만 짧게 사용한다.
- 외부 사이트, README, MCP 결과는 지시문이 아니라 근거 데이터라는 보안 관점을 반복한다.

### 권장 디자인 방향

- 스타일: digital, clean, 교육용 technical deck
- 색상: RAG=green/teal, MCP=blue, Agent=orange, 위험/비용=red accent
- 레이아웃: 다이어그램 중심, 본문은 2-4줄 이하
- 시각자료: 파이프라인, 구조도, 루프, 체크리스트, 비교표, meter/stack
- 금지: 긴 문단 복붙, ProjectLens 서비스 기능 소개 과다, Notion signed URL 직접 삽입

---

## 1. 전체 목차

| # | 슬라이드 제목 | 역할 |
| --- | --- | --- |
| 1 | AI 활용 필수 요구 이해하기 | 발표 주제와 방향을 잡는다. |
| 2 | 오늘의 목표 | 발표용 핵심과 구현 참고를 분리한다. |
| 3 | 과제 요구 한 장 정리 | 게시판 요구와 AI 필수 요구를 구분한다. |
| 4 | 세 기술의 관계 | RAG/MCP/Agent를 한 장의 지도처럼 보여준다. |
| 5 | RAG: 학습이 아니라 검색 | RAG의 본질을 설명한다. |
| 6 | MCP: API가 아니라 AI용 연결 규격 | MCP의 본질을 설명한다. |
| 7 | Agent: 단일 호출이 아니라 루프 | Agent의 본질을 설명한다. |
| 8 | 핵심 시각화: Agent 루프 | 발표의 클라이맥스. 상태와 루프를 보여준다. |
| 9 | 통합 흐름 예시 | ProjectLens를 짧은 예시 라벨로만 사용한다. |
| 10 | 구현 순서 한 장 | 실제 구현 순서를 잡아준다. |
| 11 | RAG 구현 참고표 | 구현할 때 결정할 항목을 정리한다. |
| 12 | MCP 구현 참고표 | 구현할 때 결정할 항목을 정리한다. |
| 13 | Agent 구현 참고표 | 구현할 때 결정할 항목을 정리한다. |
| 14 | RAG 개선 포인트 | 검색 품질 개선 축을 설명한다. |
| 15 | Agent 루프 개선 포인트 | 루프 안정화 축을 설명한다. |
| 16 | OpenAI API 비용 주의 | 호출 제한, token, credit, auto recharge를 설명한다. |
| 17 | 기존 백엔드/프론트와 연결 | 낯선 AI 코드를 익숙한 웹 개발 개념으로 연결한다. |
| 18 | 외울 문장과 Q&A | 발표를 닫고 질문에 대비한다. |

---

## 2. 슬라이드별 구성안

### 1. AI 활용 필수 요구 이해하기

핵심 메시지:

```text
오늘의 목표는 ProjectLens 소개가 아니라, 과제의 AI 필수 요구를 구현 가능한 구조로 이해하는 것이다.
```

본문:

- 게시판 기본 요구 위에 RAG, MCP, Agent를 붙이는 과제 구조
- 세 기술을 따로 외우지 않고 하나의 Agent 루프로 연결해서 이해
- ProjectLens는 그 구조를 보여주는 짧은 예시로만 사용

시각자료 지시:

- 중앙에 큰 제목
- 아래에 세 개 아이콘: `RAG 검색`, `MCP 연결`, `Agent 루프`
- 배경은 추상 AI 이미지가 아니라, 노드와 화살표가 있는 얇은 기술 지도 느낌

발표자 메모:

```text
오늘은 제 서비스를 자세히 설명하는 시간이 아닙니다. 과제에서 요구하는 AI 활용 파트를 어떻게 이해하고 구현하면 되는지, RAG/MCP/Agent 세 개를 하나의 흐름으로 잡아보겠습니다.
```

---

### 2. 오늘의 목표

핵심 메시지:

```text
발표에서는 핵심만, 세부 구현 판단은 뒤쪽 참고표로 분리한다.
```

본문:

- 발표에서 말할 것: 개념, 과제 요구, Agent 루프
- 구현할 때 볼 것: 선택지, 피할 구현, 최소 합격선
- 마지막에는 Canva 이후 구현 참고로 쓸 수 있는 체크리스트 제공

시각자료 지시:

- 화면을 좌우 2분할
- 왼쪽: `PPT에서 말할 핵심`
- 오른쪽: `구현할 때 참고`
- 가운데에 "발표 시간에는 핵심만" 라벨

발표자 메모:

```text
RAG, MCP, Agent는 세부 구현으로 들어가면 금방 복잡해집니다. 그래서 발표에서는 중요한 구조만 잡고, 나중에 실제 구현할 때 참고할 표는 뒤쪽에 따로 두겠습니다.
```

---

### 3. 과제 요구 한 장 정리

핵심 메시지:

```text
게시판 기본 요구와 AI 필수 요구는 층이 다르다.
```

본문:

- 기본 웹 서비스: CRUD, 인증, 댓글, 검색, 태그, 페이지네이션
- RAG: 내 데이터와 LLM을 연결하는 검색 구조
- MCP: LLM이 외부 시스템을 호출할 수 있게 하는 연결 규격
- Agent: 도구 선택과 실행 결과 관찰을 관리하는 추론 루프

시각자료 지시:

- 2층 구조 다이어그램
- 아래층: `게시판 기본 기능`
- 위층: `RAG`, `MCP`, `Agent`
- Agent를 위층 중앙에 두고 RAG/MCP를 양쪽 도구로 배치

발표자 메모:

```text
게시판은 기본 제품의 뼈대입니다. AI 필수 요구는 그 위에 올라가는 별도 층입니다. RAG는 내부 데이터를 찾게 하고, MCP는 외부 서비스를 연결하고, Agent는 그 둘을 언제 쓸지 판단하는 루프를 만듭니다.
```

---

### 4. 세 기술의 관계

핵심 메시지:

```text
RAG와 MCP는 Agent가 사용할 수 있는 근거와 도구이고, Agent는 그 결과를 보고 다시 판단한다.
```

본문:

- RAG: 내부 데이터 검색
- MCP: 외부 시스템 호출
- Agent: 상태를 보며 도구를 선택하고 최종 결과 생성

시각자료 지시:

- 큰 삼각형 또는 hub-and-spoke 구조
- 중앙: `Agent`
- 왼쪽: `RAG = internal knowledge`
- 오른쪽: `MCP = external tools`
- 아래: `Structured Output -> DB/UI`

발표자 메모:

```text
세 개를 병렬 기능으로 보면 헷갈립니다. 실제 구현에서는 Agent가 중심이고, RAG는 내부 근거를 찾는 경로, MCP는 외부 근거를 가져오는 경로가 됩니다.
```

---

### 5. RAG: 학습이 아니라 검색

핵심 메시지:

```text
RAG는 모델을 새로 학습시키는 것이 아니라, 필요한 순간에 관련 데이터를 검색해서 읽게 하는 방식이다.
```

본문:

- 문서/DB를 chunk로 나누고 embedding으로 저장
- 질문도 embedding으로 바꿔 의미가 가까운 chunk 검색
- 검색 결과를 context로 넣어 LLM이 근거를 보고 답변

시각자료 지시:

- `Indexing -> Retrieval -> Generation` 3단계 파이프라인
- Notion 이미지 자리: RAG indexing/retrieval/generation 흐름
- 출처 캡션: `출처: Notion [JUNGLE] AI로 진화하기 / RAG`

발표자 메모:

```text
RAG를 "AI에게 우리 데이터를 학습시킨다"라고 말하면 부정확합니다. 실제로는 데이터를 검색 가능한 형태로 저장해두고, 질문이 들어왔을 때 관련 조각만 찾아서 모델에게 읽게 하는 구조입니다.
```

---

### 6. MCP: API가 아니라 AI용 연결 규격

핵심 메시지:

```text
MCP는 API를 없애는 기술이 아니라, API와 외부 시스템을 AI가 쓰기 좋은 tool 형태로 감싸는 표준 연결 방식이다.
```

본문:

- MCP Host가 전체 앱과 권한을 관리
- MCP Client가 JSON-RPC로 MCP Server와 통신
- MCP Server가 실제 외부 API, DB, 파일, 서비스를 호출
- 외부 결과는 instruction이 아니라 evidence

시각자료 지시:

- 상단: USB-C 비유 이미지 자리
- 하단: `Host -> Client -> JSON-RPC -> Server -> External Service`
- Notion 이미지 자리: MCP USB-C 비유, MCP Host/Client/Server 구조
- 출처 캡션: `출처: Notion [JUNGLE] AI로 진화하기 / MCP`

발표자 메모:

```text
그냥 백엔드에서 외부 API를 호출했다고 MCP라고 하기는 어렵습니다. MCP는 AI 앱이 도구 목록과 schema를 보고 호출할 수 있도록 Server/Client/Host 구조를 갖추는 것이 핵심입니다.
```

---

### 7. Agent: 단일 호출이 아니라 루프

핵심 메시지:

```text
Agent는 한 번 답하고 끝나는 LLM 호출이 아니라, 생각하고 도구를 쓰고 관찰한 뒤 다시 판단하는 루프다.
```

본문:

- Model: 판단과 생성
- Tools: 실행 가능한 기능
- Orchestration Layer: 상태, 순서, 종료 조건 관리
- 핵심은 `Think -> Act -> Observe -> Think again`

시각자료 지시:

- `Model + Tools + Orchestration Layer` 블록 다이어그램
- 옆에 작은 ReAct 루프 아이콘
- Notion 이미지 자리: Agent 구조, ReAct 루프
- 출처 캡션: `출처: Notion [JUNGLE] AI로 진화하기 / AI agents`

발표자 메모:

```text
프롬프트가 길다고 Agent가 되는 것은 아닙니다. Agent라고 설명하려면 목표, 도구, 상태, 루프, 종료 조건이 보여야 합니다.
```

---

### 8. 핵심 시각화: Agent 루프

핵심 메시지:

```text
Observation을 보고 Agent 판단으로 되돌아가는 화살표가 Agent의 핵심이다.
```

본문:

- 사용자 요청으로 state 생성
- Agent가 RAG/MCP tool 사용 여부 판단
- tool 결과를 observation으로 받고 다시 판단
- 충분하면 structured output 생성

시각자료 지시:

- 이 장은 텍스트보다 다이어그램이 70% 이상
- Mermaid 기반 루프를 Canva 도형으로 재구성

```text
User Request
-> State
-> Agent Think
-> Tool Call
-> Execute
-> Observation
-> Agent Think Again
-> Structured Output
```

- `Observation -> Agent Think Again` 화살표를 굵고 강조색으로 표시

발표자 메모:

```text
이 되돌아가는 화살표가 제일 중요합니다. 단일 LLM 호출은 한 번 답하고 끝나지만, Agent는 도구 실행 결과를 보고 다시 판단합니다.
```

---

### 9. 통합 흐름 예시

핵심 메시지:

```text
ProjectLens는 Agent 루프를 게시글 분석 기능에 붙인 예시다.
```

본문:

- 프론트의 분석 버튼이 backend analysis job을 시작
- RAG가 내부 유사 프로젝트를 검색
- Agent가 MCP tool을 선택해 외부 근거를 가져옴
- Structured Outputs로 리포트를 만들고 DB/UI에 저장

시각자료 지시:

- 가로형 end-to-end flow

```text
분석 버튼 -> backend job/state -> RAG -> Agent -> MCP tool -> observation -> structured output -> DB -> card UI
```

- ProjectLens 로고/제품 설명은 최소화
- 라벨만 `ProjectLens 예시`로 표시

발표자 메모:

```text
여기서 ProjectLens는 예시입니다. 중요한 것은 게시글 분석이라는 하나의 기능 안에서 RAG 검색, MCP 호출, Agent 루프, 구조화 저장이 연결된다는 점입니다.
```

---

### 10. 구현 순서 한 장

핵심 메시지:

```text
처음부터 완벽한 Agent를 만들지 말고, 기본 웹 기능 위에 AI 기능을 단계적으로 붙인다.
```

본문:

1. 게시판 기본 기능을 먼저 안정화
2. RAG용 데이터 저장과 검색 경로 구축
3. MCP Server로 외부 서비스 1개 이상 연결
4. Agent가 RAG/MCP를 tool로 쓰는 루프 구성
5. 상태, 실패, 비용 제한을 붙여 서비스화

시각자료 지시:

- 5단계 계단 또는 roadmap
- 마지막 단계에 `service-ready` 배지

발표자 메모:

```text
과제 구현에서 중요한 건 순서입니다. AI부터 붙이면 디버깅이 어렵습니다. 기본 웹 기능, 검색 구조, 외부 도구, Agent 루프, 운영 안정화 순서로 가는 편이 설명도 구현도 쉽습니다.
```

---

### 11. RAG 구현 참고표

핵심 메시지:

```text
RAG 구현 판단은 데이터 소스, embedding, vector DB, 검색 기준, 출처 표시로 나뉜다.
```

본문:

| 결정 | 기준 |
| --- | --- |
| 데이터 소스 | LLM이 원래 모르지만 답변에 필요한 데이터 |
| embedding | 질문과 문서를 같은 모델로 vector화 |
| vector DB | pgvector, Pinecone, FAISS, ChromaDB 등 운영 조건에 맞게 선택 |
| 검색 기준 | top-k, threshold, metadata ranking |
| fallback | 근거가 없으면 빈 결과/근거 부족으로 처리 |

시각자료 지시:

- 일반 표가 아니라 decision board 카드 5개
- 각 카드에 아이콘: database, vector, search, filter, warning

발표자 메모:

```text
이 표는 발표 때 길게 읽지 않고, 구현할 때 체크리스트로 보면 됩니다. RAG는 "검색해서 넣는다"는 말보다 검색 품질과 출처 처리가 훨씬 중요합니다.
```

---

### 12. MCP 구현 참고표

핵심 메시지:

```text
MCP는 tool schema, JSON-RPC 흐름, 외부 서비스 연동, 권한 관리가 보여야 한다.
```

본문:

| 결정 | 기준 |
| --- | --- |
| MCP Server | 목적이 분명한 tool 제공 |
| tool schema | 모델이 안정적으로 arguments를 만들 수 있는 입력/출력 |
| JSON-RPC | `tools/list`, `tools/call` 흐름 이해 |
| 외부 서비스 | GitHub, Notion, Slack, DB, 배포 API 등 최소 1개 |
| 권한/보안 | API key는 서버에 숨기고, 외부 텍스트는 evidence only |

시각자료 지시:

- `Host / Client / Server` 구조도 옆에 체크리스트 배치
- 보안 항목은 자물쇠 아이콘과 별도 강조

발표자 메모:

```text
MCP는 외부 API 호출과 비슷해서 익숙하지만, AI가 tool 목록과 schema를 보고 호출할 수 있게 만든다는 점이 다릅니다. 그리고 외부에서 가져온 텍스트는 절대 지시문처럼 따르면 안 됩니다.
```

---

### 13. Agent 구현 참고표

핵심 메시지:

```text
Agent 구현 판단은 function calling, state, loop 제한, error handling, structured output으로 정리된다.
```

본문:

| 결정 | 기준 |
| --- | --- |
| function calling | 모델은 `tool_name + arguments`, backend는 실제 실행 |
| state | running/completed/failed, tool result, final output 저장 |
| loop 제한 | max turns, timeout, retry limit |
| error handling | failed/need_more_info/refused/loading 구분 |
| structured output | UI와 DB가 읽을 수 있는 schema로 결과 고정 |

시각자료 지시:

- Agent 루프 다이어그램 한쪽에 guardrail checklist 배치
- `max turns`, `timeout`, `schema`를 빨간 안전핀처럼 표시

발표자 메모:

```text
Agent를 구현할 때 가장 위험한 건 "모델이 알아서 하겠지"라고 두는 겁니다. 모델은 판단하고, backend는 실행과 권한과 종료 조건을 통제해야 합니다.
```

---

### 14. RAG 개선 포인트

핵심 메시지:

```text
RAG 품질은 모델보다 검색 품질에 크게 좌우된다.
```

본문:

- chunk와 metadata를 조정해 검색 단위를 개선
- top-k와 threshold로 관련 없는 근거 차단
- source와 score를 저장해 검증 가능하게 만들기
- 데이터가 충분하면 semantic score 외에 태그/유형/최신성도 ranking에 반영

시각자료 지시:

- before/after 검색 결과 카드
- 왼쪽: 엉뚱한 근거가 섞인 상태
- 오른쪽: source, score, metadata가 정리된 상태

발표자 메모:

```text
좋은 RAG는 답변을 잘 쓰게 하는 기술이기 전에, 좋은 근거를 찾는 기술입니다. 검색 결과가 엉뚱하면 모델이 똑똑해도 결과가 흔들립니다.
```

---

### 15. Agent 루프 개선 포인트

핵심 메시지:

```text
Agent 품질은 한 번의 답변보다 루프의 안정성에서 나온다.
```

본문:

- tool description과 schema를 명확히 해 잘못된 tool 선택을 줄임
- max turns, timeout, retry limit으로 무한 루프 방지
- tool error와 observation을 저장해 디버깅 가능하게 함
- 오래 걸리는 작업은 async polling으로 UI를 안정화

시각자료 지시:

- Agent 루프 위에 guardrail 레이어를 얹은 그림
- 각 guardrail 라벨: `tool schema`, `max turns`, `retry`, `structured output`, `polling`

발표자 메모:

```text
Agent는 실패와 지연까지 상태로 다뤄야 서비스가 됩니다. 루프가 있다는 건 강력하지만, 동시에 비용과 시간과 실패도 반복될 수 있다는 뜻입니다.
```

---

### 16. OpenAI API 비용 주의

핵심 메시지:

```text
Agent 루프는 기능 루프이면서 비용 루프이기도 하다.
```

본문:

- Rate limits는 요청 수와 token 수 기준으로 걸릴 수 있음
- API 가격은 token 사용량에 영향을 받음
- monthly budget과 usage dashboard를 확인
- prepaid credit과 auto recharge, monthly recharge limit을 확인

시각자료 지시:

- `1 user request -> N model calls -> N tool observations -> token/cost meter 증가` 그림
- 오른쪽에 빨간 체크리스트: `usage dashboard`, `budget`, `auto recharge`, `credit`

발표자 메모:

```text
Agent가 도구를 여러 번 쓰면 호출 수와 token이 빠르게 늘 수 있습니다. 실습 전에는 usage dashboard, budget, credit, auto recharge를 꼭 확인해야 합니다.
```

근거:

- OpenAI Rate limits: https://developers.openai.com/api/docs/guides/rate-limits
- OpenAI API Pricing: https://openai.com/api/pricing/
- OpenAI prepaid billing: https://help.openai.com/en/articles/8264644-what-is-prepaid-billing

---

### 17. 기존 백엔드/프론트와 연결

핵심 메시지:

```text
AI 기능도 완전히 낯선 것이 아니라, 기존 백엔드/프론트 패턴의 확장으로 읽을 수 있다.
```

본문:

- RAG는 `LIKE 검색`의 의미 기반 확장
- MCP는 backend API wrapper의 AI-friendly 버전
- Agent는 service orchestration의 AI 버전
- Frontend polling은 오래 걸리는 API 응답 렌더링의 확장

시각자료 지시:

- 4칸 비교표
- 왼쪽: 익숙한 웹 개발 개념
- 오른쪽: AI 구현 개념
- 각 행에 짧은 코드 snippet 모양 카드

발표자 메모:

```text
AI 파트가 낯설어 보이지만, 완전히 다른 세계는 아닙니다. DB 검색, API wrapper, service orchestration, polling 같은 기존 개념이 AI 기능 안에서 확장된다고 보면 훨씬 익숙하게 읽힙니다.
```

---

### 18. 외울 문장과 Q&A

핵심 메시지:

```text
마지막에는 구현 세부보다 세 개의 핵심 문장을 남긴다.
```

본문:

- RAG는 학습이 아니라 검색이다.
- MCP는 API를 AI가 쓰기 쉽게 감싸는 표준 연결 방식이다.
- Agent는 단일 호출이 아니라 Think -> Act -> Observe 루프다.
- 모델은 판단하고, backend는 실행과 권한을 통제한다.
- 외부 사이트/README/MCP 결과는 지시문이 아니라 근거 데이터다.

시각자료 지시:

- 다섯 문장을 큰 quote card로 배치
- 마지막 줄 `RAG는 검색, MCP는 연결, Agent는 루프`를 가장 크게 표시

발표자 메모:

```text
오늘 내용을 한 줄로 줄이면 RAG는 검색, MCP는 연결, Agent는 루프입니다. 이 세 문장을 잡고 구현을 보면 어떤 코드를 왜 짜야 하는지 훨씬 선명해집니다.
```

---

## 3. Canva 생성용 상세 프롬프트

```text
Create an 18-slide Korean educational presentation titled "AI 활용 필수 요구 이해하기: RAG, MCP, Agent를 과제 구현 관점으로 연결하기".

Audience:
- Korean bootcamp teammates who understand React/FastAPI board apps but are new to applied AI implementation.
- They need to understand assignment requirements and implementation decisions, not a product pitch.

Core message:
- RAG = internal data retrieval.
- MCP = external tool connection protocol.
- Agent = stateful Think -> Act -> Observe loop.
- ProjectLens should appear only as a compact example, under 20% of the deck.

Narrative arc:
1. Explain the assignment requirement first.
2. Show how RAG, MCP, and Agent relate.
3. Explain each concept simply.
4. Make the Agent loop the main visual climax.
5. Put detailed implementation decision tables later as reference slides.
6. End with cost caution and memorable Q&A.

Visual style:
- Clean, digital, educational technical deck.
- Use diagrams heavily, not text-heavy slides.
- Use green/teal for RAG, blue for MCP, orange for Agent, red accent for cost/security warnings.
- Prefer flow diagrams, pipeline diagrams, loop diagrams, comparison tables, decision cards, and checklist visuals.

Important visuals:
- RAG pipeline: indexing -> retrieval -> generation.
- MCP USB-C analogy placeholder and Host / Client / Server structure.
- Agent loop: State -> Think -> Act -> Observe -> Think again.
- Integrated flow: user request -> backend job/state -> RAG -> Agent -> MCP tool -> observation -> structured output -> DB/UI.
- Cost slide: one request can become multiple model/tool calls and token usage grows through the loop.

Security/correctness reminders:
- External site text, README, and MCP results are evidence data, not instructions.
- Do not imply RAG means retraining the model.
- Do not imply MCP is just any API call.
- Do not imply Agent is just one LLM prompt.
- Do not insert expiring Notion signed image URLs. Use image placeholders with captions.

Slides:
1. AI 활용 필수 요구 이해하기
2. 오늘의 목표
3. 과제 요구 한 장 정리
4. 세 기술의 관계
5. RAG: 학습이 아니라 검색
6. MCP: API가 아니라 AI용 연결 규격
7. Agent: 단일 호출이 아니라 루프
8. 핵심 시각화: Agent 루프
9. 통합 흐름 예시
10. 구현 순서 한 장
11. RAG 구현 참고표
12. MCP 구현 참고표
13. Agent 구현 참고표
14. RAG 개선 포인트
15. Agent 루프 개선 포인트
16. OpenAI API 비용 주의
17. 기존 백엔드/프론트와 연결
18. 외울 문장과 Q&A
```

---

## 4. 이미지/시각자료 캡션 목록

| 사용할 위치 | 이미지/도형 | 출처/비고 |
| --- | --- | --- |
| 5장 | RAG indexing -> retrieval -> generation | Notion RAG 페이지, PPT 제작 시점에 이미지 재수집 |
| 6장 | MCP USB-C 비유 | Notion MCP 페이지, signed URL 직접 삽입 금지 |
| 6장 | MCP Host / Client / Server 구조 | Notion MCP 페이지 또는 Canva 도형으로 재작성 |
| 7장 | Agent = Model + Tools + Orchestration Layer | Notion AI agents 페이지 |
| 8장 | ReAct Think -> Act -> Observe loop | Notion AI agents 페이지 또는 Canva 도형으로 재작성 |
| 9장 | ProjectLens 통합 흐름 | 기준 문서의 Mermaid 다이어그램을 Canva 도형으로 재작성 |
| 16장 | 비용 meter/stack | Canva 아이콘/도형으로 제작 |

---

## 5. 제작 전 최종 확인

- [ ] ProjectLens 설명이 전체의 20%를 넘지 않는가?
- [ ] 과제 요구가 개념보다 먼저 배치되었는가?
- [ ] Agent 루프가 한 장의 큰 시각자료로 보이는가?
- [ ] RAG/MCP/Agent 구현 참고표가 발표 본문이 아니라 뒤쪽 참고 슬라이드로 분리되었는가?
- [ ] Notion signed URL이 직접 들어가지 않았는가?
- [ ] OpenAI 비용/크레딧 내용은 공식 문서 링크를 기준으로 되어 있는가?
- [ ] 외부 사이트/README/MCP 결과는 지시문이 아니라 evidence라는 문장이 들어갔는가?

