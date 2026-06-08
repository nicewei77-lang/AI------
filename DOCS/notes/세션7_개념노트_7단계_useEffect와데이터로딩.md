# 세션 7 개념 노트 — 7단계 Day2 useEffect + 데이터 로딩 (`pages/PostListPage.tsx`)

> 날짜: 2026-06-09 (세션 7) · 복습용
> 다룬 단계: **7단계 Day2** — `PostListPage`에서 `MOCK_POSTS` 직접 import를 걷어내고, `useEffect`로 6단계의 `fetchPosts()`를 실제 호출해 데이터를 받아오게 전환. loading/error 3갈래 처리. (PostDetailPage는 다음 세션)
> 세션 6이 "데이터를 가져오는 창구(API 함수)를 만든" 세션이었다면, 이번엔 **그 창구를 화면이 언제·어떻게 호출하느냐**를 다룬 세션이다.
> 핵심 주제: **컴포넌트=함수와 리렌더 · useState 깊이 · useEffect · effect 안에서 async 쓰기(Promise 반환 문제) · loading/error**.
> 아래는 작성한 코드 → 내가 질문한 것들을 빠짐없이, 논리적 순서로 정리.

---

## 0. 이번 세션에서 완성한 코드 (`frontend/src/pages/PostListPage.tsx`)

```tsx
import { useState, useEffect } from "react";
import PostList from "../components/PostList";
import { fetchPosts } from "../api/posts";
import type { Post } from "../types/post";

function PostListPage() {
    // 기억 칸 3개: 데이터 / 로딩여부 / 에러메시지
    const [posts, setPosts] = useState<Post[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // 첫 마운트 시점에 데이터 로드
    useEffect(() => {
        async function load() {
            try {
                const data = await fetchPosts();
                setPosts(data.items);
            } catch {
                setError("목록을 불러오지 못했습니다.");
            } finally {
                setLoading(false);
            }
        }
        load();
    }, []);

    // 세 갈래 화면
    if (loading) return <p className="p-8">불러오는 중…</p>;
    if (error) return <p className="p-8 text-red-600">{error}</p>;

    return (
        <div className="mx-auto max-w-2xl px-4 py-8">
            <h1 className="mb-4 text-2xl font-bold">변명 게시판</h1>
            <PostList posts={posts} />
        </div>
    );
}

export default PostListPage;
```

**무엇이 바뀌었나(6단계 대비):** 전엔 `import {MOCK_POSTS}`로 데이터를 직접 손에 쥐고 `<PostList posts={MOCK_POSTS}/>`로 박았다. 이건 "데이터가 이미 있다"는 가짜 상황. 진짜 앱은 데이터가 **나중에**(네트워크 너머에서) 도착한다. 그 "나중에 도착함"을 다루는 도구가 이번 주인공 **`useEffect`**.

### 0-1. 이 코드에서 먼저 붙잡을 연결고리 3개

이 코드는 `fetchPosts()` → `await` → `data.items` 흐름만 먼저 잡아도 훨씬 덜 헷갈린다.

1. `fetchPosts()`를 호출한 직후 손에 들어오는 건 글 배열이 아니라 `Promise<{ items: Post[]; nextCursor?: string }>`다.
2. `await fetchPosts()`는 그 Promise가 끝날 때까지 `load` 안에서 기다렸다가, 끝나면 실제 객체 `{ items, nextCursor }`를 꺼내 준다.
3. 그래서 `setPosts(data.items)`의 `.items`는 "Promise에서 뽑는 것"이 아니라, **await가 끝난 뒤 받은 객체에서 목록 배열만 꺼내는 것**이다.

짧게 줄이면:
- `fetchPosts()` = 아직 미래의 값(Promise)
- `await fetchPosts()` = 미래의 값이 끝난 뒤 실제 객체 받기
- `data.items` = 그 객체 안에서 글 목록만 꺼내기

---

## 1. 컴포넌트는 "그냥 함수"이고, 자주 다시 호출된다 (리렌더)

`PostListPage()`는 함수다. React는 이 함수를 호출해 반환된 JSX를 화면에 그린다. 중요한 점: **한 번만 부르지 않는다.** 상태가 바뀔 때마다 **함수 전체를 처음부터 다시 호출**한다 = **리렌더(re-render)**.

그래서 함수 본문에 `let data = ...`라고 쓰면 리렌더마다 **매번 새로 초기화**돼 값이 보존되지 않는다. → 그래서 **state**가 필요하다(2장).

### Virtual DOM (질문: "여기서 VDOM 나오나?")

리렌더가 "함수 전체 재호출"이라면 화면 전체를 새로 그려 깜빡여야 할 것 같지만 안 그렇다. 이유가 **Virtual DOM**이다.

