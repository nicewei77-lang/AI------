# 세션 9 개념 노트 — B1 마무리(db.py·DB 연결) + B2(데이터 모델링: ERD→SQL→테이블 생성)

> 대상 파일: `backend/app/db.py`(학습자 직접), `backend/db/schema.sql`(학습자 직접), `backend/db/ALIBAI.drawio`·`ALIBAI.svg`(ERD, 학습자 직접)
> 진행분: **B1 거의 완료** — `db.py`(엔진/세션/get_db) 작성. ⚠️남은 수정 2개: import·`class_`의 `session`→`AsyncSession`, `SELECT 1` 핑 검증. **B2 핵심 완료** — ERD(draw.io 6테이블) → SQL(`schema.sql`) → **Docker Postgres에 6테이블 실제 생성 확인(`\dt`)**. 남음: SQLAlchemy 모델로 옮기기(드릴 2).
> 이 노트의 새 주제: **드라이버 vs 엔진 vs 세션 / 연결 풀(FD·소켓) / async가 서버에서 의미하는 것 / 세션·트랜잭션·commit / `async_sessionmaker`(호출가능 객체) / 제너레이터·`yield`·`get_db` / `with`의 진짜 의미(컨텍스트 매니저) / DB 설계 5단계 / ERD 관계 3종(1:N·N:M·다형) / PK·FK / 정규화·비정규화 / 까마귀발 표기 / PostgreSQL 타입·제약 메뉴 / CREATE TABLE·REFERENCES / 복합 PK 자동 NOT NULL / `\d` 출력 읽기**.

---

## 먼저 붙잡을 전체 그림

이번 세션은 두 덩어리다.

1. **B1 db.py — "앱이 DB와 대화하는 통로"를 코드로 깐다.** 핵심 한 줄: **엔진(앱당 1개, 연결 풀) → 요청마다 `get_db`가 세션 1개를 빌려 `yield`로 핸들러에 주입 → 핸들러가 SQL을 보냄 → `commit`으로 확정 → 세션 닫혀 연결 반납.**
2. **B2 데이터 모델링 — "무슨 테이블에 무슨 칼럼/관계"를 설계하고 실제로 만든다.** 핵심 흐름: **요구사항 → ERD(관계 그림) → SQL(`CREATE TABLE`) → DB에 실행 → 테이블 생성.** 관계는 단 3종(1:N, N:M, 다형)뿐이고, 전부 "어느 칼럼이 어느 테이블을 가리키나(FK)"로 환원된다.

아래는 이 두 흐름을 따라가며, 등장한 모든 용어와 내가 던진 질문을 빠짐없이 푼다.

---

# Part 1. B1 — `db.py`: DB 연결 (엔진·세션·get_db)

## 1.0 완성한 코드 (`backend/app/db.py`)

```python
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,          # ⚠️ 처음엔 `session`(소문자)으로 잘못 적었음 — 아래 1.6 참고
)
from sqlalchemy import text
from app.config import settings

# (1) 앱당 1개: 연결 풀 관리자. echo=True면 실행 SQL이 로그에 찍힘(학습용)
engine = create_async_engine(settings.database_url, echo=True)

# (2)+(3) 호출하면 AsyncSession을 생성하는 객체(인자를 미리 박아둠)
SessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# (5) 요청마다 DB 세션을 빌려주고 끝나면 반납하는 의존성
async def get_db():
    async with SessionLocal() as session:
        yield session
```

## 1.1 세 층을 구분하라 — 드라이버 vs 엔진 vs 세션 (질문: "asyncpg는 pool engine?")

**아니다. 세 층은 서로 다르다.**

| 층 | 정체 | 역할 | 비유 |
|---|---|---|---|
| **asyncpg** | **드라이버** | Postgres 와이어 프로토콜을 소켓으로 말하는 저수준 라이브러리. SQL 문자열을 바이트로 직렬화해 소켓에 쓰고, 응답 바이트를 파싱 | 전화기 |
| **engine** (`create_async_engine`) | **풀 관리자** | asyncpg 연결을 여러 개 만들어 풀에 담고 빌려줌/회수함. 앱당 1개 | 전화기 여러 대 관리하는 교환대 |
| **session** (`AsyncSession`) | **작업 단위** | engine한테 연결 하나 빌려 "이번 요청의 DB 작업"을 담음. 요청당 1개 | 통화 한 건 |

- asyncpg에도 `asyncpg.create_pool()`이 있지만 **우리는 직접 안 쓴다.** SQLAlchemy engine이 그 풀링을 대신한다.
- 정확한 그림: **"engine이 asyncpg를 드라이버로 깔고 앉아 풀링한다."**
- URL `postgresql+asyncpg://...`에서 `+asyncpg`를 보고 SQLAlchemy가 "asyncpg 드라이버로 비동기 연결을 열어라"를 고른다.

## 1.2 연결 풀 = FD 테이블의 소켓들 (질문: "연결 몇 개 미리 열어둔다 = FD table?")

**맞다.** DB 연결 1개 = **TCP 소켓 1개** = 프로세스 **FD 테이블의 엔트리 1개**.

```
프로세스 FD 테이블
 fd 3 → socket → 127.0.0.1:5432  (idle, 풀에 대기)
 fd 4 → socket → 127.0.0.1:5432  (요청 A가 빌려감)
 fd 5 → socket → 127.0.0.1:5432  (idle)
```

