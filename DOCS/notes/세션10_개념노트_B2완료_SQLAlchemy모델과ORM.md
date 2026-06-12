# 세션 10 개념 노트 — B2 완료(SQLAlchemy 선언형 모델) + ORM의 큰 그림

> 대상 파일: `backend/app/models.py`(학습자 직접 작성)
> 진행분: **B2 완전 종료.** ERD → `schema.sql`(SQL, 드릴 1) → **`models.py`(SQLAlchemy 모델 6개, 드릴 2)** → 매퍼 검증(`configure_mappers()`) + DB `\dt` 6테이블 확인. 다음은 B3(CRUD+REST+투표).
> 이 노트의 새 주제: **선언형 매핑(DeclarativeBase·Mapped·mapped_column) / SQL↔모델 1:1 번역 / ForeignKey vs relationship / "행만 연결"과 "테이블 레벨 연결"의 차이 / relationship 이름 짓기(author) / relationship은 옵션 / `__table_args__`와 복합 PK·복합 UNIQUE / 튜플은 쉼표가 만든다 / `configure_mappers()` 결과 읽는 법 / ORM이 뭔가(PostgreSQL은 SQL만 안다, SQLAlchemy는 통역) / raw SQL vs ORM / relation=테이블 그 자체 / 관계형 DB의 종류 / 행 vs 열(스키마는 열을 고정, 데이터는 행으로 쌓임) / mapped_column 이름의 뜻 / 검토에서 잡은 버그 6개**.

---

## 먼저 붙잡을 전체 그림

지난 세션(9)에 `schema.sql`로 **DB에 직접 6테이블을 만들었다.** 이번 세션은 그 **똑같은 테이블을 파이썬 클래스로 한 번 더 그린다**(`models.py`). "또 만든다"가 아니라 **같은 테이블의 "파이썬 얼굴"을 붙이는 것** — 앞으로 앱 코드(B3 라우터·리포지토리)는 SQL 문자열 대신 이 클래스들(`Post`, `User`…)을 import해서 쿼리한다.

핵심 한 줄: **SQL의 `CREATE TABLE` 한 덩어리 = 파이썬 클래스 하나, SQL의 컬럼 한 줄 = 클래스 속성 하나.** 거의 단어만 바꾸는 1:1 번역이다.

그리고 이 세션 후반부는 "그래서 ORM이 도대체 뭔가"라는 근본 질문으로 내려갔다 — PostgreSQL·SQL·SQLAlchemy·행/열이 어떻게 얽히는지. 아래는 코드 흐름을 따라가며 등장한 모든 용어와 내가 던진 질문을 빠짐없이 푼다.

---

# Part 1. 선언형 매핑(Declarative Mapping) — 모델의 뼈대

## 1.1 declarative = "선언형"의 뜻

- **declarative(선언형)** = 절차(어떻게 하라)가 아니라 **결과 모양(무엇이다)** 을 적는 방식. "이 클래스는 이런 테이블이다"라고 **선언**만 하면, SQLAlchemy가 거기서 `CREATE TABLE` SQL을 알아서 만든다.
- 반대는 명령형(imperative) — 단계를 하나하나 시키는 방식. 모델 정의는 선언형이 자연스럽다(테이블은 "구조"라서).

## 1.2 세 가지 부품: DeclarativeBase · Mapped · mapped_column

```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):     # ① 모든 모델의 공통 부모
    pass

class User(Base):                # ② Base 상속 → 이 클래스가 "테이블"이 됨
    __tablename__ = "users"       # ③ 실제 테이블 이름(문자열)
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
#   └속성  └타입힌트   └DB 컬럼 정의
```

- **`class Base(DeclarativeBase)`** — **딱 한 번** 적는 공통 부모. 모든 모델이 이걸 상속한다. 이 `Base` 안에 모든 모델의 테이블 메타데이터가 **모인다**(나중에 `Base.metadata`로 전부 꺼냄).
- **`__tablename__`** — 그냥 SQL 테이블 이름 문자열. `CREATE TABLE users`의 `users`.
- **`mapped_column(...)`** — 컬럼 하나의 DB 옵션(`primary_key`·`nullable`·`unique`·타입 등)을 담는 함수. **이 한 줄 = 테이블의 열 하나.**
- **`Mapped[int]`** — "이 속성은 ORM이 관리하는, 파이썬에선 int인 컬럼이다"라는 타입 힌트. 에디터·타입 검사기가 `user.id`가 int임을 알게 해준다.

