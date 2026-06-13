# 세션 11 개념 노트 — B3(CRUD + REST + 계층 분리): 스키마·관계·리포지토리·서비스·라우터

> 이번 세션은 "데이터 모양 정의(schemas) → 관계 보강(models) → DB 쿼리(repository) → 규칙(service) → HTTP(router)"까지, **요청 하나가 흐르는 전 구간**을 만들었다.
> 복습 포인트는 두 종류: ① 개념(왜 이렇게 생겼나) ② 검토에서 터진 버그(같은 실수 반복 방지).

---

## 먼저 붙잡을 전체 그림 — 요청 하나가 흐르는 길

```
[클라이언트]  POST /posts  {title, excuseText, tagIds:[...]}
     │
     ▼
routers/posts.py   ← HTTP를 안다: 경로·상태코드·body 받기·검증
     │   PostCreate 로 들어온 JSON 검증, Depends(get_db)로 세션 주입
     ▼
services/posts.py  ← 규칙을 안다: 태그 slug→Tag 해석, 없는 태그면 거부
     │   commit 여부 결정
     ▼
repositories/posts.py ← DB를 안다: select / insert / JOIN / 페이징
     │
     ▼
models.py / PostgreSQL
     │ (돌아 나오는 길)
     ▼
PostOut 으로 직렬화 → camelCase JSON 응답
```

핵심 원칙 한 줄: **"이 코드가 무엇을 아는가"로 층을 나눈다.** HTTP를 알면 router, 규칙을 알면 service, DB를 알면 repository, 데이터 모양이면 schemas. 한 함수가 두 가지를 알면(예: 404를 던지면서 SQL도 짜면) 쪼갠다.

이번에 만든 파일:

| 파일 | 층 | 책임 |
|---|---|---|
| `app/schemas.py` | 경계(모양) | 들어오는/나가는 JSON 모양 정의 |
| `app/models.py` (수정) | 데이터(DB모양) | Post↔Tag 다대다 관계 추가 |
| `app/repositories/posts.py` | DB | `get_post`·`list_posts`·`create_post` |
| `app/services/posts.py` | 규칙 | `create`(태그 해석·검증·commit) |
| `app/routers/posts.py` | HTTP | `GET /posts`·`GET /posts/{id}`·`POST /posts` |
| `app/main.py` (수정) | 진입점 | 라우터 등록 |

---

# Part 1. 계층 분리 — 왜 router/service/repository로 쪼개나

## 1.1 한 파일 = 한 책임

프론트에서도 "타입은 화면을 모른다"를 배웠듯, 백엔드도 **아는 것의 종류로** 코드를 나눈다.

- **router** = HTTP를 아는 층. "어떤 경로로 왔나, body가 맞는 모양인가, 몇 번 상태코드로 답하나." SQL은 모른다.
- **service** = 규칙(비즈니스 로직)을 아는 층. "태그 slug를 실제 Tag로 바꾼다, 없는 태그면 거부한다, 언제 commit한다." HTTP도 모르고(404를 직접 안 던짐), 구체적 SQL도 모른다.
- **repository** = DB를 아는 층. `select`·`insert`·JOIN·페이징. HTTP도 규칙도 모른다.

## 1.2 분할 기준 (다음에 직접 나눌 때)

> "이 코드가 HTTP를 아는가(→router)·규칙을 다루나(→service)·DB를 아는가(→repository)·데이터 모양인가(→schemas/models)."
> 둘 다 알면 쪼갠다. 같은 종류가 여러 개가 되면 **파일 → 폴더**로 승격: `routers/posts.py`, `routers/comments.py` …

지금은 `posts.py` 단일 파일이지만 comments·votes가 늘면 폴더 안에서 파일로 분화한다.

## 1.3 왜 굳이 나누나 (실익)

- **바꿀 때 한 곳만** 고친다. SQL 튜닝은 repository만, 상태코드 정책은 router만.
- **테스트가 쉽다.** repository 함수는 HTTP 없이 세션만 넘겨 단독으로 돌릴 수 있다(이번에 스모크 테스트로 그렇게 검증함).
- **프론트 계약과 분리.** router는 프론트 mock 시그니처에 맞추고, 그 아래는 자유롭게 구현.

---

# Part 2. Pydantic 스키마 — 바깥세상(JSON)과의 경계

`models.py`가 *DB 안의* 모양이라면, `schemas.py`는 *바깥과 주고받는* 모양이다. 같은 Post라도 **들어올 때(작성 요청)**와 **나갈 때(응답)** 필드가 다르다.

## 2.1 Pydantic이란 / 요청·응답을 왜 나누나

- **정의**: Pydantic = 파이썬 타입 힌트로 "이 데이터는 이런 모양이어야 한다"를 선언하면 **런타임에 검증(validation)**해주는 라이브러리. `BaseModel`을 상속한 클래스 하나 = 스키마 하나.
- **등장 배경**: 이전엔 `request.json()`으로 dict를 받아 `data["title"]`로 꺼냈다 → 키 없으면 `KeyError`, 타입 틀려도 한참 뒤 DB에서 터짐, "이 엔드포인트가 뭘 받는지" 명세가 코드에 안 남음. 그래서 "받을 모양을 클래스로 선언하면 검증·문서·자동완성이 공짜"라는 발상이 나옴.
- **요청·출력 분리 이유**: `User`를 그대로 응답에 쓰면 `password_hash`가 JSON으로 샌다. 입력 스키마(`PostCreate`)와 출력 스키마(`PostOut`)를 나눠야 "받는 필드"와 "주는 필드"를 따로 통제한다.
- **런타임 장면**: 클라이언트가 `{"title": 123}`(숫자!)을 보내면 핸들러 몸통이 **한 줄도 안 돌고** FastAPI가 자동으로 `422` + 어느 필드가 왜 틀렸는지 detail을 돌려준다. 통과한 객체만 `body.title`(이미 `str` 보장)로 손에 들어온다. `/docs`엔 이 스키마가 그대로 입력 폼·응답 예시로 그려진다.

