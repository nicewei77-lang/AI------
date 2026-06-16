# ProjectLens 리포트 V2 피봇 구현 계획

> 작업 중 계속 참고하는 실행 문서. 기존 `ProjectLens_개발_계획.md`의 M0~Q12를 갈아엎지 않고, 이미 동작하는 Agent/RAG/MCP/Lighthouse/README 흐름을 **근거 기반 AI 프로젝트 리뷰 리포트**로 재정렬한다.

---

## 0. 최종 방향

ProjectLens는 공개된 프로젝트 표면을 AI가 근거 기반으로 진단하고, 그 결과를 발표/포트폴리오에서 쓸 수 있는 언어로 번역해주는 프로젝트 리뷰 게시판이다.

이번 피봇의 핵심은 기능 확장이 아니라 **리포트의 의미 재배치**다.

- 게시판은 중심 상품이 아니라 리뷰 리포트가 공유/비교/개선되는 공간이다.
- Lighthouse는 점수판이 아니라 공개 데모의 첫인상/기술 표면을 해석하기 위한 근거다.
- GitHub는 이번 범위에서 README와 기본 repo metadata 근거로만 쓴다.
- AI 문장은 항상 `확인된 근거 -> AI 해석 -> 개선 액션 -> 분석 한계` 흐름을 따라야 한다.
- 실 OpenAI 경로에서는 Agent가 등록된 function tool 중 필요한 도구를 선택한다. mock/smoke 경로의 일괄 도구 호출은 검증용이다.

---

## 1. 범위 결정

### 이번에 한다

- 리포트 JSON 스키마를 V2 방향으로 확장하되 기존 저장 JSON과 호환되게 default를 둔다.
- 프롬프트를 근거 기반 포트폴리오/발표 리뷰어 톤으로 조정한다.
- UI를 `요약 -> 확인된 근거 -> AI 해석/리스크 -> 포트폴리오 번역 -> 유사 프로젝트 -> 분석 범위와 한계` 순서로 재배치한다.
- 실패/측정 불가/근거 부족을 오류가 아니라 리포트의 1급 UX로 보여준다.
- 기존 Q1~Q12 검증 스크립트와 품질 eval을 통과시키는 것을 완료 기준으로 삼는다.

### 이번에 하지 않는다

- PageSpeed API 신규 연동.
- GitHub 최근 커밋/PR/Issue/브랜치 상세 분석.
- 코드 내부 품질/보안 취약점 전체 판단.
- 단일 총점/합격 가능성/채용 결과 예측.
- 새 DB 테이블 또는 migration. `ai_reports.report` JSON 확장만 사용한다.
- MCP 도구 추가. 현재 allowlist를 유지한다.

---

## 2. 구현 마일스톤

### PV2-0. 구현 기준 고정 [P0]

**목표:** 작업자가 피봇 범위를 혼동하지 않게 계약을 고정한다.

**작업**

- 이 문서를 기준 문서로 삼고, 구현 중 새 기능 욕심이 생기면 먼저 여기의 범위 결정에 맞춘다.
- `ProjectLens_개발_계획.md`의 컷 리스트는 건드리지 않는다.
- PageSpeed/GitHub PR/Issue 같은 미구현 항목은 UI/프롬프트/문서에서 현재 기능처럼 말하지 않는다.

**완료 기준**

- 구현 PR/커밋 설명에서 이번 작업을 `리포트 V2 의미 재배치`로 설명할 수 있다.
- 새 외부 API나 DB migration 없이 진행된다.

---

### PV2-1. 리포트 스키마 V2 호환 확장 [P0]

**목표:** 확인된 근거, AI 해석, 액션, 한계를 구조적으로 분리할 수 있게 한다.

**주요 파일**

- `backend/app/ai/schemas.py`
- `frontend/src/types/analysis.ts`
- `backend/app/ai/runner.py`

**작업**

- `ProjectAnalysisReport`에 `report_version: str = "2.0"`을 추가한다.
- `summary` 블록을 추가한다.
  - `one_line_review: str = ""`
  - `strongest_signals: list[str] = []`
  - `main_risks: list[str] = []`
  - `priority_actions: list[str] = []`
- `AnalysisLimitations` 블록을 추가한다.
  - `seen: list[str] = []`
  - `not_seen: list[str] = []`
  - `disclaimers: list[str] = []`
- `ImprovementAction`에 아래 default 필드를 추가한다.
  - `impact: Literal["low", "medium", "high"] = "medium"`
  - `difficulty: Literal["low", "medium", "high"] = "medium"`
  - `evidence_refs: list[EvidenceKind] = []`
