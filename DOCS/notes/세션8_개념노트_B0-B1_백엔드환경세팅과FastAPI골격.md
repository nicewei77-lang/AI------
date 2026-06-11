# 세션 8 개념 노트 — 백엔드 첫 세션: B0 환경 세팅 + B1 FastAPI 골격(config·main)

> 대상 파일: `docker-compose.yml`(코치), `backend/requirements.txt`·`.env`·`app/` 골격(코치), `backend/app/config.py`(학습자 직접), `backend/app/main.py`(학습자 직접)
> 단계: 프론트(React) 7단계 종료 → **백엔드 전환**. 이번이 백엔드 첫 세션이다.
> 진행분: **B0(환경 세팅) 완전 종료**, **B1(설정·골격) 2/3** — `config.py`·`main.py` 직접 완료, `db.py`(DB 연결)만 남음.
> 이 노트의 새 주제: **이미지 vs 컨테이너**, **Flask→FastAPI 멘탈 모델(레이어드)**, **pydantic-settings로 `.env` 읽기**, **상속/클래스 vs 인스턴스/타입힌트**, **모듈 싱글톤(import 원리)**, **상대·절대경로**, **데코레이터 실행 순서**, **커널 vs uvicorn vs FastAPI(계층)**, **ASGI/WSGI**, **웹서버라는 말의 3가지 뜻**.

---

## 먼저 붙잡을 전체 그림

이번 세션은 용어가 많아서, 처음부터 각각을 따로 외우려고 하면 금방 흩어진다. 대신 아래 **세 흐름**을 먼저 잡고 읽으면 뒤의 개념들이 제자리로 들어온다.

1. **DB가 떠 있는 길**: Docker 이미지 → 컨테이너 `alibai-db` → 컨테이너 안 PostgreSQL 프로세스 → 맥의 `localhost:5432`로 연결.
2. **설정이 코드로 들어오는 길**: `backend/.env` → `Settings(BaseSettings)` → `settings = Settings()` 인스턴스 → 다른 파일들이 `from app.config import settings`로 공유.
3. **요청이 함수까지 도착하는 길**: 브라우저/`curl` → 커널(TCP 바이트) → uvicorn(HTTP 파싱 + ASGI 변환) → FastAPI(라우트 찾기) → `health()` 실행 → dict가 JSON 응답으로 변환.

즉 이번 노트의 핵심은 **"진짜 DB 프로세스 하나를 띄우고, 설정값을 파이썬 객체로 읽고, HTTP 요청 하나가 FastAPI 함수까지 오는 길을 확인했다"** 로 요약된다. `이미지/컨테이너`, `클래스/인스턴스`, `uvicorn/FastAPI` 같은 구분은 전부 이 세 흐름 안에서 다시 등장한다.

---

## 0. 이번 세션에서 완성한 코드 / 인프라

### `docker-compose.yml` (프로젝트 루트, 코치가 작성 — 인프라 예외)

```yaml
services:
  db:
    image: pgvector/pgvector:pg16        # Postgres 16 + pgvector 확장(다음 AI 단계 대비)
    container_name: alibai-db
    environment:
      POSTGRES_USER: alibai
      POSTGRES_PASSWORD: alibai_dev_pw
      POSTGRES_DB: alibai
    ports:
      - "5432:5432"                        # 호스트 5432 ↔ 컨테이너 5432
    volumes:
      - alibai_pgdata:/var/lib/postgresql/data   # 데이터 영속화(컨테이너 지워도 데이터 보존)
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U alibai -d alibai"]
      interval: 5s
      timeout: 3s
      retries: 5

volumes:
  alibai_pgdata:
```

### `backend/.env` (코치 작성 — 비밀값은 `.env`에만, `.gitignore` 처리)

```
DATABASE_URL=postgresql+asyncpg://alibai:alibai_dev_pw@localhost:5432/alibai
JWT_SECRET=dev-secret-change-me-in-prod
```

### `backend/app/config.py` (학습자 직접)

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):          # BaseSettings 상속 → .env 자동 로딩 능력 물려받음
    database_url: str                  # .env의 DATABASE_URL을 받을 필드
    jwt_secret: str                    # .env의 JWT_SECRET을 받을 필드

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()                  # 인스턴스화 → 이 순간 .env를 읽어 값이 채워짐
```

검증(돌려보는 게 본체):
```bash
cd backend && source .venv/bin/activate
python -c "from app.config import settings; print(settings.database_url, '|', settings.jwt_secret)"
# → postgresql+asyncpg://alibai:alibai_dev_pw@localhost:5432/alibai | dev-secret-change-me-in-prod
```

### `backend/app/main.py` (학습자 직접)

```python
from fastapi import FastAPI

app = FastAPI()                        # FastAPI 앱 인스턴스

@app.get("/health")                    # GET /health 요청 → 아래 함수로 등록(데코레이터)
async def health():
    return {"status": "ok"}            # dict → FastAPI가 JSON으로 자동 직렬화
