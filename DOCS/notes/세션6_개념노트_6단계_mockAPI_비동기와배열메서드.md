# 세션 6 개념 노트 — 6단계 Day2 mock API (`api/posts.ts`)

> 날짜: 2026-06-08 (세션 6) · 복습용
> 다룬 단계: **6단계 Day2 mock API** — `api/posts.ts`에 `fetchPosts` / `fetchPostById` / `createPost` 세 함수 작성.
> 세션 5가 "App.tsx 라우터 연결(화면 쪽)"이었다면, 이번엔 **데이터를 가져오는 창구(API 함수)** 를 처음 만든 세션이다.
> 핵심 주제: **비동기(async/await/Promise) + 배열 메서드(filter/some/find/push) + 계약형 시그니처**.
> 아래는 작성한 코드 → 개념을 내가 질문한 순서대로 전부 정리.

---

## 0. 이번 세션에서 작성한 코드 (`frontend/src/api/posts.ts`)

```ts
import type { Post, NewPost } from "../types/post";   // 타입 → import type
import { MOCK_POSTS } from "./mockData";              // 실제 값 → 그냥 import

/* post 목록을 가져오는 함수 */
export async function fetchPosts(
    params?: { q?: string; tagId?: string; cursor?: string }
): Promise<{ items: Post[]; nextCursor?: string }> {
    await new Promise((resolve) => setTimeout(resolve, 300));   // 네트워크 지연 흉내
    let result = MOCK_POSTS;

    if (params?.q) {                                            // 검색어 필터
        result = result.filter((post) => post.title.includes(params.q!));
    }
    if (params?.tagId) {                                        // 태그 필터
        result = result.filter((post) => post.tags.some((t) => t.id === params.tagId));
    }
    return { items: result, nextCursor: undefined };
}

/* id로 post 한 개를 가져오는 함수 */
export async function fetchPostById(id: string): Promise<Post> {
    await new Promise((resolve) => setTimeout(resolve, 300));
    const found = MOCK_POSTS.find((post) => post.id === id);
    if (!found) {
        throw new Error("글을 찾을 수 없습니다: " + id);
    }
    return found;
}

/* 새 변명글을 제출하는 함수 */
export async function createPost(input: NewPost): Promise<Post> {
    await new Promise((resolve) => setTimeout(resolve, 300));
    const newPost: Post = {
        ...input,
        id: crypto.randomUUID(),
        createdAt: new Date().toISOString(),
    };
    MOCK_POSTS.push(newPost);
    return newPost;
}
```

### 작성 중 거친 버그/수정 (전부 같은 패턴의 오해에서 나옴)

| 위치 | 잘못 쓴 것 | 고친 것 | 왜 |
|---|---|---|---|
| fetchPosts | `let result = {Post}` | `MOCK_POSTS` | `Post`는 타입(모양)이지 데이터가 아님 |
| fetchPosts | `result.title(...)` | `result.filter(...)` | `.title`은 글 1개의 필드, 배열 메서드 아님 |
| fetchPosts | `post.title.filter(...)` | `post.title.includes(...)` | 문자열엔 `.includes`, 배열엔 `.filter` (자리 뒤바뀜) |
| fetchPostById | `Promise<item: Post>` / `Promise<(item: Post)>` | `Promise<Post>` | 단일 리소스는 봉투 안 씌움 + 문법 오류 |
| fetchPostById | `return (item: found)` | `return found` | 같은 봉투 오해 |
| createPost | `MOCK_POSTS.concat(newPost)` | `MOCK_POSTS.push(newPost)` | concat은 비파괴(새 배열 버림), push가 원본 수정 |
| import | `{ Post }`만 | `{ Post, NewPost }` | NewPost를 안 가져오면 `TS2304 Cannot find name` |

→ 세 함수 완성 + import 보강 후 `tsc -b`·`lint` 통과 목표. (마지막에 `NewPost` import 빠뜨려 tsc 에러 → 추가해서 해결.)

---

## 1. 이 파일(`api/posts.ts`)이 "무엇"인가 — 타입도 컴포넌트도 아닌 "API/로직 함수"

우리가 만든 것은 종류가 셋으로 나뉜다. **판별 기준은 "함수가 무엇을 `return` 하는가".**