### "그래서 mapped_column인거야?" (질문)
**그렇다.** 이름을 뜯으면:
- **column** = 테이블의 **열**. `mapped_column(...)` 한 줄 = 열 하나 정의.
- **mapped** = "매핑된" — 그 열을 **파이썬 속성에 이어 붙인다**(ORM의 'M').
```python
title: Mapped[str] = mapped_column(Text, nullable=False)
#  ↑ 파이썬 속성(post.title)      ↑ DB의 열(posts.title) 정의
```
이 한 줄이 동시에 두 가지를 한다: **DB 쪽** `posts`에 `title TEXT NOT NULL` 열을 만들고, **파이썬 쪽** `post.title`로 그 값을 꺼내쓰게 한다. 그래서 클래스 안의 `mapped_column` 줄들을 모으면 **그게 곧 그 테이블의 열 목록**이다(검증 출력의 `posts | ['id','author_id','title',...]`가 바로 이것).

## 1.3 실제 런타임 장면 — 클래스가 곧 CREATE TABLE 청사진

`class User(Base): ...`를 **import하는 순간**, SQLAlchemy가 클래스를 훑어 내부에 테이블 메타데이터를 등록한다. 나중에 `Base.metadata.create_all()`을 부르면 **이 클래스들을 보고 `CREATE TABLE` SQL을 자동 생성**해 DB로 보낸다. 즉 클래스 = `CREATE TABLE`의 청사진.

## 1.4 SQL ↔ 모델 1:1 번역표 (User 예시)

| SQL (`schema.sql`) | 모델 (`models.py`) |
|---|---|
| `id BIGSERIAL PRIMARY KEY` | `mapped_column(BigInteger, primary_key=True)` |
| `username TEXT UNIQUE NOT NULL` | `mapped_column(Text, unique=True, nullable=False)` |
| `created_at TIMESTAMPTZ DEFAULT now()` | `mapped_column(server_default=func.now())` |

규칙: SQL `UNIQUE`=`unique=True`, `NOT NULL`=`nullable=False`, `DEFAULT now()`=`server_default=func.now()`. **거의 기계적 치환.** (`server_default` = DB가 기본값을 넣는다는 뜻. 파이썬이 아니라 DB 쪽에서 `now()`가 실행됨.)

---

# Part 2. ForeignKey vs relationship — 이번 세션의 핵심

## 2.1 두 개는 역할이 완전히 다르다

| | `ForeignKey("users.id")` | `relationship()` |
|---|---|---|
| 정체 | **DB에 실재하는 연결선**(컬럼 제약) | **파이썬 편의 속성**(컬럼 아님) |
| 만드는 것 | `posts`에 실제 컬럼/제약 | 아무 컬럼도 안 만듦 |
| 하는 일 | "이 값은 저 테이블에 실재해야" 강제(무결성) | FK를 따라가 객체를 꺼내주는 통로 |
| 필수? | **필수**(데이터 무결성) | **선택**(편할 때만) |

핵심 한 줄: **`ForeignKey`는 DB에 실재하는 연결선, `relationship`은 그 선을 파이썬에서 걷는 통로.** 둘은 짝이다.

## 2.2 "왜 table도 연결할까? 행만 하면 되지 않나?" (질문 — 가장 중요)

### "행만 연결" = 그냥 숫자만 적는 것
`posts` 행에 `author_id = 7`이라고 **숫자만** 적는 것. 이건 데이터일 뿐 — **아무도 그 7이 진짜 user인지 검사하지 않는다.** `author_id = 999`라고 적어도 통과한다(user 999가 없는데도). 그럼:
```
글은 있는데 글쓴이가 존재하지 않는 유령 행 → 나중에 post.author 꺼낼 때 터짐
```

### 테이블 레벨 연결(FK 제약)이 하는 일
`ForeignKey("users.id")`를 **테이블 정의에 한 번** 박아두면, DB가 **모든 INSERT/UPDATE마다** "이 author_id가 users에 실재하나?"를 자동 검사해 999 같은 건 그 자리에서 거절(`ForeignKeyViolation`)한다.

