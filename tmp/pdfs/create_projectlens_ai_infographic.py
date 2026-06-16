from __future__ import annotations

import math
import os
from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "output" / "pdf"
OUT_PATH = OUT_DIR / "ProjectLens_AI파트_코어타임_인포그래픽.pdf"

PAGE_W, PAGE_H = landscape(A4)
M = 34


PALETTE = {
    "ink": HexColor("#172033"),
    "muted": HexColor("#5D6678"),
    "line": HexColor("#D9DEE8"),
    "bg": HexColor("#F6F8FB"),
    "card": HexColor("#FFFFFF"),
    "rag": HexColor("#0F8B8D"),
    "mcp": HexColor("#2F6FEB"),
    "agent": HexColor("#D97706"),
    "good": HexColor("#15803D"),
    "warn": HexColor("#C2410C"),
    "danger": HexColor("#B91C1C"),
    "soft_rag": HexColor("#E6F5F5"),
    "soft_mcp": HexColor("#EAF1FF"),
    "soft_agent": HexColor("#FFF3E0"),
    "soft_warn": HexColor("#FFF1E8"),
    "soft_good": HexColor("#EAF7EF"),
    "code_bg": HexColor("#1E293B"),
}


def register_fonts() -> tuple[str, str, str]:
    candidates = [
        "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/Library/Fonts/Arial Unicode.ttf",
    ]
    font_name = "Helvetica"
    for path in candidates:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont("Korean", path))
                font_name = "Korean"
                break
            except Exception:
                continue

    code_font = "Courier"
    mono_candidates = [
        "/System/Library/Fonts/Menlo.ttc",
        "/System/Library/Fonts/Supplemental/Courier New.ttf",
    ]
    for path in mono_candidates:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont("CodeFont", path))
                code_font = "CodeFont"
                break
            except Exception:
                continue

    return font_name, font_name, code_font


FONT, FONT_BOLD, CODE_FONT = register_fonts()


def style(size: float, leading: float | None = None, color=PALETTE["ink"], align=TA_LEFT) -> ParagraphStyle:
    return ParagraphStyle(
        name=f"s{size}",
        fontName=FONT,
        fontSize=size,
        leading=leading or size * 1.35,
        textColor=color,
        alignment=align,
        wordWrap="CJK",
        spaceAfter=0,
        spaceBefore=0,
    )


def para(text: str, size=10.5, leading=None, color=PALETTE["ink"], align=TA_LEFT) -> Paragraph:
    html = escape(text).replace("\n", "<br/>")
    return Paragraph(html, style(size, leading, color, align))


def draw_para(c: canvas.Canvas, text: str, x: float, y_top: float, w: float, size=10.5, leading=None,
              color=PALETTE["ink"], align=TA_LEFT) -> float:
    p = para(text, size, leading, color, align)
    _, h = p.wrap(w, 1000)
    p.drawOn(c, x, y_top - h)
    return h


def para_height(text: str, w: float, size=10.5, leading=None) -> float:
    p = para(text, size, leading)
    _, h = p.wrap(w, 1000)
    return h


def round_rect(c: canvas.Canvas, x: float, y_top: float, w: float, h: float, fill, stroke=PALETTE["line"],
               radius=8, sw=0.8) -> None:
    c.saveState()
    c.setFillColor(fill)
    c.setStrokeColor(stroke)
    c.setLineWidth(sw)
    c.roundRect(x, y_top - h, w, h, radius, stroke=1, fill=1)
    c.restoreState()