- **DOM:** 브라우저가 화면을 표현하는 실제 객체 트리. 직접 조작은 느리다.
- **Virtual DOM(VDOM):** React가 메모리에 든 **JS 객체로 된 가벼운 화면 설계도**. 컴포넌트가 반환하는 JSX가 이 VDOM 조각이다.
- **리렌더 시 실제 동작:** state 바뀜 → 함수 재호출 → 새 VDOM 생성 → **이전 VDOM과 비교(diffing)** → **달라진 부분만** 실제 DOM에 반영. 이 비교 과정을 **reconciliation(재조정)** 이라 한다.
- 그래서 "함수를 매번 다시 부르는데도 화면이 안 깜빡이고 바뀐 노드만 갱신"된다. `PostList`의 `key={post.id}`(4단계)가 바로 이 diffing이 "어느 항목이 같은 항목인지" 알아보게 돕는 장치.

---

## 2. 화면 계산의 경계 = 렌더 단계 (질문: "화면 계산의 경계가 정확히 어디까지?")

**경계 = 컴포넌트 함수가 호출되어 `return`으로 JSX를 돌려주기까지 실행되는 모든 코드.** React 용어로 **렌더 단계(render phase)**.

```tsx
function PostListPage() {
    // ┌─ 여기부터
    const [posts, setPosts] = useState([]);
    const visible = posts.filter(...);   // 순수 계산 OK
    // └─ return 까지가 "화면 계산"
    return <div>...</div>;
}
```

**렌더 단계의 철칙: 순수(pure)해야 한다.** 같은 입력이면 항상 같은 JSX를 내고, **바깥 세계를 건드리면 안 된다.**

| 렌더 단계에서 **금지** | 렌더 단계에서 **허용** |
|---|---|
| `fetch`/네트워크 요청 | props/state 읽기 |
| `setPosts(...)` 등 state 변경 | 그걸로 변수 계산 |
| `document.title=`, `localStorage`, 타이머 | `filter`/`map` 등 순수 변환 |
| 외부에 흔적 남기는 모든 것 | JSX 조립 |

금지된 것들은 **렌더가 끝난 뒤**, 즉 `useEffect` 안에서 한다. React 두 단계로 정리:
1. **렌더 단계** = 화면 계산(순수). 함수 호출 → JSX.
2. **커밋 이후** = 화면이 실제 DOM에 박힌 뒤 → `useEffect` 실행(부수효과 허용).

---

## 3. `useState` 깊이 파기

```ts
const [posts, setPosts] = useState<Post[]>([]);
```

### 3-1. 기억 칸(state)이란 (질문: "기억 칸이 `[]` 여기야?")

- **기억 칸(state)은 React가 컴포넌트 바깥(내부 메모리)에 만들어 들고 있다.** 코드에 직접 안 보인다.
- `useState<Post[]>([])` 호출 = "그 칸 하나 만들어줘(처음 값 `[]`), 그리고 **손잡이 2개** 줘"라는 요청.
- 돌려받는 손잡이 `[posts, setPosts]`:
  - `posts` = 지금 칸에 든 값을 **읽는** 손잡이
  - `setPosts` = 칸의 값을 **바꾸는** 손잡이 (호출하면 리렌더 예약)
- 선택했던 `[]`는 **기억 칸 자체가 아니라**, 그 칸에 **맨 처음 한 번** 넣는 초기값. 두 번째 렌더부터 이 `[]`는 무시된다(이미 칸이 있으니).

요약: `useState([])`는 **"칸 생성 + 초기화 + 손잡이 발급"을 한 번에 하는 함수.** `[]`는 그중 "초기화"의 입력값. 칸은 이름 없는 React 내부 저장소이고 손잡이로만 접근.

### 3-2. `<Post[]>`(타입) vs `([])`(값) — 층위가 다르다

- `<Post[]>` = **TS에게** 하는 말. "이 칸 값의 타입은 `Post[]`." 컴파일 후 **소멸**(런타임 영향 없음).
- `([])` = **JS 런타임에게** 하는 말. "실제 시작값은 이거." 실제 메모리에 들어감.
- `useState`는 `<>`(타입)과 `()`(값)를 **동시에** 받는다. 하나는 검사용, 하나는 실행용.

### 3-3. 왜 순서로 받나 (이름은 자유, 순서는 고정)

`useState`는 `{value, setValue}` 같은 이름표 붙은 객체가 아니라 그냥 `[값, 함수]` **배열**을 돌려준다. 배열은 이름 없이 **순서(0,1)** 만 있다. 그래서 `const [a, b] = useState(...)` → `a`=현재값, `b`=변경함수. **이름은 내 자유, 순서는 고정.** (관례상 `x`/`setX`.)

---

## 4. 구조분해(destructuring) = 언패킹 (질문: "구조분해가 뭐야? 언패킹?")

