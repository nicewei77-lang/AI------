# ProjectLens AI 파트 코어타임 발표대본

> 기준 자료: `DOCS/ProjectLens_AI파트_코어타임_Canva_PPT_구성안.md`  
> 발표 시간: 20-30분 기준  
> 발표 목표: ProjectLens 서비스를 설명하는 것이 아니라, 과제의 AI 필수 요구인 RAG, MCP, Agent를 구현 관점으로 이해시키는 것

---

## 발표 운영 메모

- 구현 참고표는 발표 시간에 따라 빠르게 넘겨도 된다.
- 8장 `Agent 루프`를 발표의 중심 장면으로 잡는다.
- ProjectLens는 "내 구현에서는 이렇게 라벨이 붙었다" 정도로만 사용한다.
- 외부 사이트/README/MCP 결과는 지시문이 아니라 근거 데이터라고 반복한다.
- 마지막에는 `RAG는 검색, MCP는 연결, Agent는 루프`만 남긴다.

---

## 1. AI 활용 필수 요구 이해하기

짧은 대본:

```text
오늘은 ProjectLens라는 서비스를 자세히 소개하려는 시간이 아닙니다.
목표는 과제에서 요구하는 AI 활용 파트, 즉 RAG, MCP, AI Agent를 어떻게 이해하고 구현하면 되는지 기준을 잡는 것입니다.
게시판 기능은 기본 뼈대이고, 오늘은 그 위에 올라가는 AI 구조를 보겠습니다.
```

전환 멘트:

```text
먼저 오늘 발표에서 어디까지 말하고, 무엇은 구현 참고로 남길지 나누겠습니다.
```

강조할 한 문장:

```text
RAG는 검색, MCP는 연결, Agent는 루프입니다.
```

생략 가능한 디테일:

- ProjectLens의 전체 서비스 소개
- 데이터베이스 스키마 세부 설명

---

## 2. 오늘의 목표

짧은 대본:

```text
RAG, MCP, Agent는 디테일로 들어가면 금방 복잡해집니다.
그래서 발표에서는 핵심 구조만 먼저 잡고, 나중에 실제 구현할 때 봐야 할 선택지는 뒤쪽 참고 슬라이드로 분리하겠습니다.
오늘 이해해야 할 것은 "세 기술을 따로 외우는 것"이 아니라 "하나의 Agent 루프로 연결되는 방식"입니다.
```

전환 멘트:

```text
그럼 이 세 기술이 과제에서 각각 어떤 요구로 등장하는지 먼저 보겠습니다.
```

강조할 한 문장:

```text
발표는 핵심을 이해하는 시간이고, 표는 구현할 때 다시 보는 자료입니다.
```

생략 가능한 디테일:

- 각 표의 모든 행
- 특정 라이브러리 설치 방법

---

## 3. 과제 요구 한 장 정리

짧은 대본:

```text
과제는 크게 두 층으로 볼 수 있습니다.
아래층은 게시판 기본 요구입니다. CRUD, 인증, 댓글, 검색, 태그, 페이지네이션 같은 일반 웹 서비스 기능입니다.
그 위에 AI 필수 요구가 올라갑니다. RAG는 내 데이터와 LLM을 연결하는 검색 구조, MCP는 외부 시스템을 호출할 수 있게 하는 연결 규격, Agent는 이 도구들을 선택하고 실행 결과를 관찰하는 추론 루프입니다.
```

전환 멘트:

```text
이제 세 개를 따로 보지 말고, 서로 어떤 관계인지 한 장으로 묶어보겠습니다.
```

강조할 한 문장:

```text
게시판은 제품의 뼈대이고, RAG/MCP/Agent는 그 위에 붙는 AI 실행 구조입니다.
```

생략 가능한 디테일:

- 게시판 기본 요구의 세부 API 목록

---

## 4. 세 기술의 관계

짧은 대본:

```text
세 기술을 병렬로 보면 헷갈립니다.
실제로는 Agent가 중심에 있고, RAG는 내부 데이터를 찾는 경로, MCP는 외부 시스템을 호출하는 경로라고 보면 됩니다.
Agent는 이 둘을 필요할 때 사용하고, 결과를 보고 다시 판단한 뒤 최종 결과를 만듭니다.
```

전환 멘트:

```text
그럼 먼저 RAG부터 보겠습니다. RAG는 가장 많이 오해되는 지점이 하나 있습니다.
```

강조할 한 문장:

```text
RAG와 MCP는 Agent가 사용할 수 있는 근거와 도구입니다.
```

생략 가능한 디테일:

- ProjectLens의 tool 이름 목록

---

## 5. RAG: 학습이 아니라 검색

짧은 대본:

```text
RAG는 Retrieval-Augmented Generation, 즉 검색으로 보강된 생성입니다.
중요한 점은 모델을 새로 학습시키는 것이 아니라는 겁니다.
문서나 DB를 chunk로 나누고 embedding으로 저장해두었다가, 질문이 들어오면 의미적으로 가까운 조각을 찾아 LLM이 읽게 합니다.
그래서 RAG의 핵심은 생성보다 검색입니다.
```

전환 멘트:

```text
내부 데이터를 찾는 구조가 RAG라면, 외부 서비스를 연결하는 구조는 MCP입니다.
```

강조할 한 문장:

```text
RAG는 AI에게 데이터를 학습시키는 것이 아니라, 필요한 순간에 검색해서 읽게 하는 방식입니다.
```

생략 가능한 디테일:

- embedding 차원 수
- vector DB별 세부 성능 비교

---

## 6. MCP: API가 아니라 AI용 연결 규격

짧은 대본:

```text
MCP는 Model Context Protocol입니다.
외부 API를 없애는 기술이 아니라, 외부 API나 DB나 파일 시스템을 AI Agent가 쓰기 좋은 tool 형태로 감싸는 표준 연결 방식입니다.
Notion에서는 USB-C 비유가 좋습니다. USB-C가 여러 주변기기를 공통 포트로 연결하듯, MCP는 AI 앱과 외부 도구를 공통 규격으로 연결합니다.
다만 LLM이 직접 API key를 들고 호출하는 것이 아니라, Host와 Client가 통제하고 MCP Server가 실제 실행을 담당합니다.
```

전환 멘트:

```text
이제 이 RAG와 MCP를 언제 쓸지 판단하는 Agent를 보겠습니다.
```

강조할 한 문장:

```text
MCP는 API의 경쟁자가 아니라, AI가 API를 쓰기 쉽게 감싸는 계층입니다.
```

생략 가능한 디테일:

- JSON-RPC payload 전문
- MCP Server 구현 코드 전체

---

## 7. Agent: 단일 호출이 아니라 루프

짧은 대본:

```text
Agent는 단일 LLM 호출이 아닙니다.
프롬프트를 길게 넣고 답변 한 번 받는 것은 Agent라고 말하기 약합니다.
Agent는 목표, 모델, 도구, 상태, 실행 구조를 가지고 여러 단계를 수행합니다.
가장 중요한 작동 방식은 Think, Act, Observe입니다. 생각하고, 도구를 쓰고, 결과를 관찰하고, 다시 생각합니다.
```

전환 멘트:

```text
이제 오늘 발표에서 가장 중요한 그림을 보겠습니다. Agent 루프입니다.
```

강조할 한 문장:

```text
Agent의 핵심은 결과를 관찰하고 다시 판단하는 루프입니다.
```

생략 가능한 디테일:

- ReAct 논문 배경
- LangGraph와 Agents SDK 비교

---

## 8. 핵심 시각화: Agent 루프

짧은 대본:

```text
이 슬라이드에서 제일 중요한 것은 Observation에서 Agent Think Again으로 돌아가는 화살표입니다.
사용자 요청이 들어오면 backend가 상태를 만들고, Agent는 현재 목표와 context를 봅니다.
근거가 부족하면 tool call을 만들고, backend는 권한과 입력을 검증한 뒤 실제 도구를 실행합니다.
그 결과가 observation으로 돌아오고, Agent는 그 결과를 보고 다시 판단합니다.
충분하다고 판단하면 structured output을 만들고 DB와 UI로 넘어갑니다.
```

전환 멘트:

```text
이제 이 루프가 실제 서비스 예시에서는 어떻게 보이는지 아주 짧게 보겠습니다.
```

강조할 한 문장:

```text
Observation을 보고 다시 판단하는 되돌아감이 Agent를 단일 호출과 구분합니다.
```

생략 가능한 디테일:

- 모든 내부 함수명
- 모든 DB 컬럼명

---

## 9. 통합 흐름 예시