- 매 요청마다 소켓을 새로 `connect()`하면 **TCP 3-way handshake + Postgres 인증 핸드셰이크**를 매번 다시 해야 해서 느리다(수십 ms).
- 그래서 연결 몇 개를 **미리 열어 풀에 담아두고**, 요청이 끝나면 `close()` 안 하고 **풀에 반납** → 다음 요청이 같은 fd(이미 TCP·인증 끝난 소켓)를 재사용한다.
- "엔진을 앱당 1개만, 모듈 최상단에 둔다"는 이유가 이것 — 요청마다 엔진을 새로 만들면 풀의 의미가 사라진다.

## 1.3 async가 서버에서 의미하는 것

DB 쿼리는 네트워크 I/O라 결과가 올 때까지 수 ms~수십 ms를 **기다린다.**

- **동기(sync) 서버:** 기다리는 동안 워커 스레드 하나가 통째로 묶여 다른 요청을 못 받는다.
- **async/await:** 기다리는 지점(`await`)에서 손을 놓고 다른 요청을 처리하다가, 결과가 오면 돌아온다 → **같은 자원으로 더 많은 동시 요청**을 소화.

그래서 엔진(`create_async_engine`)·세션(`AsyncSession`)·쿼리(`await session.execute(...)`)를 전부 **async 계통으로 통일**한다. `config.py`의 URL을 일부러 `+asyncpg`로 둔 이유.

## 1.4 `create_async_engine` 사용법

```python
engine = create_async_engine(<url 문자열>, <옵션들...>)
```

- 어디서: `from sqlalchemy.ext.asyncio import create_async_engine` (동기용은 `sqlalchemy.create_engine`).
- 반환값: `AsyncEngine` 인스턴스 1개. **모듈 최상단 변수에 담아 앱 전체가 공유.**
- 1번째 인자(필수): DB URL 문자열 → `settings.database_url` (config가 `.env`에서 읽어둔 값).
- 옵션:
  - `echo=True` → 실행되는 SQL을 콘솔에 로그로 찍음(학습 단계엔 켜둠, 운영엔 끔).
  - (참고) `pool_size`, `max_overflow` → 풀 크기. 안 주면 기본값.

## 1.5 세션이란 무엇인가 (질문: "세션 이해 못함 / 인스턴스인데 왜 세션? / 트랜잭션·insert/update가 뭐지?")

### 먼저 "여러 insert/update"
DB에 보내는 명령 한 줄이 SQL **statement**다.
```sql
INSERT INTO posts (...) VALUES (...);   -- 행 추가
UPDATE votes SET value = -1 WHERE ...;   -- 행 수정
```
한 요청이 이런 statement를 **여러 줄** 보낼 수 있다. 예: 투표하면 ① `votes`에 INSERT, ② `posts.score`를 UPDATE → 한 요청에 2개.

### 트랜잭션 = "전부 성공 아니면 전부 취소"인 묶음
①만 되고 ②에서 죽으면 **깨진 상태**(투표는 됐는데 점수 안 오름). 그래서 묶는다:
```sql
BEGIN;            -- 묶음 시작
  INSERT ...;     -- ①
  UPDATE ...;     -- ②
COMMIT;           -- 둘 다 확정. 도중 에러면 ROLLBACK → 둘 다 없던 일로
```
이 `BEGIN...COMMIT` 묶음이 **트랜잭션**. "원자적(atomic)" = 쪼개지지 않는다 = 다 되거나 다 안 되거나.

### 그래서 세션 = 이번 요청의 DB 작업을 담는 객체
세션은 세 가지를 들고 있다:
1. **빌린 연결**(FD 하나)
2. **아직 안 확정한 변경들의 버퍼** — `session.add(post)` 하면 바로 DB로 안 쏘고 모아둠
3. **트랜잭션 상태** — `commit()` 할 때까지 BEGIN 상태

### "인스턴스인데 왜 세션이라 부르나?"
**인스턴스 맞다.** `SessionLocal()`을 호출하면 `AsyncSession` **클래스의 인스턴스**가 나온다. 다만 그 인스턴스가 하는 역할이 "DB와의 한 차례 대화 세션(연결 빌림→작업→commit→반납)"이라서 클래스 이름이 `Session`인 것. `Socket` 클래스의 인스턴스를 "소켓"이라 부르는 것과 같다. **인스턴스 vs 세션은 대립 개념이 아니다.**

## 1.6 commit이란 (질문: "commit이 뭐야?")

트랜잭션 안의 변경은 **확정 전까지 "보류(pending)"** — 나한테만 보이고, 다른 연결엔 안 보이고, 디스크에 영구 반영도 안 된 상태.

- **`commit()`** = "이 트랜잭션의 모든 변경을 **영구 확정**" → 디스크 반영 + 다른 요청도 보게 됨. (`COMMIT;`)
- **`rollback()`** = "다 취소, 시작 전으로." (`ROLLBACK;`)
- C로 치면 임시 버퍼에 쓰다가 `fsync`로 진짜 파일에 박는 그 순간이 commit. commit 안 하고 세션 닫으면 변경은 버려진다(자동 rollback).

## 1.7 `async_sessionmaker` = 호출가능 객체 (질문: "세션 메이커 인스턴스 / 주석 뭐라 쓰지?")

`SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)`