**구조분해 = 배열/객체를 통째로 받지 않고, 안의 원소를 꺼내 각각 변수에 바로 묶는 문법.** Python의 `a, b = (1, 2)`와 같은 개념.

```ts
// 구조분해 없이 (수동)
const result = useState(true);
const loading = result[0];
const setLoading = result[1];

// 구조분해로 (한 줄, 위와 완전히 동일)
const [loading, setLoading] = useState(true);
```

두 종류:
- **배열 구조분해 — 순서로 꺼냄:** `const [a, b] = [10, 20]` → `a=10, b=20`. 대괄호 `[]`. `useState`가 이걸 씀.
- **객체 구조분해 — 이름(key)으로 꺼냄:** `const {items} = data`. 중괄호 `{}`. 순서 무관, key 이름 일치 필요.

Python과 다른 점: JS는 **껍데기 기호가 필수.** 배열이면 `[a,b]`, 객체면 `{a,b}`. 이 껍데기가 "언패킹 중 + 배열이냐 객체냐"를 알려준다.

### 4-1. `{}`는 위치(맥락)에 따라 정반대 (질문: "중괄호로 감싸면 풀어받는 거랬는데 뭐야")

"`{}` = 풀어받기"는 **반쪽만 맞다.** `{}`의 본질은 "객체 모양"이고, 어느 쪽에 놓이느냐로 방향이 갈린다.

| 어디에 나오나 | 하는 일 | 예시 |
|---|---|---|
| `=`의 **왼쪽** | **풀어받기**(구조분해) | `const {items} = data;` |
| `=`의 **오른쪽** | **만들기**(객체 리터럴) | `const data = {items: []};` |
| `import ___ from` 안 | 골라 가져오기(named import) | `import {useState} from "react";` |
| 함수/if/for 뒤 | 코드 블록(문장 묶음) | `function f() { ... }` |
| JSX 안 | "여기 JS 값 꽂기" | `<p>{error}</p>` |

핵심: **`{}`가 받는 자리(`=` 왼쪽, import)면 푼다/꺼낸다, 주는 자리(`=` 오른쪽, return, 인자)면 만든다.** 대입 `=`을 기준으로 거울처럼 대칭. 배열도 똑같다 — `const arr = [10,20]`(오른쪽=만들기) vs `const [a,b] = arr`(왼쪽=풀기).

---

## 5. state 3칸의 타입은 왜 그렇게? (`posts` / `loading` / `error`)

비동기는 데이터가 **시간이 걸려** 도착하므로 화면이 항상 세 갈래다. 그래서 보통 state 3개.

```ts
const [posts, setPosts]     = useState<Post[]>([]);          // 데이터
const [loading, setLoading] = useState(true);                // 불러오는 중?
const [error, setError]     = useState<string | null>(null); // 에러 메시지
```

### 5-1. `<>` 쓸지 말지 — 타입 추론(inference)

TS는 초기값을 보고 타입을 **알아서 추측**한다.

| 칸 | 초기값 | `<>` | 이유 |
|---|---|---|---|
| `posts` | `[]` | **필요** `<Post[]>` | 빈 배열은 원소 타입을 모름 → `never[]`로 빠짐 → 직접 명시 |
| `loading` | `true` | **불필요** | `true`로 `boolean` 추론됨 |
| `error` | `null` | **필요** `<string\|null>` | null만 보면 "null만 담는 칸"으로 추론 → 나중에 `setError("실패")`에서 타입 에러. "문자열도 온다"고 미리 알려야 함 |

규칙: **초기값이 타입을 충분히 드러내면(`true`/`0`/`"hi"`) `<>` 생략, 빈 배열·`null`처럼 모호하면 `<>`로 명시.**

### 5-2. `loading`은 왜 boolean? (질문: "loading은 왜 boolean인데?")

`loading`이 답하는 질문은 **"지금 데이터를 불러오는 중인가?"** 하나뿐. 답은 **예(true)/아니오(false)** 둘뿐 → 그게 boolean의 정의. 시작은 `true`(아직 못 받았으니 "불러오는 중"), `finally`에서 `false`(기다림 끝).

> 원래 내가 `useState([])`로 잘못 썼던 이유: `[]`은 예/아니오가 아니고, JS에서 빈 배열은 **truthy**라 `if(loading)`이 늘 참 → 영원히 로딩에 갇힘.

### 5-3. 세 가지 화면 상태는 `loading`/`error`로 갈린다

목록 화면은 결국 **로딩 중 / 성공 / 실패** 3갈래다. 여기서 `posts`는 "무엇을 보여줄지"라는 **데이터 본체**이고, `loading`과 `error`는 "지금 어떤 상황인지"를 말해주는 **상태 표지판**이다.