| 종류 | 무엇 | return | 파일 | 확장자 |
|---|---|---|---|---|
| **타입** | 데이터의 모양(설계도) | 없음 — 컴파일 후 사라짐 | `types/post.ts` | `.ts` |
| **컴포넌트** | 데이터 → 화면(JSX)으로 바꾸는 함수 | **JSX** (`<div>...`) | `PostCard.tsx`, `App.tsx` | `.tsx` |
| **API/로직 함수** | 데이터를 가져오거나 가공 | **데이터(값)** | **`api/posts.ts`** | `.ts` |

- `fetchPosts`는 `return { items, nextCursor }` → **데이터**를 돌려준다 → 컴포넌트 아님(화면 한 조각도 안 만듦).
- `.tsx` = JSX(`<태그>`)를 쓸 수 있는 파일. `.ts` = JSX 없는 순수 TS. → `posts.ts`가 `.ts`인 건 "화면 안 그린다"는 신호.
- 단, 타입 파일도 `.ts`라 확장자만으론 타입/로직 구분이 안 됨 → "return이 화면이냐 데이터냐"로 가른다.

### 이 파일의 존재 이유 (중간 창구)
지금까지 `PostListPage`는 `MOCK_POSTS`를 **직접** import해 썼다(냉장고 직접 열기). API 함수가 생기면 화면은 냉장고를 안 열고 **"글 목록 주세요"라고 주문**만 한다(웨이터). 화면은 어디서 어떻게 가져오는지 모른다.
→ **목적:** 다음 주 진짜 서버(axios)로 바꿀 때, 이 함수 **본문만** 고치면 화면 코드는 한 글자도 안 바뀌게 하려고. 그래서 함수의 **겉모양(시그니처)** 을 진짜 REST 계약 모양에 미리 맞춘다.

---

## 2. 동기 vs 비동기, 그리고 async / await / Promise

### 동기 vs 비동기
- 지금까지 코드는 **동기(synchronous)**: 위→아래로, 한 줄 끝나야 다음 줄. 계산은 즉시 끝나니까.
- 네트워크 요청은 답이 **나중에**(0.1초~몇 초) 온다. 동기처럼 "올 때까지 줄 세워 기다리면" 화면 전체가 얼어붙음. 그래서 **비동기(asynchronous)**: "요청만 던지고, 답은 도착하면 그때 받는다."

### 키워드 뜻
- **`async`** = asynchronous(비동기)의 줄임. 함수 앞에 붙이면 "이 함수는 비동기다 = 안에서 `await`를 쓸 수 있고, 결과는 Promise에 담겨 나간다".
- **`await`** = "기다리다". `await 값` = "그 값이 도착할 때까지 **이 함수 안에서만** 잠깐 멈춤". 화면 전체는 안 멈춤(이 함수만 대기실에 들어갔다 나옴).

### Promise = "나중에 올 값"을 담는 상자
- `Promise<Post>` = "나중에 Post 하나가 올 거야", `Promise<Post[]>` = "나중에 배열이 올 거야".
- `async` 함수는 반환이 자동으로 `Promise<...>`로 감싸진다. 그래서 시그니처에 `: Promise<...>`라고 적는다.
- `await`는 그 상자를 **열어서 안의 진짜 값을 꺼내는** 동작.

---

## 3. 줄 12 `await new Promise((resolve) => setTimeout(resolve, 300))` — 가짜 지연

서버가 없으니 "기다림"을 가짜로 만든다.

### setTimeout
- `setTimeout(함수, 밀리초)` = "지정 시간 뒤에 함수를 실행하라". `setTimeout(resolve, 300)` = 0.3초 뒤 `resolve` 실행.
- 단, `setTimeout`은 **Promise를 안 돌려준다** → `await`를 직접 못 붙인다(`await`는 Promise한테만 통함).
- 그래서 "0.3초 대기"를 `await`로 기다릴 수 있게 **`new Promise`로 감싼다.**

### `resolve`의 정확한 정체 (비유 말고 사실)
`resolve`는 **함수**다. `new Promise(executor)`를 호출하면 Promise 생성자가 `executor`를 **즉시 동기 실행**하면서 두 개의 함수를 인자로 넣어준다 — 그 첫 번째가 `resolve`(두 번째는 `reject`). 즉 **우리가 만드는 게 아니라 Promise 생성자가 만들어 주입**한다.