- `async_sessionmaker`는 **클래스**다. 이 줄은 그 클래스의 **인스턴스 하나를 만들고, 생성 인자(engine·class_·expire_on_commit)를 그 안에 저장**한다.
- 그 인스턴스는 `__call__`이 정의돼 있어 **자체를 함수처럼 호출**할 수 있다. `SessionLocal()`을 호출하면 `__call__`이 돌아 **저장해둔 인자로 새 `AsyncSession`을 생성·반환**한다.
- 기능적으로 `functools.partial(AsyncSession, bind=engine, expire_on_commit=False)`와 같다 — **인자를 미리 묶어둔 `AsyncSession` 생성자.**
- **핵심 구분:** 이 줄(`= async_sessionmaker(...)`)은 **공장 만들기**, `SessionLocal()` 호출이 **세션 만들기**. 세션은 `get_db`에서 호출할 때 비로소 생긴다.
- 주석 예: `# 호출하면 AsyncSession을 생성하는 객체. 인자를 미리 박아둠 (세션은 SessionLocal() 호출 때 생성)`

### `class_=AsyncSession`
공장이 찍어낼 세션의 클래스를 비동기용 `AsyncSession`으로 지정. (⚠️ 처음에 `session`(소문자)으로 적었는데, 이건 클래스가 아니라 `sqlalchemy.ext.asyncio.session` **모듈**이라 틀림. 에러는 안 나지만 모듈이 들어가 세션 생성 시 깨진다. 둘 다 `AsyncSession`으로 고쳐야 함.)

### `expire_on_commit=False`
기본값 `True`면 commit 직후 그 객체 속성에 접근할 때 DB를 다시 조회(lazy refresh)하는데, async에서는 그 자동 재조회가 사고를 내기 쉬워 **끄는 게 정석.** "commit 후에도 방금 다룬 객체 값을 만료시키지 말라."

## 1.8 `get_db` — 의존성 주입 통로 (질문: "get_db 뭐하는 함수? 제너레이터가 뭐야?")

### get_db가 하는 일 (한 문장)
> **`Depends(get_db)`라고 쓴 라우터마다, 요청 시작에 DB 세션을 빌려주고 응답 후 자동 반납해주는 의존성 함수.** 라우터는 "세션 주세요"만 선언하고, 열고 닫는 잡일은 get_db가 대신 한다. **get_db 자체는 DB 작업을 하지 않는다.**

### 없으면 어떻게 되나
get_db가 없으면 모든 라우터가 `session = SessionLocal()` → `try/finally: session.close()`를 복붙해야 한다. 하나라도 `close()`를 빠뜨리면 연결(FD)이 풀로 안 돌아와 **풀 고갈**. 그 잡일을 한 곳에 모은 게 get_db.

### 제너레이터 = 중간에 멈췄다 재개되는 함수
보통 함수는 `return`하면 끝나고 지역변수가 사라진다. 제너레이터는 `yield`에서 **값을 내보내고 그 자리에서 일시정지**, 나중에 **그 줄 다음부터 재개**한다(상태 보존).
```python
def g():
    print("준비")
    yield 42          # 멈추고 42 내보냄
    print("정리")     # 재개되면 여기부터
it = g(); x = next(it)   # "준비", x=42, yield에서 멈춤
next(it)                 # 재개 → "정리"
```
C로 치면 호출 사이에 지역 상태를 들고 이어서 도는 **수동 상태머신/코루틴**을 언어가 공짜로 만들어 주는 것.

### get_db가 제너레이터인 이유
세션은 "요청 전에 열고 → 핸들러가 쓰고 → 요청 후에 닫아야" 한다. 이 "쓰는 중간"에 핸들러를 끼워야 하니 `yield`로 둘로 쪼갠다:
```python
async def get_db():
    async with SessionLocal() as session:   # ── 준비: 세션 염
        yield session                        # ── 핸들러에 넘기고 멈춤
    #   (핸들러 끝나면 여기 재개 → async with 빠져나가며 세션 닫힘) ── 정리
```
FastAPI 입장의 시간순:
1. 요청 도착 → `get_db()` 실행, `yield`까지 → 세션 객체 받음
2. 그 세션을 라우터의 `db` 매개변수에 **주입(inject)** → 핸들러 실행
3. 핸들러 끝 → `get_db` **재개** → `async with` 닫힘 → 세션 풀에 반납

라우터 사용 예:
```python
async def create_post(body: NewPost, db = Depends(get_db)):
    db.add(...); await db.commit()
```
"통로"란 get_db가 yield로 세션을 바깥(FastAPI)에 건네고, 닫기까지 책임지는 **양방향 파이프**라는 뜻.

## 1.9 `with`의 진짜 의미 (질문: "with 원래 그런 뜻 아닌데? / async with가 뭔데")

### `with`는 "자동 닫기"가 본뜻이 아니다
영어 그대로 **"~을 끼고/가지고"**. `with open(f) as f:` = "파일 f를 끼고 이 블록을 해라." 핵심은 **"블록에 들어갈 때·나올 때 정해진 동작을 자동 실행"**하는 것. "닫기"는 파일의 경우일 뿐.

### 메커니즘: 컨텍스트 매니저 (`__enter__`/`__exit__`)
```python
class 뭔가:
    def __enter__(self):   # with 진입 시 자동 호출 → 리턴값이 as x로
        ...준비...; return self
    def __exit__(self, ...):  # with 탈출 시 자동 호출 (예외 나도 호출)
        ...정리...
```
`with 뭔가() as x:` → 진입 시 `__enter__()`, 탈출 시(정상이든 예외든) `__exit__()`. 객체마다 그 안에 뭘 넣었느냐로 동작이 달라진다:

| 객체 | `__enter__`(준비) | `__exit__`(정리) |
|---|---|---|
| 파일 | 열기 | **닫기** |
| 락(Lock) | 잠그기 | 풀기 |
| DB 세션 | 트랜잭션/연결 준비 | **연결 반납** |

### `with`의 정체
> **`try/finally`(반드시 정리)를 객체에 위임해 한 줄로 쓰는 문법.**
원래는 `f=open(); try: ... finally: f.close()`를 매번 써야 했는데, 그 패턴을 객체에 묶은 것.

### `async with`
세션은 **열고/닫는 동작 자체가 await 해야 하는 비동기 작업**(소켓 주고받기)이라, `__enter__`/`__exit__`의 async 버전인 `__aenter__`/`__aexit__`를 쓴다. 그래서 `with`가 아니라 `async with`. 정리: **`with`=자동 정리, `async with`=비동기용 자동 정리.**

## 1.10 db.py 1차 출처 메모

`create_async_engine`/`async_sessionmaker`/`AsyncSession`/`get_db`는 전부 **SQLAlchemy** API라, 우리 `공식문서_레퍼런스.md`의 3축(MDN·FastAPI·PostgreSQL)에 **없다.** 진짜 출처:
- SQLAlchemy — asyncio 확장: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- FastAPI — SQL (Relational) Databases: https://fastapi.tiangolo.com/tutorial/sql-databases/ (SQLModel 기준이라 순수 SQLAlchemy와 살짝 다름)

---

# Part 2. B2 — 데이터 모델링 (ERD → SQL → 테이블)

## 2.1 DB 설계 5단계 레시피 (질문: "어떻게 설계하냐 / 5단계가 뭐지?")

1. **명사(thing) 찾기 → 테이블 후보.** "유저가 글을 쓰고, 글에 댓글·태그가 붙고, 투표한다" → user, post, comment, tag, vote. (동사는 보통 관계, 명사가 테이블)
2. **각 명사의 속성 → 칼럼.** "글 하나 저장하려면 뭘 알아야 하나?" → title, excuse_text, created_at. (프론트 타입 필드 ≈ 칼럼)
3. **명사끼리 관계 따지기 → 1:N? N:M?** 양방향으로 묻는다: "유저 1명이 글 여럿? 예 / 글 1개가 유저 여럿? 아니" → 1:N. "글 1개에 태그 여럿? 예 / 태그 1개에 글 여럿? 예" → N:M.
4. **관계를 칼럼으로 구현 → FK 위치.** 1:N=N쪽에 FK / N:M=중간 테이블 / 다형=target_type+target_id.
5. **각 칼럼에 제약.** PK? NOT NULL? UNIQUE? FK 동작(ON DELETE)?
- **관통 원칙 — 정규화:** 같은 데이터를 두 곳에 복사하지 마라(id로 가리켜라).

## 2.2 설계 워크플로 & 도구 (질문: "무슨 툴 쓰냐 / draw.io에서 코드 변환되냐?")

```
① ERD 그리기  →  ② DDL(SQL) 작성  →  ③ DB에 실행  →  ④ 확인  →  ⑤ 모델 코드로
   다이어그램 툴    CREATE TABLE       psql/클라이언트   \dt        SQLAlchemy
```

- **ERD 도구:** dbdiagram.io(텍스트→다이어그램+SQL Export, 입문 추천), draw.io(자유 그리기), DBeaver/pgAdmin(GUI+ERD 역생성).
- **중요:** **draw.io는 그림 도구지 코드 변환 도구가 아니다.** 표→SQL export는 빈약. 진짜 다이어그램↔SQL이 되는 건 **dbdiagram.io**(Export → PostgreSQL)나 DBeaver.
- **그래도 지금은 자동 변환을 안 쓴다** — 드릴 목표가 `CREATE TABLE`을 손으로 쳐 문법을 익히는 것. draw.io 그림은 "SQL 칠 때 보고 베낄 설계도" 역할.

## 2.3 PostgreSQL 데이터 타입 메뉴

| 종류 | 타입 | 언제 |
|---|---|---|
| 정수 | `INTEGER`(=INT,4B), `BIGINT`(8B), `SMALLINT`(2B) | 투표값은 SMALLINT |
| 자동증가 PK | `SERIAL`, `BIGSERIAL` | id. 넣을 때마다 1,2,3 자동 |
| 문자열 | `TEXT`(무제한), `VARCHAR(n)` | PG는 TEXT가 성능손해 없음 → 거의 TEXT |
| 불리언 | `BOOLEAN` | 참/거짓 |
| 시간 | `TIMESTAMPTZ`(타임존 포함), `DATE`, `TIME` | created_at은 TIMESTAMPTZ |
| 실수 | `NUMERIC(p,s)`(정확), `REAL`/`DOUBLE` | 돈은 NUMERIC |
| JSON | `JSONB`(이진, 인덱싱 가능), `JSON` | 유동적 덩어리(context) |
| UUID | `UUID` | 랜덤 식별자 |
| (AI단계) | `VECTOR`(pgvector) | 임베딩 |