```

검증:
```bash
cd backend && source .venv/bin/activate
uvicorn app.main:app --reload
# http://127.0.0.1:8000/health → {"status":"ok"} (200)
# http://127.0.0.1:8000/docs   → Swagger UI에 /health 자동 등록
```

---

## 1. B0 환경 세팅 — Docker로 PostgreSQL 띄우기

### 1-1. 왜 DB를 Docker로?

DB를 내 맥에 직접 설치하지 않고 **격리된 컨테이너**로 띄운다. 버리고 다시 만들기 쉽고, 팀원/다른 기기에서도 같은 환경이 재현된다. `pgvector` 이미지를 고른 이유는 **다음 AI 단계(임베딩 검색)** 에서 쓸 pgvector 확장을 미리 깔아두기 위함.

### 1-2. ❓질문: "도커 앱 켜기만 했는데 이미지랑 컨테이너 전부 만들어준 건가?"

그렇다. 학습자가 Docker Desktop을 **켜기만**(데몬을 깨우기만) 하면, 그 다음 명령은 코치가 터미널에서 실행했다. 일어난 일을 시간순으로:

1. **이미지 받기(pull)** — `docker compose up -d` 실행 시, Docker가 `pgvector/pgvector:pg16` **이미지**(= Postgres가 설치된 '붕어빵 틀')를 인터넷에서 내려받았다. (`Downloading... 110MB` 로그가 이것.)
2. **컨테이너 만들기(create + start)** — 그 이미지로 `alibai-db`라는 **컨테이너**(= 틀로 찍어낸 실제 '붕어빵' = 진짜 돌아가는 DB 프로세스)를 만들고 띄웠다.

### 1-3. 🔑 이미지 vs 컨테이너 (핵심 구분)

| | 정체 | 비유 |
|---|---|---|
| **이미지(image)** | 읽기 전용 설계도/틀. 한 번 받으면 재사용. | 붕어빵 **틀** |
| **컨테이너(container)** | 그 틀로 띄운, 실제로 돌아가는 인스턴스. | 틀로 찍은 **붕어빵** |

- 이미지 1개로 컨테이너 여러 개를 찍을 수도 있다.
- **이 구도는 뒤에 나올 "클래스 vs 인스턴스"와 정확히 같다**(틀 vs 실물). 기억해 둘 것.

### 1-4. Docker Desktop 화면의 `ai` 묶음

- 화면의 초록 점 **`ai`** 는 compose **프로젝트** 묶음 이름이다. 프로젝트 폴더명(`AI로 진화하기`)에서 영문/숫자만 따 `ai`로 자동 생성됐다.
- `>` 화살표를 펼치면 그 안에 실제 컨테이너 **`alibai-db`** 가 보인다(Port `5432`).

### 1-5. `localhost:5432`가 진짜 가리키는 곳

`docker-compose.yml`의 `ports: "5432:5432"`는 **맥의 5432번 포트를 컨테이너의 5432번 포트에 연결**한다는 뜻이다. 왼쪽 `5432`는 호스트(내 맥), 오른쪽 `5432`는 컨테이너 안 PostgreSQL 포트다.

그래서 `backend/.env`의 DB 주소가 `@localhost:5432/alibai`여도, 실제 데이터베이스는 맥에 직접 설치된 Postgres가 아니라 **Docker 컨테이너 안의 Postgres**다. 흐름은 이렇게 읽으면 된다.

```text
파이썬 앱 → localhost:5432(맥) → Docker 포트 포워딩 → alibai-db:5432(컨테이너) → PostgreSQL
```

나중에 FastAPI 앱까지 Docker 컨테이너로 올리면 이 주소가 달라진다. 컨테이너끼리는 보통 `localhost`가 아니라 compose 서비스 이름인 `db:5432`로 서로를 찾는다. 지금은 FastAPI를 맥에서 직접 실행하고 DB만 Docker에 있으므로 `localhost:5432`가 맞다.

### 1-6. B0 완료 기준(4개) — 전부 충족

1. `uvicorn`으로 서버가 뜬다
2. `/health` 200
3. `/docs`(Swagger UI) 열림
4. DB 컨테이너 healthy

검증 명령: `docker exec alibai-db psql -U alibai -d alibai -c "SELECT 1;"` → `1` 반환(DB 살아있음 확인).

---

## 2. 멘탈 모델 전환 — Flask 뷰가 다 하던 일을 FastAPI는 어떻게 쪼개나

학습자는 Flask 경험이 있다. 그 위에 얹는다.

- **Flask(기존):** 보통 동기. 뷰 함수 하나가 요청을 받아 **직접** SQL도 날리고 응답도 만든다. 위→아래로 즉시 실행.
- **FastAPI(이제):** 네 가지가 다르다.
  1. **타입 기반** — 요청/응답을 Pydantic 스키마로 *선언*하면 검증·문서가 자동 생성.
  2. **async** — `async def` 핸들러가 DB·네트워크를 *기다리는 동안* 다른 요청을 처리.
  3. **레이어드** — 뷰가 다 하지 않고 `router(입출력) → service(규칙) → repository(DB)`로 책임을 쪼갬.
  4. **의존성 주입(`Depends`)** — "로그인 유저", "DB 세션"을 핸들러에 *주입*받음.

**레이어드 분할 기준 (한 파일 = 한 책임):** "이 코드가 **HTTP를 아나**(→`router`)·**업무 규칙이냐**(→`service`)·**DB를 아나**(→`repository`)·**데이터의 모양이냐**(→`models/schemas`)." 둘 다 알면 쪼갠다. 같은 종류가 여러 개가 되면 **파일 → 폴더로 승격**(그래서 `auth/`·`routers/`는 처음부터 폴더).

> 예: Flask 뷰의 "요청 받기·응답 검증" = router(+schema), "같은 값 재투표면 취소" 같은 규칙 = service, "실제 SELECT/INSERT" = repository, "데이터 모양" = models/schemas.

---

## 3. `config.py` — `.env`를 파이썬 코드로 읽어들이기

### 3-1. 이 파일의 역할

`.env`(비밀값: DB 주소·JWT 시크릿)를 **파이썬 코드가 쓸 수 있는 객체로 읽어들이는 입구**. 코드 곳곳에서 `settings.database_url`처럼 꺼내 쓴다. 비밀을 코드에 직접 박지 않고 `.env` → `config.py`를 거치게 해서 **비밀은 한 곳(.env)에만** 둔다.

### 보충: `DATABASE_URL` 한 줄 쪼개서 읽기

`DATABASE_URL=postgresql+asyncpg://alibai:alibai_dev_pw@localhost:5432/alibai`는 길지만, 한 줄짜리 연결 정보다. 쪼개면 이렇게 생겼다.