def section_label(c: canvas.Canvas, text: str, x: float, y_top: float, color) -> None:
    h = 18
    w = max(58, len(text) * 7.2)
    c.saveState()
    c.setFillColor(color)
    c.roundRect(x, y_top - h, w, h, 7, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont(FONT, 8.5)
    c.drawCentredString(x + w / 2, y_top - 12.5, text)
    c.restoreState()


def header(c: canvas.Canvas, page_no: int, kicker: str, title: str, accent=PALETTE["ink"]) -> None:
    c.setFillColor(PALETTE["bg"])
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    section_label(c, kicker, M, PAGE_H - 24, accent)
    draw_para(c, title, M, PAGE_H - 50, PAGE_W - 2 * M - 60, size=19, leading=24, color=PALETTE["ink"])
    c.setStrokeColor(accent)
    c.setLineWidth(2)
    c.line(M, PAGE_H - 78, PAGE_W - M, PAGE_H - 78)
    c.setFont(FONT, 8.5)
    c.setFillColor(PALETTE["muted"])
    c.drawRightString(PAGE_W - M, PAGE_H - 33, f"{page_no:02d}")


def footer(c: canvas.Canvas, note: str = "ProjectLens AI core-time infographic - source: local draft, repo code, Notion concept notes, OpenAI official docs") -> None:
    c.setFont(FONT, 7.3)
    c.setFillColor(PALETTE["muted"])
    c.drawString(M, 18, note)


def bullet_list(c: canvas.Canvas, bullets: list[str], x: float, y_top: float, w: float, size=9.2,
                color=PALETTE["ink"], bullet_color=PALETTE["muted"], gap=4.5) -> float:
    y = y_top
    for item in bullets:
        h = para_height(item, w - 14, size=size, leading=size * 1.35)
        c.setFillColor(bullet_color)
        c.circle(x + 4, y - 7.2, 2.2, stroke=0, fill=1)
        draw_para(c, item, x + 13, y, w - 13, size=size, leading=size * 1.35, color=color)
        y -= h + gap
    return y_top - y


def card(c: canvas.Canvas, x: float, y_top: float, w: float, h: float, title: str, body: list[str] | str,
         accent=PALETTE["ink"], fill=PALETTE["card"], title_size=12, body_size=9.2) -> None:
    round_rect(c, x, y_top, w, h, fill)
    c.setFillColor(accent)
    c.rect(x, y_top - h, 5, h, stroke=0, fill=1)
    draw_para(c, title, x + 14, y_top - 13, w - 24, size=title_size, leading=title_size * 1.25, color=accent)
    if isinstance(body, str):
        draw_para(c, body, x + 14, y_top - 39, w - 24, size=body_size, leading=body_size * 1.35, color=PALETTE["ink"])
    else:
        bullet_list(c, body, x + 14, y_top - 39, w - 24, size=body_size, bullet_color=accent)


def arrow(c: canvas.Canvas, x1: float, y1: float, x2: float, y2: float, color=PALETTE["muted"], width=1.5) -> None:
    c.saveState()
    c.setStrokeColor(color)
    c.setFillColor(color)
    c.setLineWidth(width)
    c.line(x1, y1, x2, y2)
    ang = math.atan2(y2 - y1, x2 - x1)
    size = 6
    pts = [
        (x2, y2),
        (x2 - size * math.cos(ang - math.pi / 6), y2 - size * math.sin(ang - math.pi / 6)),
        (x2 - size * math.cos(ang + math.pi / 6), y2 - size * math.sin(ang + math.pi / 6)),
    ]
    c.line(pts[0][0], pts[0][1], pts[1][0], pts[1][1])
    c.line(pts[0][0], pts[0][1], pts[2][0], pts[2][1])
    c.restoreState()


def flow_box(c: canvas.Canvas, x: float, y_top: float, w: float, h: float, title: str, body: str,
             accent=PALETTE["ink"], fill=PALETTE["card"]) -> None:
    round_rect(c, x, y_top, w, h, fill, stroke=accent, sw=1)
    draw_para(c, title, x + 9, y_top - 9, w - 18, size=10.3, leading=12, color=accent, align=TA_CENTER)
    if body:
        draw_para(c, body, x + 9, y_top - 31, w - 18, size=8.2, leading=10.5, color=PALETTE["muted"], align=TA_CENTER)


def code_block(c: canvas.Canvas, x: float, y_top: float, w: float, title: str, lines: list[str], accent=PALETTE["ink"]) -> None:
    line_h = 12.5
    h = 27 + len(lines) * line_h + 9
    round_rect(c, x, y_top, w, h, PALETTE["code_bg"], stroke=PALETTE["code_bg"], radius=7)
    c.setFillColor(accent)
    c.roundRect(x + 8, y_top - 21, 6, 6, 3, stroke=0, fill=1)
    c.setFont(FONT, 8.5)
    c.setFillColor(colors.white)
    c.drawString(x + 20, y_top - 19, title)
    c.setFont(CODE_FONT, 7.6)
    c.setFillColor(HexColor("#E5E7EB"))
    y = y_top - 37
    for line in lines:
        c.drawString(x + 12, y, line)
        y -= line_h


def mini_table(c: canvas.Canvas, x: float, y_top: float, w: float, headers: list[str], rows: list[list[str]],
               col_fracs: list[float], accent=PALETTE["ink"], font_size=8.4) -> float:
    col_ws = [w * f for f in col_fracs]
    header_h = 24
    c.setFillColor(accent)
    c.roundRect(x, y_top - header_h, w, header_h, 6, stroke=0, fill=1)
    cx = x
    for i, head in enumerate(headers):
        draw_para(c, head, cx + 6, y_top - 7, col_ws[i] - 12, size=8.3, leading=10.5, color=colors.white, align=TA_CENTER)
        cx += col_ws[i]
    y = y_top - header_h
    for r, row in enumerate(rows):
        heights = [para_height(cell, col_ws[i] - 12, size=font_size, leading=font_size * 1.32) for i, cell in enumerate(row)]
        rh = max(27, max(heights) + 13)
        fill = colors.white if r % 2 == 0 else HexColor("#FAFBFD")
        c.setFillColor(fill)
        c.rect(x, y - rh, w, rh, stroke=0, fill=1)
        c.setStrokeColor(PALETTE["line"])
        c.setLineWidth(0.5)
        c.line(x, y - rh, x + w, y - rh)
        cx = x
        for i, cell in enumerate(row):
            if i > 0:
                c.line(cx, y, cx, y - rh)
            draw_para(c, cell, cx + 6, y - 7, col_ws[i] - 12, size=font_size, leading=font_size * 1.32,
                      color=PALETTE["ink"])
            cx += col_ws[i]
        y -= rh
    c.setStrokeColor(PALETTE["line"])
    c.roundRect(x, y, w, y_top - y, 6, stroke=1, fill=0)
    return y_top - y


def page_1(c: canvas.Canvas) -> None:
    header(c, 1, "문서 목적", "ProjectLens AI 코어타임 인포그래픽", PALETTE["ink"])
    draw_para(
        c,
        "목표는 ProjectLens 서비스 소개가 아니라, 과제의 AI 필수 요구인 RAG, MCP, Agent를 정확히 이해하고 구현 판단 기준을 잡는 것이다.",
        M,
        PAGE_H - 104,
        PAGE_W - 2 * M,
        size=12,
        leading=16,
        color=PALETTE["muted"],
    )

    y = PAGE_H - 155
    w = (PAGE_W - 2 * M - 28) / 3
    card(c, M, y, w, 132, "RAG", ["내 데이터 검색", "학습이 아니라 retrieval", "검색 결과를 context로 주입"], PALETTE["rag"], PALETTE["soft_rag"], 18, 10.5)
    card(c, M + w + 14, y, w, 132, "MCP", ["외부 시스템 연결", "Host/Client/Server 구조", "JSON-RPC 기반 tool 호출"], PALETTE["mcp"], PALETTE["soft_mcp"], 18, 10.5)
    card(c, M + (w + 14) * 2, y, w, 132, "Agent", ["상태와 루프 관리", "Think -> Act -> Observe", "도구 선택과 최종 output"], PALETTE["agent"], PALETTE["soft_agent"], 18, 10.5)
    arrow(c, M + w, y - 65, M + w + 14, y - 65, PALETTE["muted"], 1.8)
    arrow(c, M + 2 * w + 14, y - 65, M + 2 * w + 28, y - 65, PALETTE["muted"], 1.8)

    card(
        c,
        M,
        y - 162,
        (PAGE_W - 2 * M - 16) / 2,
        138,
        "발표에서 말할 것",
        [
            "세 기술의 본질: 검색, 연결, 루프",
            "과제가 왜 이 세 가지를 요구하는지",
            "Agent가 RAG와 MCP 결과를 보고 다시 판단하는 구조",
            "비용과 크레딧 폭주를 막는 운영 감각",
        ],
        PALETTE["good"],
        colors.white,
        13,
        9.8,
    )
    card(
        c,
        M + (PAGE_W - 2 * M - 16) / 2 + 16,
        y - 162,
        (PAGE_W - 2 * M - 16) / 2,
        138,
        "구현할 때 참고할 것",
        [
            "embedding, vector DB, threshold, source metadata",
            "MCP Server, tool schema, JSON-RPC, 권한 관리",
            "function calling, state, max turns, error handling",
            "기존 backend/frontend 코드와 무엇이 비슷하고 다른지",
        ],
        PALETTE["ink"],
        colors.white,
        13,
        9.8,
    )

    card(
        c,
        M,
        112,
        PAGE_W - 2 * M,
        56,
        "한 줄로 외우기",
        "RAG는 검색, MCP는 연결, Agent는 루프다. 모델은 판단하고, backend는 실행과 권한을 통제한다.",
        PALETTE["agent"],
        PALETTE["soft_agent"],
        12.5,
        11,
    )
    footer(c)


def page_2(c: canvas.Canvas) -> None:
    header(c, 2, "과제 요구", "게시판 기본 기능 위에 AI 필수 요구를 얹는다", PALETTE["ink"])
    x = M
    top = PAGE_H - 112
    base_w = PAGE_W - 2 * M
    round_rect(c, x, top, base_w, 72, colors.white)
    draw_para(c, "게시판 기본 요구", x + 18, top - 15, 130, size=13, color=PALETTE["ink"])
    labels = ["CRUD", "인증", "댓글", "검색/태그", "페이지네이션", "정렬/상태 UI"]
    chip_x = x + 155
    for label in labels:
        tw = max(58, len(label) * 10 + 22)
        c.setFillColor(PALETTE["bg"])
        c.setStrokeColor(PALETTE["line"])
        c.roundRect(chip_x, top - 47, tw, 26, 9, stroke=1, fill=1)
        c.setFillColor(PALETTE["muted"])
        c.setFont(FONT, 9)
        c.drawCentredString(chip_x + tw / 2, top - 38, label)
        chip_x += tw + 8
    draw_para(c, "AI 요구는 게시판과 별개로 평가되는 구현 책임이다.", x + 18, top - 49, 300, size=8.5, color=PALETTE["muted"])

    y = top - 102
    rows = [
        ["RAG", "개인 또는 사내 데이터와 LLM을 연결", "embedding/vector DB에 저장하고 질문에 맞게 검색해 context로 넣는다."],
        ["MCP", "LLM이 외부 시스템을 호출", "MCP Server가 tool을 제공하고 Host/Client가 JSON-RPC 흐름으로 호출한다."],
        ["Agent", "스스로 도구 선택과 실행 루프 관리", "function calling, state, observation, max turns, 예외처리, structured output을 보여준다."],
    ]
    mini_table(c, x, y, base_w, ["필수 기술", "과제 설명의 의미", "구현에서 보여줘야 하는 것"], rows, [0.15, 0.30, 0.55], PALETTE["ink"], 9.1)

    y2 = 166
    card(c, x, y2, 246, 84, "RAG 최소선", ["데이터 소스", "embedding 모델", "vector DB", "similarity search", "검색 결과의 출처"], PALETTE["rag"], PALETTE["soft_rag"], 12, 8.8)
    card(c, x + 262, y2, 246, 84, "MCP 최소선", ["MCP Server", "tool schema", "JSON-RPC 이해", "외부 서비스 1개 이상", "API key/권한 관리"], PALETTE["mcp"], PALETTE["soft_mcp"], 12, 8.8)
    card(c, x + 524, y2, base_w - 524, 84, "Agent 최소선", ["function calling", "state/memory", "tool observation", "무한 루프 방지", "예외처리"], PALETTE["agent"], PALETTE["soft_agent"], 12, 8.8)
    footer(c)


def page_3(c: canvas.Canvas) -> None:
    header(c, 3, "RAG", "학습이 아니라 검색해서 읽게 하는 구조", PALETTE["rag"])
    left = M
    right = M + 444
    y = PAGE_H - 116
    flow_labels = [
        ("Data", "문서/DB/웹페이지"),
        ("Chunk", "작은 단위로 분할"),
        ("Embedding", "vector로 변환"),
        ("Vector DB", "의미 검색 저장소"),
        ("Retrieval", "질문과 가까운 chunk"),
        ("Generation", "근거를 읽고 답변"),
    ]
    bx = left
    bw = 116
    for i, (t, b) in enumerate(flow_labels):
        flow_box(c, bx, y, bw, 60, t, b, PALETTE["rag"], PALETTE["soft_rag"] if i < 5 else colors.white)
        if i < len(flow_labels) - 1:
            arrow(c, bx + bw, y - 30, bx + bw + 14, y - 30, PALETTE["rag"], 1.4)
        bx += bw + 18

    card(
        c,
        left,
        y - 88,
        392,
        108,
        "오해 -> 정확한 설명",
        [
            "우리 데이터를 모델에 학습시킨 것? 아니다. 검색 결과를 현재 context로 넣은 것이다.",
            "문서 전체를 프롬프트에 붙이면 RAG? 아니다. 핵심은 retrieval 계층이다.",
            "RAG면 정답 보장? 아니다. 검색 품질과 출처 검증이 같이 필요하다.",
        ],
        PALETTE["rag"],
        colors.white,
        12.5,
        9.2,
    )
    card(
        c,
        right,
        y - 88,
        PAGE_W - M - right,
        108,
        "이미지 자리",
        "RAG indexing -> retrieval -> generation 흐름\n출처: Notion [JUNGLE] AI로 진화하기 / RAG\n주의: signed URL은 PDF에 직접 삽입하지 않는다.",
        PALETTE["muted"],
        colors.white,
        12.5,
        9.1,
    )

    rows = [
        ["데이터 소스", "LLM이 원래 모르지만 답변에 필요한 데이터"],
        ["chunking", "맥락이 끊기지 않도록 token 크기와 overlap을 조정"],
        ["embedding", "저장 데이터와 질문을 같은 모델로 vector화"],
        ["vector DB", "Pinecone, FAISS, Chroma, pgvector 등 운영 맥락에 맞게 선택"],
        ["metadata", "source id, 제목, URL, 작성일, score를 남겨 검증 가능하게 함"],
        ["fallback", "threshold 미달이면 추측하지 않고 근거 부족 상태로 처리"],
    ]
    mini_table(c, left, 285, 392, ["결정할 것", "좋은 기준"], rows, [0.28, 0.72], PALETTE["rag"], 8.15)

    code_block(c, right, 285, PAGE_W - M - right, "기존 LIKE 검색", [
        "SELECT * FROM posts",
        "WHERE title LIKE '%refund%';",
    ], PALETTE["rag"])
    code_block(c, right, 204, PAGE_W - M - right, "RAG semantic search", [
        "distance = Embedding.embedding.cosine_distance(query_vector)",
        "stmt = stmt.order_by(distance).limit(limit)",
    ], PALETTE["rag"])
    card(
        c,
        right,
        114,
        PAGE_W - M - right,
        61,
        "발표 문장",
        "RAG는 AI가 데이터를 외운 것이 아니라, 필요한 순간에 관련 데이터를 찾아 읽는 구조입니다.",
        PALETTE["rag"],
        PALETTE["soft_rag"],
        11.5,
        9.4,
    )
    footer(c, "Sources: local draft section 1/5/10, OpenAI retrieval and semantic search docs")


def page_4(c: canvas.Canvas) -> None:
    header(c, 4, "MCP", "외부 API를 AI가 쓰기 쉬운 tool 계층으로 감싼다", PALETTE["mcp"])
    x = M
    y = PAGE_H - 118

    host_x, client_x, server_x = x + 20, x + 300, x + 575
    flow_box(c, host_x, y, 190, 86, "MCP Host", "AI 앱 전체\n권한, 승인, context 관리", PALETTE["mcp"], PALETTE["soft_mcp"])
    flow_box(c, client_x, y, 190, 86, "MCP Client", "tools/list, tools/call\nJSON-RPC 2.0 포장", PALETTE["mcp"], colors.white)
    flow_box(c, server_x, y, 190, 86, "MCP Server", "실제 외부 API/DB/파일 호출\nTools/Resources/Prompts 제공", PALETTE["mcp"], PALETTE["soft_mcp"])
    arrow(c, host_x + 190, y - 43, client_x, y - 43, PALETTE["mcp"], 1.8)
    arrow(c, client_x + 190, y - 43, server_x, y - 43, PALETTE["mcp"], 1.8)
    draw_para(c, "LLM은 tool_name + arguments를 제안하고, 실행과 권한 통제는 Host/Client/Server 코드가 맡는다.",
              x + 86, y - 108, PAGE_W - 2 * M - 172, size=10.5, leading=14, color=PALETTE["muted"], align=TA_CENTER)

    card(
        c,
        x,
        386,
        238,
        124,
        "USB-C 비유",
        "이미지 자리: MCP USB-C 비유\n출처: Notion MCP 페이지\n의도: AI 앱과 외부 도구의 공통 연결 포트라는 감각을 보여준다.",
        PALETTE["mcp"],
        colors.white,
        12.5,
        9.0,
    )
    rows = [
        ["MCP Server", "어떤 기능을 tool로 제공할지 정한다."],
        ["tool schema", "LLM이 안정적으로 arguments를 만들 수 있게 입력/출력 구조를 명확히 한다."],
        ["외부 서비스", "GitHub, Notion, Slack, Google 등 실제 서비스 1개 이상을 연결한다."],
        ["JSON-RPC", "Client/Server 사이의 tools/list, tools/call 흐름을 이해한다."],
        ["권한/키", "secret은 서버 환경에 두고 tool result에는 노출하지 않는다."],
        ["보안", "allowlist, timeout, body limit, URL 검증을 둔다."],
    ]
    mini_table(c, x + 254, 386, PAGE_W - M - (x + 254), ["결정할 것", "구현 기준"], rows, [0.24, 0.76], PALETTE["mcp"], 8.2)

    code_block(c, x, 189, 370, "익숙한 backend API wrapper", [
        '@router.get("/github/readme")',
        "async def readme(github_url: str):",
        "    return await fetch_github_readme(github_url)",
    ], PALETTE["mcp"])
    code_block(c, x + 388, 189, PAGE_W - M - (x + 388), "MCP tool", [
        "@mcp.tool()",
        "async def fetch_github_readme(github_url: str) -> dict[str, Any]:",
        "    return await fetch_github_readme_tool(github_url)",
    ], PALETTE["mcp"])
    footer(c, "Sources: local draft section 1/6/10, OpenAI MCP and connectors docs")


def page_5(c: canvas.Canvas) -> None:
    header(c, 5, "Agent", "단일 LLM 호출이 아니라 상태와 observation을 가진 루프", PALETTE["agent"])
    x = M
    y = PAGE_H - 126

    loop = [
        ("State", "목표, 입력, 진행 상태"),
        ("Think", "다음 행동 판단"),
        ("Act", "tool call 생성"),
        ("Observe", "tool 결과 관찰"),
        ("Think again", "재판단 또는 종료"),
    ]
    cx = x + 32
    bw = 126
    for i, (t, b) in enumerate(loop):
        flow_box(c, cx, y, bw, 70, t, b, PALETTE["agent"], PALETTE["soft_agent"] if i != 3 else colors.white)
        if i < len(loop) - 1:
            arrow(c, cx + bw, y - 35, cx + bw + 20, y - 35, PALETTE["agent"], 1.8)
        cx += bw + 24
    arrow(c, x + 32 + 4 * (bw + 24) + 35, y - 72, x + 32 + bw / 2, y - 72, PALETTE["agent"], 1.4)
    draw_para(c, "되돌아가는 화살표가 핵심이다. 결과를 보고 다시 판단하기 때문에 Agent는 한 번의 답변 생성과 다르다.",
              x + 68, y - 99, PAGE_W - 2 * M - 136, size=10.5, color=PALETTE["muted"], align=TA_CENTER)

    card(c, x, 386, 247, 86, "Model", ["목표와 context를 읽고 판단", "tool_name + arguments 제안"], PALETTE["agent"], colors.white, 12.5, 9.2)
    card(c, x + 264, 386, 247, 86, "Tools", ["검색, 외부 호출, 계산, 저장", "입출력 schema가 명확해야 함"], PALETTE["agent"], colors.white, 12.5, 9.2)
    card(c, x + 528, 386, PAGE_W - M - (x + 528), 86, "Orchestration", ["상태, 순서, retry, 종료 조건", "backend가 실행 권한 통제"], PALETTE["agent"], colors.white, 12.5, 9.2)

    rows = [
        ["function calling", "모델은 호출할 함수와 arguments를 만들고 앱이 실제 함수를 실행"],
        ["state", "running/completed/failed, tool 결과, 최종 report를 저장"],
        ["loop 제한", "max turns, timeout, retry limit으로 무한 루프 방지"],
        ["예외 처리", "failed/need_more_info/refused/loading 같은 상태 구분"],
        ["output", "UI와 DB가 읽을 수 있는 structured output 사용"],
    ]
    mini_table(c, x, 278, 382, ["결정할 것", "좋은 기준"], rows, [0.32, 0.68], PALETTE["agent"], 8.4)
    code_block(c, x + 402, 278, PAGE_W - M - (x + 402), "Agent 구조 예시", [
        "return Agent(",
        "    instructions=PROJECT_ANALYSIS_INSTRUCTIONS,",
        "    tools=analysis_tools,",
        "    model=settings.agent_model,",
        "    output_type=ProjectAnalysisReport,",
        ")",
    ], PALETTE["agent"])
    card(c, x + 402, 139, PAGE_W - M - (x + 402), 68, "발표 문장", "Agent는 프롬프트가 긴 LLM 호출이 아니라, 생각하고 도구를 쓰고 결과를 관찰한 뒤 다시 판단하는 실행 구조입니다.", PALETTE["agent"], PALETTE["soft_agent"], 11.5, 9.4)
    footer(c, "Sources: local draft section 1/7/10, OpenAI Agents SDK and function calling docs")


def page_6(c: canvas.Canvas) -> None:
    header(c, 6, "통합 흐름", "Agent 루프 안에서 RAG와 MCP가 도구처럼 쓰인다", PALETTE["agent"])
    x = M
    top = PAGE_H - 118
    step_w = 94
    gap = 9
    steps = [
        ("사용자 요청", "분석 버튼"),
        ("Backend state", "job/status 생성"),
        ("RAG 검색", "내부 데이터 근거"),
        ("Agent 판단", "목표 + context"),
        ("tool call", "함수명 + 인자"),
        ("MCP 호출", "외부 근거"),
        ("Observation", "결과 관찰"),
    ]
    sx = x
    for i, (t, b) in enumerate(steps):
        accent = PALETTE["rag"] if t.startswith("RAG") else PALETTE["mcp"] if t.startswith("MCP") else PALETTE["agent"] if "Agent" in t or "tool" in t or "Observation" in t else PALETTE["ink"]
        fill = PALETTE["soft_rag"] if accent == PALETTE["rag"] else PALETTE["soft_mcp"] if accent == PALETTE["mcp"] else PALETTE["soft_agent"] if accent == PALETTE["agent"] else colors.white
        flow_box(c, sx, top, step_w, 66, t, b, accent, fill)
        if i < len(steps) - 1:
            arrow(c, sx + step_w, top - 33, sx + step_w + gap, top - 33, accent, 1.6)
        sx += step_w + gap

    agent_center_x = x + 3 * (step_w + gap) + step_w / 2
    obs_center_x = x + 6 * (step_w + gap) + step_w / 2
    c.setStrokeColor(PALETTE["agent"])
    c.setLineWidth(2.2)
    loop_x = agent_center_x - 34
    loop_w = obs_center_x - agent_center_x + 68
    c.roundRect(loop_x, top - 144, loop_w, 72, 14, stroke=1, fill=0)
    arrow(c, obs_center_x, top - 78, agent_center_x, top - 78, PALETTE["agent"], 2.2)
    draw_para(c, "Observation -> Agent 재판단\n이 되돌아감이 Agent의 핵심", agent_center_x + 28, top - 96, obs_center_x - agent_center_x - 56, size=9.8, color=PALETTE["agent"], align=TA_CENTER)

    out_top = top - 190
    out_w = 148
    out_gap = 28
    out_x1 = x + 238
    out_x2 = out_x1 + out_w + out_gap
    out_x3 = out_x2 + out_w + out_gap
    flow_box(c, out_x1, out_top, out_w, 62, "Structured Output", "schema에 맞춘 최종 report", PALETTE["good"], PALETTE["soft_good"])
    flow_box(c, out_x2, out_top, out_w, 62, "DB 저장", "report/evidence/status", PALETTE["good"], colors.white)
    flow_box(c, out_x3, out_top, out_w, 62, "UI 렌더링", "polling 후 카드 표시", PALETTE["good"], PALETTE["soft_good"])
    arrow(c, out_x1 + out_w, out_top + 31, out_x2, out_top + 31, PALETTE["good"], 1.5)
    arrow(c, out_x2 + out_w, out_top + 31, out_x3, out_top + 31, PALETTE["good"], 1.5)

    rows = [
        ["사용자 요청", "게시글 상세의 AI 분석 버튼"],
        ["상태 생성", "analysis job endpoint와 posts.analysis_status"],
        ["RAG", "embedding 기반 유사 프로젝트 검색"],
        ["tool call/MCP", "function_tool wrapper -> local/private MCP Server"],
        ["Observation", "사이트/GitHub 근거 결과"],
        ["최종 output", "Pydantic Structured Outputs -> ai_reports, mcp_evidences"],
        ["UI", "분석 상태 polling 후 카드 UI 렌더링"],
    ]
    mini_table(c, x, 228, PAGE_W - 2 * M, ["일반 흐름", "ProjectLens 예시 라벨"], rows, [0.27, 0.73], PALETTE["agent"], 8.7)
    footer(c, "Sources: local draft section 4, repo implementation labels")


def page_7(c: canvas.Canvas) -> None:
    header(c, 7, "구현 참고표", "발표 중 길게 읽지 말고, 만들 때 확인하는 결정표", PALETTE["ink"])
    rows = [
        ["RAG", "데이터 소스", "무엇을 검색할 것인가?", "LLM이 원래 모르지만 답변에 꼭 필요한 데이터만 넣는다."],
        ["RAG", "embedding/vector DB", "어떻게 의미 검색할 것인가?", "같은 embedding 모델로 저장/질문 vector를 만들고 pgvector/FAISS/Chroma/Pinecone 중 운영에 맞게 선택한다."],
        ["RAG", "metadata/fallback", "검색 결과를 믿을 수 있는가?", "source, score, 작성일을 저장하고 threshold 미달은 근거 부족으로 처리한다."],
        ["MCP", "MCP Server", "어떤 외부 기능을 tool로 제공할 것인가?", "범용 call_api보다 fetch_github_readme처럼 목적이 분명한 tool을 둔다."],
        ["MCP", "JSON-RPC/tool schema", "LLM이 안정적으로 호출할 수 있는가?", "tools/list와 tools/call 흐름, 입력 schema, 출력 형태를 설명 가능하게 만든다."],
        ["MCP", "권한/보안", "API key와 외부 입력을 어떻게 제한할 것인가?", "secret은 서버에 두고 allowlist, timeout, body limit, URL 검증을 적용한다."],
        ["Agent", "function calling", "모델과 backend의 책임을 나눴는가?", "모델은 tool_name + arguments, backend는 실행과 검증을 맡는다."],
        ["Agent", "state/loop 제한", "무한 루프와 새로고침을 견딜 수 있는가?", "running/completed/failed, max turns, timeout, retry limit을 둔다."],
        ["Agent", "structured output", "UI가 안정적으로 렌더링할 수 있는가?", "자유 텍스트 대신 schema 기반 결과를 저장한다."],
    ]
    mini_table(c, M, PAGE_H - 116, PAGE_W - 2 * M, ["영역", "결정", "질문", "좋은 기준"], rows, [0.10, 0.18, 0.30, 0.42], PALETTE["ink"], 8.0)
    card(
        c,
        M,
        104,
        PAGE_W - 2 * M,
        48,
        "읽는 방법",
        "이 표는 발표용 문장이 아니라 구현 체크리스트다. 발표에서는 'RAG는 검색 구조, MCP는 외부 tool 연결, Agent는 그 둘을 쓰는 루프'만 먼저 잡아준다.",
        PALETTE["ink"],
        colors.white,
        11.5,
        9.2,
    )
    footer(c)


def page_8(c: canvas.Canvas) -> None:
    header(c, 8, "개선 축 1", "RAG 개선은 검색 품질을 끌어올리는 일이다", PALETTE["rag"])
    x = M
    y = PAGE_H - 118
    card(
        c,
        x,
        y,
        250,
        112,
        "문제 신호",
        [
            "검색 결과가 엉뚱하다.",
            "관련 없는 문서가 context에 섞인다.",
            "검색 결과가 없는데 그럴듯한 답을 한다.",
            "출처가 없어 검증이 어렵다.",
        ],
        PALETTE["danger"],
        colors.white,
        12.5,
        9.5,
    )
    card(
        c,
        x + 272,
        y,
        250,
        112,
        "조정할 레버",
        [
            "chunk 크기와 overlap",
            "embedding 입력 텍스트",
            "top-k와 similarity threshold",
            "metadata와 source 표시",
        ],
        PALETTE["rag"],
        PALETTE["soft_rag"],
        12.5,
        9.5,
    )
    card(
        c,
        x + 544,
        y,
        PAGE_W - M - (x + 544),
        112,
        "고급 개선",
        [
            "semantic score 외 ranking signal 추가",
            "태그, 최신성, 유형 기반 weighted RAG",
            "빈 결과를 정상 상태로 처리",
        ],
        PALETTE["good"],
        colors.white,
        12.5,
        9.5,
    )
    arrow(c, x + 250, y - 56, x + 272, y - 56, PALETTE["rag"], 1.7)
    arrow(c, x + 522, y - 56, x + 544, y - 56, PALETTE["rag"], 1.7)

    rows = [
        ["검색 결과가 엉뚱함", "chunk/metadata/embedding 입력 텍스트를 조정"],
        ["낮은 관련도 결과가 섞임", "threshold와 top-k 조정"],
        ["근거가 빈약함", "source title, URL, 작성일, score를 함께 표시"],
        ["데이터가 쌓였는데 정렬이 단순함", "semantic score 외 태그, 최신성, 유형 signal을 섞음"],
        ["결과가 없는데 답함", "근거 부족 상태로 처리하고 추측을 막음"],
    ]
    mini_table(c, x, 360, PAGE_W - 2 * M, ["문제", "개선 방향"], rows, [0.34, 0.66], PALETTE["rag"], 9.0)
    card(c, x, 143, PAGE_W - 2 * M, 70, "발표 문장", "RAG 품질은 모델이 얼마나 똑똑한가보다 무엇을 검색해 넣었는가에 크게 좌우됩니다. 그래서 검색 결과의 관련도, 출처, 빈 결과 처리가 핵심입니다.", PALETTE["rag"], PALETTE["soft_rag"], 12, 10)
    footer(c, "Sources: local draft section 8, OpenAI retrieval docs")


def page_9(c: canvas.Canvas) -> None:
    header(c, 9, "개선 축 2", "Agent 개선은 루프를 안정적으로 끝내게 만드는 일이다", PALETTE["agent"])
    x = M
    top = PAGE_H - 122
    nodes = [
        ("Tool schema", "이름/설명/입력"),
        ("State", "running/completed/failed"),
        ("Max turns", "무한 루프 방지"),
        ("Retry/Error", "실패 이유 저장"),
        ("Structured output", "UI/DB가 읽는 결과"),
        ("Async polling", "오래 걸리는 분석 분리"),
    ]
    sx = x
    for i, (t, b) in enumerate(nodes):
        flow_box(c, sx, top, 116, 64, t, b, PALETTE["agent"], PALETTE["soft_agent"] if i % 2 == 0 else colors.white)
        if i < len(nodes) - 1:
            arrow(c, sx + 116, top - 32, sx + 130, top - 32, PALETTE["agent"], 1.4)
        sx += 130

    rows = [
        ["tool을 잘못 고름", "tool name, description, input schema를 구체화"],
        ["같은 tool을 반복", "max turns, retry limit, 중복 호출 방지"],
        ["실패 이유를 모름", "tool error와 status를 저장"],
        ["응답이 UI에 맞지 않음", "structured output schema 강제"],
        ["분석이 오래 걸림", "async job + frontend polling으로 분리"],
        ["근거와 결론이 섞임", "observation은 evidence, 최종 output은 schema로 분리"],
    ]
    mini_table(c, x, 372, PAGE_W - 2 * M, ["문제", "개선 방향"], rows, [0.34, 0.66], PALETTE["agent"], 9.0)
    card(
        c,
        x,
        134,
        382,
        66,
        "핵심",
        "Agent는 실패와 지연까지 상태로 다뤄야 서비스가 된다. 성공 경로만 있으면 데모는 되지만 운영 가능한 기능이라고 설명하기 어렵다.",
        PALETTE["agent"],
        PALETTE["soft_agent"],
        12,
        9.8,
    )
    card(
        c,
        x + 402,
        134,
        PAGE_W - M - (x + 402),
        66,
        "ProjectLens 예시",
        "async polling과 structured output retry는 Agent 루프 안정화의 예시다. 발표에서는 예시로만 짧게 언급한다.",
        PALETTE["muted"],
        colors.white,
        12,
        9.8,
    )
    footer(c, "Sources: local draft section 8, OpenAI function calling and structured outputs docs")


def page_10(c: canvas.Canvas) -> None:
    header(c, 10, "비용과 제한", "Agent 루프는 호출 수와 token 비용을 빠르게 키울 수 있다", PALETTE["warn"])
    x = M
    top = PAGE_H - 126
    flow_box(c, x + 74, top, 132, 64, "사용자 요청", "1번 클릭", PALETTE["ink"], colors.white)
    flow_box(c, x + 254, top, 132, 64, "Agent loop", "모델 판단 반복", PALETTE["agent"], PALETTE["soft_agent"])
    flow_box(c, x + 434, top, 132, 64, "Tool calls", "추가 호출/근거", PALETTE["mcp"], PALETTE["soft_mcp"])
    flow_box(c, x + 614, top, 132, 64, "Token cost", "입력 + 출력 증가", PALETTE["warn"], PALETTE["soft_warn"])
    arrow(c, x + 206, top - 32, x + 254, top - 32, PALETTE["warn"], 1.7)
    arrow(c, x + 386, top - 32, x + 434, top - 32, PALETTE["warn"], 1.7)
    arrow(c, x + 566, top - 32, x + 614, top - 32, PALETTE["warn"], 1.7)

    card(c, x, 386, 186, 112, "Rate limits", ["RPM: 분당 요청 수", "TPM: 분당 token 수", "실패/retry도 제한에 영향을 줄 수 있음"], PALETTE["warn"], colors.white, 12, 9)
    card(c, x + 204, 386, 186, 112, "Pricing", ["API는 token 기준 과금", "입력 token과 출력 token 모두 비용 요인", "가격은 공식 pricing에서 확인"], PALETTE["warn"], colors.white, 12, 9)
    card(c, x + 408, 386, 186, 112, "Usage dashboard", ["사용량을 직접 확인", "monthly budget과 알림 threshold 설정", "한도 반영 지연 가능성 고려"], PALETTE["warn"], colors.white, 12, 9)
    card(c, x + 612, 386, PAGE_W - M - (x + 612), 112, "Prepaid credits", ["auto recharge 상태 확인", "monthly recharge limit 설정", "만료/환불 불가 조건 확인"], PALETTE["danger"], PALETTE["soft_warn"], 12, 9)

    card(
        c,
        x,
        232,
        382,
        86,
        "발표에서 꼭 말할 것",
        "ChatGPT 구독과 OpenAI API 과금은 별도입니다. 실습 전에는 usage dashboard, monthly budget, auto recharge 상태를 확인해야 합니다.",
        PALETTE["danger"],
        colors.white,
        12.5,
        10,
    )
    card(
        c,
        x + 402,
        232,
        PAGE_W - M - (x + 402),
        86,
        "실습 권장",
        ["작은 prepaid credit으로 시작", "Agent max turns를 낮게 설정", "데모 전 remaining credits 확인", "대량 embedding은 batch와 rate limit 확인"],
        PALETTE["good"],
        PALETTE["soft_good"],
        12.5,
        9,
    )
    footer(c, "Sources: OpenAI Rate limits, API Pricing, Prepaid billing official pages")


def page_11(c: canvas.Canvas) -> None:
    header(c, 11, "코드 읽기", "기존 backend/frontend 감각으로 AI 코드를 해석하기", PALETTE["ink"])
    x = M
    y = PAGE_H - 116
    code_block(c, x, y, 374, "RAG: LIKE 검색의 확장", [
        "SELECT * FROM posts WHERE title LIKE '%refund%';",
        "",
        "distance = Embedding.embedding.cosine_distance(query_vector)",
        "stmt = stmt.order_by(distance).limit(limit)",
    ], PALETTE["rag"])
    card(c, x + 394, y, PAGE_W - M - (x + 394), 100, "해석", "둘 다 DB에서 관련 데이터를 찾는다. 차이는 LIKE가 문자열 일치 검색이고, RAG는 embedding vector의 의미적 거리 검색이라는 점이다.", PALETTE["rag"], PALETTE["soft_rag"], 12, 9.6)

    y2 = 382
    code_block(c, x, y2, 374, "MCP: API wrapper의 AI-friendly 버전", [
        '@router.get("/github/readme")',
        "async def readme(github_url: str): ...",
        "",
        "@mcp.tool()",
        "async def fetch_github_readme(github_url: str) -> dict: ...",
    ], PALETTE["mcp"])
    card(c, x + 394, y2, PAGE_W - M - (x + 394), 116, "해석", "둘 다 외부 서비스를 호출한다. 다른 점은 MCP tool이 Agent/Host가 schema를 보고 호출할 수 있는 표준 tool 표면을 제공한다는 점이다.", PALETTE["mcp"], PALETTE["soft_mcp"], 12, 9.6)

    y3 = 226
    code_block(c, x, y3, 374, "Agent: service orchestration의 AI 버전", [
        "async def run_analysis(post_id: int):",
        "    post = await load_post(post_id)",
        "    evidence = await fetch_evidence(post)",
        "    report = build_report(post, evidence)",
        "",
        "Agent(instructions=..., tools=..., output_type=...)",
    ], PALETTE["agent"])
    card(c, x + 394, y3, PAGE_W - M - (x + 394), 132, "해석", "일반 service는 개발자가 순서를 고정한다. Agent는 모델이 tool 사용 여부와 arguments를 선택하고, backend가 실행과 권한을 통제한다.", PALETTE["agent"], PALETTE["soft_agent"], 12, 9.6)

    card(c, x, 68, PAGE_W - 2 * M, 42, "Frontend 연결", "기존 fetch 후 렌더링과 비슷하지만, AI 분석은 오래 걸릴 수 있어 start job -> polling status -> completed/failed 카드 렌더링으로 확장된다.", PALETTE["ink"], colors.white, 11.5, 9.4)
    footer(c, "Sources: local draft section 10, repo code-reading comparison")


def page_12(c: canvas.Canvas) -> None:
    header(c, 12, "보안과 Q&A", "외부 결과는 지시문이 아니라 근거 데이터다", PALETTE["danger"])
    x = M
    card(
        c,
        x,
        PAGE_H - 116,
        382,
        134,
        "보안 원칙",
        [
            "외부 사이트, README, MCP 결과는 instruction이 아니라 evidence로만 취급한다.",
            "API key와 secret은 tool output, 로그, AI context에 넣지 않는다.",
            "URL fetch는 SSRF 가드, timeout, body limit, redirect 재검증이 필요하다.",
            "AI 출력은 structured output으로 검증 가능한 형태로 저장한다.",
        ],
        PALETTE["danger"],
        colors.white,
        12.5,
        9.2,
    )
    card(
        c,
        x + 402,
        PAGE_H - 116,
        PAGE_W - M - (x + 402),
        134,
        "외울 문장",
        [
            "RAG는 학습이 아니라 검색이다.",
            "MCP는 API를 AI가 쓰기 쉽게 감싸는 표준 연결 방식이다.",
            "Agent는 단일 호출이 아니라 Think -> Act -> Observe 루프다.",
            "모델은 판단하고 backend는 실행과 권한을 통제한다.",
        ],
        PALETTE["ink"],
        PALETTE["soft_warn"],
        12.5,
        9.2,
    )

    rows = [
        ["RAG를 쓰면 학습한 건가요?", "아니다. 모델 파라미터를 바꾸지 않고 검색 결과를 현재 context로 넣는다."],
        ["SQL 검색도 RAG인가요?", "retrieval은 가능하지만 과제에서 기대하는 RAG는 보통 embedding 기반 semantic search와 vector DB를 포함한다."],
        ["MCP와 API는 뭐가 다른가요?", "API는 범용 연결이고 MCP는 AI Agent가 tool로 발견/호출하기 좋은 표준 계층이다."],
        ["LangGraph를 꼭 써야 하나요?", "핵심은 라이브러리 이름보다 state와 loop가 보이는 agentic 구조다."],
        ["왜 structured output이 필요한가요?", "UI 카드와 DB 저장을 안정적으로 만들기 위해 필드가 일정해야 한다."],
        ["비용은 어디서 커지나요?", "Agent가 tool을 여러 번 호출하고 긴 evidence를 읽을 때 token과 요청 수가 늘어난다."],
    ]
    mini_table(c, x, 330, PAGE_W - 2 * M, ["질문", "짧은 답"], rows, [0.32, 0.68], PALETTE["danger"], 8.45)

    source_text = (
        "출처: DOCS/ProjectLens_AI파트_코어타임_설명초안.md, AGENTS.md, repo code paths "
        "backend/app/ai, backend/app/rag, backend/app/mcp_client, mcp-server, frontend/src/components/analysis. "
        "Notion: RAG, MCP, AI agents 페이지의 개념과 이미지 캡션. OpenAI official docs: Rate limits, API Pricing, Prepaid billing, Agents SDK, Function calling, Structured Outputs, Retrieval, MCP and Connectors."
    )
    draw_para(c, source_text, x, 82, PAGE_W - 2 * M, size=7.8, leading=10.5, color=PALETTE["muted"])
    footer(c, "Final check: Notion signed image URLs are not embedded; image slots are captions only.")


def build_pdf() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(OUT_PATH), pagesize=landscape(A4))
    c.setTitle("ProjectLens AI 코어타임 인포그래픽")
    for fn in [
        page_1,
        page_2,
        page_3,
        page_4,
        page_5,
        page_6,
        page_7,
        page_8,
        page_9,
        page_10,
        page_11,
        page_12,
    ]:
        fn(c)
        c.showPage()
    c.save()
    print(OUT_PATH)


if __name__ == "__main__":
    build_pdf()