**노하우:** 문자열은 거의 `TEXT`, id는 `BIGSERIAL`, 시간은 `TIMESTAMPTZ`로 기본 깔면 90% 맞다.

## 2.4 제약(constraint) 메뉴

| 제약 | 뜻 | 예 |
|---|---|---|
| `PRIMARY KEY` | 행 식별, 중복·NULL 불가 | id |
| `NOT NULL` | 비울 수 없음 | title |
| `UNIQUE` | 값 중복 불가 | email, tag.slug |
| `REFERENCES 테이블(칼럼)` | FK(다른 테이블 가리킴) | author_id REFERENCES users(id) |
| `ON DELETE CASCADE` | 가리킨 게 지워지면 같이 삭제 | 작성자 탈퇴→글 삭제 |
| `DEFAULT 값` | 안 주면 기본값 | created_at DEFAULT now() |
| `CHECK (조건)` | 값 범위 검사 | value CHECK (value IN (-1,1)) |

## 2.5 PK (Primary Key)

행 하나를 유일하게 식별하는 칸. 중복·NULL 불가, 보통 `id BIGSERIAL`로 자동증가. C의 배열 인덱스/고유 주소 같은 것.

## 2.6 FK (Foreign Key) — 핵심 (질문 다발: "FK가 뭐였지 / 왜 N쪽 / 왜 user.id에 / 왜 post.id 아니라 author_id에 / 그 행에 연결하는 이유 / 보통 그렇게 해?")

### 정의
> **FK = 이 테이블의 한 칼럼이, 다른 테이블의 PK 값을 담아서 그 행을 가리키는 것.**

`posts.author_id`에 `1`이 들어있으면 = "이 글의 작성자는 `users.id=1`인 행". **남의 테이블 행을 id로 콕 찍어 가리키는 포인터.** C의 포인터와 같은데, **DB가 "가리키는 곳이 진짜 있는지" 강제로 검사**해준다는 게 차이.

데이터로:
```
users                  posts
 id │ username          id │ title    │ author_id
  1 │ wei      ◄────      10 │ 늦잠     │    1     ──┐
  2 │ minji             11 │ 차막힘   │    1     ──┤ 다 wei(1) 가리킴
                        12 │ 알람     │    2     (minji)
```

### FK가 강제하는 것
1. **참조 무결성** — 없는 걸 가리키면 거부. `INSERT ... author_id=99` → users에 99 없으면 ❌. 포인터가 쓰레기 주소를 못 가리키게 보장.
2. **`ON DELETE CASCADE`** — 가리킨 대상이 삭제되면 같이 삭제. wei(1) 탈퇴 → wei의 글 10·11도 자동 삭제.

### "왜 FK를 N쪽에 두나" (1:N)
users(1)─posts(N)에서, posts에 `author_id` 하나 두면 글이 많아도 각자 "내 작성자 1명"을 가리키면 끝. 반대로 users에 "내 글 목록"을 두려면 한 칸에 여러 id를 담아야 하는데 **관계형 DB 한 칸엔 값 하나**라 불가능. → **"여러 개" 가진 쪽(N)이 "하나"를 가리킨다. 항상 FK는 N쪽.**

### "왜 users.id에 연결? 왜 posts.id가 아니라 author_id에서?"
선의 양 끝 = **가리키는 칼럼(FK) ↔ 가리켜지는 칼럼(PK)**.
- `author_id`(posts) = 남을 가리키는 칼럼(안에 users의 id 값을 담음) → **선의 시작.**
- `users.id` = 가리켜지는 대상 → **선의 끝.**
- `posts.id`는 **이 글 자신의 번호(자기 PK)**라 작성자와 무관 → 이 선과 안 붙음.
```
posts 10번:  id=10(자기 번호),  author_id=1(users.id=1 가리킴=FK=선의 시작)
```

### "행 단위로 연결하는 게 보통인가?"
두 스타일 다 통용:
- **테이블끼리만 연결**(개략 ERD): 박스 대 박스.
- **행(칼럼)끼리 연결**(상세/물리 ERD): FK 칼럼 행 ↔ PK 칼럼 행. dbdiagram.io·draw.io가 미는 방식.
- **FK가 여러 개일 때 행 단위가 결정적.** comments는 post_id·author_id 둘 다 FK라, 행 단위로 이어야 어느 칼럼이 어디로 가는지 보인다. votes·post_tags도 동일 → **행 단위 추천.** (단 너무 지저분하면 일부는 테이블끼리. "읽기 쉬우면 장땡".)

## 2.7 관계 ① 1:N (일대다)

한 쪽이 여럿 거느림. 예: users→posts(유저 1명이 글 N개). **N쪽(posts)에 1쪽의 id를 FK로.** (`posts.author_id → users.id`)

## 2.8 관계 ② N:M (다대다) — 중간 테이블 + 복합 PK (질문: "중간 테이블 만들면 되잖아? / posts에 tag 들어가야 하는 거 아냐?")

양쪽 다 여럿. 예: posts↔tags(글 1개에 태그 여럿, 태그 1개에 글 여럿).

### 왜 본체에 FK를 못 넣나
- posts에 `tag_id` 한 칸 → 글의 태그 여러 개를 못 담음. `"1,2"`로 우겨넣으면 FK 검사 불가 + 검색 지옥. ❌
- tags에 `post_id`도 마찬가지. ❌