```python
class PostCreate(BaseModel):
    """글 작성 요청 body. 사용자가 직접 적는 필드만 (id·createdAt·verdict는 서버/AI 몫이라 제외)."""
    title: str
    excuse_text: str = Field(alias="excuseText")
    tag_ids: list[str] = Field(default_factory=list, alias="tagIds")
    context: dict | None = None
    model_config = ConfigDict(populate_by_name=True)
```

> **`default_factory=list`** (≠ `= []`): 가변 기본값(리스트)을 **매 인스턴스마다 새로** 만든다. `= []`로 두면 모든 인스턴스가 **같은 리스트 하나를 공유**하는 함정(한 곳에서 append하면 다른 데도 바뀜). 그래서 list·dict 같은 가변 기본값은 항상 `default_factory`.

## 2.2 alias — camelCase(바깥) ↔ snake_case(안)

- **정의**: alias = 한 필드에 "JSON에서 쓸 이름"을 따로 붙이는 것. 파이썬 필드는 `excuse_text`(snake_case 관례), 프론트 JSON 키는 `excuseText`(JS 관례 camelCase). `Field(alias="excuseText")`로 잇는다.
- **등장 배경**: 파이썬(snake)과 JS(camel)의 명명 관례가 다르다. 한쪽에 맞추면 다른 쪽이 어색하고, 수동으로 키를 바꿔 담으면 실수투성이 → "필드는 내 관례대로, 직렬화 때 이름만 갈아끼우자"가 alias.
- **`populate_by_name=True`**: alias(`excuseText`)로도, 원래 필드명(`excuse_text`)으로도 **둘 다** 채우기 허용.
- **런타임 장면**: 들어올 때 `{"excuseText": "..."}` → Pydantic이 alias 보고 `body.excuse_text`에 담음. alias를 안 걸면 프론트엔 `excuse_text`가 그대로 나가 프론트 `Post.excuseText`와 어긋나 `undefined`.

## 2.3 (질문) Annotated 메타데이터 — "this is just metadata"

> FastAPI 문서의 `say_hello(name: Annotated[str, "this is just metadata"])` 예시를 보고 `Annotated[str, "본문 설명"]`을 써봤다.

- **정의**: `Annotated[T, X]` = "타입은 `T`, `X`는 **읽을 사람이 정해진** 추가 메타데이터 쪽지". 파이썬 3.10+ `typing`에서.
- **핵심**: 문서가 예시 문자열을 **`"this is just metadata"`(그냥 메타데이터)**라고 이름 붙인 게 신호다 — "여기에 생 문자열을 넣으면 **읽는 도구가 없어서 아무 일도 안 일어난다**". Pydantic은 `Annotated`의 메타 칸을 훑어 **자기가 아는 객체**(`FieldInfo`=`Field(...)`, `Gt`, `MinLen` 같은 제약)만 줍고, 생 문자열은 **조용히 무시**한다.
- **그래서**: `excuse_text: Annotated[str, "본문"] = Field(alias="excuseText")`는 사실상 `excuse_text: str = Field(alias="excuseText")`와 똑같다(문자열은 헛수고).
- **"강력해지는" 형태**: 메타 칸에 도구가 읽을 줄 아는 객체(`Field`/`Query`/`Path`)를 넣을 때. 이게 FastAPI가 미는 관용형:

```python
# 생 문자열 — 아무도 안 읽음
excuse_text: Annotated[str, "본문"] = Field(alias="excuseText")
# 관용형 — 메타 칸에 Field, 뒤의 = Field 는 뺀다
excuse_text: Annotated[str, Field(alias="excuseText", description="변명글 본문")]
```

> 한 줄: **`Annotated[T, X]`의 X는 "읽을 사람이 정해진 쪽지". 생 문자열은 읽을 사람이 없어 버려지고, `Field()`를 넣으면 Pydantic이 집어 읽는다.**

## 2.4 (버그) 아래첨자 안 키워드 인수 — `Annotated[str, description="..."]`

설명을 박으려고 `Annotated[str, description="..."]`로 썼더니 검사기가 **"아래 첨자 내의 키워드 인수는 지원되지 않습니다"** 에러.

- **왜**: `Annotated[...]`의 대괄호 `[]`는 **subscript(아래첨자) 문법** → `list[int]`나 `d["key"]`처럼 **값(value)만** 놓을 수 있다. `description="..."`는 **키워드 인수** 문법이고, 그건 오직 **함수 호출 괄호 `f(...)` 안에서만** 허용된다.
- **고치는 법**: `description`을 `Field()`라는 함수 호출로 **감싸서** 그 호출이 만든 값(FieldInfo)을 슬롯에 넣는다: `Annotated[str, Field(alias="excuseText", description="...")]`.

> 구분 한 줄: **대괄호 `[]` = 값만(subscript) / 소괄호 `()` = 키워드 인수 OK(함수 호출).** `key=value`를 쓰고 싶으면 반드시 `()` 안.

(결론적으로 이번엔 description을 빼고 `excuse_text: str = Field(alias="excuseText")`로 단순화.)

## 2.5 validation_alias — "읽는 이름"과 "쓰는 이름"을 다르게 (TagOut)

```python
class TagOut(BaseModel):
    """ORM Tag(.slug/.name/.id) → 프론트 Tag({id, label})."""
    id: str = Field(validation_alias="slug")     # ORM의 .slug 에서 읽어 id 에 담음
    label: str = Field(validation_alias="name")  # ORM의 .name 에서 읽어 label 에 담음
    model_config = ConfigDict(from_attributes=True)
```

- **정의**: 지금까지 쓴 `alias=`는 **읽기·쓰기 이름을 한꺼번에** 같은 값으로 바꾼다. 이걸 둘로 쪼갠 게:
  - `validation_alias` = **입력을 읽을 때** 찾는 이름(검증 단계)
  - `serialization_alias` = **출력으로 내보낼 때** 쓰는 이름
  - `alias` = 둘 다 한 번에 설정하는 단축
