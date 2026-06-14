# ProjectLens M5 운영 노트

M5 목적은 "개방 전 작동 증명"이다. 먼저 본인 프로젝트 시드 5개를 넣고, 분석·근거 저장·RAG 추천·외부 사용자 업로드 smoke가 통과하는지 확인한 뒤에만 데이터 수집을 연다.

## 로컬 실행

```bash
cd /Users/wiseungcheol/Desktop/AI로\ 진화하기
docker compose up -d db
cd backend
source .venv/bin/activate
python -m app.db
```

DB가 비어 있거나 스키마가 오래됐으면 루트에서 `backend/db/schema.sql`을 한 번 적용한다.

## M5 시드와 검증

```bash
cd /Users/wiseungcheol/Desktop/AI로\ 진화하기/backend
source .venv/bin/activate
python scripts/seed_projectlens_m5.py
```

스크립트가 하는 일:

- `projectlens_seed_owner` 사용자로 본인 프로젝트 시드 5개를 삽입한다.
- `projectlens_external_smoke` 사용자로 외부 사용자 업로드 smoke 1개를 삽입한다.
- 접속 불가 URL smoke 1개를 삽입해 `failed` 또는 `need_more_info` 처리를 확인한다.
- 각 게시글에 실제 `run_analysis_for_post()` 흐름을 실행한다.
- `ai_reports`, `mcp_evidences`, `embeddings`, RAG source 수를 JSON으로 출력한다.

`OPENAI_API_KEY`가 없으면 OpenAI 호출과 embedding은 fake/mock 경로로 검증된다. 이 경우 DB/RAG/evidence 저장 계약은 확인할 수 있지만, 실제 `gpt-5.5` Agent Function Calling 경로는 아직 미검증으로 남긴다.
