# ProjectLens Q1/Q5 검증 노트

작성일: 2026-06-15
후속 상태: Q5 보류 결정은 Q6~Q11 MCP 확장으로 대체됨.

## 결론

- Q1 실패 모드 5종은 전용 smoke로 통과했다.
- Q5 시점에는 추가 MCP 확장을 보류했다. 이후 Q6~Q11에서 `fetch_site_context`, `capture_screenshot`, `run_lighthouse_summary`, async polling이 구현됐다.
- Q1 보강 뒤에도 Q2~Q4 실 OpenAI 품질 루프는 깨지지 않았다.

## Q1 실패 모드 판정

| 실패 모드 | 판정 | 확인 방식 |
|---|---|---|
| URL 실패 graceful 안내 | 통과 | 접속 불가 URL과 SSRF URL이 `failed` 리포트로 저장되고 사용자 안내 문구를 노출 |
| 사이트 텍스트 빈약 | 통과 | 얇은 `example.com` 본문에 게시글 설명 + GitHub README 근거를 폴백으로 사용해 `completed` |
| RAG 빈 결과 | 통과 | 유사글 없음 상태에서 `비슷한 게시물이 아직 충분하지 않습니다.` 표시 |
| Structured Output/refusal/failure | 통과 | mock refusal은 `ai_reports.status=refused`, post 상태는 CHECK 제약에 맞춰 `failed`; mock failure는 `failed`; 짧은 입력은 `need_more_info` |
| 느린 분석/loading | 통과 | 분석 중 별도 세션에서 `posts.analysis_status=running` 관측 후 최종 `completed` |

## Q5 결정

검토 후보는 screenshot, Lighthouse, robots, broken links다.

- screenshot/Lighthouse: Playwright 또는 브라우저 런타임 비용이 커지고 컷 리스트와 충돌한다.
- robots: 단일 URL bounded fetch 중심인 현재 분석에는 제품 가치가 낮다.
- broken links: 크롤링 범위가 커져 데모 지연과 실패면이 늘어난다.

따라서 Q5 시점에는 새 MCP 도구를 추가하지 않고 보류했다. 이후 실 URL 품질 eval과 Q6~Q11 계획에 따라 bounded context, screenshot metadata, Lighthouse summary로 승격했다.

## 검증 명령

```bash
cd backend
.venv/bin/python scripts/run_projectlens_q1_q5_smoke.py --fail-under-threshold
.venv/bin/python scripts/run_projectlens_quality_eval.py --fail-under-threshold
```

```bash
backend/.venv/bin/python -m compileall backend/app backend/scripts mcp-server
cd frontend && npm run build
```

브라우저 확인:

- `/posts/99`: completed 리포트, MCP/RAG 근거, 포트폴리오/발표 카드, 복사 버튼 `복사됨`.
- `/posts/97`: failed 리포트, URL 접속 실패 안내, MCP 실패 근거.
- `/posts/103`: `정보가 더 필요합니다`, 보강 질문, 빈 유사 프로젝트/근거 상태.