| loading | error | 화면 |
|---|---|---|
| `true` | `null` | 불러오는 중 |
| `false` | `null` | 성공(목록) |
| `false` | `"메시지"` | 실패 |

`error`가 boolean이 아니라 `string|null`인 이유: error는 "있다/없다"만이 아니라 **무슨 메시지를 보여줄지**(내용)까지 담아야 해서. `null`=에러 없음, 문자열=그 내용. (초기값 `""`보다 `null`이 의도가 명확하고 타입과 일관적.)

---

## 6. `useEffect` — "렌더 끝난 뒤에 이걸 해" 예약

```ts
useEffect(() => { /* 부수효과 */ }, []);
//        ^1번 인자(콜백)        ^2번 인자(의존성 배열)
```

- **부수효과(side effect):** 화면 계산 자체가 아닌 모든 바깥 작업 — 데이터 가져오기, 타이머, 구독 등. React는 렌더 도중이 아니라 **렌더가 끝나 화면에 반영된 뒤** 실행하게 한다.
- `useEffect`는 "지금 실행"이 아니라 **"이 함수를 받아뒀다가 적절한 때 내가 부를게"** — 콜백을 React에 **맡기는** 호출.
- **1번 인자:** 실행할 부수효과 콜백.
- **2번 인자 = 의존성 배열(dependency array):** "이 안 값이 바뀌면 콜백을 다시 실행하라"는 목록.

헷갈리기 쉬운 포인트 하나: effect는 기본적으로 **렌더가 끝난 뒤 실행 후보**가 되고, 의존성 배열은 그 effect를 **언제 다시 실행할지**를 정한다. 즉 `[]`는 "effect가 없다"가 아니라 **"첫 실행 뒤 다시 돌 이유가 없다"**에 더 가깝다.

| 2번 인자 | 의미 | 결과 |
|---|---|---|
| `[]` (빈 배열) | 의존값 없음 | **개념적으로 첫 마운트 뒤 실행**. 개발 StrictMode에선 확인용으로 한 번 더 보일 수 있음 |
| `[id]` | id 바뀌면 재실행 | 상세페이지에서 쓸 것(다음 세션) |
| (생략) | 매 렌더마다 실행 | 보통 무한 루프 위험 |

---

## 7. 왜 렌더 단계에서 `setPosts`를 직접 부르면 무한 루프? (질문)

**`setPosts` 호출 = "리렌더 예약"** 이라는 정의 때문. 렌더 단계에서 부르면 자기 자신을 다시 부르는 꼴:

```tsx
function PostListPage() {
    const [posts, setPosts] = useState([]);
    setPosts([...]);   // ❌ 렌더 도중 호출
    return <div>...</div>;
}
```

추적: ① 함수 호출(1차 렌더) → ② `setPosts` 실행 → 리렌더 예약 → ③ 렌더 끝나면 함수 **다시 호출**(2차) → ④ 또 `setPosts` → 또 예약 → … **무한 루프.** (React가 감지하면 "Too many re-renders" 에러.)

**핵심:** `setPosts`가 위험한 게 아니라 **"렌더 단계에서" 부르는 게** 위험. `useEffect` 안에서 부르면 안전 — effect는 렌더가 **끝난 뒤** 실행되고, 의존성 `[]` 덕에 다시 안 돌아 루프가 안 생긴다. 그래서 fetch+setPosts를 effect 안에 넣는다.

---

## 8. ⭐ effect 안에서 async 쓰기 = Promise 반환 문제 (이 세션 최대 난관)

> 이 한 줄이 전부였다(내가 늦게 줘서 6~7턴 헤맴):
> **"`await`를 쓰려면 콜백이 `async`여야 하는데, `async`면 반환이 Promise가 되고, 그 반환 자리(`useEffect` 콜백의 반환)는 Promise면 안 되는 자리라서, async를 안쪽 `load`로 밀어 우회한다."**

아래는 그 한 줄을 떠받치는 사실들을 순서대로.

### 8-0. 먼저 `fetchPosts()`가 주는 값부터 정확히

이번 코드에서 `fetchPosts`의 반환 타입은 대략 아래처럼 생겼다.

```ts
Promise<{ items: Post[]; nextCursor?: string }>
```

층위를 나누면:
- `fetchPosts()` 호출 결과 = **Promise**
- `await fetchPosts()` 결과 = **`{ items, nextCursor }` 객체**
- `data.items` = 그 객체 안의 **`Post[]`**

이 구분을 먼저 잡아두면 `await`가 Promise를 "없애는 마법"이 아니라, **Promise가 끝난 뒤 그 안에 약속돼 있던 실제 값을 꺼내 주는 문법**이라는 감각이 생긴다.

### 8-1. 동기 함수 vs 비동기 함수 (질문: "동기 함수가 뭐야?")