### 정답: 중간 테이블 `post_tags`
"어느 글에 어느 태그" 연결만 한 줄씩 기록:
```
post_tags
 post_id │ tag_id
   10    │   1     글10 ─ 지각
   10    │   2     글10 ─ 수면
   12    │   1     글12 ─ 지각
```
- **N:M을 1:N 두 개로 쪼갬:** `posts ←1:N─ post_tags ─N:1→ tags`. 중간 테이블이 FK 2개를 가짐.
- **posts엔 tag 칼럼이 없다 (중요).** 태그 정보는 전부 post_tags에. posts에 tag_id를 넣으면 "글에 태그 딱 1개"가 돼 N:M이 깨진다. → **여럿이면 중간 테이블, 하나면 직접 FK.** (author는 1명이라 posts에 author_id 직접 FK.)

### 복합 PK (composite PK)
post_tags의 PK는 `post_id` 혼자도 `tag_id` 혼자도 중복 가능 → **둘을 묶어서 PK:**
```sql
PRIMARY KEY (post_id, tag_id)
```
"(글, 태그) 짝이 유일" = **같은 글에 같은 태그 두 번 금지**(중복 방지 자동). draw.io에선 두 행 키 칸에 둘 다 `PK`로 표시. "PK 두 개"가 아니라 **"두 칼럼을 묶은 PK 하나"**.

## 2.9 관계 ③ 다형(polymorphic) — votes (질문: "중간 테이블로 안 되나?")

투표는 글에도 댓글에도 달림. FK 하나로 "posts일 수도 comments일 수도"를 못 가리킨다(일반 FK는 한 테이블 고정).

### 다형 패턴: `target_type` + `target_id`
```
votes
 user_id │ target_type │ target_id │ value
    1    │ 'post'      │    10     │  +1     wei → 글10에 +1
    1    │ 'comment'   │    55     │  -1     wei → 댓글55에 -1
```
- `target_type` = 어느 테이블('post'|'comment'), `target_id` = 그 테이블의 id. **둘을 합쳐 읽어야** 대상이 정해짐 → "다형(여러 형을 받음)".
- **대가:** `target_id`에 진짜 FK(`REFERENCES`)를 못 건다 → **DB가 참조 무결성을 자동 검사 못 함**(앱이 책임). 다형의 트레이드오프.

### N:M 중간 테이블로는 왜 안 되나
중간 테이블은 "정해진 두 테이블 사이의 N:M"용. votes는 "한 표가 posts냐 comments냐 **택1**"이라 N:M이 아니다. 중간 테이블을 넣어도 "글용이냐 댓글용이냐"를 어딘가 적어야 해 문제가 안 사라진다.

### "진짜 FK 쓰자"의 정석 해법 3개
- **① 다형(채택)**: target_type+target_id. 단순, FK 무결성 없음.
- **② 배타적 FK(exclusive arc)**: `post_id`(FK→posts,NULL) + `comment_id`(FK→comments,NULL) + `CHECK`(정확히 하나만 채움). 진짜 FK 무결성 유지, 대상 종류 늘면 칼럼 늘어남.
- **③ 분리 테이블**: post_votes/comment_votes 따로. 로직 두 벌.
- ALIBAI는 ①로 확정(로직 한곳·단순·확장 여지). 학습상 다형 패턴 경험.

### 1인 1표 = 묶음 UNIQUE
```sql
UNIQUE (user_id, target_type, target_id)
```
"(유저, 대상종류, 대상id) 조합이 유일" → 같은 사람이 같은 대상에 한 줄만. **⚠️ 함정:** 세 칼럼에 **각각** UNIQUE를 걸면 안 된다 — user_id 단독 UNIQUE면 "한 유저 평생 1표", target_type 단독이면 "'post' 행 하나만" 같은 재앙. 반드시 **세 칼럼을 묶은 하나의 UNIQUE.** (복합 PK처럼 테이블 레벨 제약.)
- **칼럼 칸 UNIQUE = "이 칼럼 하나가 유일", 묶음 UNIQUE = "이 칼럼들 조합이 유일".**

## 2.10 정규화 vs 비정규화 — score (질문: "score가 뭔데?")

`score` = 글의 투표 합산 순점수(net = up−down). Reddit식 추천/비추천.

- **① votes에서 매번 SUM(정규화):** `SELECT SUM(value) FROM votes WHERE ...`. 항상 정확·중복 없음. 단 목록 조회마다 SUM이라 느려질 수 있음.
- **② posts.score에 저장(비정규화):** 칼럼에 두고 투표 때마다 갱신. 조회 빠름. 단 votes와 score를 **한 트랜잭션으로 일치**시켜야 함(B3).
- **비정규화** = 원칙(중복 금지)을 어기고, **성능을 위해 일부러 중복 허용.** 게시판은 읽기가 쓰기보다 잦아 ② 채택. `score INT NOT NULL DEFAULT 0`.

## 2.11 JSONB — context

프론트 `ExcuseContext`(date/location/time/route)를 **한 칸에 통째로**. `JSONB` = JSON을 이진으로 저장(인덱싱·검색 가능). context로 검색·정렬 안 하면 칼럼 4개로 쪼개기보다 JSONB 한 칸이 단순. NULL 허용(글 쓸 때 비어 있을 수 있음).

## 2.12 draw.io 사용법 (질문: 행추가 / 표 레이블 / 밑에 타입 칸)