Promise는 내부에 **상태(state)** 와 **결과값**을 가진다:
- `pending`(대기) — 생성 직후 기본
- `fulfilled`(이행됨)
- `rejected`(거부됨)

`resolve(v)`를 호출하면 → **상태가 `pending → fulfilled`로 전이되고 결과값이 `v`로 확정**된다. 그게 전부다. `await`는 그 Promise가 `pending`인 동안 async 함수 실행을 **중단(suspend)** 시키고, `fulfilled`로 전이되면 **결과값으로 평가되며 실행을 재개**한다.

### 줄 12 동작 순서
1. `new Promise(...)` 생성 → 상태 `pending`. 생성자가 `executor`를 즉시 실행하며 `resolve` 주입.
2. `executor` 본문 `setTimeout(resolve, 300)` 실행 → **300ms 뒤 resolve 호출 예약**(아직 `pending`).
3. `await`가 이 `pending` Promise를 만나 async 함수 중단.
4. 300ms 경과 → 타이머가 `resolve()` 호출 → 상태 `pending → fulfilled`(결과값 `undefined`).
5. `await`가 `undefined`로 평가되고 함수 재개 → 다음 줄로.

한마디: **"0.3초 기다렸다가 다음 줄로." setTimeout은 await가 안 되니 Promise로 감쌌고, 안의 함수는 '언제 완료할지' 정하는 설명서다.**

---

## 4. `new Promise`(값) vs `Promise<...>`(타입) — 같은 단어, 다른 층위

| | `Promise<T>` | `new Promise(...)` |
|---|---|---|
| 정체 | **타입**(모양 설명) | **값**(실제 객체 생성, 런타임) |
| `new` | 없음 | 있음 |
| 괄호 | `<T>` 제네릭 타입 인자 | `(executor)` 실행 함수 인자 |
| 존재 시점 | 컴파일 타임(빌드 후 사라짐) | 런타임(메모리에 실제) |
| 위치 | `: 타입` 자리(시그니처) | 식(expression) 자리(본문) |

- 줄 10 `Promise<{items,...}>` = "이 함수의 **반환 타입**은 이거다"(설명).
- 줄 12 `new Promise(...)` = "0.3초 대기용 **실제 Promise 객체**를 만든다"(동작).
- 비유: `let p: Promise<number>`(타입)와 `p = new Promise(...)`(값)의 관계 = `let x: Post`와 `{id:"p1",...}`의 관계와 같음.

### 함수 반환값은 어디서 Promise에 담기나? → `async`가 자동으로
`return` 줄에는 `new Promise`가 없다. **줄 8의 `async`가 포장기다.** 규칙: **async 함수의 `return 값`은 자동으로 Promise로 감싸져 나간다.**
```ts
async function f() { return 3; }
const x = f();        // x는 3이 아니라 Promise<number>! (async가 포장)
const y = await f();  // y는 3 (await가 풂)
```
⚠️ **함수 안엔 Promise가 둘**이고 무관하다:
- 줄 12 `new Promise(...)` = **명시적**, 0.3초 대기용, 함수 **안**의 await가 즉시 풂, 담긴 값 `undefined`.
- 반환 Promise = **암묵적**(async가 자동), 결과 전달용, **호출한 쪽**의 await가 풂, 담긴 값 `{items, nextCursor}`.

호출 흐름: `const r = await fetchPosts(...)` → ① 호출 즉시 Promise(pending) 반환 → ② 호출자 await가 대기 → ③ 함수 안 return 실행되며 fulfilled로 확정 → ④ await가 열어 알맹이를 `r`에 넣음.
- 비유: `return`=택배 물건, `async`=자동 포장기(상자=Promise), `await`=상자 뜯어 물건 꺼내기.

---

## 5. 시그니처를 "계약 모양"으로 — params 객체와 반환 봉투

```ts
fetchPosts(params?: { q?: string; tagId?: string; cursor?: string })
    : Promise<{ items: Post[]; nextCursor?: string }>
```
- `params?`의 `?` = "이 인자는 있어도 없어도 됨(옵셔널)". `fetchPosts()` 빈손 호출도 허용.
- `q` = query(검색어), `tagId` = 태그 id, `cursor` = 페이징 위치.
- 반환이 `Post[]`가 아니라 `{ items, nextCursor }` 객체인 이유: 진짜 서버는 "글 목록 + 다음 페이지 커서"를 같이 준다. 미리 맞춰두면 다음 주 axios로 바꿔도 화면이 그대로.
- **핵심 규칙:** 검색·태그·페이징 같은 거르기 로직은 **화면이 아니라 이 함수 안**에 둔다. 화면은 조건만 넘기고 결과만 받는다.