- **왜 여기서 필요한가**: ORM `Tag`는 `.slug`·`.name`·`.id`(숫자 PK)를 갖고, 프론트는 `{id: <slug값>, label: <name값>}`을 원한다. 즉 **"`slug`에서 읽되 `id`라는 이름으로 내보내라"**. `alias="slug"`로 퉁치면 출력도 `slug`로 나가 프론트 `Tag.id`와 어긋난다 → 읽기/쓰기를 갈라야 한다.
- **런타임 장면**: `from_attributes=True`라 Pydantic이 ORM 객체에서 속성 이름으로 값을 끌어온다. `validation_alias="slug"` → `tag.slug`("t1")를 읽어 `id` 필드에 담음. 출력 땐 필드명 `id`로 나감 → `{"id":"t1","label":"지각"}`. 숫자 PK(`tag.id=7`)는 새지 않는다.

## 2.6 from_attributes — ORM 객체 → 스키마

- **정의**: `from_attributes=True`(구 `orm_mode`) = "dict뿐 아니라 **속성 접근(`obj.title`)이 되는 객체**(=SQLAlchemy 모델 인스턴스)로도 이 스키마를 만들 수 있게 하라".
- **등장 배경**: repository가 돌려주는 건 dict가 아니라 `Post` ORM 객체. 기본 Pydantic은 dict만 받으므로 ORM을 일일이 dict로 풀어 담아야 했다 → 귀찮고 누락 위험. 그래서 "속성으로 읽어 채우기" 모드가 생김.
- **런타임 장면**: `PostOut.model_validate(post_orm)` 한 줄이면 `post.title`·`post.excuse_text`를 알아서 읽어 스키마를 만든다. FastAPI에선 `response_model=PostOut`만 걸면 핸들러가 ORM 객체를 `return`해도 자동 변환.

## 2.7 by_alias — 나갈 때 camelCase JSON

```python
class PostOut(BaseModel):
    id: int                                          # ⚠️ 프론트 Post.id는 string → B4에서 정리
    title: str
    excuse_text: str = Field(alias="excuseText")
    created_at: datetime = Field(alias="createdAt")
    score: int                                       # 백엔드 응답 계약(프론트는 B4에 추가)
    verdict: str | None = None
    credibility: int | None = None
    context: dict | None = None
    tags: list[TagOut] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
```

- alias를 걸어둬도 **응답 JSON이 camelCase로 나가려면** 직렬화 시 `by_alias=True`를 줘야 한다. 두 경로:
  - 라우터에서 `response_model_by_alias=True` (FastAPI가 자동 직렬화) — `GET /posts/{id}`·`POST /posts`가 이 방식.
  - 직접 `model_dump(by_alias=True)` — `GET /posts`의 목록 envelope가 이 방식(아래 Part 6).
- **검증으로 본 결과**(가짜 ORM 객체로 `model_dump(by_alias=True)`):
  `{'id':1,'title':..,'excuseText':..,'createdAt':..,'score':3,'tags':[{'id':'t1','label':'지각'}], ...}` = **프론트 `Post` 모양 + score**.

> ⚠️ 계약 플래그: `PostOut.id`는 `int`(DB bigint)인데 프론트 `Post.id`는 `string`("p1"). 이 불일치는 **B4 axios 전환 때** 프론트를 number로 바꾸거나 백엔드에서 str 변환 중 하나로 정리. (`tag.id`=slug 문자열과는 별개 결정.)

---

# Part 3. 다대다 관계와 중간 테이블 (models.py 보강)

`PostOut.tags`가 `post.tags`를 읽는데, 기존 `Post`엔 `author` 관계만 있고 `tags` 관계가 없었다. 한 줄 추가:

```python
class Post(Base):
    ...
    author: Mapped["User"] = relationship()
    tags: Mapped[list["Tag"]] = relationship(secondary="post_tags")   # ← 추가
```

## 3.1 (질문) 중간 테이블이 왜 필요한가 — "한 칸 = 하나"

핵심은 **FK 컬럼 하나엔 값이 딱 하나만 들어간다**는 제약.

- **시도 1 — posts에 `tag_id` 컬럼**: 글 1개에 태그 하나밖에 못 적음(칸이 하나). `tag_id1, tag_id2…`로 늘리면 "몇 개까지?"가 안 정해져 파탄.
- **시도 2 — tags에 `post_id` 컬럼**: 한 태그를 글 하나에만 묶게 됨. 여러 글이 `지각` 태그를 공유 못 함.
- → 어느 쪽에 FK를 넣어도 "한 칸=하나" 때문에 한 방향이 1개로 고정. 이게 다대다를 직접 표현 못 하는 이유.

**그래서 연결 하나하나를 별도의 "행"으로 빼낸다:**

```
post_tags
 post_id | tag_id
    1    |   5      ← 글1 - 지각
    1    |   8      ← 글1 - 교통   (글1에 태그 2개 = 행 2개)
    2    |   5      ← 글2 - 지각   (지각 태그를 글2도 공유)
```

각 행은 여전히 "post_id 하나 + tag_id 하나"(컬럼 제약 지킴)지만, **연결을 행으로 쌓으니** 양방향 다수가 표현된다. 복합 PK `(post_id, tag_id)`는 같은 글–태그 쌍 중복 삽입을 막는다.

> 한 줄: **컬럼은 한 칸에 하나뿐 → 다대다는 "연결을 행으로" 풀어야 한다 → 그 행들을 담는 게 중간 테이블.** (일대다는 자식 쪽 FK 한 칸이면 끝나 중간 테이블이 필요 없다 — 차이가 여기.)

## 3.2 `secondary`와 두 FK 다리

`relationship(secondary="post_tags")`는 post_tags를 *경유지*로 삼아 **양쪽 FK를 모두** 탄다. PostTag엔 FK가 둘:

```python
class PostTag(Base):
    __tablename__ = "post_tags"
    post_id: ... = mapped_column(ForeignKey("posts.id"), primary_key=True)  # posts 가리킴
    tag_id:  ... = mapped_column(ForeignKey("tags.id"),  primary_key=True)  # tags 가리킴
```

```
posts.id ──(post_tags.post_id)── post_tags ──(post_tags.tag_id)── tags.id
   └──────────── 가까운 다리 ─────────┘└─────────── 먼 다리 ──────────────┘
```

## 3.3 (질문) post → post_tags → tags 까지 어떻게 이어지나

**relationship이 길을 아는 게 아니라, FK가 지도다.** SQLAlchemy의 4단계 자동 조립:

1. **목표가 누구?** → 타입 주석 `list["Tag"]`를 보고 도착지는 **Tag**.
2. **경유지는?** → `secondary="post_tags"`라서 post_tags를 거침.
3. **가까운 다리** → 출발이 Post니까 post_tags의 FK 중 **posts를 가리키는 것**(`post_id`) → `posts.id == post_tags.post_id`.
4. **먼 다리** → 도착이 Tag니까 **tags를 가리키는 것**(`tag_id`) → `post_tags.tag_id == tags.id`.

→ `posts JOIN post_tags JOIN tags` 완성. **우리가 조인 컬럼을 안 적어도 되는 이유 = FK에 이미 다 적혀 있어서.**

**런타임 장면 — `post`(id=1)의 `post.tags`:**
1. 나의 id=1에서 출발.
2. 가까운 다리: post_tags에서 `post_id=1`인 행만 추림 → `(1,5)`,`(1,8)`.
3. 먼 다리: 그 행들의 `tag_id`=5,8 → tags로 건너감 → `tags.id IN (5,8)`.
4. 결과: `[Tag(5), Tag(8)]`. (`(2,5)`는 post_id가 2라 1단계에서 걸러짐.)

실제 SQL:
```sql
SELECT tags.* FROM tags
JOIN post_tags ON tags.id = post_tags.tag_id     -- 먼 다리
WHERE post_tags.post_id = :post_id               -- 가까운 다리
```

> 한 줄: **`secondary`는 "경유 테이블이 여기"라고만 알려주고, 실제 조인 컬럼은 그 테이블의 FK 두 개에서 읽는다.** FK 없으면 길을 못 찾아 에러.

## 3.4 (질문) 단방향 vs 양방향 — "어느 쪽에 써야 하나?"

> "여기도(author 옆) 추가해야 하는 거 아냐?" / "어느 쪽에 쓰든 상관 없다 이거야?"

- **연결(JOIN 자체)**: `secondary`가 post_tags 양다리로 Post↔Tag를 **이미 다 잇는다.** 어느 클래스에 써도 연결은 똑같이 작동.
- **하지만 속성은 "쓴 쪽에만" 생긴다**:
  - Post에 `tags` 선언 → `post.tags` **있음**, `tag.posts` **없음**
  - Tag에 `posts` 선언 → `tag.posts` **있음**, `post.tags` **없음**
- 그래서 "아무 데나"가 아니라 **"내가 따라갈 방향" 쪽에 쓴다.** 우리는 상세 응답에서 `post.tags`(글 → 그 글의 태그들)를 읽으니 **Post에** 썼고, `tag.posts`(태그 → 그 태그 글 목록)는 안 쓰니 Tag엔 안 단다.
- **양쪽 다 필요하면** `back_populates`로 묶는다:

```python
# Post 쪽
tags: Mapped[list["Tag"]] = relationship(secondary="post_tags", back_populates="posts")
# Tag 쪽
posts: Mapped[list["Post"]] = relationship(secondary="post_tags", back_populates="tags")
```

`back_populates`(서로 채워줌)를 걸면 `post.tags.append(tag)` 했을 때 메모리상 `tag.posts`도 자동 일관 유지. 안 묶으면 같은 관계를 독립된 두 길로 봐 한쪽 변경이 안 비친다.

> 한 줄: **연결은 양쪽 어디 써도 되지만, 속성은 "쓴 쪽"에만 생긴다 → 그래서 "쓸 방향"에 쓴다.** 지금은 단방향(`post.tags`)으로 충분.

(검증: `configure_mappers()` 통과, `Post.tags.property.secondary == post_tags`, target == `Tag`.)

---

# Part 4. Repository — DB를 아는 층 (SQL의 본판)

`검색·태그·페이징·정렬`은 라우터가 아니라 **여기 안에** 둔다(설계 원칙). 입출력은 ORM 객체/원시값이고 Pydantic 스키마는 안 쓴다.

## 4.1 (질문) SELECT — 행을 읽어오는 동사

- **정의**: SQL의 읽기 동사. "**어느 테이블**(FROM)의 **어떤 행**(WHERE)에서 **어떤 컬럼**(SELECT 절)을 가져와라". *선언형* = "어떻게 찾을지"는 안 적고 "무엇을 원하는지"만 적으면 DB가 실행계획을 짠다.
- **등장 배경**: 데이터는 테이블(행×열)에 쌓이고, 읽기/쓰기 동사가 나뉜다(INSERT 추가/UPDATE 수정/DELETE 삭제/SELECT 읽기).
- **런타임 장면**: `SELECT id, title FROM posts WHERE id=1;` → 조건 맞는 행 1개를 두 컬럼만 담아 **결과 집합**으로. 없으면 0행. SQLAlchemy `select(Post)`가 이 SELECT의 설계도.
- **1차 출처**: PostgreSQL *SQL Commands → SELECT*.

## 4.2 (질문) JOIN — 흩어진 테이블을 매칭해 옆으로 붙이기