### 왜 "행"이 아니라 "테이블(스키마)"에 다나
- **행은 그냥 값일 뿐, 규칙을 품을 수 없다.** "author_id는 실재 user여야 한다"는 규칙은 *특정 한 행*이 아니라 **앞으로 들어올 모든 행**에 똑같이 적용돼야 한다 → 그래서 "이 테이블은 원래 이런 테이블"이라는 **설계도(스키마)** 에 한 번 선언한다.
- `ON DELETE CASCADE`(user 지우면 그 글도 같이 삭제)도 *행 하나*의 일이 아니라 **두 테이블 사이의 규칙**이라 테이블 레벨에서만 표현된다.

### 눈에 보이는 차이
| | 행만 (숫자만) | 테이블 FK |
|---|---|---|
| `author_id=999` INSERT | 그냥 들어감(쓰레기 데이터) | DB가 즉시 거절 |
| user 7 삭제 | 그 글들이 유령으로 남음 | CASCADE면 글도 같이 삭제 |
| 무결성 보증 | 앱 코드가 일일이 책임 | **DB가 보장** |

→ "행만 하면 된다"는 **앱이 절대 실수 안 한다**는 가정에서만 맞다. FK는 그 가정을 DB가 대신 강제해주는 안전장치.

## 2.3 relationship이 뭐냐 (질문 — 4종 정리)

**1. 정의** — DB 컬럼이 아니라, FK로 이어진 다른 테이블의 객체를 파이썬에서 꺼내쓰게 해주는 **ORM 전용 편의 속성.** `posts` 테이블에 **컬럼을 만들지 않는다.** 이미 있는 `author_id`(FK)를 따라가 `User` 객체를 채워주는 "통로".

**2. 등장 배경** — FK만 있으면 손에 쥐는 건 `author_id = 7`이라는 **숫자뿐.** 글쓴이 이름을 알려면 매번 `SELECT * FROM users WHERE id = 7`을 직접 짜야 했다. 이 반복 조회가 귀찮고 실수가 많아서 → "그 조회/JOIN을 **속성 접근 한 번**으로 감추자"가 relationship.

**3. 실제 런타임 장면**
```python
post.author_id        # 7                          ← 진짜 컬럼(숫자)
post.author           # <User id=7 username="kim"> ← relationship(객체)
post.author.username  # "kim"
```
`post.author`에 **접근하는 순간** SQLAlchemy가 뒤에서 `users` 조회 SQL을 몰래 날려 `User` 객체를 채워 돌려준다(코드엔 SQL이 안 보임). relationship을 **빼도 테이블·DB는 멀쩡** — 단지 `author_id`(숫자)만 쥐고 User는 직접 조회해야 할 뿐.

**4. 1차 출처** — SQLAlchemy 2.0 → *Relationship Configuration*.

## 2.4 "왜 author로 만들어?" (relationship 이름 짓기)

`author`는 **문법이 아니라 그냥 내가 고른 속성 이름.** `post.author`로 꺼내쓰겠다는 뜻일 뿐, 다른 이름이어도 동작한다. 관례:
- DB에 실재하는 컬럼은 `author_id` — **숫자 하나**(예: `7`).
- relationship에는 보통 **FK 컬럼 이름에서 `_id`만 뗀 이름**을 붙인다: `author_id`(숫자) ↔ `author`(객체). 짝이 눈에 보이게.
- 이름은 "글의 입장에서 이 User가 무슨 역할이냐"로 정한다. 글 입장에서 연결된 user = 글쓴이 → `author`. (votes는 `user_id`, comments는 `author_id` — 역할로 구분하면 읽기 좋다.)

## 2.5 "왜 comment에는 relationship 없어?" (질문 — relationship은 옵션)

답: **규칙이 아니라 선택.** relationship은 **언제나 선택사항**이다. FK가 있으면 원하는 만큼 통로를 달 수 있고, 안 달아도 테이블은 멀쩡하다. `Comment`도 FK가 둘(`post_id`, `author_id`)이라 통로를 둘 다 달 수 있다(`comment.post`, `comment.author`). 처음에 `Post`에만 `author`를 달아둔 건 "어떻게 생겼나" 보여주려는 **샘플 하나**였을 뿐.

**판단 기준** — "이 객체에서 저쪽 객체를 **자주 꺼내쓸 것 같나**":
- 댓글 보여줄 때 작성자 이름이 필요하다 → `comment.author` 있으면 편함 → 달자.
- 안 쓸 것 같으면 → `author_id`(숫자)만 두고 나중에 필요할 때 추가.