### cursor / nextCursor (페이징)
- **페이징(paging):** 글이 많으면 한 번에 다 안 주고 "20개씩" 끊어 준다.
- **cursor** = "직전에 어디까지 줬는지" 가리키는 **책갈피**(불투명 토큰).
- 두 이름은 같은 책갈피인데 방향이 반대:

| | 방향 | 뜻 |
|---|---|---|
| `cursor` | 들어갈 때(params) | "**여기서부터** 줘"(요청) |
| `nextCursor` | 나올 때(반환) | "**여기까지** 줬어, 다음은 이 위치부터"(응답) |

- 흐름: `fetchPosts()` → `{items, nextCursor:"40"}` → 화면이 보관 → 더보기 → `fetchPosts({cursor:"40"})` → ... → `nextCursor: undefined`면 "마지막 페이지(더 없음)".
- **cursor가 string인 이유:** 서버마다 cursor 내용이 다름(id `"p3"`, 인코딩 문자열, 타임스탬프...). 다 담을 공통 그릇이 string. 우리 `Post.id`도 string이고, 보통 cursor = "마지막 글의 id"라 자연스러움. number로 두면 숫자 위치에만 묶임.
- 지금은 페이징이 stretch라 **자리(시그니처)만 만들고 `nextCursor: undefined`로 비워둠.**

---

## 6. 매개변수(parameter) vs 인자(argument)

한국어로 둘 다 "인자"라 섞어 쓰지만 다른 개념.

| | 매개변수(parameter) | 인자(argument) |
|---|---|---|
| 언제 | 함수를 **만들 때** | 함수를 **부를 때** |
| 정체 | **빈 그릇**(이름표) | 그릇에 담는 **실제 값** |
| 위치 | 함수 정의의 `( )` 안 | 호출의 `( )` 안 |

- 식당 비유: 메뉴판의 빈 칸(매개변수) vs 손님이 적은 "콜라"(인자).
- 우리 코드: `function fetchPosts(params?: {...})`의 `params` = 매개변수 / `fetchPosts({ q: "지하철" })`의 `{ q: "지하철" }` = 인자. 호출 순간 인자가 매개변수 그릇에 담긴다.
- 함수는 만들 때 값을 모르니 빈 이름(`params`)으로 자리만 잡고, 나중에 어떤 값으로 부르든 **같은 함수를 재사용**한다.

### 파라미터 순서 / 이름 규칙
**(A) 위치 기반 파라미터 — 순서 중요, 이름 자유**
```ts
function f(a: string, b: number) {}
f("hi", 3)   // 적은 순서대로 꽂힘. f(3,"hi")는 타입 에러.
```
정의 안의 이름(a, b)은 내부 변수명일 뿐, 호출자는 위치로 넘긴다.

**(B) 객체 프로퍼티 — 순서 무관, 키 이름 고정** ← 우리 `fetchPosts`
```ts
fetchPosts({ q:"지하철", tagId:"t1" })  // 순서 바꿔도 동일(이름으로 찾으니까)
```
- 바깥 이름(`params`)은 자유, **안의 키(`q`/`tagId`/`cursor`)는 고정**. 본문이 `params.q`로 이름 접근하므로 호출자도 정확히 `q`라고 줘야 함.
- 객체로 묶는 이유 중 하나가 이 "순서에서 자유로움". 또 진짜 서버 쿼리 파라미터 이름과 맞춰야 해서 키는 함부로 못 바꿈.

---

## 7. 배열 메서드와 콜백 — filter / includes / some / find / push

### 콜백(callback)이란
"내가 직접 부르지 않고, 다른 함수에 넘겨서 **그쪽이 대신 불러주는** 함수." `.filter`가 원소를 하나씩 꺼내 `(post)=>...`를 대신 부르고, `setTimeout`이 0.3초 뒤 `resolve`를 대신 부른다.
- `fetchPosts` 자체는 콜백 아님(우리가 직접 호출). 콜백은 그 **안의 작은 함수**들.