```text
postgresql+asyncpg:// alibai : alibai_dev_pw @ localhost : 5432 / alibai
드라이버              사용자   비밀번호          호스트      포트    DB이름
```

- `postgresql+asyncpg` — PostgreSQL에 붙되, SQLAlchemy가 **asyncpg 드라이버**를 사용하라는 뜻.
- `alibai:alibai_dev_pw` — Docker compose에서 만든 DB 사용자와 비밀번호.
- `localhost:5432` — 맥의 5432번 포트. 위에서 본 것처럼 Docker 컨테이너의 Postgres로 이어진다.
- 마지막 `/alibai` — 접속할 데이터베이스 이름.

이 URL은 아직 DB에 실제로 연결하지 않는다. `config.py`는 **문자열을 안전하게 읽어오는 단계**이고, 다음 `db.py`에서 이 문자열을 SQLAlchemy 엔진에 넘기는 순간 실제 연결 준비가 시작된다.

### 3-2. 왜 `.env`를 따로 두고 코드로 읽나 (등장 배경)

옛날엔 DB 비번·API 키를 코드에 문자열로 박았다. 그러면 ① git에 올리는 순간 비밀 노출, ② 개발용/배포용 값을 바꾸려면 코드를 고쳐야 했다. 그래서 **"설정은 코드 바깥(환경)에 두고 코드는 읽기만 한다"**(12-factor의 config 원칙)가 자리잡았다. `.env`가 그 "환경"이고 `.gitignore`로 git에서 빠진다.

### 3-3. `pydantic-settings`의 정체

`os.environ["DATABASE_URL"]`로 직접 읽어도 되지만, 그러면 ① 오타·누락을 런타임에야 발견, ② 전부 문자열이라 타입이 없다. `pydantic-settings`는 **클래스에 필드와 타입을 선언해두면 `.env`(또는 OS 환경변수)에서 같은 이름을 찾아 자동으로 채우고 타입까지 검증**한다. 빠진 값이 있으면 **서버 시작 시점에 바로 에러**를 내, "한참 돌다 DB 붙을 때 터지는" 사고를 막는다.

용어:
- **`BaseSettings`** — pydantic-settings가 주는 부모 클래스. 상속하면 "필드 이름과 같은 환경변수를 자동으로 찾아 채워라" 능력이 생긴다. **대소문자 무시** → 필드 `database_url` ↔ `.env`의 `DATABASE_URL` 매칭.
- **`SettingsConfigDict`** — 이 Settings 클래스의 *동작 옵션*을 담는 설정 객체. `env_file="..."`로 "어느 파일에서 읽을지" 지정.
- **`model_config = ...`** — pydantic v2에서 클래스 설정을 담는 **약속된 이름의 변수**. 여기에 `SettingsConfigDict(...)`를 넣으면 그 옵션대로 동작.
- **`settings = Settings()`** — 클래스를 *인스턴스화*하는 순간 `.env`를 읽어 필드를 채운다. 다른 파일은 `from app.config import settings`로 이 객체를 가져다 쓴다.

### 3-4. ❓질문: 상속이란? ("클래스를 인자/필드로 받는 것"이라 알고 있었는데?)