- **동기(synchronous):** 부르면 그 자리에서 일을 다 끝내고 다음 줄로 넘어감. 중간에 "기다림" 없음.
  ```ts
  const x = add(2, 3);   // 즉시 5. 멈춤 없음.
  ```
- **비동기(asynchronous):** 일을 시작만 해놓고 "나중에 끝나면 알려줄게" 하며 **먼저 다음 줄로** 넘어감(`fetch`처럼 시간 걸리는 일).

"바깥 콜백은 동기 함수로 두라" = **`async`를 안 붙인 평범한 함수**로 두라 = React에 Promise를 안 돌려준다.

### 8-2. 정리 함수(cleanup function) (질문: "정리 함수가 뭐야?")

**effect가 "치웠다 다시 시작할 때" React가 불러주는 뒷정리용 함수.** effect 콜백이 함수를 **반환**하면 React가 그걸 정리 함수로 인식한다.

```ts
useEffect(() => {
    const id = setInterval(() => console.log("tick"), 1000);  // 켬
    return () => clearInterval(id);   // ← 반환된 이 함수가 cleanup
}, []);
```

타이머·구독·리스너를 **켜면** 컴포넌트가 사라질 때 **꺼야** 한다(안 끄면 누수). 그 "끄는 코드"를 콜백이 `return`하면 React가 보관했다가 언마운트/재실행 직전에 호출해준다. → **우리 fetch effect는 정리할 게 없어** `return` 안 하고 끝낸다(React가 받는 cleanup은 `undefined`).

**그래서 useEffect 콜백의 반환 슬롯은 "정리 함수 또는 없음(undefined)" 전용이다.**

### 8-3. async는 못 끄는 "Promise 포장기" (질문: "load가 뭘 돌려줘? await있으니 promise? 모순돼")

`async`가 붙은 함수는 **무조건 Promise를 반환**한다. `return`을 안 써도, 안에 `await`가 없어도.

| 함수 | return 썼나 | 실제 반환값 |
|---|---|---|
| `function a(){}` | 안 씀 | `undefined` |
| `async function b(){}` | 안 씀 | **`Promise<undefined>`** |

→ **`load`는 Promise를 돌려준다.** "await 있으니 Promise냐?"의 답은 예. 모순 아님. (6단계의 "async는 return을 Promise로 자동 포장"과 같은 얘기.)

### 8-4. 모순처럼 느껴진 이유 = 층위(어느 함수의 반환인가)

내가 한 말은 두 개였고 서로 다른 함수 얘기였다:
- "**바깥 effect 콜백**(`()=>{...}`)은 Promise를 돌려주면 안 된다." ✅
- "**안쪽 load**는 Promise를 반환한다." ✅ (모순 아님 — 다른 함수)

```ts
useEffect(() => {            // 함수 A (바깥 콜백). React가 A의 반환값을 본다.
    async function load() {  // 함수 B. async라 Promise 반환.
        await fetchPosts();
    }
    load();                  // B 호출. B의 Promise는 A 안에서 버려짐.
    // A에는 return 없음 → A는 undefined 반환
}, []);
```

**핵심: "Promise가 존재하느냐"가 문제가 아니라 "React에게 건네지느냐"가 문제.** `load`의 Promise는 A 안에서 버려지니 OK. 콜백 자체의 Promise(`useEffect(async ()=>...)`)는 React 손에 들어가니 NO.

### 8-5. 그럼 그냥 밖에서 await 하면? (질문) — 못 한다

```ts
useEffect(() => {
    const data = await fetchPosts();   // ❌ 문법 에러
}, []);
```

**`await`는 `async` 함수 안에서만 쓸 수 있는 문법.** 바깥 콜백은 async가 아니라 거기서 `await` 쓰면 **문법 자체가 안 됨**. 그렇다고 콜백을 async로 만들면 → 8-4의 금지 상황(React가 Promise 받음).

**딜레마:** await 쓰려면 async 필요 ↔ 콜백을 async로 만들면 React 규칙 위반.
**탈출구:** 안에 async `load`를 만들어 거기서 await를 쓰고, 바깥 콜백은 비-async로 둬 `load()`만 호출(Promise는 버림). → `load`는 **"await를 합법적으로 쓸 async 울타리"**.

> "저장 안 할 거면 load로 감쌀 이유 없잖아?"의 답: 저장이 목적이 아니라 **await를 쓸 async 함수가 필요해서** 감싸는 것.

### 8-6. Promise는 인자/반환으로 못 쓰나? (질문: "일반 컴포넌트에선 되잖아")

**된다. Promise 자체엔 아무 금지도 없다.** 인자로 받기·반환하기·변수에 담기·async 핸들러 전부 정상. 제한은 **React가 반환값을 특정 용도로 예약한 두 자리**뿐:

| 자리 | React가 반환값을 뭘로 해석 | 그래서 금지 |
|---|---|---|
| ① 컴포넌트 함수 본체 | "화면(JSX)" | `async function PostListPage()` ❌ — Promise를 JSX로 못 그림 |
| ② `useEffect`의 콜백 | "정리 함수 또는 없음" | `useEffect(async ()=>...)` ❌ — Promise는 cleanup 아님 |

이 두 슬롯 **바깥에서는** async·Promise 전부 자유(이벤트 핸들러 `onClick={async ...}`, 일반 헬퍼 등). 그래서 "일반 컴포넌트에선 잘 되는" 게 맞다.

### 8-7. "인자로도 안 된다며?" — 인자가 아니라 그 인자의 반환이 문제 (질문)

`useEffect(async ()=>{...}, [])`에서 `async ()=>{...}`는 **함수**다(Promise 아님). useEffect는 정상적으로 함수를 인자로 받는다. 문제는 React가 그 함수를 **호출했을 때**:

```
React 내부: const cleanup = 콜백();   // 콜백이 async면 → cleanup에 Promise가 담김 → 깨짐
```

| 단계 | 문제? |
|---|---|
| useEffect에 `async ()=>{}` 전달(인자) | ❌ 문제없음(함수는 정상 인자) |
| React가 콜백 호출 → Promise 반환 | ✅ 여기서 깨짐 |

**→ "인자가 막힌 게 아니라, 인자로 받은 함수의 반환이 cleanup 슬롯과 충돌."**

### 8-8. "인자로 넣고 반환 안 하게 만들면?" (질문) — async는 못 끈다

이게 실제 막혔던 전제였다. **`async`를 붙인 순간 "반환 안 함"이라는 선택지가 사라진다.** `return`을 안 써도 `Promise<undefined>`가 나온다(8-3 표).

```ts
useEffect(async () => {
    await fetchPosts();   // return 안 씀
}, []);                    // 그래도 콜백은 Promise<undefined> 반환 → cleanup 자리 깨짐
```  

undefined를 돌려주려면 콜백이 **async가 아니어야** 한다 → 그러면 await를 못 쓴다 → 그래서 async를 안쪽 `load`로 옮긴다.

| 콜백 | return 썼나 | 실제 반환 | cleanup 자리 |
|---|---|---|---|
| `async () => {}` | 안 씀 | `Promise<undefined>` | ❌ |
| `() => {}` | 안 씀 | `undefined` | ✅ |
| `() => { load(); }` | 안 씀 | `undefined` | ✅ (load의 Promise는 버려짐) |

### 8-9. 결론 — 두 요구를 두 함수에 나눠 맡김 (질문: "await 쓰고 싶은데 반환값 때문에 맞춘 거라고?")

맞다. 한 함수가 "await 쓰기"와 "반환 깨끗히 두기"를 동시에 만족 못 한다. 그래서 역할을 쪼갠다:

| 함수 | 역할 | async? |
|---|---|---|
| 바깥 콜백 `()=>{}` | cleanup 규칙 지키기(반환 깨끗) | ✗ |
| 안쪽 `load` | await 쓰기 | ✓ |

await는 `load` 안에서 쓰고, "반환 깨끗"은 바깥이 지킨다.

---

## 9. 더 간단한 방법 없어? 실무에서도 이래? (질문)

솔직히 raw useEffect는 "기초 골격"이고, 실무는 대부분 라이브러리로 이 전체를 몇 줄로 줄인다.

**① IIFE(즉시실행) — 이름 생략:**
```ts
useEffect(() => {
    (async () => {
        const data = await fetchPosts();
        setPosts(data.items);
    })();
}, []);
```

**② `.then()` — async 아예 안 씀:**
```ts
useEffect(() => {
    fetchPosts().then(d => setPosts(d.items));
}, []);
```
await를 안 쓰니 async 울타리 불필요 → 한 줄. (단 try/catch/finally로 loading/error 깔끔히 다루긴 ①이 편함.)

**③ 커스텀 훅(실무 정통) — 복잡함을 한 번 만들어 숨김:**
```ts
function usePosts() {
    const [posts, setPosts] = useState<Post[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    useEffect(() => { /* fetch + set */ }, []);
    return { posts, loading, error };
}
// 쓰는 쪽: const { posts, loading, error } = usePosts();
```

**④ React Query(TanStack)/SWR(진짜 실무):**
```ts
const { data, isLoading, error } = useQuery({ queryKey: ["posts"], queryFn: fetchPosts });
```
loading/error/캐싱/재요청/중복제거까지 다 해준다. 실무 데이터 패칭은 거의 이쪽.