⚠️ 헷갈리지 말 것: **FK는 필수(무결성), relationship은 옵션(편의).** B2(테이블 생성) 단계에선 relationship을 **하나도 안 달아도 테이블은 똑같이 만들어진다.**

---

# Part 3. 테이블 레벨 제약 — `__table_args__`

## 3.1 `__table_args__`가 뭔가 (질문)

**한 컬럼에 못 붙는 테이블 전체 레벨 제약/인덱스를 모아두는 특수 속성.** `mapped_column(unique=True)`는 컬럼 하나짜리지만, "여러 컬럼 **조합**"에 거는 규칙(복합 UNIQUE·복합 PK·복합 인덱스)은 특정 컬럼에 못 달아서 여기 **튜플**로 넣는다.

```python
class Vote(Base):
    ...
    __table_args__ = (
        UniqueConstraint("user_id", "target_type", "target_id"),   # 1인 1표
    )
```

## 3.2 "이 세 개 짝이 유니크해야 하니까?" (질문 — 복합 UNIQUE)

**맞다.** 개별이 아니라 **조합**이 유일해야 한다는 뜻. `(user_id, target_type, target_id)` 묶음이 테이블에서 딱 한 번만.
- `user_id` = **누가**, `target_type` = **무엇에**('post'냐 'comment'냐), `target_id` = **그 중 몇 번.**
- 이 셋이 같은 행이 두 개면 = "같은 사람이 같은 대상에 두 번 투표" → DB가 거절(`UniqueViolation`). **이게 "1인 1표"의 정체.**

**왜 한 컬럼씩 유니크면 안 되나** (함정):
- `user_id`만 유니크 → 한 사람이 평생 딱 한 번만 투표 가능 ❌
- `target_id`만 유니크 → 한 글엔 딱 한 명만 투표 가능 ❌
- **조합** 유니크 → 한 사람이 여러 글에 투표 O, 단 **같은 글엔 한 번만** O ✅

런타임: user 7이 post 3에 +1 → 행 생성. 같은 user가 post 3에 또 투표 시도 → DB가 막음 → B3에서 이걸 잡아 "취소(삭제)/전환(value 변경)"으로 토글 구현. (`target_type`을 같이 넣는 이유 — post의 3번과 comment의 3번을 구별. 다형 투표.)

## 3.3 복합 PK vs 복합 UNIQUE — 왜 처리 방식이 다른가

`post_tags`는 **복합 PK**, `votes`는 **복합 UNIQUE**인데, 모델에선 처리가 다르다:

```python
class PostTag(Base):                              # 복합 PK → 컬럼에 직접
    __tablename__ = "post_tags"
    post_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True)
    tag_id:  Mapped[int] = mapped_column(BigInteger, ForeignKey("tags.id",  ondelete="CASCADE"), primary_key=True)
    # __table_args__ 필요 없음

class Vote(Base):                                 # 복합 UNIQUE → __table_args__
    __table_args__ = (UniqueConstraint("user_id", "target_type", "target_id"),)
```

- **복합 PK**는 그냥 **두 컬럼에 각각 `primary_key=True`** 를 주면 SQLAlchemy가 자동으로 "둘을 묶은 PK 하나"로 인식한다 → `__table_args__` 불필요.
- **복합 UNIQUE**는 컬럼에 직접 붙일 문법이 없다(컬럼 단위 `unique=True`는 단독 유니크라 의미가 다름) → **테이블 레벨 `UniqueConstraint`** 로 가야 한다.
- 검증 출력에서 확인됨: `post_tags | PK ['post_id', 'tag_id']` ← 복합 PK 정상.

## 3.4 튜플은 괄호가 아니라 쉼표가 만든다 (검토에서 터진 버그)

```python
__table_args__ = (UniqueConstraint(...))      # ❌ 그냥 괄호 → 값 = UniqueConstraint 1개
__table_args__ = (UniqueConstraint(...),)     # ✅ 쉼표 → 튜플
```
에러 메시지: `__table_args__ value must be a tuple`. 파이썬에서 `(x)`는 그냥 x, **`(x,)`라야 튜플.** 괄호가 아니라 **쉼표가** 튜플을 만든다. `__table_args__`는 항상 튜플(또는 dict)이어야 해서, 원소가 하나뿐이라도 끝에 `,`가 필수.

---