**그 이해는 틀렸다.** "클래스를 인자/필드로 받는 것"은 **합성(composition)** 이다. 상속은 **한 클래스를 다른 클래스를 '토대로' 정의해, 부모의 필드·메서드를 자동으로 물려받는 것**이다.

```python
class Animal:
    def breathe(self): return "숨쉼"

class Dog(Animal):        # 상속: "Dog는 Animal을 기반으로"
    def bark(self): return "멍"

d = Dog()
d.bark()      # Dog 자신의 것
d.breathe()   # Animal에서 물려받음(Dog에 안 써도 있음)
```

상속(is-a) vs 합성(has-a) 대조:
```python
class A: ...
class B(A): ...                          # 상속: "B는 A의 일종"(is-a)
class C:
    def __init__(self, a: A): self.a = a # 합성: "C는 A를 가진다"(has-a)
```

**우리 코드:** `class Settings(BaseSettings)` → "Settings는 BaseSettings의 일종"이라 `.env`를 읽는 능력을 공짜로 물려받는다. 우리는 `database_url` 같은 필드만 얹는다.

### 3-5. ❓질문: 타입 힌트는 컴파일/데이터 인식에 영향을 주나? 자동완성뿐? 함수 선언도 같은 역할?

**경우에 따라 다르다 (핵심 함정).**

**(a) 보통의 파이썬에서는 타입 힌트가 "장식"이다.** 인터프리터는 실행 시 타입 힌트를 **무시**한다(C/Java 컴파일러처럼 검사하지 않음).
```python
def f(x: int) -> int:
    return x
f("문자열")   # 에러 안 남! int 힌트는 강제력 0
```
이때 타입 힌트를 *읽는 주체*는 **사람 + 외부 정적 분석기**(Pylance, mypy)뿐. 빨간 줄은 그어줘도 실행은 못 막는다.

**(b) pydantic은 예외다.** `BaseSettings`/`BaseModel`은 **실행 시점에 타입 힌트를 읽어(introspection) 실제로 검증·변환**한다.
```python
class Settings(BaseSettings):
    port: int    # .env의 PORT="5432"(문자열)를 → int 5432로 변환까지
```
즉 **같은 `이름: 타입` 문법인데 "누가 읽느냐"에 따라** 장식(함수 선언)이 되기도, 진짜 검증(pydantic 필드)이 되기도 한다. 함수 선언의 타입 힌트도 문법·의도는 같지만(읽는 도구가 같음), 실행 동작에 영향을 주려면 그걸 읽고 행동하는 라이브러리/검사기가 있어야 한다.

### 3-6. ❓질문: `SettingsConfigDict`로 조건 설정하는 법은? (객체=조건?)

`SettingsConfigDict(...)`는 **키워드 인자**로 옵션을 받는 설정 객체다("설정을 담은 dict"의 타입 안전 버전).
```python
model_config = SettingsConfigDict(
    env_file=".env",            # 어느 파일에서 읽나
    env_file_encoding="utf-8",  # 인코딩
    case_sensitive=False,       # 대소문자 구분 안 함(database_url ↔ DATABASE_URL)
    extra="ignore",             # .env에 모르는 키가 있어도 무시(에러 안 냄)
    env_prefix="ALIBAI_",       # 환경변수 앞에 접두사 요구(선택)
)
```
지금은 `env_file=".env"` 하나면 충분. 나머지는 "이런 옵션도 있다" 정도.

### 3-7. ❓질문: `settings`만 써놔도 전역? 클래스 아닌 인스턴스를 import하는 이유? (+ 5. 클래스 vs 인스턴스)

**파이썬엔 "파일을 넘나드는 암묵적 전역"이 없다.** `config.py`에 `settings`를 써뒀다고 다른 파일에서 그냥 `settings`라고 못 쓴다. **각 파일에서 명시적으로 `from app.config import settings`** 로 가져와야 한다. 그런데 가져오면 마치 전역처럼 느껴지는데, 그 원리:

**모듈은 "처음 import될 때 딱 한 번" 실행되고 결과가 캐시된다.** 파이썬은 `sys.modules`에 이미 불러온 모듈을 저장한다.
```python
# main.py
from app.config import settings   # 이 순간 config.py 본문이 처음이자 마지막으로 실행됨
                                   # settings = Settings()도 이때 1번 실행 → .env 1번 읽음
# db.py
from app.config import settings   # config.py 재실행 안 함! 캐시된 그 settings 객체를 그대로 줌
```
→ **앱 전체가 똑같은 `settings` 객체 하나를 공유**한다(싱글톤 효과). 이게 "전역처럼 느껴지는" 진짜 원리.

**왜 클래스(`Settings`)가 아니라 인스턴스(`settings`)를 import하나?**
- 클래스를 가져가면 각 파일이 `Settings()`를 또 호출 → **.env를 매번 다시 읽고, 객체가 여러 개** 생긴다(설정이 흩어짐).
- 인스턴스를 가져가면 **이미 만들어진 단 하나**를 공유 → .env는 시작 시 1번만 읽고 설정이 일관.
- 관용구: "`config.py`에서 한 번 `settings = Settings()` 만들고, 나머지는 그 인스턴스를 import."