- 기존 저장 리포트가 신규 필드 없이도 로드되도록 모든 신규 필드는 default를 둔다.
- `build_need_more_info_report`, `build_failed_report`, `build_refused_report`, mock report에도 V2 필드를 채운다.

**완료 기준**

- 기존 `ai_reports.report` JSON을 `ProjectAnalysisReport.model_validate()`로 읽어도 깨지지 않는다.
- 신규 completed report에는 summary/limitations/action impact/difficulty가 비어 있더라도 필드가 존재한다.

---

### PV2-2. 프롬프트와 Agent 지시문 피봇 [P0]

**목표:** 모델 출력이 “AI 기능 많은 게시판”이 아니라 “근거 기반 프로젝트 리뷰”처럼 나오게 한다.

**주요 파일**

- `backend/app/ai/prompts.py`

**작업**

- 역할을 `evidence-based AI project reviewer`로 명확히 바꾼다.
- 출력 원칙을 다음 순서로 강제한다.
  1. observed evidence
  2. AI interpretation
  3. portfolio/presentation translation
  4. actionable recommendations
  5. analysis limitations
- 금지 표현을 명시한다.
  - 합격 가능성이 높다
  - 코드 품질이 좋다
  - 보안이 안전하다
  - 이 프로젝트는 평범하다
  - 반드시 고쳐야 한다
- PageSpeed 표현을 쓰지 않는다. 현재 근거는 `Lighthouse summary`라고 쓴다.
- GitHub 근거는 README/basic metadata 기준임을 명시한다.
- `summary`, `limitations`, `impact`, `difficulty`, `evidence_refs`를 채우도록 지시한다.
- 실 Agent 경로는 도구 선택형이며, mock/smoke는 검증용 일괄 호출임을 README/발표 문구에 쓸 수 있게 한 문장으로 정리한다.

**완료 기준**

- completed 리포트가 사실/해석을 섞어 단정하지 않는다.
- Lighthouse 점수가 낮아도 프로젝트 가치 자체를 낮게 단정하지 않는다.
- GitHub README가 없거나 약하면 `근거 부족`으로 다룬다.

---

### PV2-3. 리포트 UI 재구성 [P0]

**목표:** 사용자가 첫 화면에서 “근거를 바탕으로 해석한 리뷰”라고 느끼게 한다.

**주요 파일**

- `frontend/src/components/analysis/AnalysisReport.tsx`
- `frontend/src/components/analysis/DiagnosisCard.tsx`
- `frontend/src/components/analysis/ServiceUnderstandingCard.tsx`

**작업**

- 리포트 제목을 `AI 프로젝트 리뷰 리포트`로 바꾼다.
- 새 `ReviewSummaryCard`를 추가한다.
  - 한 줄 총평
  - 강한 신호 2~3개
  - 주요 리스크 2~3개
  - 우선 개선 액션 3개
- 카드 순서를 아래로 재배치한다.
  1. 상태/요약
  2. 확인된 근거
  3. 서비스 이해와 AI 해석
  4. 리스크와 우선 개선 액션
  5. 포트폴리오/발표 번역
  6. 유사 프로젝트
  7. 분석 범위와 한계
- `EvidenceCard` 제목을 `확인된 근거`로 바꾸고 성공/실패보다 `확인됨`, `측정 불가`, `근거 부족` 표현을 우선한다.
- `DiagnosisCard` 문구를 바꾼다.
  - `보완점` -> `리스크`
  - `개선 계획` -> `우선 개선 액션`
  - 액션별 영향도/난이도/근거 배지 표시
- 새 `LimitationsCard`를 추가한다.
  - `seen`, `not_seen`, `disclaimers`를 표시한다.
  - 값이 비어 있으면 기본 한계 문구를 fallback으로 보여준다.
- UI에 `PageSpeed`라는 단어를 쓰지 않는다.

**완료 기준**

- 리포트 상단만 봐도 프로젝트의 강점, 리스크, 먼저 고칠 것이 보인다.
- 근거 원문과 AI 해석이 시각적으로 구분된다.
- 실패/부분 성공 리포트도 빈 카드나 깨진 레이아웃 없이 표시된다.

---

### PV2-4. 실패/부분 성공 UX 정리 [P1]

**목표:** 분석 실패를 서비스 오류처럼 숨기지 않고 분석 범위 한계로 설명한다.

**주요 파일**

- `backend/app/services/analysis_service.py`
- `backend/app/ai/runner.py`
- `frontend/src/components/analysis/AnalysisReport.tsx`

**작업**