### `(arg) => 실행` = 화살표 함수(콜백)
```ts
result.filter( (post) => post.title.includes(params.q!) )
//             └────────── 이 화살표 함수가 콜백 ─────────┘
```
- `(post)` = filter가 꺼내준 원소 하나를 받는 매개변수.
- 이름은 자유(`post`/`p`/`x`). 안쪽 `.some((t)=>...)`의 `t`도 마찬가지 — `post.tags`(Tag 배열)에서 꺼낸 Tag 하나. "갑자기 등장"한 게 아니라 some이 넘겨주는 원소를 받는 이름.

### 반복문이 메서드 안에 숨어있다
`for`를 안 써도 `.filter`/`.some`/`.find`/`.map`이 **내부에 반복문을 품고** 원소를 0번부터 순서대로 꺼내 콜백을 호출한다.
```ts
// post.tags.some((t)=>t.id===x) 가 내부에서 하는 일(개념)
for (let i=0; i<post.tags.length; i++){
  const t = post.tags[i];
  if (t.id === x) return true;   // 하나라도 참이면 즉시 true
}
return false;
```

### 각 메서드 성격 (★중요: 파괴적 vs 비파괴적)
| 메서드 | 대상 | 하는 일 | 원본 변경? | 결과 처리 |
|---|---|---|---|---|
| `.filter(조건)` | 배열 | 조건 참인 원소만 모은 **새 배열** | 안 함(비파괴) | `result = arr.filter(...)` 재대입 필요 |
| `.some(조건)` | 배열 | **하나라도** 참이면 true(즉시 멈춤) | 안 함 | boolean 사용 |
| `.find(조건)` | 배열 | 조건 맞는 **첫 원소 1개**, 없으면 `undefined` | 안 함 | 받아서 사용 |
| `.includes("글자")` | 문자열/배열 | 그게 들어있나? true/false | 안 함 | boolean 사용 |
| `.map(변환)` | 배열 | 각각 변환한 **새 배열** | 안 함(비파괴) | 재대입/사용 |
| `.push(x)` | 배열 | 끝에 밀어넣음 | **함(파괴적)** | 재대입 불필요(원본 직접) |
| `.concat(x)` | 배열 | x 붙인 **새 배열** | 안 함(비파괴) | 받아야 의미 |

- **버그 교훈 1:** `result.filter(...)`만 쓰고 재대입을 빼면 거른 결과가 사라진다 → `result = result.filter(...)`. 이래서 `let result`(재대입하니 const 아님).
- **버그 교훈 2:** `MOCK_POSTS.concat(newPost)`는 새 배열을 만들어 **버린다** → 원본 안 바뀜(새 글 안 보임). 원본에 직접 추가하려면 `MOCK_POSTS.push(newPost)`.
- 정리: filter/map/concat/slice = **새 배열 반환(비파괴)** / push/sort/splice = **원본 수정(파괴적)**.

### 검색·태그 필터 구조
```ts
// 검색: 각 글의 title이 q를 포함하는 것만
result = result.filter((post) => post.title.includes(params.q!));
// 태그: 각 글의 tags 중 하나라도 tagId와 일치하는 것만
result = result.filter((post) => post.tags.some((t) => t.id === params.tagId));
```
- 바깥 `.filter`는 배열(result)에, 안쪽 `.includes`는 문자열(title)에, `.some`은 배열(tags)에. **대상 타입에 맞는 메서드를 써야 함.**

---

## 8. `===` vs `==`

| | `==` (느슨) | `===` (엄격) |
|---|---|---|
| 타입 다르면 | 억지로 변환해 비교 | 무조건 false |
| 비교 | 값만 | 값 + 타입 |

```ts
"1" == 1     // true  (변환됨) — 예측 어려움
"1" === 1    // false (string vs number)
"t1" === "t1"// true
```
- `==`의 자동 변환(`0==""`이 true 등)은 버그 온상 → **JS/TS 표준은 `===`/`!==`**. 이 프로젝트 lint도 권장.
- 우리 `post.id === id`, `t.id === params.tagId`는 양쪽 다 string이라 결과는 같지만 습관적으로 `===`.

---

## 9. `tag` → `tagId` 이름 변경 (설계 결정)