**클래스 vs 인스턴스:**
| | 정체 | C 비유 |
|---|---|---|
| **클래스** | 설계도/틀/타입. "이런 필드·동작을 가진 것"의 정의. | `struct Point { int x, y; }` 선언 |
| **인스턴스** | 그 틀로 찍어낸 실제 객체. 메모리에 값이 들어참. | `struct Point p = {1,2};` 변수 `p` |
```python
Settings            # 클래스(틀) — 아직 .env 안 읽음
settings = Settings()   # 인스턴스(실물) — 이 순간 .env 읽어 값 채워짐
```
→ 앞의 **이미지 vs 컨테이너**와 정확히 같은 구도(틀 vs 실물).

### 3-8. ❓질문: `env_file`은 상대경로 `../.env`로 쓰면 되나? (+ 8. 절대/상대경로, 9. 디렉터리/루트)

**함정 주의.** `env_file`의 상대경로는 **파일(config.py) 위치가 아니라, 프로세스를 실행한 위치(현재 작업 디렉터리, CWD)** 기준이다.

우리는 항상 `cd backend && uvicorn app.main:app --reload`로 실행 → **CWD = `backend/`**. `.env`도 `backend/.env`에 있으니 **`env_file=".env"` 가 맞다.** `../.env`로 쓰면 `backend/`의 부모(프로젝트 루트)를 가리켜 **못 읽는다.**

**절대경로 vs 상대경로:**
- **절대경로** = 파일시스템 뿌리(`/`)부터 끝까지 다 적은 길. 어디서 실행하든 같은 곳. 예: `/Users/wiseungcheol/Desktop/AI로 진화하기/backend/.env`
- **상대경로** = **CWD 기준**의 길. `.`=현재, `..`=부모. CWD가 `backend/`일 때 `.env`=`backend/.env`, `../.env`=프로젝트 루트의 .env.
- 핵심: 상대경로는 **"지금 어디서 돌리느냐"에 따라 가리키는 곳이 바뀐다**(그래서 위 함정이 생김).

**디렉터리 = 폴더** (같은 말. 터미널/CS=디렉터리, GUI=폴더). "루트"는 문맥상 둘:
1. **파일시스템 루트(`/`)** — 디스크 전체 최상위. 모든 절대경로의 시작.
2. **프로젝트 루트** — 우리 프로젝트 최상위 폴더 = `AI로 진화하기/`. `git` 관리 꼭대기이자 `frontend/`·`backend/`·`DOCS/`가 나란히 든 폴더.

---

## 4. `main.py` — FastAPI 앱 진입점 + `/health`

### 4-1. 이 파일의 역할

앱의 **진입점(entrypoint)**. `uvicorn app.main:app`의 그 `app`이 이 파일이 만드는 FastAPI 객체다. 앞으로 라우터 등록·CORS·미들웨어가 전부 여기 모인다. 오늘은 **서버가 살아있는지 확인하는 `/health`** 하나만 단다.

### 보충: `uvicorn app.main:app`은 어떻게 읽나

`uvicorn app.main:app --reload`에서 헷갈리는 지점은 `app`이 두 번 나온다는 점이다.

```text
uvicorn app.main:app
        └──────┘ └─┘
         모듈 경로  변수 이름
```

- `app.main` — `backend/app/main.py` 파일을 파이썬 모듈 경로로 쓴 것. 슬래시(`/`) 대신 점(`.`)을 쓴다.
- 뒤의 `:app` — 그 파일 안에 있는 `app = FastAPI()` 변수.

즉 이 명령은 "uvicorn아, `app/main.py`를 import해서 그 안의 `app` 객체를 ASGI 앱으로 실행해줘"라는 뜻이다. 앞의 `app`은 폴더/패키지 이름이고, 뒤의 `app`은 변수 이름이라 역할이 다르다.

### 4-2. 개념

- **`app = FastAPI()`** — `FastAPI` 클래스로 앱 인스턴스 생성. 라우트 목록·설정을 들고 있는 앱의 중심.
- **데코레이터 `@app.get("/health")`** — `@`로 시작하는 줄. 바로 아래 함수를 **인자로 받아 동작을 덧씌워 돌려주는** 함수. "아래 함수를 **`GET /health` 요청이 오면 부를 함수로 등록**." Flask의 `@app.route`와 같은 역할인데, FastAPI는 메서드별로 `.get`/`.post`/`.put`/`.delete`를 따로 둬 의도가 명확.
- **`async def`** — DB·네트워크 I/O를 **기다리는 동안** uvicorn이 다른 요청을 처리. `/health`는 효과 없지만 **앞으로 DB 핸들러와 형태를 통일**하려 처음부터 `async def`.
- **`/docs`는 공짜** — 타입·경로를 *선언*해두면 FastAPI가 읽어 **Swagger UI(`/docs`)** 자동 생성. "타입 기반"의 실제 이득.
- **반환값 `{"status": "ok"}`** — dict를 반환하면 FastAPI가 **JSON으로 자동 직렬화**(`Content-Type: application/json`). Flask의 `jsonify`를 알아서 해줌.