# Part 4. 완성한 `backend/app/models.py`

```python
from datetime import datetime
from sqlalchemy import ForeignKey, BigInteger, Text, Integer, SmallInteger, JSON, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class Tag(Base):
    __tablename__ = "tags"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    slug: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, unique=True, nullable=False)


class Post(Base):
    __tablename__ = "posts"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    author_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    excuse_text: Mapped[str] = mapped_column(Text, nullable=False)
    score: Mapped[int] = mapped_column(default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    context: Mapped[dict | None] = mapped_column(JSON, nullable=True)       # JSONB
    verdict: Mapped[str | None] = mapped_column(Text, nullable=True)
    credibility: Mapped[int | None] = mapped_column(Integer, nullable=True)

    author: Mapped["User"] = relationship()


class Comment(Base):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    post_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    author_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    post: Mapped[Post] = relationship()
    author: Mapped[User] = relationship()


class Vote(Base):
    __tablename__ = "votes"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    target_type: Mapped[str] = mapped_column(Text, nullable=False)
    target_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    value: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    __table_args__ = (UniqueConstraint("user_id", "target_type", "target_id"),)


class PostTag(Base):
    __tablename__ = "post_tags"
    post_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True)
    tag_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)
```

> 참고: `Post.context`는 schema.sql에선 `JSONB`인데 모델에선 `JSON`으로 적었다. SQLAlchemy의 `JSON`은 PostgreSQL에서 자동으로 적절히 처리되지만, JSONB의 인덱싱/연산을 정확히 쓰려면 나중에 `from sqlalchemy.dialects.postgresql import JSONB`로 바꾸는 게 더 정확하다(지금은 저장만 하므로 무방).

---

# Part 5. 검토에서 잡은 버그 6개 (직접 다 고침 — 복습 포인트)

내가 작성 → 코치 검토 → 직접 수정 사이클로 잡은 버그들. **전부 "돌리면 터지는" 실전 오류**라 패턴을 기억해둘 것.

| # | 버그 | 증상 | 교훈 |
|---|---|---|---|
| 1 | `ForeignKey("Posts.id")` 대문자 | 매퍼 설정 시 "그런 테이블 없음" | **FK 인자는 클래스명이 아니라 `__tablename__`(실제 테이블 이름, 소문자)** |
| 2 | `author_id: Mapped[User] = relationship()` | FK 컬럼이 **사라짐** | 같은 클래스에 같은 속성명 2번 → 파이썬이 **나중 것으로 덮어씀.** FK 컬럼 `author_id`와 relationship `author`는 **이름이 달라야** |
| 3 | `Post`에 `context/verdict/credibility` 누락 | schema.sql과 불일치 | 모델은 **테이블을 똑같이 복제**해야. 빠지면 `create_all` 결과가 어긋남 |
| 4 | `mapped_column(JSON, nullable=True) (JSONB)` | import 시 `NameError` | 주석 `(JSONB)`를 코드로 붙임 → 파이썬이 "결과를 JSONB로 호출"로 읽음. 주석은 `#` |
| 5 | `__table_args__ = (UniqueConstraint(...))` | `must be a tuple` | **쉼표가 튜플을 만든다** → `(...,)` |
| 6 | `ondelete="cascade"` 소문자 | (동작은 함) | 다른 곳과 통일 안 됨 → 스타일 일관성. `"CASCADE"` |

핵심 교훈: **"OK 떴다"가 나올 때까지 매퍼 검증을 돌려라.** 매퍼는 import 시점에 모든 모델을 훑어 FK·relationship·제약의 일관성을 검사하므로, 위 버그들이 거기서 줄줄이 잡혔다.

---

# Part 6. 검증 — `configure_mappers()` 결과 읽는 법

## 6.1 검증 명령 (반드시 `backend/`에서)

```bash
cd backend && .venv/bin/python -c "
from app.models import Base
from sqlalchemy.orm import configure_mappers
configure_mappers()
print('OK: 매퍼 설정 통과')
for t in Base.metadata.sorted_tables:
    print(' -', t.name, '|', [c.name for c in t.columns])
"
```

### "ModuleNotFoundError: No module named 'app'" (이번에 겪음)
- 프로젝트 루트(`AI로 진화하기 %`)에서 돌리면 `app`을 못 찾는다. `app` 패키지는 `backend/` **안**에 있다.
- `app`이 패키지로 잡히려면 **그 부모 폴더인 `backend`가 현재 위치**여야 한다 → 항상 `cd backend` 후 실행. (`python -m app.db`, `app.config` import도 전부 동일.)