`tag?: string`이 "Tag 객체"처럼 읽혀 혼란 → **`tagId?: string`으로 이름만 변경**(세 군데: 시그니처·조건·비교).
- 이유: 담는 값이 **Tag 객체가 아니라 id 문자열**임을 이름으로 드러냄. `t.id === params.tagId`가 "id === id"로 자연스럽게 읽힘.
- `t`(= `post.tags`의 원소)는 **Tag 객체** `{id, label}` → `t.id`로 꺼내야 함. 반면 `params.tagId`는 타입이 `string` → 이미 id 그 자체라 `.id` 꺼낼 게 없음.
- id로 비교하는 이유: `label`은 화면 표시용(바뀔 수 있음), `id`가 고유 식별자.
- 계약 메모(다음 주 axios): 함수 파라미터는 `tagId`로 두되, 실제 URL 쿼리 키는 보통 `?tag=t1`. 그건 **함수 본문 안에서** `{ params: { tag: tagId } }`로 변환하면 됨(바깥 시그니처가 `tagId`여도 무방). → **세션 끝에 체크포인트 "설계 결정 로그"에 기록 대상.**

---

## 10. 타입 문법 디테일 (질문 모음)

### (a) `id: string`의 `:` — 객체가 아니라 "타입 표기"
`이름: 타입` 형식. `fetchPostById(id: string)` = "id라는 매개변수의 타입은 string". 중괄호 없으면 객체 아님(값 하나).
`:`이 헷갈리는 이유 — 세 군데서 같은 모양:

| 위치 | 예 | `:` 뒤에 오는 것 |
|---|---|---|
| 매개변수/변수 타입 | `id: string` | **타입** |
| 타입 안 객체 모양 | `{ q?: string }` | **타입** |
| 값 객체 프로퍼티 | `{ id: "p1" }` | **실제 값** |

→ **`:` 뒤가 타입 이름이면 타입표기, 실제 값이면 객체 프로퍼티.**

### (b) `;` vs `,` — 타입 리터럴 vs 값 객체
- **타입 리터럴**(`:` 뒤, `<>` 안): `{ q?: string; tagId?: string }` → 관례상 **`;`**(쉼표도 허용). 빌드 후 사라짐.
- **값 객체 리터럴**(`return`/`=` 우변): `{ items: result, nextCursor: undefined }` → **`,` 필수**(`;` 쓰면 문법 에러). 런타임에 남음.
- 구분법: **`:` 바로 뒤 중괄호 = 타입(`;`), 그 외 값 중괄호 = 값(`,`).**

### (c) `Promise<>` 의 `<>` vs JSX `</>`
- `Promise<T>`의 `< >` = **제네릭 인자 괄호**(`( )`와 같은 부류). 안에 **타입 하나**. 닫을 때 `>` 하나.
- JSX `<div>...</div>`의 태그 = 콘텐츠를 감싸는 **여닫이 문**이라 닫는 `</div>` 필요(자식 콘텐츠 범위 표시). 자식 없으면 `<X />`로 한 번에 닫음.
- 비유: `<>`는 괄호, `<태그>`는 문. 같은 부등호를 쓸 뿐 문법이 다름.

### (d) 봉투(envelope) — 목록 vs 단일, 그리고 빨간 줄의 의미
- `fetchPosts`(목록)만 `{ items, nextCursor }` **봉투**를 쓴다(글 배열 + 페이징 메타 = 둘을 한 봉투에). `fetchPostById`/`createPost`(한 개)는 **봉투 없이 `Promise<Post>`**(곁들일 게 없음).
- REST 계약과 일치: `GET /posts` → `{items, nextCursor}`, `GET /posts/{id}`·`POST /posts` → Post 그 자체.
- **`Promise<item: Post>` 가 안 된 두 겹의 이유:**
  1. **문법:** `이름: 타입`은 `{ }` 안에서만 됨. `< >` 바로 안엔 타입만 → 중괄호 없는 `<item: Post>`는 컴파일 자체 안 됨.
  2. **설계:** `Promise<{item: Post}>`는 문법은 되지만 단일 리소스엔 불필요한 봉투(쓸 때 `result.item.title`로 한 겹 더 까야 함).
- **중괄호로 감쌌더니 빨간 줄 뜬 이유:** `Promise<{item: Post}>`로 약속해놓고 `return found`(맨 Post)를 하면 **타입 불일치**(약속=봉투, 실제=알맹이). 없애려면 `return {item: found}`로 맞춰야 하지만 그건 번거로움 → 그래서 **`Promise<Post>` + `return found`**(둘 다 봉투 없음)가 정답.