### 4-3. ❓질문: FastAPI 인스턴스부터 만들어도 돼? `@` 선언은 밑에 있는데?

**그 순서가 맞을 뿐 아니라 반드시 그래야 한다.** 핵심: **파이썬은 위에서 아래로 한 줄씩 실행**하고, **데코레이터는 함수가 정의되는 그 순간 즉시 실행**된다.

`@app.get("/health")`는 **`app`을 사용하는** 코드라, 그 줄에 도달했을 때 `app`이 이미 있어야 한다.
```python
app = FastAPI()          # ① 먼저 app 생성(없으면 ③에서 NameError)
@app.get("/health")      # ③ "이 함수를 GET /health에 등록" — 정의 시점에 즉시 실행
async def health():      # ② health 함수 정의
    return {"status": "ok"}
```
순서를 뒤집어 `app = FastAPI()`를 데코레이터 아래 두면 → `NameError: name 'app' is not defined`.

**오해 풀기:** 데코레이터는 마법이 아니라 **그 줄을 읽는 순간 `app.get(...)`을 실제로 호출**하는 평범한 코드다. `@`는 문법 설탕:
```python
async def health():
    return {"status": "ok"}
health = app.get("/health")(health)   # @app.get("/health")가 실제로 하는 일
```
→ `app.get(...)`을 호출하니 `app`이 위에 있어야 당연.

여기서 또 하나 중요하다. **데코레이터 실행과 `health()` 함수 실행은 다른 시점**이다.

```text
서버 시작/import 시점: app = FastAPI() 생성 → @app.get("/health")가 health 함수를 라우트 테이블에 등록
요청 도착 시점: GET /health 요청이 올 때마다 FastAPI가 등록된 health()를 호출
```

즉 서버가 켜질 때 `health()` 본문이 미리 실행되는 게 아니다. 서버 시작 시에는 "이 경로가 오면 이 함수를 부르자"는 **등록**만 일어나고, 함수 본문은 실제 요청이 들어올 때 실행된다. 이 차이를 잡아야 데코레이터가 "함수를 즉시 호출하는 코드"처럼 보이는 혼란을 피할 수 있다.

---

## 5. ❓질문: uvicorn / ASGI / "커널이 하는 거 아냐?" / "uvicorn이 웹서버였어, Flask 같은?"

세션 후반 질문 묶음. 계층을 정확히 나누는 게 핵심.

### 5-1. uvicorn이 뭐냐 — 그리고 "소켓+HTTP 파서인 줄"은 맞다

이름: `u`(마이크로 μ) + `vicorn`(unicorn) + 내부적으로 `uvloop`(초고속 이벤트 루프)를 쓴다는 말장난. 가벼운 ASGI 서버.

**학습자 모델("소켓 통신 + HTTP 파서")은 틀린 게 아니다** — 그게 정확히 uvicorn이 하는 일이고, 그걸 하는 프로그램을 "웹서버"라 부를 뿐.

### 5-2. 커널 질문(날카로움) — 절반 맞다. 계층을 나누자

| 계층 | 담당 | 하는 일 |
|---|---|---|
| **커널** | OS | TCP 연결, 소켓, **바이트 전송**. 3-way handshake. **HTTP는 모름** |
| **uvicorn** | ASGI 서버 | 소켓 열기(커널에 `bind/listen/accept`) → 바이트를 **HTTP로 파싱** → 파이썬이 알아들을 형태(ASGI scope)로 변환 → 앱 호출 → 반환값을 **다시 HTTP 바이트로 직렬화** → 커널에 전송 요청 |
| **FastAPI** | 앱 | "GET /health면 health() 호출" 라우팅·검증·응답 모양 |

**커널이 주는 건 "의미 없는 바이트 덩어리"** 다. 소켓에서 읽으면 날것의 텍스트가 나온다:
```
GET /health HTTP/1.1\r\n
Host: 127.0.0.1:8000\r\n
\r\n
```
이걸 **HTTP로 해석(첫 줄을 메서드·경로·버전으로, 헤더를 키:값으로, 빈 줄 뒤를 본문으로)** 하는 건 HTTP 규칙을 아는 **유저 공간 프로그램(uvicorn)** 의 몫. 커널은 TCP까지만 안다.