## 6.2 출력을 어떻게 해석하나 (질문: "이 테스트 결과 어떻게 해석했는데?")

```
OK: 매퍼 설정 통과
 - tags | ['id', 'slug', 'name']
 - users | [...]
 - posts | ['id','author_id','title','excuse_text','score','created_at','context','verdict','credibility']
 - votes | [...]
 - comments | [...]
 - post_tags | PK ['post_id', 'tag_id'] | ['post_id', 'tag_id']
```

판정은 **두 단계**:

**① `OK` 줄이 떴나? → 기계 검증 (가장 중요)**
- 그 print는 `configure_mappers()` **다음**에 있다. FK나 relationship에 문제가 있으면 `configure_mappers()`에서 **예외가 터져 그 print까지 못 간다**(앞서 `__table_args__` 튜플 에러 때처럼 중간에 죽음).
- 즉 "OK가 보인다 = import도 됐고, 6개 모델의 FK 대상·relationship 짝이 전부 말이 된다"를 SQLAlchemy가 보증한 것.

**② 컬럼 목록이 schema.sql과 같나? → 사람 대조**
- 각 `CREATE TABLE`의 컬럼과 출력 리스트를 테이블별로 맞춰본다(`posts`는 9개 전부 있는지 등). 순서는 무관 — **존재 여부**만.

**③ 안 보이는 게 정상인 것**
- `author`·`post` 같은 **relationship은 목록에 없다**(컬럼이 아니므로). 만약 떴다면 오히려 버그.
- 처음엔 `post_tags`가 **안 보였다** → 일부러 안 만들었으니 예상대로. "5개만 떴다 = 6번째가 빠졌다"는 신호.

## 6.3 이 검증이 확인 안 해주는 것 (한계)
`configure_mappers()`는 "파이썬/매핑이 일관되나"만 본다. **실제 DB에 테이블이 진짜 만들어지나, schema.sql과 타입·제약까지 100% 같나**는 별개 → 그건 DB에서 `\dt`/`\d posts`로 확인.

## 6.4 DB 실재 확인 (B2 완료 판정)
```bash
docker exec alibai-db psql -U alibai -d alibai -c "\dt"
# → comments / post_tags / posts / tags / users / votes (6 rows)
```
6테이블 모두 실재 → **B2 완전 종료.** (테이블은 지난 세션 `schema.sql`로 이미 생성됨. 모델은 그 테이블에 일치하는 "파이썬 얼굴"을 붙인 것.)

---

# Part 7. ORM의 큰 그림 — 근본 질문들

## 7.1 "postgres도 sql을 써? 왜 sql alchemy를 썼어?" (질문)

### PostgreSQL은 SQL **밖에** 못 알아듣는다
DB에 들어올 수 있는 명령은 **오직 SQL 문자열**(`SELECT * FROM posts WHERE id=3`)뿐. 파이썬 객체나 SQLAlchemy 모델을 DB가 직접 이해하는 게 아니다.

### SQLAlchemy는 SQL을 **대체**하는 게 아니라 **만들어준다**
ORM은 SQL을 없애는 게 아니라, **파이썬 코드 → SQL 문자열로 번역**해서 DB에 보내는 **중간 통역**이다.
```
파이썬:  session.get(Post, 3)
   ↓  (SQLAlchemy가 번역)
SQL:    SELECT * FROM posts WHERE id = 3
   ↓  (PostgreSQL에 전송)
DB:     실행
```
- 증거: `db.py`에서 준 `echo=True` → 모델로 쿼리하면 **터미널에 진짜 SQL이 찍힌다.** ORM을 써도 바닥엔 항상 SQL이 흐른다.

### 왜 raw SQL 문자열 대신 ORM을 쓰나 (실익)
| 손 SQL 문자열 | SQLAlchemy ORM |
|---|---|
| `"SELECT * FROM psots"` 오타 → **실행해야** 터짐 | `Post` 클래스 → 에디터가 오타 즉시 잡음 |
| 결과가 튜플 `(3, 7, "제목")` → 인덱스로 꺼냄 | `post.title`처럼 **속성**으로 꺼냄 |
| 글+태그 조회 = JOIN 직접 작성 | `post.tags`로 통로 접근 |
| 입력값 이어붙이면 **SQL 인젝션** 위험 | 파라미터 자동 바인딩(안전) |
| DB 바뀌면 방언 차이 직접 대응 | 상당 부분 추상화 |
→ **파이썬답게·안전하게·오타를 일찍** 다루려고 한 겹 얹은 것. 성능 극한이 필요한 일부 쿼리는 여전히 raw SQL을 섞기도 한다.