- **정의**: 두 테이블의 행을, 조건(`ON`)이 맞는 것끼리 짝지어 한 줄로 이어 붙이는 연산.
- **등장 배경**: DB는 **정규화(normalization)**로 데이터를 쪼개 저장(글 본문 posts, 태그 이름 tags, 연결 post_tags) → 중복을 없애 일관성 확보(태그 이름이 글마다 복붙돼 있으면 이름 바꿀 때 지옥). 합쳐 보려면 다시 이어야 하고 그게 JOIN.
- **런타임 장면**:
```sql
SELECT tags.name FROM posts
JOIN post_tags ON posts.id = post_tags.post_id
JOIN tags      ON post_tags.tag_id = tags.id
WHERE posts.id = 1;
```
`ON` 조건 참인 쌍만 살아 한 줄로 붙는다.
- **INNER JOIN**(그냥 JOIN): 양쪽 다 맞는 것만 → 태그 없는 글은 빠짐.
- **LEFT JOIN**: 왼쪽(posts)은 다 남기고 짝 없으면 오른쪽을 `NULL`로 → "태그 없는 글도 포함"할 때.
- **1차 출처**: PostgreSQL *Queries → Joined Tables*.

## 4.3 (질문) 스칼라 — "행(튜플)"에서 "값 하나" 꺼내기

- **정의**: 스칼라(scalar) = "값 하나". SQLAlchemy `execute()`가 돌려주는 건 항상 **행(Row=튜플)들의 묶음**. `select(Post)`처럼 컬럼이 하나면 각 행은 `(Post,)`라는 **1칸 튜플**. *스칼라로 꺼낸다* = 튜플 껍데기를 벗겨 첫 칸(Post)만 집는 것.
- **등장 배경**: `execute(select(Post)).all()`은 `[(Post1,),(Post2,)]`처럼 1칸 튜플 리스트 → 매번 `row[0]` 까는 건 실수의 온상 → "스칼라(첫 컬럼)만 자동으로 까주는" 헬퍼:
  - `.scalars().all()` → `[Post1, Post2]` (리스트)
  - `.scalar_one_or_none()` → 0개면 `None`, 1개면 그 `Post`, 2개+면 에러
  - `.scalar_one()` → 정확히 1개 강제(0개도 에러)
- (참고: SQL에서 "스칼라"는 단일 값을 돌려주는 서브쿼리/식 — 예 `SUM(value)` 한 칸 — 을 가리키기도 함. score를 B안(매번 계산)으로 했다면 그 SUM이 스칼라였을 것. 우리는 A안이라 "결과에서 값 꺼내기" 의미만 씀.)
- **1차 출처**: SQLAlchemy *Result → scalars / scalar_one_or_none*.

## 4.4 async 조회 3박자 + (질문) `stmt` 뜻

```python
async def get_post(session: AsyncSession, post_id: int) -> Post | None:
    stmt = (
        select(Post)
        .where(Post.id == post_id)
        .options(selectinload(Post.tags))
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
```

- `stmt` = **statement**(명령문)의 흔한 줄임말. 여기선 SQL statement(SELECT … WHERE … 설계도). `query`라 써도 동작은 같지만 관례를 따르면 남이 빨리 읽는다. (비슷한 줄임: `conn`=connection, `col`=column, `cur`=cursor.)
- **3박자**: (a) `select(...).where(...)` = 쿼리 **설계도**(아직 DB 안 감), (b) `await session.execute(stmt)` = 설계도를 **DB에 보내 실행**(I/O라 `await`), (c) `.scalar_one_or_none()` = 결과에서 **Post 1개**(없으면 None → 라우터가 404).
- **런타임 장면**: `select(Post)`만 했을 땐 SQL이 안 나간다(설계도 생성뿐). `await session.execute(...)`를 만나야 비로소 SQL이 DB로 날아간다(`echo=True`면 콘솔에 찍힘).

## 4.5 async엔 lazy load가 없다 → 미리 당겨라(`selectinload`)

- **정의**: *lazy load*(지연 로딩) = `post.tags`를 **건드리는 순간** SQLAlchemy가 그제서야 추가 SQL을 몰래 날려 채우는 기본 동작. *eager load*(즉시 로딩) = 처음 조회할 때 관계까지 미리 같이 당겨오는 것. `selectinload(Post.tags)` = "tags를 별도 SELECT로 미리 채워라".
- **등장 배경**: 동기 ORM에선 lazy load가 편했지만 **async에선 "건드리는 순간 몰래 SQL"이 불가능**(그 순간 `await`를 못 걸어서). 그래서 async에선 *쓸 관계를 조회 시점에 명시적으로* 당겨와야 한다. 안 그러면 `post.tags` 읽을 때 `MissingGreenlet`/lazy-load 에러.
- **런타임 장면**: `selectinload(Post.tags)`를 붙이면 `SELECT posts...` 직후 `SELECT tags... WHERE post_tags.post_id IN (...)` 한 방을 더 자동으로 날려 `post.tags`를 채워둔다. 나중에 `PostOut`이 `post.tags`를 읽어도 추가 SQL 없이 이미 메모리에 있음. 빠뜨리면 직렬화 때 폭발.
- **1차 출처**: SQLAlchemy *Relationship Loading → selectinload*; *AsyncSession* "no lazy loading" 경고.

## 4.6 `list_posts` — 검색 `q` (ilike)

```python
async def list_posts(session, q=None, tag=None, cursor=None, limit=20) -> tuple[list[Post], str | None]:
    stmt = select(Post).options(selectinload(Post.tags)).order_by(Post.id.desc())
    if q:
        stmt = stmt.where(Post.title.ilike(f"%{q}%"))
    ...
```

- **ilike**: `LIKE` = SQL 패턴 매칭. `%`는 "아무 문자 0개 이상" 와일드카드라 `%지하철%` = "지하철 **포함**". `ILIKE`(I=insensitive)는 대소문자 무시(PostgreSQL).
- **등장 배경**: `=`는 완전일치만(`title='지하철'`은 "지하철이 멈췄어요"를 못 찾음). 검색창은 "포함"을 원하니 `LIKE %키워드%`, 대소문자 보장 못 하니 `ILIKE`.
- **동적 쿼리 빌드**: `stmt = stmt.where(...)`로 조건을 **있을 때만 재대입하며 쌓는다**. select 객체는 **불변** — `.where()`는 새 객체를 *반환*만 하므로 반드시 `stmt =`로 받아야 쌓인다.