**흐름:**
```
브라우저 → [커널: TCP로 바이트 도착] → [uvicorn: 바이트→HTTP 파싱→ASGI] → [FastAPI: health() 실행]
        → [uvicorn: 결과→HTTP 바이트] → [커널: 전송] → 브라우저
```
파이썬 함수(`health()`)는 소켓·바이트·HTTP를 전혀 모르고 `{"status":"ok"}` dict만 반환한다. 그 **"날것의 소켓 세계 ↔ 깔끔한 파이썬 함수 세계"** 를 통역하는 게 uvicorn의 존재 이유.
> 비유: 커널=우체국(봉투를 집까지 배달), uvicorn=비서(봉투 뜯어 읽고 사장님이 이해할 메모로 전달, 답을 다시 편지로 써서 우체국에 맡김). 사장님(파이썬 함수)은 봉투·우표를 만질 일이 없다.

### 5-3. ASGI가 뭐야 — **A**synchronous **S**erver **G**ateway **I**nterface

**"웹서버(uvicorn)와 파이썬 앱(FastAPI) 사이의 약속된 인터페이스(호출 규약)."** 프로토콜이 아니라 둘이 함수를 어떻게 주고받을지 정한 규격.

**왜 생겼나 — WSGI의 한계.** 원래 파이썬 웹엔 **WSGI**(Flask·Django가 씀)가 있었다. WSGI 앱은 본질적으로 **동기 함수**:
```python
def app(environ, start_response):   # WSGI: 동기로 처리 → 반환
    start_response("200 OK", [...])
    return [b"Hello"]
```
문제: **동기**라 요청 하나를 끝까지 처리할 때까지 자리를 붙잡는다(DB 1초 대기 = 1초 멈춤 → 서버가 스레드/프로세스를 늘려 버팀). 또 구조상 **WebSocket·async를 표현 못 함**.

**ASGI가 푼 것 — async + 이벤트 기반:**
```python
async def app(scope, receive, send):   # async! + 이벤트를 주고받음
    # scope   = 이 연결의 메타데이터(메서드/경로/헤더... dict)  ← uvicorn이 HTTP 파싱해 만든 그것
    # receive = 들어오는 이벤트를 await로 받는 함수(요청 본문 등)
    # send    = 나가는 이벤트를 await로 보내는 함수(응답 시작/본문)
    await send({"type": "http.response.start", "status": 200, ...})
    await send({"type": "http.response.body", "body": b"Hello"})
```
1. **`async def`** — I/O를 `await`로 기다리는 동안 서버가 다른 요청 처리(한 프로세스로 많은 동시 요청).
2. **`receive`/`send` 이벤트 모델** — 요청·응답을 통째가 아니라 이벤트 스트림으로 → HTTP뿐 아니라 **WebSocket**도 같은 규격으로 표현.
3. **`scope`** — uvicorn이 HTTP 바이트를 파싱해 만든 "파이썬이 알아들을 형태".

**우리 그림:**
```
커널(TCP) → uvicorn(HTTP 파싱) → [ASGI 규격: scope/receive/send] → FastAPI(앱)
                                  ↑ 이 약속된 인터페이스가 ASGI
```
- uvicorn = ASGI **서버**(규격대로 앱을 호출하는 쪽)
- FastAPI = ASGI **앱/프레임워크**(규격대로 호출당하는 쪽)
- 덕분에 uvicorn을 다른 ASGI 서버(hypercorn)로 갈아껴도 FastAPI 코드는 그대로. "서버와 앱을 분리하는 표준 콘센트."
> ℹ️ 우리는 ASGI를 직접 구현하지 않는다. `scope/receive/send`를 손으로 만질 일은 없고, FastAPI가 `@app.get` 같은 껍데기를 씌워준다(범위 가드: 내부는 더 안 판다).

### 5-4. "uvicorn이 웹서버였어? Flask 같은?" — "웹서버"라는 말의 3가지 뜻

"웹서버"가 3가지를 가리켜서 헷갈린다. 분리하면:

| 부르는 이름 | 정체 | 예시 | 하는 일 |
|---|---|---|---|
| **앱 서버 / ASGI·WSGI 서버** | 소켓 + HTTP 파서 + 앱 호출 | **uvicorn**, gunicorn | TCP 받기 → HTTP 파싱 → 앱 호출 → 응답 직렬화 |
| **웹 프레임워크** | 라우팅·로직 정의 | **Flask**, **FastAPI** | "이 URL이면 이 함수" 규칙·검증·응답 모양 |
| **(리버스 프록시) 웹서버** | 정적파일·앞단 분배 | nginx, Apache | 정적 파일 서빙, 트래픽 분배, HTTPS 종료 |

→ **uvicorn은 1번.** 학습자가 말한 "소켓+HTTP 파서"가 1번의 핵심 업무다(맞게 봄).

**"Flask 같은?" — 여기가 진짜 혼란 지점.** **Flask는 uvicorn과 같은 역할이 아니다.** Flask=프레임워크(2번)라 FastAPI와 짝. 헷갈리는 이유: **Flask는 개발용 WSGI 서버(werkzeug)를 안에 끼워서 판다.** 그래서 `flask run`이면 서버가 딸려와 바로 뜬다. 그 "딸려온 서버"가 uvicorn 자리이고, Flask 자체는 위에 얹힌 앱. 배포 땐 그 개발 서버를 버리고 **gunicorn**(별도 WSGI 서버)에 얹는다.