| 시그니처 | 본문 | 결과 |
|---|---|---|
| `Promise<{item: Post}>` | `return found` | ❌ 빨간 줄(불일치) |
| `Promise<{item: Post}>` | `return {item: found}` | ✅ 되지만 번거로움 |
| `Promise<Post>` | `return found` | ✅ 정답 |

---

## 11. `fetchPostById` — find + throw + narrowing

```ts
const found = MOCK_POSTS.find((post) => post.id === id);   // 첫 일치 1개, 없으면 undefined
if (!found) {                                              // 없으면
    throw new Error("글을 찾을 수 없습니다: " + id);          // 에러를 "던진다"
}
return found;                                              // 여기선 found가 Post로 확정
```
- `.find` = 조건 맞는 **첫 원소 하나** 반환, 없으면 `undefined`(`.filter`는 배열 전체라 단일엔 부적절).
- `!found` = "found가 없으면(undefined면)". 여기 `!`는 **boolean 부정**(non-null `!`와 다른 용도).
- `throw` = 에러를 **던진다** — 함수 즉시 중단하고 호출한 쪽에 문제 전파(반환이 아님). 7단계에서 `try/catch`로 받아 error 화면 표시 예정.
- **타입 좁히기(narrowing):** `if(!found) throw`를 통과한 시점이면 TS가 `found`를 Post로 좁혀준다 → `return found`에 `!` 같은 거 불필요.

---

## 12. `createPost` — 게시판의 C(생성)

### 왜 필요한가 (CRUD)
ALIBAI는 게시판 = "글이 쌓이는(축적)" 공간. 읽기 함수(`fetchPosts`/`fetchPostById` = R)만 있으면 새 글이 영영 안 생긴다. 사용자가 변명을 **제출**하는 통로 = `createPost`(C).

| CRUD | 동작 | 함수 |
|---|---|---|
| **C**reate | 생성 | `createPost` |
| **R**ead | 읽기 | `fetchPosts`, `fetchPostById` |
| Update/Delete | 수정/삭제 | 이번 주 범위 밖 |

- 시나리오: 글쓰기 폼(8단계 `ExcuseForm`) → [제출] → `createPost(input)` → `MOCK_POSTS`에 추가 → 목록에 보임.
- **입력 `NewPost`, 반환 `Post`인 이유:** 사용자는 title/excuseText/tags/context만 적음(`NewPost`). 저장 시 서버가 `id`, 시계가 `createdAt`을 붙여 완성형 `Post`가 됨. `createPost`가 그 변환 담당.

### `...input` — 스프레드(펼치기)
- "객체의 껍데기 `{}`를 벗기고, 안의 키-값들을 그 자리에 낱개로 풀어놓는다."
```ts
const newPost: Post = { ...input, id: ..., createdAt: ... };
// = { title:input.title, excuseText:input.excuseText, tags:input.tags, context:input.context, id, createdAt }
```
- 비유: 도시락 통을 통째로 넣는 게 아니라 뚜껑 열고 반찬을 식판 칸에 하나씩 옮김.
- `{ input }`(통째 한 칸) vs `{ ...input }`(펼쳐서 낱개) — 다름.
- **덮어쓰기:** 같은 키 겹치면 나중에 적은 게 이김(`{...input, id:"새값"}`). NewPost엔 id 없어 겹칠 일 없음.
- 배열에도: `[...arr, newItem]` = 펼치고 끝에 추가한 새 배열.

### 얕은 복사(shallow copy) / 참조 복사 ★
`...input`은 **한 겹만** 복사한다.
- **원시값**(string/number/boolean): 값 자체가 복제 → 독립적. `newPost.title` 바꿔도 `input.title` 그대로.
- **객체**(`context` 등): 변수엔 "객체의 메모리 주소(참조)"가 담김 → **주소만** 복제. `newPost.context`와 `input.context`는 **같은 객체 하나**를 가리킴.
```ts
newPost.context.location = "부산";
input.context.location;   // "부산" ← 원본도 바뀜!(같은 객체)
```
- `createPost`에선 만든 뒤 context를 안 건드려 당장은 문제없음. 하지만 "복사했는데 원본이 같이 바뀌네?" 버그의 원인이 이것. (깊은 복사 필요시 `structuredClone` — 이번 주 범위 밖.)