## 4.7 (질문) 커서 페이징 — "페이지 번호"가 아니라 "책갈피"

> 처음에 "Page 4/5의 4"(페이지 번호)로 오해 → 그게 우리가 **안 쓰는** OFFSET 방식이라 헷갈림.

- **OFFSET 방식(안 씀)**: `OFFSET 100 LIMIT 20` = "앞 100개 세고 버리고 101~120번째". 뒤로 갈수록 느리고, 그 사이 새 글이 끼면 행이 밀려 **중복/누락**.
- **커서(keyset) 방식**: "내가 마지막으로 본 게 **id 9번**이야. 그 **다음부터** 줘." 페이지 번호가 아니라 **"어디서 멈췄는지 책갈피(마지막 id)"**를 들고 다닌다. `cursor="9"` = "9번째 페이지"가 아니라 "id 9에서 멈춤".

```python
    if cursor:
        stmt = stmt.where(Post.id < int(cursor))   # 내림차순이라 "다음"=더 작은 id
    stmt = stmt.limit(limit + 1)                   # +1 peek
    rows = (await session.execute(stmt)).scalars().all()
    has_more = len(rows) > limit
    items = rows[:limit]
    next_cursor = str(items[-1].id) if has_more else None
    return items, next_cursor
```

**진짜 숫자로 (글 6개 id=10..5, 페이지당 2개):**

요청 1(커서 없음):
```
WHERE 없음 → 10,9,8,7,6,5
LIMIT 2+1=3 → 실제 [10,9,8] 3개
```
- 3개 옴(`len=3 > limit=2`) → 다음 페이지 있다.
- 보여줄 건 앞 2개 `[10,9]`(3번째 8은 버림).
- 책갈피 = 보여준 마지막 id = `"9"` → `next_cursor="9"`.

요청 2(커서 "9"):
```
WHERE id < 9 → 8,7,6,5
LIMIT 3 → [8,7,6] → items [8,7], next "7"
```
마지막쯤 가져온 게 limit 이하면 `len > limit` 거짓 → `next_cursor=None` → 끝.

- **`Post.id < int(cursor)`의 `<`**: id를 **큰 순서(desc)**로 보여주니 "다음 글"은 더 작은 id. (오름차순이었으면 `>`.)
- **`limit + 1`은 사용자에게 1개 더 주는 게 아니다.** "다음 페이지 있나?"를 알려고 **한 개 몰래 떠보는(peek) 트릭**. 그 +1번째는 `rows[:limit]`로 잘라 버린다.
- `items[-1]` = 리스트의 마지막 원소(파이썬 `-1`=맨 뒤). 그 id가 다음 요청의 책갈피.

> 한 줄: **커서 = 마지막 본 id(책갈피). `id < cursor`로 그 다음부터, `limit+1`로 다음 페이지 유무만 peek.**

## 4.8 태그 필터 — 필터용 JOIN vs 로딩용 selectinload (다른 일)

```python
    if tag:
        stmt = stmt.join(Post.tags).where(Tag.slug == tag)
```

- 같은 `Post.tags`를 **두 목적**으로 쓴다:
  - `selectinload(Post.tags)` = **로딩**. 뽑힌 글들의 태그를 화면 표시용으로 **다 채워옴**. 어떤 글이 뽑힐지엔 영향 없음.
  - `.join(Post.tags)` = **필터**. post_tags 거쳐 tags와 이어 붙여 **그 태그 달린 글로 결과를 좁힘**. 표시할 태그를 채우는 게 아님.
- **slug로 비교하는 이유**: 프론트 `tagId`는 slug 문자열("지각"·"t1")이지 숫자 PK가 아니다(TagOut.id=slug 계약) → `Tag.slug == tag`.
- **검증으로 본 핵심 차이**: `tag='late'`로 걸러 `[여친과 싸움, 지하철 멈춤]`이 나왔는데, 여친 글의 태그 칩은 `['fight','late']` **둘 다** 표시됨 → "JOIN은 글을 고르고, selectinload는 그 글의 **전체** 태그를 채운다".

## 4.9 `create_post` — INSERT (add / flush / refresh)

```python
async def create_post(session, *, author_id, title, excuse_text, context, tags: list[Tag]) -> Post:
    post = Post(author_id=author_id, title=title, excuse_text=excuse_text, context=context, tags=tags)
    session.add(post)
    await session.flush()
    await session.refresh(post, ["created_at"])
    return post
```

- **`tags=tags`**: 관계 속성에 Tag 객체 리스트를 그대로 넘기면 SQLAlchemy가 **post_tags 연결 행까지 자동 INSERT**(중간 테이블을 직접 안 건드림). 다대다 관계의 실익.
- **`session.add(post)`**: "이 객체를 다음 flush 때 INSERT 대상에 올려라"(아직 SQL 안 감).
- **`flush`**: 보류된 INSERT를 **DB로 보냄**(트랜잭션 안, commit 전). 이때 DB가 `id`를 발급.
- **`refresh(post, ["created_at"])`**: `created_at`은 DB의 `server_default=now()`로 채워지므로, 그 값을 **다시 읽어와** 파이썬 객체에 반영(안 하면 `post.created_at`이 비어 PostOut 직렬화 때 문제).
- **`*` (키워드 전용 인수)**: `*` 뒤 인자는 **반드시 이름을 붙여** 호출해야 함(`author_id=...`) → 인자 순서 헷갈림 방지.
- **commit은 여기 없다**: repository는 flush까지만, **commit 결정은 service** (트랜잭션 경계는 위층이 쥔다).

---

# Part 5. Service — 규칙을 아는 층