대응:
```
[프레임워크(앱)]   [서버]
Flask            ↔  werkzeug(개발) / gunicorn(배포)   ← 동기 / WSGI
FastAPI          ↔  uvicorn                          ← async / ASGI
```
→ **Flask ≈ FastAPI**(둘 다 앱), **gunicorn ≈ uvicorn**(둘 다 서버). FastAPI는 서버를 끼워 팔지 않아 우리가 `uvicorn`을 **명시적으로 따로** 실행한다(`uvicorn app.main:app`). 그래서 역할 구분이 오히려 더 잘 드러난다.

---

## 6. 곁가지: Pylance "pydantic_settings 확인할 수 없음" 경고

`config.py`에 빨간 줄(`reportMissingImports`)이 떴는데, **코드 오류가 아니라 에디터(Pylance)가 엉뚱한 파이썬을 보고 있어서**다. 패키지는 `backend/.venv`에 설치돼 있는데 Pylance는 기본적으로 시스템 파이썬을 본다.

해결: `Cmd+Shift+P` → **`Python: Select Interpreter`** → `./backend/.venv/bin/python` 선택. (모노레포라 워크스페이스 루트는 프로젝트 폴더인데 venv는 `backend/` 안이라 자동으로 못 찾음. 한 번만 잡으면 됨.) **빨간 줄이 있어도 실행은 `.venv` 파이썬으로 하니 결과는 정확.** → 정적 분석기 vs 실행 환경의 어긋남.

---

## 7. 헷갈리기 쉬운 구분 6쌍

이번 세션은 "비슷하게 들리지만 계층이 다른 것"을 분리하는 게 거의 전부다.

| 구분 | 한 줄로 잡기 |
|---|---|
| **이미지 vs 컨테이너** | 이미지는 실행 재료/틀, 컨테이너는 그 이미지로 실제 떠 있는 프로세스 묶음 |
| **클래스 vs 인스턴스** | 클래스는 타입/설계도, 인스턴스는 메모리에 만들어져 값을 가진 실제 객체 |
| **`.env` vs `settings`** | `.env`는 코드 밖 문자열 파일, `settings`는 그 값을 읽어 만든 파이썬 객체 |
| **FastAPI vs uvicorn** | FastAPI는 라우팅/검증을 가진 앱 프레임워크, uvicorn은 HTTP를 받아 앱을 호출하는 ASGI 서버 |
| **커널 vs uvicorn** | 커널은 TCP 바이트 운반, uvicorn은 그 바이트를 HTTP로 해석해 ASGI 앱에 전달 |
| **서버 시작 시점 vs 요청 시점** | import 때는 앱 생성/라우트 등록, 요청 때는 등록된 핸들러 함수 실행 |

이 6쌍을 구분하면 오늘 나온 대부분의 질문이 한 줄로 정리된다. 특히 `Settings()`와 `FastAPI()`는 둘 다 **클래스로 인스턴스를 만들고, 그 인스턴스를 앱 전체에서 재사용**한다는 점에서 같은 패턴이다.

---

## 8. 이번 세션 한 줄 요약 / 다음 위치

- **B0 완전 종료**(Docker Postgres healthy + 서버 기동 + `/health` 200 + `/docs`), **B1 2/3**(`config.py`·`main.py` 직접 완료).
- **다음:** `backend/app/db.py` — SQLAlchemy **async 엔진/세션**으로 떠 있는 Postgres에 실제로 붙어 연결 확인 → B1 완료 → 이어서 **B2(데이터 모델링: ERD→SQL→SQLAlchemy 모델, 6개 테이블 생성)**.

### 이번 세션에서 던진 질문 체크리스트(복습용)
1. 도커 켜기만 했는데 이미지/컨테이너 다 만들어진 건가? → §1-2, 1-3
2. 상속이란? (인자/필드로 클래스 받는 것?) → §3-4 (틀림: 그건 합성)
3. 타입 힌트가 컴파일/데이터 인식에 영향? 자동완성뿐? 함수 선언도 같은 역할? → §3-5
4. `SettingsConfigDict`로 조건 설정하는 법? → §3-6
5. `settings`만 써놔도 전역? 클래스 아닌 인스턴스 import 이유? → §3-7
6. 클래스 vs 인스턴스 차이 → §3-7 표
7. `env_file` 상대경로 `../.env`? → §3-8 (아니오: `.env`)
8. 절대경로/상대경로란? → §3-8
9. 프로젝트 디렉터리/루트 = 폴더? → §3-8 (그렇다)
10. 인스턴스부터 만들어도 돼? `@`가 밑에 있는데? → §4-3
11. uvicorn이 뭐야? 소켓+HTTP 파서? 커널이 하는 줄? → §5-1, 5-2
12. ASGI가 뭐야? → §5-3
13. uvicorn이 웹서버였어? Flask 같은? → §5-4