**그럼 왜 손으로 배우나?** 라이브러리는 이 raw 패턴을 자동화한 것. 안에서 무슨 일이 일어나는지 모르면 라이브러리가 이상하게 굴 때 못 고친다. 이번 주는 의도적으로 **React 맨바닥(useState/useEffect)**. 골격을 익힌 뒤 React Query를 얹으면 "아 이게 그 useEffect를 대신해주는구나" 하고 바로 이해된다.

---

## 10. `try / catch / finally` — 비동기 3갈래 처리

```ts
try {
    const data = await fetchPosts();
    setPosts(data.items);       // 성공 경로
} catch {
    setError("...");            // 실패(throw) 경로
} finally {
    setLoading(false);          // 무조건(성공/실패 둘 다) 마지막
}
```

- `try` = "이 안에서 throw 나면 `catch`로 점프".
- `await`는 Promise가 **reject**되면 그 자리에서 `throw`된 것처럼 동작한다. 그래서 `fetchPosts()`가 실패하면 `await fetchPosts()` 줄에서 바로 `catch`로 넘어간다.
- `catch` = throw된 에러를 잡아 대응. (에러 객체를 안 쓰면 `catch (e)` 대신 `catch {` — optional catch binding. lint의 "`e` 안 씀" 경고 해소.)
- `finally` = 성공이든 실패든 **무조건** 마지막에 실행 → 로딩 끄기는 둘 다 해야 하므로 여기 한 줄.

| 경우 | try | catch | finally |
|---|---|---|---|
| 성공 | 실행(`setPosts`) | 건너뜀 | 실행(`setLoading(false)`) |
| 실패(throw) | 도중 중단 | 실행(`setError`) | 실행(`setLoading(false)`) |

---

## 11. `setPosts`의 정체와 호출 시 동작 (질문: "setPosts가 정확히 뭐야? useState에서 어떻게 나왔지?")

### 정체
`setPosts`는 **`posts` 칸에 묶인 "변경 명령" 함수(setter).** React가 만들어 `useState` 반환 배열의 1번 자리에 넣어 건넨 것.

### useState에서 나온 과정
`useState([])` 호출 시 React가 ① state 칸 생성(초기값 `[]`) → ② 그 칸 전용 setter 생성 → ③ `[현재값, setter]` 배열 반환. 우리가 1번을 `setPosts`로 이름 붙인 것. setter는 그 칸이 어딘지 내부적으로 알아서, `setPosts(x)`만 부르면 정확히 그 칸을 바꾼다.

### `setPosts(data.items)` 호출 시
1. **칸 값 예약 변경:** "다음 렌더 때 `posts`를 `data.items`로." (즉시 아님 — 부른 직후 줄에서 `posts`를 읽으면 **옛 값**.)
2. **리렌더 예약.**
3. **함수 재호출:** React가 `PostListPage()`를 다시 호출 → `useState`가 **새 값**을 `posts`로 돌려줌.
4. 새 `posts`로 JSX 재계산 → VDOM diff → 바뀐 부분만 화면 갱신.

### 왜 `posts = data.items`로 직접 안 바꾸나
직접 대입하면 **React가 바뀐 걸 모른다** → 리렌더 안 일어나 화면 안 바뀜. (게다가 `const`라 에러.) `setPosts`를 거쳐야 React가 "바뀜 + 다시 그려야 함"을 안다. **setter = 변경 사실을 React에 알리는 리모컨.**

`data.items`의 `.items`는 `data`(`{items, nextCursor}`) 객체에서 글 목록만 꺼내는 **점 접근**. 화면에 뿌릴 건 `items`뿐.

---

## 12. StrictMode — effect 2회 실행 vs 무한 루프

개발 모드(`<React.StrictMode>`, main.tsx)에서 React는 effect를 **일부러 두 번** 실행(마운트→정리→다시 마운트). 버그가 아니라 "정리(cleanup)를 제대로 했는지" 검사하는 것. **프로덕션 빌드에선 1번만.**

```
1) effect 실행      → 로그 1번째
2) cleanup 실행      → 반환한 정리 함수가 있으면 호출
3) effect 다시 실행  → 로그 2번째
```

**구분:**
- 콘솔에 **딱 2번** 찍히고 멈춤 = **StrictMode 검사**(개발 모드 정상). 의심 X.
- 콘솔에 **끝없이** 찍힘 = **의존성 배열 실수**(진짜 버그). `[]`를 빠뜨렸거나, 배열에 매 렌더 새로 만들어지는 객체/함수를 넣은 것.

```ts
useEffect(() => { ...; setPosts(...); }, []);   // ✅ 처음 한 번(개발 2번). 그 뒤 조용.
useEffect(() => { ...; setPosts(...); });        // ❌ 의존성 없음 → 매 렌더 → setPosts → 리렌더 → 폭주
```

---

## 13. 이번 세션에서 고친 버그