- URL 접근 실패: `배포 URL에 접근하지 못해 화면 분석을 수행하지 못했습니다.` 류의 문구로 표시한다.
- Lighthouse 실패: 성능 점수를 추측하지 않고 `측정 불가`로 표시한다.
- GitHub README 실패/비공개: README 기반 판단이 제한된다고 표시한다.
- 사이트 차단/anti-bot/403: 우회하지 않고 `자동 수집 차단, 추가 근거 필요`로 표시한다.
- RAG 빈 결과: `비슷한 게시물이 아직 충분하지 않습니다.` 유지.

**완료 기준**

- 실패 케이스에서도 completed/failed/need_more_info/refused 상태별 UI가 자연스럽다.
- 측정 실패 항목이 다른 점수나 판단에 섞여 과장되지 않는다.

---

### PV2-5. 검증 루프와 문서 갱신 [P1]

**목표:** 피봇이 실제 품질 개선으로 이어졌는지 기존 검증 루프로 확인한다.

**작업**

- 로컬 구조 검증을 먼저 돌린다.
- 실 OpenAI 키가 있으면 고정 3개 URL 품질 eval로 before/after를 비교한다.
- 완료 후 `진도_체크포인트.md`에는 파일명과 검증 결과만 짧게 남긴다.

**검증 명령**

```bash
cd backend && .venv/bin/python -m compileall app ../mcp-server
cd frontend && npm run build
cd backend && .venv/bin/python scripts/run_projectlens_q1_q5_smoke.py
cd backend && .venv/bin/python scripts/run_projectlens_mcp_expansion_smoke.py --fail-under-threshold
cd backend && .venv/bin/python scripts/run_projectlens_quality_eval.py --fail-under-threshold
```

**주의**

- 마지막 quality eval은 `OPENAI_API_KEY`가 있는 실 모델 경로에서만 최종 품질 근거로 인정한다.
- mock/fake 경로는 구조와 실패 처리 검증에는 유효하지만, 리포트 품질 완료 근거로 과장하지 않는다.

---

## 3. 구현 순서 체크리스트

```text
[ ] PV2-0 범위 고정
[ ] PV2-1 backend/frontend 타입 V2 호환 확장
[ ] PV2-1 runner의 failed/need_more_info/refused/mock report V2 필드 보강
[ ] PV2-2 prompts.py 피봇 반영
[ ] PV2-3 ReviewSummaryCard 추가
[ ] PV2-3 AnalysisReport 카드 순서 재배치
[ ] PV2-3 Diagnosis/Evidence/Limitations UI 문구 정리
[ ] PV2-4 실패/부분 성공 문구 확인
[ ] PV2-5 compileall 통과
[ ] PV2-5 frontend build 통과
[ ] PV2-5 Q1/Q5 smoke 통과
[ ] PV2-5 MCP expansion smoke 통과
[ ] PV2-5 real OpenAI quality eval 통과 또는 미실행 사유 기록
[ ] 진도_체크포인트.md에 다음 실행 기준 갱신
```

---

## 4. 수용 기준

피봇 구현은 아래를 만족해야 완료다.

- 사용자가 리포트를 봤을 때 `AI가 그냥 조언을 지어냈다`가 아니라 `공개 근거를 바탕으로 해석했다`고 느낀다.
- Lighthouse는 보이지만 서비스가 Lighthouse 복제품처럼 보이지 않는다.
- README/GitHub 정보는 코드 품질 보장이 아니라 포트폴리오 설득력의 근거로 쓰인다.
- 분석 실패가 발생해도 리포트가 무너지지 않고 무엇을 보지 못했는지 설명한다.
- AI 문장은 공격적이지 않지만, 차별화 부족/문제 정의 부족/데모 리스크는 충분히 직접적으로 말한다.
- mock/smoke 경로와 실 Agent Function Calling 경로를 혼동해서 설명하지 않는다.

---

## 5. 작업 중 판단 규칙

- 구현자가 새 필드를 추가할지 고민되면, 먼저 기존 `confirmed_facts`, `inferred_facts`, `evidence_kind`, `based_on`, `portfolio.limitations`로 해결 가능한지 본다.
- 새 필드가 필요하면 기존 저장 JSON 호환을 깨지 않게 default를 둔다.
- UI에서 한 문장이 너무 강하면 `보장합니다` 대신 `보일 수 있습니다`, `약하게 느껴질 수 있습니다`, `개선하면 좋습니다`를 쓴다.
- 수집하지 못한 항목은 추측하지 말고 `근거 부족`, `측정 불가`, `범위 밖`으로 표시한다.
- 기능을 더 붙이고 싶어질 때는 이 문서의 `이번에 하지 않는다`를 먼저 확인한다.