```python
async def create(session: AsyncSession, body: PostCreate, author_id: int) -> Post:
    tags: list[Tag] = []
    if body.tag_ids:
        stmt = select(Tag).where(Tag.slug.in_(body.tag_ids))
        tags = list((await session.execute(stmt)).scalars().all())
    if len(tags) != len(set(body.tag_ids)):
        found = {t.slug for t in tags}
        missing = set(body.tag_ids) - found
        raise ValueError(f"unknown tags: {missing}")
    post = await create_post(session, author_id=author_id, title=body.title,
                             excuse_text=body.excuse_text, context=body.context, tags=tags)
    await session.commit()
    return post
```

## 5.1 역할 — "slug(외부 계약) → Tag 객체(내부)"

프론트는 태그를 **slug 문자열**(`tagIds: ["t1","t2"]`)로 보낸다. 하지만 DB 연결은 숫자 PK 기반의 `Tag` 객체가 필요 → service가 **slug를 실제 Tag로 해석(resolve)**한다. 이 "외부 표현 ↔ 내부 표현 변환"이 규칙 층의 전형적인 일.

## 5.2 `Tag.slug.in_(body.tag_ids)` — IN 절

- `in_([...])` = SQL `WHERE slug IN ('t1','t2')`. 여러 slug에 해당하는 Tag를 **한 방의 쿼리**로 가져온다(slug마다 따로 조회하면 N번 왕복).

## 5.3 없는 태그 검출 — 집합 차집합

- `set(body.tag_ids)` = 요청한 slug들(중복 제거), `{t.slug for t in tags}` = DB에서 실제 찾은 slug들.
- **개수가 다르면** 요청한 slug 중 DB에 없는 게 있다는 뜻 → `missing = 요청 - 찾음`(집합 차집합)으로 누락분을 뽑아 **`ValueError`**.
- 왜 service에서 `ValueError`(HTTP 아닌 일반 예외)를 던지나: service는 HTTP를 모른다(400을 직접 안다는 건 책임 침범). "잘못된 입력이다"라는 **규칙 위반**만 알리고, 그걸 몇 번 상태코드로 바꿀지는 router가 정한다.

## 5.4 commit 위치 — 트랜잭션 경계는 service가 쥔다

repository의 `create_post`는 flush까지만(연결 행·id 발급). **`session.commit()`은 service에서** 한 번 — "태그 해석 + post INSERT + 연결 행"이 **한 트랜잭션**으로 묶여 다 되거나 다 안 되거나(원자성). 이게 votes 토글에서 더 중요해진다(다음 세션).

---

# Part 6. Router — HTTP를 아는 층

```python
router = APIRouter()

@router.get("/posts")
async def list_posts(q=None, tag=None, cursor=None, session: AsyncSession = Depends(get_db)):
    items, next_cursor = await repo.list_posts(session, q=q, tag=tag, cursor=cursor)
    return {
        "items": [PostOut.model_validate(p).model_dump(by_alias=True) for p in items],
        "nextCursor": next_cursor,
    }

@router.get("/posts/{post_id}", response_model=PostOut, response_model_by_alias=True)
async def get_post(post_id: int, session: AsyncSession = Depends(get_db)):
    post = await repo.get_post(session, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="post not found")
    return post

@router.post("/posts", response_model=PostOut, response_model_by_alias=True, status_code=201)
async def create_post(body: PostCreate, session: AsyncSession = Depends(get_db)):
    try:
        post = await service.create(session, body, author_id=1)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return post
```

## 6.1 APIRouter + main 등록

- `APIRouter()` = 경로들을 한 묶음으로 모으는 작은 라우터. `main.py`에서 `app.include_router(router)`로 앱에 붙인다 → 파일을 기능별로 쪼개도(posts/comments/votes) main은 등록만.

## 6.2 `Depends(get_db)` — 의존성 주입

- **정의**: `Depends(get_db)`를 인자에 걸면, 요청마다 FastAPI가 `get_db`를 실행해 **DB 세션을 핸들러에 주입**한다. 핸들러는 "세션을 어디서 얻나"를 몰라도 된다.
- `get_db`는 `async with SessionLocal() as session: yield session` 형태(`yield` 앞=빌려줌, 뒤=반납). 요청이 끝나면 세션이 자동 정리된다.
- **런타임 장면**: `GET /posts` 요청 → FastAPI가 세션 하나 만들어 `session=`에 넣어줌 → 응답 후 닫음. 다음 요청은 새 세션.

## 6.3 `response_model` + `by_alias`

- `response_model=PostOut` = "이 핸들러가 뭘 return하든 **PostOut 모양으로 걸러서** 내보내라". ORM 객체를 return해도 `from_attributes`로 자동 변환되고, **스키마에 없는 필드(password 등)는 잘려 나간다**(누출 방지).
- `response_model_by_alias=True` = 그 직렬화를 **camelCase(alias)로** → `excuseText`/`createdAt`.

## 6.4 목록은 왜 `response_model` 대신 수동 `model_dump`인가

- `GET /posts`는 단일 PostOut이 아니라 `{items: [...], nextCursor}` **봉투(envelope) 모양**을 돌려준다 → `response_model=PostOut`로는 안 맞음. 그래서 각 글을 `PostOut.model_validate(p).model_dump(by_alias=True)`로 직접 변환해 리스트에 담고, `nextCursor`는 그대로 붙인다. (별도 래퍼 모델을 만들 수도 있지만 수동 dump도 충분.)

## 6.5 상태코드 — 201 / 404 / 400

- **POST 성공 = `status_code=201`(Created)**: "새 자원이 만들어졌다". (그냥 200이 아니라 201이 의미를 더 정확히.)
- **GET 없는 id = `404`(Not Found)**: repo가 `None`을 주면 `HTTPException(404)`. (repo는 None만 알고, "그게 404다"는 router가 안다 — 책임 분리.)
- **POST 잘못된 입력 = `400`(Bad Request)**: service가 던진 `ValueError`(없는 태그)를 `try/except`로 받아 `HTTPException(400, detail=...)`로 **번역**. → service의 규칙 위반이 HTTP 세계의 400으로 바뀌는 지점.
- (참고: 검증 실패=`422`는 Pydantic이 자동, 우리가 안 던짐.)