### 그럼 왜 `schema.sql`도 따로 만들었나 (둘 다 만든 이유)
**학습 설계**(드릴 1 vs 2): 드릴 1(schema.sql)은 SQL을 손으로 쳐 "DB가 실제로 뭘 받나"를 날것으로 봤고, 드릴 2(models.py)는 그걸 ORM으로 옮기며 "SQL↔파이썬 대응"을 눈으로 익혔다. **앞으로 앱 코드(B3)는 `models.py`만 쓴다.** schema.sql은 학습용 + 사람이 읽는 참고본. (실무에선 보통 모델을 진실의 원천으로 두고 `create_all`이나 Alembic 마이그레이션으로 테이블을 만든다.)

## 7.2 "테이블을 객체로 그리고 .으로 꺼내는 게 ORM이네" (질문 — 정확)

이름 그대로 **ORM = Object-Relational Mapping**:
- **Object(객체)** = 파이썬 세계 (`Post` 클래스, `post.title`)
- **Relational(관계형)** = DB 세계 (테이블·행·컬럼)
- **Mapping(매핑)** = 둘을 1:1로 이어줌

| DB (관계형) | 파이썬 (객체) |
|---|---|
| 테이블 `posts` | 클래스 `Post` |
| 행 1개 | 객체 1개(`post`) |
| 컬럼 `title` | 속성 `post.title` |
| FK로 이어진 다른 행 | `post.author`(relationship 통로) |

→ SQL 결과 `(3, 7, "지각함")` 같은 숫자·튜플 대신, `post.title`·`post.author.username`처럼 **파이썬 객체.속성**으로 다루게 된다. **딱 하나 잊지 말 것: `.`으로 꺼내는 그 순간에도 바닥에선 SQLAlchemy가 SQL을 만들어 DB에 보낸다. ORM은 SQL을 숨기지, 없애지 않는다.**

## 7.3 "Relational(관계형)이 왜 DB인데?" (질문 — 흔한 오해 교정)

### relation = FK 관계가 아니라 **테이블 그 자체**
많은 사람이 "relational = 테이블끼리 FK로 **관계** 맺어서"라고 오해한다. **틀렸다.**
- **relation(릴레이션)** 은 수학(집합론) 용어로 **"표(테이블) 그 자체"** 를 가리킨다. 행(row)들의 집합 = 하나의 relation.
- 1970년 E.F. Codd의 **관계형 모델(relational model)** 에서 온 말 — "데이터를 표(relation) 형태로 조직하자"는 이론.
- 그래서 **relation = 테이블 1개.** (`\dt` 쳤을 때 `List of relations`라고 나온 게 바로 이것 — PostgreSQL이 테이블을 relation이라 부른다.)
- 즉 "관계형"은 테이블들 사이의 FK 연결이 아니라 **데이터가 표(relation)로 저장된다**는 뜻. FK 관계는 그 위에 얹은 부가 기능일 뿐.

### 모든 DB가 관계형인 건 아니다
"DB = 관계형"이 아니라 **관계형은 DB의 한 종류**:
| 종류 | 데이터 모양 | 예 |
|---|---|---|
| **관계형(Relational)** | 표(테이블·행·컬럼) | **PostgreSQL**, MySQL, SQLite |
| 문서(Document) | JSON 덩어리 | MongoDB |
| 키-값(Key-Value) | 딕셔너리 | Redis |
| 그래프(Graph) | 노드·엣지 | Neo4j |
- 우리가 쓰는 **PostgreSQL이 관계형 DB**라 데이터가 `posts`·`users` 같은 **표**로 저장된다. 그래서 ORM의 'R'이 "관계형(=표 기반 DB)"을 가리킨다.
- MongoDB(문서형)였다면 ORM이 아니라 **ODM(Object-Document Mapping)** 이라 불렀을 것.

## 7.4 행 vs 열 — 스키마는 열을 고정, 데이터는 행으로 쌓인다 (질문: "데이터가 들어가면 열 레이블로 바뀌나?")