- ER 테이블 도형: 검색창에 `table` → 머리글+행 있는 표 드래그. (안 보이면 More Shapes → Software → Entity Relation)
- **표 레이블(머리글) = 테이블 이름**(필수). `CREATE TABLE users`의 users가 됨.
- **행 = 칼럼.** 행 추가: 행 복사(Ctrl+C/V) / 우클릭 Insert Row / Arrange 패널.
- **행 안의 3칸:** ①왼쪽=키 표시(PK/FK, 선택) ②가운데=칼럼명 ③오른쪽=타입(필수). 각 칸 더블클릭 편집.
- 관계선: 도형 가장자리 연결점에서 드래그해 상대 행에 놓음.

## 2.13 까마귀발(crow's foot) 표기 (질문: 동그라미 / "하나 있다"는 어느 것?)

선 끝마다 기호 2개 = **(최소, 최대)**. 안쪽=최소, 바깥쪽=최대.

| 기호 | 뜻 |
|---|---|
| 막대 `\|` | 1 (one) |
| 까마귀발 `<` | 여럿 (many) |
| 동그라미 `○` | **0 (선택적, optional)** |

조합:
| 끝 모양 | 뜻 |
|---|---|
| `\|\|` | 정확히 1 (one and only one) ← "하나 있다(필수 하나)"는 보통 이것 |
| `○\|` | 0 또는 1 |
| `\|<` | 1 이상 |
| `○<` | 0 이상 |

- **동그라미 = 0 가능(없어도 됨)**, **막대 = 최소 1(필수)**, **까마귀발 = 여럿.**
- **NOT NULL과 직결:** FK가 NOT NULL → "필수 1"(막대), NULL 허용 → "0 또는"(동그라미). 그림의 막대/동그라미가 곧 NOT NULL 유무.
- "author_id 값이 하나인데 왜 posts쪽 까마귀발?" → 까마귀발의 "여럿"은 **행이 여럿**이란 뜻. "wei 한 명에 글 10·11·12 여러 행이 매달림" → posts가 many. author_id 값이 여러 개란 뜻이 아니다.
- 우리 적용 예: `users ‖────○< posts` (글마다 작성자 정확히 1명 / 유저당 글 0개 이상).

## 2.14 CREATE TABLE 문법 & "선은 어떻게?" (질문: 열 구분 / 선 표현)

```sql
CREATE TABLE 테이블명 (
    칼럼명  타입  제약,       -- 인라인 제약: PRIMARY KEY, NOT NULL, UNIQUE, DEFAULT now(), REFERENCES ... ON DELETE CASCADE
    ...,
    테이블레벨_제약           -- 복합 PK: PRIMARY KEY (a,b) / 묶음 UNIQUE: UNIQUE (a,b,c)
);
```
- **열(칼럼) 구분:** SQL 파서는 공백 종류(탭/스페이스/줄바꿈) 안 가린다. 관례는 **스페이스로 정렬**(탭은 에디터마다 폭 달라 정렬 깨짐). 칼럼 하나당 한 줄 + 끝에 쉼표(마지막 줄은 쉼표 없음).
- **다이어그램의 "선"은 별도 문장이 아니라 FK 칼럼의 `REFERENCES` 절이다:**
```sql
author_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE
```
`REFERENCES users(id)` = 선의 화살표 끝, `ON DELETE CASCADE` = 선의 삭제 규칙. **선 하나 = FK 칼럼 하나의 REFERENCES 절.**
- **카디널리티(까마귀발/막대/동그라미)는 SQL에 직접 안 적는다.** `NOT NULL`·`UNIQUE`·FK 조합에서 자연히 따라온다.

## 2.15 테이블 생성 순서 = FK 의존성

FK는 가리켜지는 테이블이 **먼저** 있어야 한다:
```
users → tags → posts → comments → post_tags → votes
(FK없음)(FK없음)(→users)(→posts,users)(→posts,tags)(→users)
```

## 2.16 완성한 `backend/db/schema.sql`

```sql
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE tags (
    id BIGSERIAL PRIMARY KEY,
    slug TEXT UNIQUE NOT NULL,          -- API Tag.id로 노출('t1' 등)
    name TEXT UNIQUE NOT NULL           -- 프론트 Tag.label에 해당
);

CREATE TABLE posts (
    id BIGSERIAL PRIMARY KEY,
    author_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    excuse_text TEXT NOT NULL,          -- 프론트 excuseText (B3 alias)
    context JSONB,                      -- ExcuseContext 통째로, NULL 허용
    verdict TEXT NULL,                  -- AI 판결, 지금은 비움
    credibility INT NULL,               -- AI 신뢰도, 지금은 비움
    score INT NOT NULL DEFAULT 0,       -- 투표 합산(비정규화), 투표 때 갱신(B3)
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE comments (
    id BIGSERIAL PRIMARY KEY,
    post_id BIGINT NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    author_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    body TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE post_tags (
    post_id BIGINT REFERENCES posts(id) ON DELETE CASCADE,
    tag_id BIGINT REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (post_id, tag_id)        -- 복합 PK → 둘 다 자동 NOT NULL
);

CREATE TABLE votes (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    target_type TEXT NOT NULL,           -- 'post' | 'comment'
    target_id BIGINT NOT NULL,           -- 다형: REFERENCES 안 붙임
    value SMALLINT NOT NULL,             -- +1 / -1
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (user_id, target_type, target_id)   -- 1인 1표(묶음)
);
```