| 위치 | 잘못 | 고침 | 종류 |
|---|---|---|---|
| import & 마지막 줄 | `posts={MOCK_POSTS}` (직접 import 안 걷어냄) | import 삭제 + `posts={posts}` | 빌드 깨짐 |
| `loading` 초기값 | `useState([])` | `useState(true)` | truthy 빈배열로 영원히 로딩 |
| `error` 초기값 | `useState<string\|null>("")` | `useState<string\|null>(null)` | 의도/일관성 |
| `finally` | `setLoading()` (인자 없음) | `setLoading(false)` | undefined 들어감 |
| 의존성 배열 | `}, posts)` | `}, [])` | posts 의존 → effect가 posts 바꿈 → 무한 루프 |
| `catch (e)` | `e` 안 써서 lint 에러 | `catch {` (optional catch binding) | lint |
| `p-9` | Tailwind에 없는 클래스 | `p-8` | 그 자리 패딩 무시(빌드는 통과) |

검증: `./node_modules/.bin/tsc -b`·`npm run lint` 둘 다 통과.

---

## 14. 전체 흐름 한 번에 (시간 순)

1. **1차 렌더:** 함수 호출 → `loading=true, posts=[], error=null` → useEffect는 콜백 **등록만** → `if(loading)` 참 → **"불러오는 중…" 화면**.
2. **화면 그린 직후:** 등록된 콜백 실행 → `load()` → `await fetchPosts()` (0.3초 대기).
3. **0.3초 후 성공:** `setPosts(data.items)` + `finally` `setLoading(false)` → state 2개 바뀜 → 리렌더 예약.
4. **2차 렌더:** 함수 재호출 → `loading=false, posts=[실제 글]` → `if`들 통과 → **목록 화면**.
5. 의존성 `[]`이라 **같은 마운트 안에서는** effect가 다시 안 돈다 → 무한 루프 없음.
6. 개발 StrictMode에선 이 1~5 흐름이 **확인용으로 한 번 더** 보일 수 있다. 이건 재마운트 검사이지, 무한 루프 버그가 아니다.

---

## 15. 한 줄 요약 모음

- 컴포넌트 = 함수, state 바뀌면 **함수 전체 재호출**(리렌더). 화면 깜빡임 없는 건 **Virtual DOM diff** 덕.
- **렌더 단계는 순수해야** 한다(fetch·setState 금지). 부수효과는 **`useEffect`**(렌더 끝난 뒤)에서.
- `useState(초기값)` = **칸 생성+초기화+`[값, setter]` 발급.** 손잡이는 **순서로** 받음(구조분해).
- `<>`=타입(TS, 소멸), `()`=값(런타임). 초기값이 모호(`[]`/`null`)할 때만 `<>` 명시.
- 의존성 `[]` = **개념적으로 첫 마운트 뒤 실행.** 개발 StrictMode에서는 확인용으로 2회 보일 수 있다. 렌더 단계 setState·의존성 누락 = **무한 루프**.
- effect에서 **await 쓰려면** async 함수가 필요한데 **콜백을 async로 만들면 반환이 Promise가 돼 cleanup 슬롯과 충돌** → async를 **안쪽 헬퍼(load)** 로 밀고 바깥 콜백은 비-async로.
- **async는 못 끄는 Promise 포장기**(빈손도 `Promise<undefined>`). Promise 금지가 아니라 **두 예약 슬롯(컴포넌트 본체=JSX, useEffect 콜백=cleanup)** 만 async 불가.
- 비동기는 **loading/error/성공 3갈래** → `try/catch/finally`로 처리.
- `setPosts` = React 발급 리모컨, **"값 바꿔라 + 다시 그려라"를 알림.** 직접 대입은 React가 모름.
- StrictMode **2번 실행=정상**(개발 검사), **무한=버그**(의존성 실수).

---

## 16. 헷갈리기 쉬운 구분 4쌍

- `fetchPosts()` = Promise / `await fetchPosts()` = 실제 객체 / `data.items` = 그 객체 안의 글 배열
- `posts` = 지금 들고 있는 state 값 / `setPosts(...)` = 다음 렌더를 예약하는 setter
- `[]` = 재실행할 의존값 없음 / 의존성 생략 = 매 렌더마다 재실행
- StrictMode 2회 = 개발 검사 / 무한 루프 = state 변경 타이밍이 잘못된 버그

---

## 17. 다음 세션 예고 (7단계 나머지)

`PostDetailPage.tsx` — `useParams()`로 URL의 id를 꺼내 `fetchPostById(id)`로 글 하나를 받아온다. 새 포인트: **의존성 배열을 `[]`이 아니라 `[id]`** 로 둬서 "id가 바뀌면 다시 불러오기". + `App.tsx`에 상세 라우트(`/posts/:id`) 추가.