짧은 대본:

```text
ProjectLens에서는 이 루프를 게시글 분석 기능에 붙였습니다.
사용자가 분석 버튼을 누르면 backend analysis job이 시작되고, RAG는 기존 게시글과 리포트에서 유사한 근거를 찾습니다.
Agent는 외부 근거가 더 필요하다고 판단하면 MCP tool을 호출합니다.
그 결과를 보고 최종적으로 구조화된 리포트를 만들고, DB에 저장한 뒤 프론트에서는 카드 UI로 보여줍니다.
```

전환 멘트:

```text
그럼 실제로 구현할 때는 어떤 순서로 만드는 게 좋을까요?
```

강조할 한 문장:

```text
ProjectLens는 주제가 아니라, Agent 루프가 서비스 기능에 붙은 예시입니다.
```

생략 가능한 디테일:

- 서비스 상세 기능
- 포트폴리오 카드 등 부가 기능

---

## 10. 구현 순서 한 장

짧은 대본:

```text
처음부터 완벽한 Agent를 만들려고 하면 디버깅이 어려워집니다.
먼저 게시판 기본 기능을 안정화하고, 그다음 RAG 검색 경로를 만듭니다.
그 후 MCP Server로 실제 외부 서비스 하나를 연결하고, 마지막에 Agent가 RAG와 MCP를 tool처럼 쓰는 루프를 붙입니다.
그리고 서비스로 만들려면 상태, 실패 처리, 비용 제한이 꼭 필요합니다.
```

전환 멘트:

```text
이제부터 세 장은 발표용이라기보다 구현할 때 다시 보는 참고표입니다.
```

강조할 한 문장:

```text
기본 웹 기능, RAG, MCP, Agent 루프, 운영 안정화 순서로 붙이면 됩니다.
```

생략 가능한 디테일:

- 마일스톤 M0-M5 전체 설명

---

## 11. RAG 구현 참고표

짧은 대본:

```text
RAG를 구현할 때는 데이터 소스, 저장 단위, embedding 모델, vector DB, 검색 기준, fallback을 결정해야 합니다.
예를 들어 기존 PostgreSQL을 쓴다면 pgvector가 자연스러운 선택일 수 있고, 운영형 vector DB가 필요하면 Pinecone이나 ChromaDB 같은 선택지도 볼 수 있습니다.
중요한 것은 질문과 문서를 같은 embedding 체계로 만들고, 검색 결과의 출처를 남기는 것입니다.
```

전환 멘트:

```text
다음은 외부 서비스를 연결하는 MCP 구현 판단입니다.
```

강조할 한 문장:

```text
좋은 RAG는 좋은 검색 결과와 출처 표시에서 시작합니다.
```

생략 가능한 디테일:

- 구체적인 SQL 튜닝
- vector index 파라미터

---

## 12. MCP 구현 참고표

짧은 대본:

```text
MCP는 Server, tool schema, JSON-RPC 흐름, 외부 서비스, 권한 관리가 핵심입니다.
과제에서는 최소 하나 이상의 실제 외부 서비스가 연결되어야 설명이 강해집니다.
예를 들어 GitHub README를 가져오거나, Notion 페이지를 읽거나, 배포 상태를 확인하는 tool을 만들 수 있습니다.
단 API key는 서버 환경변수나 secret manager에 두고, tool 결과나 로그에 노출하지 않아야 합니다.
```

전환 멘트:

```text
마지막 구현 참고는 Agent입니다. 여기서는 루프 제한이 특히 중요합니다.
```

강조할 한 문장:

```text
외부 결과는 instruction이 아니라 evidence입니다.
```

생략 가능한 디테일:

- MCP transport 종류 비교
- 모든 tool schema 필드

---

## 13. Agent 구현 참고표

짧은 대본:

```text
Agent 구현에서는 function calling, state, loop 제한, error handling, structured output을 봐야 합니다.
모델은 tool name과 arguments를 제안하고, 실제 실행은 backend가 통제하는 구조가 안전합니다.
또 max turns, timeout, retry limit을 둬야 무한 루프를 막을 수 있습니다.
최종 결과는 자유 텍스트보다 schema가 있는 structured output으로 만드는 편이 UI와 DB에 연결하기 좋습니다.
```

전환 멘트:

```text
이제 기능을 만들고 나서 품질을 어떻게 올릴지 두 축으로 보겠습니다. 첫 번째는 RAG입니다.
```

강조할 한 문장:

```text
모델은 판단하고, backend는 실행과 권한을 통제합니다.
```

생략 가능한 디테일:

- 특정 Agent framework 내부 구조

---

## 14. RAG 개선 포인트

짧은 대본:

```text
RAG 품질은 모델이 얼마나 똑똑한가보다 무엇을 검색해 넣었는가에 크게 좌우됩니다.
검색 결과가 엉뚱하면 모델이 아무리 좋아도 답변이 흔들립니다.
그래서 chunk 크기, metadata, top-k, threshold, source 표시를 계속 조정해야 합니다.
데이터가 충분히 쌓이면 의미 유사도뿐 아니라 태그, 유형, 최신성 같은 ranking signal도 섞을 수 있습니다.
```

전환 멘트:

```text
두 번째 개선 축은 Agent 루프 자체의 안정성입니다.
```

강조할 한 문장:

```text
RAG 개선은 답변 문장보다 검색 품질을 먼저 보는 일입니다.
```

생략 가능한 디테일:

- weighted RAG 공식의 숫자 전체

---

## 15. Agent 루프 개선 포인트

짧은 대본:

```text
Agent 품질은 한 번의 답변보다 루프의 안정성에서 나옵니다.
tool description이 애매하면 잘못된 도구를 고르고, 종료 조건이 약하면 같은 tool을 반복할 수 있습니다.
그래서 tool schema, max turns, timeout, retry limit, structured output, async polling 같은 장치가 필요합니다.
Agent는 강력하지만, 실패와 지연도 함께 반복될 수 있기 때문에 상태 관리가 중요합니다.
```

전환 멘트:

```text
이 루프는 기능 루프이면서 비용 루프이기도 합니다. 그래서 API 비용 주의가 필요합니다.
```

강조할 한 문장:

```text
Agent는 실패와 지연까지 상태로 다뤄야 서비스가 됩니다.
```

생략 가능한 디테일:

- 특정 에러 코드 전체

---

## 16. OpenAI API 비용 주의

짧은 대본:

```text
OpenAI API에는 요청 수와 token 수 기준의 rate limits가 있습니다.
또 API 가격은 token 사용량에 영향을 받습니다.
Agent는 한 번의 사용자 요청 안에서 여러 번 모델을 부르고 tool 결과를 다시 읽을 수 있기 때문에 비용이 예상보다 빨리 늘 수 있습니다.
실습 전에는 usage dashboard, monthly budget, prepaid credit, auto recharge 상태를 꼭 확인해야 합니다.
특히 자동 충전을 원하지 않으면 auto recharge를 끄거나 monthly recharge limit을 작게 잡아야 합니다.
```

전환 멘트:

```text
마지막으로 이 AI 코드를 기존 웹 개발 개념과 연결해서 읽어보겠습니다.
```

강조할 한 문장:

```text
Agent 루프는 비용 루프이기도 합니다.
```

생략 가능한 디테일:

- 최신 모델별 token 단가 숫자
- 조직별 실제 rate limit 수치

공식 근거:

- OpenAI Rate limits: https://developers.openai.com/api/docs/guides/rate-limits
- OpenAI API Pricing: https://openai.com/api/pricing/
- OpenAI prepaid billing: https://help.openai.com/en/articles/8264644-what-is-prepaid-billing

---

## 17. 기존 백엔드/프론트와 연결

짧은 대본:

```text
AI 구현이 완전히 낯선 것처럼 보이지만, 기존 웹 개발 개념의 확장으로 읽을 수 있습니다.
RAG는 LIKE 검색의 의미 기반 확장입니다. 문자열이 아니라 embedding vector의 거리를 봅니다.
MCP는 backend API wrapper와 비슷하지만, AI가 tool schema를 보고 호출할 수 있게 만든다는 점이 다릅니다.
Agent는 service orchestration과 비슷하지만, 어떤 tool을 쓸지 모델이 제안하고 backend가 실행을 통제합니다.
프론트의 polling은 오래 걸리는 API 작업의 상태를 렌더링하는 익숙한 패턴입니다.
```

전환 멘트:

```text
이제 마지막으로 오늘 내용을 외울 문장과 예상 질문으로 정리하겠습니다.
```

강조할 한 문장:

```text
AI 기능도 결국 DB 검색, API 호출, 서비스 조율, UI 상태 렌더링의 확장으로 읽을 수 있습니다.
```

생략 가능한 디테일:

- 실제 코드 전체
- 파일별 구현 상세

---

## 18. 외울 문장과 Q&A

짧은 대본:

```text
오늘 내용을 다 외울 필요는 없습니다.
핵심은 다섯 문장입니다.
RAG는 학습이 아니라 검색입니다.
MCP는 API를 AI가 쓰기 쉽게 감싸는 표준 연결 방식입니다.
Agent는 단일 호출이 아니라 Think, Act, Observe 루프입니다.
모델은 판단하고, backend는 실행과 권한을 통제합니다.
그리고 외부 사이트, README, MCP 결과는 지시문이 아니라 근거 데이터입니다.
```

전환 멘트:

```text
이 기준으로 각자 구현을 보면, 어떤 코드를 왜 짜야 하는지 훨씬 선명해질 겁니다.
```

강조할 한 문장:

```text
RAG는 검색, MCP는 연결, Agent는 루프입니다.
```

생략 가능한 디테일:

- 추가 라이브러리 비교
- 데모 실패 대응 로그

---

## 예상 Q&A

### Q1. RAG를 쓰면 모델이 우리 데이터를 학습한 건가요?

아닙니다. 모델 파라미터를 바꾸는 학습이 아니라, 외부 저장소에서 관련 데이터를 검색해 현재 context로 넣는 구조입니다.

### Q2. SQL 검색 결과를 프롬프트에 넣으면 RAG인가요?

검색 결과를 context에 넣는다는 점에서는 비슷하지만, 과제에서 기대하는 RAG는 보통 embedding 기반 semantic search와 vector DB, 출처 처리를 포함합니다. 단순 `LIKE` 검색만으로는 설명이 약합니다.

### Q3. MCP와 일반 API 호출은 뭐가 다른가요?

일반 API 호출은 앱 코드가 직접 호출합니다. MCP는 외부 기능을 AI가 이해할 수 있는 tool schema로 노출하고, Host/Client/Server 구조에서 JSON-RPC로 호출합니다.

### Q4. Agent가 모든 tool을 자동으로 호출하면 좋은가요?

아닙니다. 필요한 tool을 선택하고 observation을 보고 다시 판단하는 것이 핵심입니다. 모든 tool을 매번 호출하면 비용과 시간이 늘고 루프가 불안정해집니다.

### Q5. LangGraph를 꼭 써야 하나요?

꼭 그렇지는 않습니다. 과제의 핵심은 특정 라이브러리가 아니라 state와 loop가 보이는 agentic 구조입니다. LangGraph, OpenAI Agents SDK, 직접 function calling loop 모두 가능하지만 상태와 종료 조건을 설명할 수 있어야 합니다.

### Q6. 왜 Structured Outputs가 필요한가요?

AI 결과를 카드 UI와 DB에 안정적으로 연결하려면 필드가 일정해야 합니다. 자유 텍스트는 매번 형식이 흔들릴 수 있으므로, schema 기반 output이 더 안전합니다.

### Q7. API 비용은 어디서 많이 늘어나나요?

Agent가 tool을 여러 번 호출하고 긴 evidence를 다시 읽을 때 입력 token과 출력 token이 늘어납니다. retry와 실패 요청도 rate limit에 영향을 줄 수 있으므로 budget, usage dashboard, auto recharge를 확인해야 합니다.

---

## 10분 압축 버전

시간이 부족하면 아래 순서로만 말한다.

1. 과제 요구 한 장 정리
2. 세 기술의 관계
3. RAG 한 장
4. MCP 한 장
5. Agent 한 장
6. Agent 루프
7. 통합 흐름 예시
8. 비용 주의
9. 외울 문장

생략:

- 구현 참고표 3장
- RAG/Agent 개선 포인트 상세
- 코드 비교 상세

---

## 마지막 클로징

```text
이번 과제에서 AI 파트는 "모델을 한 번 호출한다"가 아니라,
내 데이터를 찾고, 외부 시스템을 연결하고, 그 결과를 보고 다시 판단하는 구조를 만드는 일입니다.
그래서 오늘의 마지막 문장은 이것입니다.
RAG는 검색, MCP는 연결, Agent는 루프입니다.
```