오해를 바로잡음 — **정반대다.**

### 스키마 = 열(컬럼) 정의 = 표의 머리(헤더)
우리가 만든 스키마(`schema.sql`/`models.py`)는 **열 이름·타입을 고정**한 것. 즉 표의 **머리(헤더)**:
```
posts (스키마 = 이 헤더를 고정)
┌──────┬───────────┬──────────┬─────────────┬───────┐
│ id   │ author_id │ title    │ excuse_text │ score │   ← 열(컬럼) = 스키마가 정한 고정 라벨
├──────┼───────────┼──────────┼─────────────┼───────┤
```

### 데이터가 들어가면 = 행(로우)이 한 줄씩 쌓인다 (열은 그대로 고정)
```
posts (INSERT 후)
┌──────┬───────────┬──────────────┬──────────────────┬───────┐
│ id   │ author_id │ title        │ excuse_text      │ score │   ← 열은 그대로
├──────┼───────────┼──────────────┼──────────────────┼───────┤
│ 1    │ 7         │ 지각 변명    │ 차가 막혀서...   │ 3     │   ← 행 1개 = 글 1개
│ 2    │ 7         │ 숙제 변명    │ 개가 먹어서...   │ 0     │   ← 행 2개
│ 3    │ 12        │ 결석 변명    │ 아파서...        │ 5     │   ← 행 3개
└──────┴───────────┴──────────────┴──────────────────┴───────┘
```

| | 정체 | 변하나? |
|---|---|---|
| **열(컬럼)** | 스키마가 정한 **고정 라벨**(id, title, score…) | 스키마 안 바꾸면 **고정** |
| **행(로우)** | 실제 데이터 1건 = **글 1개** | 데이터 넣을 때마다 **계속 늘어남** |

- "글을 하나 작성한다" = `posts`에 **행 하나 추가**(INSERT). 그 행 안에서 `title`·`excuse_text` 같은 **열은 정해진 칸**이고 거기에 값이 채워진다.
- ORM 대응: **행 1개 = 객체 1개(`post`), 열 = 객체의 속성(`post.title`).**
```python
post = Post(title="지각 변명", excuse_text="차가 막혀서", author_id=7)
session.add(post)   # → posts 테이블에 "행 하나" INSERT
```
- **열이 바뀌는 건** 데이터 넣을 때가 아니라 `ALTER TABLE`로 **스키마 자체를 바꿀 때**뿐.

---

## 이번 세션 핵심 한 줄 요약

- **선언형 모델:** 클래스=테이블, `mapped_column` 한 줄=열 하나, `Mapped[타입]`=파이썬 쪽 얼굴. SQL↔모델은 1:1 번역(`UNIQUE`=`unique=True` 등).
- **ForeignKey vs relationship:** FK=DB에 실재하는 연결선(필수, 무결성 강제), relationship=파이썬에서 객체를 꺼내는 통로(옵션, 컬럼 아님). "행만 연결"은 검사가 없어 유령 행을 막지 못함 → 규칙은 행이 아니라 스키마(테이블 레벨)에 단다.
- **테이블 레벨 제약:** 복합 PK는 `primary_key=True`를 두 컬럼에, 복합 UNIQUE는 `__table_args__`의 `UniqueConstraint`로. 튜플은 쉼표가 만든다(`(...,)`).
- **검증:** `configure_mappers()`가 OK면 매핑 일관성 통과(기계), 컬럼 목록 대조로 schema.sql 일치 확인(사람), `\dt`로 DB 실재 확인. → **B2 종료.**
- **ORM 본질:** PostgreSQL은 SQL만 안다. SQLAlchemy는 파이썬→SQL 통역(echo=True로 보임). ORM=Object↔Relational 매핑이고, relation=테이블 그 자체. 스키마=열 고정, 데이터=행으로 쌓임.

## 다음 세션 예고 (B3)
CRUD + REST + 투표. `schemas.py`(Pydantic 요청/응답, camelCase↔snake_case alias) → `router → service → repository` 흐름. 검색·태그·페이징·정렬은 repository 내부에. 투표 토글은 votes의 묶음 UNIQUE 위에서 "재클릭=취소/반대=전환"을 트랜잭션으로 구현. 1차 출처: FastAPI *Request Body / Response Model*, *Handling Errors*.