### id / createdAt
- `id: crypto.randomUUID()` = 브라우저 내장, 전역 고유한 긴 문자열(`"f47ac10b-..."`). 그 자체로 고유라 `"p"+` 접두 불필요. (짧게 `"p"+(MOCK_POSTS.length+1)`도 가능 — 둘 중 하나로 통일.)
- `new Date()` = 현재 시각 Date 객체. `.toISOString()` = ISO 8601 표준 문자열로 변환 → `"2026-06-08T14:30:00.000Z"`(`T`=날짜·시간 구분, `Z`=UTC). `Post.createdAt`이 string이고 MOCK_POSTS 기존값과 형식이 같아 정렬·비교·표시 일관. ISO는 사전순=시간순이라 다루기 편하고 서버 표준.

---

## 13. import — 타입을 쓰려면 먼저 가져와야

```ts
import type { Post, NewPost } from "../types/post";
import { MOCK_POSTS } from "./mockData";
```
- `import type` = 가져오는 게 **타입**(런타임에 사라짐). `Post`, `NewPost`처럼 순수 타입은 `type` 붙임 → "타입만 가져온다" 명확 + 빌드 깔끔.
- `MOCK_POSTS`는 실제 값이라 `type` 없이 `import`.
- 경로: `../types/post`(한 단계 위 types 폴더), `./mockData`(같은 폴더). 확장자 생략.
- **버그:** `NewPost`를 import 안 하고 `input: NewPost`를 쓰면 → `TS2304 Cannot find name 'NewPost'`(빨간 줄). import된 이름만 쓸 수 있음. → 줄 4에 `, NewPost` 추가하면 해결.

---

## 14. 주석 작성 원칙 (피드백 정리)

- **"무엇(what)"보다 "왜(why)"** 에 주석을 아낀다. 코드만 봐서 자명한 곳(`const newPost: Post =` 위 "Post를 만든다")엔 주석 생략.
- **동작 용어는 정확히:** `throw`는 "반환"이 아니라 "던진다(중단+전파)".
- "임의 데이터"처럼 부정확한 표현 주의 — `MOCK_POSTS`는 임의(random)가 아니라 "원본 전체".
- 같은 패턴(세 함수의 `await new Promise(...)`)이 반복되면 한 곳만 설명하고 나머지 생략 가능.
- AGENTS.md 원칙: 개념 요약 주석은 요청받을 때만.

---

## 15. 한 줄 요약 모음 (빠른 복습)

- **posts.ts** = 화면도 타입도 아닌, "데이터를 가져와 돌려주는 API 함수 모음"(판별: return이 화면이냐 데이터냐).
- **async** = 비동기 함수 표시(반환을 Promise로 자동 포장). **await** = Promise를 열어 값 꺼냄(이 함수만 잠깐 멈춤). **Promise** = 나중에 올 값을 담는 상자.
- **resolve** = Promise 생성자가 주입하는 함수, 호출 시 상태를 `pending→fulfilled`로 전이.
- **new Promise**(값, 런타임) ≠ **Promise<T>**(타입, 컴파일).
- **매개변수**(정의의 빈 그릇) ≠ **인자**(호출 때 담는 값).
- **filter/map/concat** = 새 배열(비파괴, 재대입 필요) / **push** = 원본 수정(파괴적).
- **`.find`** = 첫 일치 1개 or undefined / **`.some`** = 하나라도 참? / **`.includes`** = 들어있나?
- **`===`** = 값+타입 엄격 비교(표준).
- **목록=봉투(`{items,nextCursor}`)** / **단일=`Promise<Post>`**.
- **`...input`** = 객체 펼치기(얕은 복사 — 안쪽 객체는 참조 공유).
- **타입 쓰려면 import 먼저.** `이름: 타입` 표기, `< >` 안엔 타입만, `이름:타입`은 `{}` 안에서만.

---

## 16. 다음 세션 이어갈 지점

- 6단계 완료 후 **7단계: useEffect + 상세 페이지** — `PostListPage`에서 `fetchPosts()` 호출(직접 import 걷어내기), `PostDetailPage`에서 `useParams()` + `fetchPostById()`, `loading`/`error` 상태, StrictMode의 "effect 2회 실행" vs "무한 루프" 구분.
- 미적용 코칭 메모: mockData `tagId` 일관성(t1~t4 등) 점검, 줄 잔여 주석 정리.