## 2.17 실행 & 확인 (psql)

Docker 컨테이너 안 Postgres에 SQL을 흘려넣음:
```bash
docker compose exec -T db psql -U alibai -d alibai < backend/db/schema.sql
# → CREATE TABLE 6번 출력 = 6개 생성 성공
```
확인:
```bash
docker compose exec -T db psql -U alibai -d alibai -c "\dt"        # 테이블 목록
docker compose exec -T db psql -U alibai -d alibai -c "\d posts"   # posts 구조
```
결과: comments/post_tags/posts/tags/users/votes 6개 생성 확인.

## 2.18 복합 PK는 왜 자동 NOT NULL? (질문)

**SQL 표준: PRIMARY KEY 칼럼은 NULL을 가질 수 없다.** PK로 지정하면 DB가 그 칼럼들에 NOT NULL을 자동으로 붙인다(복합이면 묶인 모든 칼럼).
- 이유: PK 임무는 "각 행 유일 식별" → 값을 비교해 같다/다르다 판정 가능해야 함. 근데 NULL은 "모름"이라 `NULL = NULL`이 참이 아니라 `unknown` → 비교 불가 → 식별자 역할 불가. 그래서 PK 칼럼은 NULL 금지.
- **대조:** posts.author_id는 PK가 아니라 그냥 FK → 자동 NOT NULL 안 됨 → 직접 `NOT NULL` 붙여야 "작성자 없는 글" 막힘. **PK=자동 NOT NULL, 일반 FK=직접 붙여야.**
- 증거: `post_tags`엔 NOT NULL을 한 번도 안 썼는데 `\d post_tags`에서 post_id·tag_id 둘 다 `not null`로 나옴(`post_tags_pkey PRIMARY KEY (post_id, tag_id)` 때문).

## 2.19 `\d posts` 출력 읽기 (질문: Indexes / FK / Referenced by)

```
Indexes:
    "posts_pkey" PRIMARY KEY, btree (id)
Foreign-key constraints:
    "posts_author_id_fkey" FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE CASCADE
Referenced by:
    TABLE "comments"  CONSTRAINT ... FOREIGN KEY (post_id) REFERENCES posts(id) ...
    TABLE "post_tags" CONSTRAINT ... FOREIGN KEY (post_id) REFERENCES posts(id) ...
```

### Indexes (인덱스)
- **인덱스** = 특정 칼럼으로 행을 빨리 찾기 위한 자료구조(책 뒤 "찾아보기"). 전체 훑기(full scan) 대신 위치를 바로 찾음.
- `posts_pkey` = 인덱스 이름(자동: `테이블_pkey`). `PRIMARY KEY` = PK 제약을 떠받침 → **PK 만들면 인덱스 자동 생성**(중복 검사·`WHERE id=` 조회 빠르게).
- `btree` = 인덱스 종류(균형 트리). 등호·범위·정렬에 강해 PG 기본값.

### Foreign-key constraints (나가는 FK)
- posts가 **밖으로 거는** FK. "posts.author_id → users.id". = 다이어그램에서 **나가는 화살표.** schema.sql의 `REFERENCES`가 등록된 것.

### Referenced by (들어오는 FK)
- **반대 방향** — "어떤 테이블들이 나(posts)를 가리키나". comments.post_id, post_tags.post_id가 posts.id를 가리킴 = **들어오는 화살표.** posts 정의엔 안 썼지만 상대 쪽 `REFERENCES posts(id)`를 거꾸로 보여주는 것.

### 두 블록의 차이 (핵심)
같은 FK를 **방향만 바꿔** 보여줌: **Foreign-key constraints=posts가 남을 가리킴(나가는)**, **Referenced by=남이 posts를 가리킴(들어오는)**. posts 박스에 연결된 선들이 이 텍스트로 나타난 것.
- **CASCADE 방향:** posts 글 하나 삭제 → 그 글을 가리키던 comments·post_tags 행도 줄줄이 삭제. posts가 삭제 출발점, comments/post_tags가 따라 지워지는 쪽.

---

## 다음 세션 예고 (남은 것)

1. **B1 닫기:** `db.py`의 `session`→`AsyncSession` 수정(import·class_) + `SELECT 1` 핑으로 연결 확인.
2. **B2 드릴 2:** `schema.sql`을 **SQLAlchemy 선언형 모델**로 옮기기(우리 앱이 실제로 쓸 형태). SQL(DB에 직접) ↔ 모델(Python 코드)의 대응을 눈으로 본다.
3. 이후 **B3**: CRUD+REST+투표(스키마 alias, 검색/태그/페이징/정렬, 투표 트랜잭션).

### 이번 세션 핵심 한 줄 요약
- **db.py:** 엔진(앱당1, 풀=FD 여러 개) → get_db가 요청마다 세션 1개 빌려 yield로 주입 → 핸들러가 SQL → commit으로 확정 → 세션 닫혀 반납.
- **데이터 모델링:** 관계는 1:N(N쪽 FK)·N:M(중간 테이블+복합 PK)·다형(type+id+묶음 UNIQUE) 셋. 선=REFERENCES, 카디널리티=NOT NULL/UNIQUE 조합. 복합 PK는 자동 NOT NULL. ERD→SQL→`\dt`로 6테이블 생성 확인.