> 층별 에러 흐름 한 줄: **repo는 None/예외만, service는 규칙 위반(ValueError)만, router가 그걸 HTTP 상태코드로 번역한다.**

## 6.6 임시 의존 — `author_id=1` 하드코딩

- POST는 아직 로그인이 없어 `author_id=1`로 박아 둠 → DB에 `users` id=1 seed가 있어야 작성됨(DB 리셋하면 다시 넣어야 함). **B4에서 `get_current_user`로 교체**하면 소거.

---

# Part 7. 검토에서 잡은 버그들 (복습 포인트 — 같은 실수 반복 방지)

| # | 틀린 코드 | 고친 것 | 왜 |
|---|---|---|---|
| 1 | `Annotated[str, "본문"]` | (생 문자열 제거) | 읽는 도구가 없어 무시됨(헛수고). 설명은 `Field(description=)`로. |
| 2 | `Annotated[str, description="..."]` | `Annotated[str, Field(description="...")]` | 대괄호 `[]`(subscript)엔 값만. `key=value`는 `()` 함수호출에서만. |
| 3 | `result.one_or_none()` | `result.scalar_one_or_none()` | `one_or_none`은 `(Post,)` 튜플(Row)을 줌. `scalar_`가 껍데기를 까 Post를 줌(`-> Post` 타입과 일치). |
| 4 | `Post.id.__reduce__()` | `Post.id.desc()` | `__reduce__`는 피클용 던더(무관). 내림차순은 `desc()`. |
| 5 | `ilike(f"%{q}")` | `ilike(f"%{q}%")` | 뒤 `%` 빠지면 "끝나는" 것만 매칭. "포함"은 양쪽 `%`. |
| 6 | `.list().all()` | `.scalars().all()` | `.list()`는 Result에 없는 메서드(에러). 튜플 까서 리스트는 `.scalars()`. |
| 7 | `stmt - stmt.join(...)` | `stmt = stmt.join(...)` | `-`면 결과를 안 담아 필터가 **조용히 증발**(에러도 없이 전체 목록). `.where()/.join()`은 새 stmt를 반환 → 반드시 `stmt =`로 받기. |

> 반복 교훈: SQLAlchemy의 `.where()`·`.join()`·`.options()`·`.limit()`는 전부 **새 객체를 반환하는 불변 빌더** → `stmt =`로 다시 받지 않으면 사라진다.

---

# Part 8. 동작 검증 (진도 판정 = 실제로 돌아가는가)

실DB에 임시 데이터를 넣고 함수를 호출한 뒤 **롤백**(흔적 없음)으로 확인:

- **페이징**: `page1 ids=[6,5] next=5` → `page2(cursor=5) ids=[4,3] next=3` — 커서가 중복·누락 없이 연결.
- **검색**: `q='글3' → ['글3']` (ilike 부분일치).
- **단건**: `get_post(존재) → 제목`, `get_post(999999) → None`(→404 재료).
- **태그 필터**: `tag='late' → [여친과 싸움, 지하철 멈춤]`, 그 글의 태그 칩은 `['fight','late']` 전부 표시(JOIN 필터 ≠ selectinload 로딩).
- **REST 전체**: `/docs`에서 GET 목록·GET/{id}(404)·POST(201)·없는 태그(400) 확인.

검증 시 주의: 실행 venv는 **`backend/.venv`**(루트 `.venv`엔 greenlet 없음). 명령은 `backend/`에서.

---

## 이번 세션 핵심 한 줄 요약

> **요청 하나가 router(HTTP·상태코드) → service(slug→Tag 해석·검증·commit) → repository(select/JOIN/페이징/insert) → DB로 흐르고, 그 경계마다 Pydantic 스키마가 모양을 검증·변환(alias로 camel↔snake, validation_alias로 slug→id, from_attributes로 ORM→스키마, by_alias로 camel JSON)한다. 다대다 태그는 중간 테이블(post_tags)을 secondary로 잇고, 목록은 커서 페이징(책갈피+peek)으로 끊는다.**

## 핵심 대비표

| 헷갈리기 쉬운 짝 | 차이 |
|---|---|
| `alias` vs `validation_alias` | 전자=읽기·쓰기 동시 / 후자=읽는 이름만(쓰기는 필드명) — slug→id처럼 다를 때 |
| `from_attributes` vs `by_alias` | 전자=ORM 객체로 **채우기**(입력) / 후자=camel로 **내보내기**(출력) |
| `.join(rel)` vs `selectinload(rel)` | 전자=결과를 **좁히는** 필터 / 후자=뽑은 글의 관계를 **채우는** 로딩 |
| `scalar_one_or_none` vs `scalars().all()` | 까서 1개(or None) / 까서 리스트 |
| 커서 vs OFFSET 페이징 | 책갈피(마지막 id)부터 / 앞 N개 세고 버림(느림·중복) |
| flush vs commit | DB로 보냄(트랜잭션 안, id 발급) / 트랜잭션 확정(service가 결정) |
| 404 vs 400 vs 422 | 자원 없음 / 입력 규칙 위반(없는 태그) / 스키마 검증 실패(Pydantic 자동) |

## 다음 세션 예고 (B3 마저)

- **comments(평면)**: `post_id` FK로 글에 댓글 — repository/service/router 같은 패턴 반복.
- **votes 토글 트랜잭션 (이번 단계 주인공)**: `POST /posts/{id}/vote` body `{value:1|-1}`. 같은 값 재클릭=취소, 반대 값=전환. votes upsert/delete + `posts.score` ±갱신을 **한 트랜잭션**으로(commit 위치가 진짜 중요해지는 곳). 응답 `{score, myVote}`.
- 그 뒤 **B4**: 해싱/JWT/`get_current_user`(→ author_id 하드코딩 소거)/CORS/rate limit + 프론트 axios 연결.
