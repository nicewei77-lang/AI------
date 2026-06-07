# 세션 4 개념 노트 — 5단계(페이지 조립) + JSX/엘리먼트/훅

> 날짜: 2026-06-08 (세션 4) · 복습용
> 다룬 단계: **5단계 Day1 페이지 조립** (PostListPage 작성 완료 + App.tsx 라우터는 다음 세션)
> 이번 세션은 코드보다 **개념 Q&A**가 중심이었음. 아래는 내가 던진 질문 순서대로 전부 정리.
> 라우터 코드는 다음 세션에 손으로 붙이지만, 오늘은 **왜 그런 모양으로 쓰는지**를 먼저 이해하는 쪽에 초점을 둠.

---

## 0. 이번 세션에서 실제로 작성한 코드

`frontend/src/pages/PostListPage.tsx` — 첫 "페이지 컴포넌트" 완성:

```tsx
// 데이터와 부품 컴포넌트를 불러온다.
import PostList from "../components/PostList";   // default export → 중괄호 없음
import { MOCK_POSTS } from "../api/mockData";    // 이름 있는 export → 중괄호 필요

function PostListPage() {                         // 인자 없음 (이유는 §11)
    return (
        <div className="mx-auto max-w-2xl px-4 py-8">
            <h1 className="mb-4 text-2xl font-bold">변명 게시판</h1>
            <PostList posts={MOCK_POSTS} />
        </div>
    );
}

export default PostListPage;
```

`tsc -b` 통과. **남은 일: App.tsx에 라우터 연결** (§2 참고).

---

## 1. 페이지 컴포넌트란? 일반 컴포넌트와 뭐가 다른가

**문법은 100% 똑같다.** 둘 다 "데이터 받아 JSX 반환하는 함수". React는 둘을 구분 안 함. "페이지"는 사람이 정한 **역할 컨벤션**.

차이 3가지:

1. **크기/계층** — `PostCard`(카드 1장, 최소 부품) → `PostList`(카드 묶음, 중간 부품) → `PostListPage`(화면 전체, 최상위 조립).
2. **데이터 조달 방식** ⭐ 가장 중요
   - 부품 컴포넌트(`PostCard`, `PostList`): 데이터를 **밖에서 props로 받기만** 함. 어디서 왔는지 몰라야 재사용됨.
   - **이번 단계의 페이지 컴포넌트(`PostListPage`)는** 데이터를 **직접 import해서 조달**하고 부품에 내려줌. (다음 주엔 `import {MOCK_POSTS}`가 `fetchPosts()`로 바뀜.)
   - 즉, "페이지는 항상 import만 한다"가 아니라 **지금 우리가 연습 중인 페이지가 그렇게 동작한다**는 뜻.
3. **라우터에 직접 연결됨(URL을 가짐)** — **이 커리큘럼에선** 페이지를 `<Route element={<PostListPage/>}>`에 꽂는다. 부품은 URL이 없음.

> 한 줄: **지금 만든 페이지 = URL에 연결되고, 현재 단계에서는 데이터를 직접 가져와, 부품을 조립하는 최상위 컴포넌트.**

---

## 2. 라우터 3총사 (오늘 당장 쓰는 핵심)

오늘 App.tsx에서 실제로 손으로 쓸 건 `Routes`와 `Route`다. 다만 이름이 비슷해서 헷갈리니, 먼저 **세 개가 한 세트로 움직인다**는 감각부터 잡는 게 중요하다.

```
<BrowserRouter>      ← ① "지금 URL이 뭔지" 감시·방송 (main.tsx에 이미 있음, 안 건드림)
  <Routes>           ← ② 후보 중 URL에 맞는 것 "하나만" 고르는 심사위원
    <Route .../>     ← ③ "이 주소 = 이 화면" 짝 1개
  </Routes>
</BrowserRouter>
```

비유: BrowserRouter=엘리베이터 층 센서, Routes=맞는 문 하나만 여는 제어기, Route=각 층의 문.

### ① BrowserRouter
- 현재 주소를 추적해 안의 모든 컴포넌트가 쓰게 깔아줌. `Routes`/`Route`/`Link`는 **반드시 이 안에** 있어야 작동.
- 앱당 하나, 가장 바깥(main.tsx)에. 우리는 안 건드림.

### ② Routes
- 후보 `Route` 중 **현재 URL과 가장 잘 맞는 단 하나만** 렌더. `if/else if/else`처럼 동시에 여러 개 안 켜짐.
- `Route`는 항상 `Routes` 안에 있어야 함.

### ③ Route
- props 2개: `path="/"`(언제=주소) + `element={<PostListPage/>}`(무엇=화면).
- 함정 1: element엔 **`<PostListPage />`** (꺾쇠 형태). `PostListPage`(이름만)도 `PostListPage()`(직접호출)도 아님.
- 함정 2: `element`는 "컴포넌트 함수 자체"가 아니라 **렌더할 엘리먼트**를 원함. 그래서 `<PostListPage />`처럼 쓴다.
- 함정 3: `path`의 `:id`는 자리표시자(변수). `/posts/:id` → `/posts/p1`, `/posts/p99` 다 매칭. 값은 `useParams`로 꺼냄(7단계).

### 흐름 (/posts/p1 입력 시)
```
1. BrowserRouter: URL이 /posts/p1로 바뀜 감지 → 방송
2. Routes: 후보 심사 → path="/" ✗ / path="/posts/:id" ✓ 채택
3. Route: 채택된 element={<PostDetailPage/>} 렌더
```

이번 5단계에선 ②·③만 직접 쓰면 됨(①은 이미 있음). 작성할 것:
```tsx
<Routes>
  <Route path="/" element={<PostListPage />} />
</Routes>
```

### 보너스: Link
`<a>` 대신 `<Link to="/posts/p1">`. `<a>`는 페이지 통째 새로고침(React 상태 날아감), `Link`는 새로고침 없이 화면만 교체(SPA 핵심).

---

## 3. 보충: 라우터 종류 (전체 분류)

위 3총사를 이해한 뒤에 보면 덜 헷갈린다. 여기서 말하는 "라우터 종류"는 **맨 바깥에서 URL을 어떤 방식으로 추적하느냐**에 대한 분류다.

### ① 최상위 라우터 3종 (URL을 어떻게 추적하느냐)

| 라우터 | URL 모양 | 언제 |
|---|---|---|
| **`BrowserRouter`** | `site.com/posts/p1` (깔끔) | 일반 웹앱 표준 — **우리가 쓰는 것** |
| `HashRouter` | `site.com/#/posts/p1` | 정적 호스팅(GitHub Pages), 서버 라우팅 설정 못 할 때 |
| `MemoryRouter` | URL 안 바뀜(메모리에만) | 테스트, React Native |

- `BrowserRouter`는 주소가 깨끗한 대신 새로고침 시 서버가 404 낼 수 있어 "모든 경로를 index.html로" 설정 필요(Vite 개발서버는 자동).
- `HashRouter`는 `#` 뒤가 서버로 안 가서 그 설정 불필요(대신 주소 지저분).
- **우리는 `BrowserRouter` 하나만. 이미 `main.tsx`에 깔려 있음.**

---

## 4. `<PostList posts={MOCK_POSTS}/>` — 무슨 문법? 함수 호출인가?

**JSX**. HTML처럼 생겼지만 HTML 아니고, 함수 호출처럼 보이지만 직접 호출도 아님.

개념적으로는 평범한 JS 호출 형태로 번역된다:
```tsx
<PostList posts={MOCK_POSTS} />
// ↓ 이런 식의 엘리먼트 생성 호출로 이해하면 됨
React.createElement(PostList, { posts: MOCK_POSTS })
```

> 정확한 내부 변환 함수 이름은 빌드 도구/설정에 따라 달라질 수 있다. 핵심은 **JSX가 그냥 문자열이 아니라, 결국 JS 코드로 바뀐다**는 점.

- **직접 호출이 아님.** `PostList(...)`를 내가 부르는 게 아니라 "이걸 그려줘"라고 React에게 **부탁(주문서)**. 실제로 언제 부를지는 React가 결정.
- 그래서 라우터도 `element={<PostListPage/>}` (호출 아닌 주문서 형태).

### 헷갈리기 쉬운 3개 구분
- `PostList` = **컴포넌트 함수 자체**(설계도)
- `<PostList />` = **그 설계도를 써 달라는 JSX 엘리먼트**(주문서)
- `<div>` = 나중에 실제 화면에 반영될 **HTML 태그를 가리키는 JSX 표기**

문법 해부:
```
<PostList posts={MOCK_POSTS} />
 컴포넌트   props    값(JS)    self-closing(/>=빈 태그 한방에 닫기)
 (대문자)  이름
```
- `{}` = "여기부터 JS" 탈출구. `posts="MOCK_POSTS"`(따옴표)면 글자 11개, `posts={MOCK_POSTS}`면 변수(배열).

> JSX = "이 컴포넌트를 이 props로 그려달라"는 명령서를 만드는 문법. 결국 **엘리먼트 생성 JS 코드**로 바뀐다.

---

## 5. 반복문도 없는데 어떻게 카드 여러 개가 그려져?

**반복문은 있다. 페이지가 아니라 `PostList` 안에 숨어 있음.**

페이지는 데이터 뭉치를 통째로 넘기기만:
```tsx
<PostList posts={MOCK_POSTS} />   // "3개 줄게, 알아서 그려"
```

반복은 4단계에서 직접 쓴 `PostList.tsx` 안의 `.map()`:
```tsx
{posts.map((post) => (
  <PostCard key={post.id} post={post} />
))}
```

- `.map()` = 배열의 각 원소를 변환해 **새 배열**로 만드는 메서드. `[p1,p2,p3]` → `[<PostCard/>, <PostCard/>, <PostCard/>]`.
- JSX는 **배열을 넣으면 그 안 요소를 다 나란히 렌더**. 그래서 데이터 개수만큼 자동(3개→3장, 100개→100장).
- `key={post.id}`: `.map()`으로 같은 종류 여러 개 만들 때 React가 구분할 표. 고유값(id) 줘야 함. 안 주면 콘솔 경고.

흐름: 페이지(묶음 던짐) → PostList(`.map()`으로 풀어 반복) → PostCard×3(한 장씩 그림). **반복 책임이 부품 쪽**이라 페이지는 한 줄로 끝남.

---

## 6. 왜 함수를 호출 안 하고 태그로 넘겨? 이름 있나?

이름 3개:
1. 문법 자체 = **JSX** (JavaScript XML)
2. 결과물 = **React Element(엘리먼트)** = "화면 한 조각을 설명하는 작은 객체"
3. 방식 철학 = **선언형(Declarative) UI**

정식 표현: "컴포넌트를 JSX 엘리먼트로 **선언**한다."

### 호출 vs 태그
- `PostList()` (명령형): **내가** 지금 즉시 실행. React가 끼어들 틈 없음.
- `<PostList />` (선언형): 실행 안 함. `{type, props}` 메모만 만듦. **언제 부를지는 React가 결정.**

### React가 호출권을 가져야 가능한 것들
1. **re-render 제어** — 데이터 바뀌면 React가 알아서 다시 호출해 갱신.
2. **Hooks 작동** — 훅은 "React가 부르는 타이밍"에만 동작. 직접 호출하면 깨짐(§7,§8).
3. **reconciliation** — 엘리먼트는 가벼운 객체라 "이전 vs 새것" 싸게 비교 → 바뀐 부분만 DOM 반영.
4. **합성** — 엘리먼트가 객체라서 변수에 담고, props로 넘기고, 배열에 넣음(=§5의 `.map()`이 가능한 이유).

> 비유: `PostList()`=내가 요리해서 접시 내놓기, `<PostList/>`=주방(React)에 주문서 내밀기. 주문서라서 React가 언제/몇 번/뭐 바뀜을 관리 가능.

### 대문자 vs 소문자
- `<PostList/>` (대문자) → 내 컴포넌트. ← 그래서 `<posts/>`(소문자)는 "posts라는 HTML 태그 찾기"로 빗나갔던 것.
- `<div/>` (소문자) → 진짜 HTML 태그.

---

## 7. 훅(Hook)이 뭔데? + 객체를 또 객체로 넘기는 거야?

### 훅 = 컴포넌트(함수)에 "기억력 + 생명주기"를 달아주는 특수 함수. 전부 `use`로 시작.

> 지금 단계 핵심 한 줄: **훅은 React가 컴포넌트를 호출하는 흐름 안에서만 안전하게 동작한다.**

**왜 필요:** 함수는 부를 때마다 처음부터 시작하고 끝나면 다 잊음. 근데 화면엔 기억이 필요(검색어, 로딩 여부, 받아온 목록…). 평범한 변수는 다시 불리면 사라짐. **그 "다시 불려도 안 사라지는 기억"을 React가 대신 보관해주는 창구가 훅.**

대표 훅:
- `useState` — 기억할 값 1개. `const [query, setQuery] = useState("")`. 바뀌면 자동 re-render. (8단계 폼)
- `useEffect` — "그려진 뒤에 할 일" 예약(예: 화면 뜨면 목록 가져오기). (7단계)
- `useParams` — URL의 `:id` 꺼냄 (`/posts/p1`→`p1`). (7단계)
- `useContext` — 멀리 있는 데이터(로그인 등)를 props 없이 꺼냄. (9단계)

**왜 직접 호출하면 깨지나:** 훅은 "React가 정식으로 부르는 타이밍"에만 작동(React가 "몇 번째 훅"인지 순서 추적 중). 멋대로 `PostList()` 부르면 그 추적 밖이라 기억을 못 찾음. → `<PostList/>`로 넘겨 React가 부르게 해야 함.

### 객체 속 객체 — 맞음

```tsx
<PostList posts={MOCK_POSTS} />
// 개념적으로는 이런 엘리먼트 생성 코드가 된다고 이해하면 됨
// 결과 엘리먼트:
{
  type: PostList,
  props: { posts: [ {id:"p1",…}, {id:"p2",…}, {id:"p3",…} ] }
}
```

객체 두 겹:
```
엘리먼트 객체 { type, props }      ← React에 넘기는 주문서(봉투)
  └ props 객체 { posts: ... }      ← 무슨 데이터 줄지
      └ MOCK_POSTS (배열=객체)     ← 진짜 데이터
```

---

## 8. 엘리먼트와 훅의 관계

> 핵심: **엘리먼트 = 매 렌더마다 새로 만드는 일회용 주문서(휘발성). 훅 = 그 주문서들 사이를 가로질러 살아남는 기억(지속성).**

| | 엘리먼트 | 훅(상태) |
|---|---|---|
| 정체 | `{type, props}` 객체(설명서) | React가 따로 보관하는 기억 |
| 수명 | 렌더마다 새로 생성, 쓰고 버림 | 렌더 가로질러 지속 |
| 사는 곳 | 임시 객체 | React 내부 저장소(컴포넌트 "자리"에 묶임) |

### 한 사이클 (검색어 useState 예)
```
1. <PostList/> 엘리먼트 생성 (주문서)
2. React가 보고 PostList() 호출  ← 부를 권한은 React
3. useState 만남 → React가 "이 자리 기억" 건넴 (query="")
4. 새 엘리먼트 반환 → 화면 그림
─────
5. 검색창 "지각" 입력 → setQuery("지각")
6. React: 기억 바뀜 → PostList 다시 호출 (2로)
7. 이번엔 query="지각" 건넴  ← 기억 살아남음!
8. 새 엘리먼트(걸러진 목록) → 바뀐 부분만 갱신
```

엘리먼트는 매번 새로 만들어져도 `query`는 안 사라짐 = 훅이 하는 일.

**기억은 어디?** 엘리먼트 객체 안엔 상태 없음(그냥 `{type,props}`). React가 컴포넌트의 **"자리(트리 위치)"에 묶어** 따로 보관. 같은 자리에 같은 type이 다시 오면 이전 기억을 그대로 꺼내줌. → 그래서 React가 엘리먼트 보고 "자리·순서" 세며 호출해야 훅이 작동(직접 호출 금지 이유).

> 비유: 엘리먼트 = 매번의 주문서, 훅 = 단골 기록.

---

## 9. 왜 `{MOCK_POSTS}`로 쓰나 — 역참조? "JS로 해석"이 무슨 말? "변수로 해석"이 맞나?

오해 2개 교정:

### `{}`는 "역참조"가 아니라 "표현식 평가" 스위치
JSX엔 두 모드:
```tsx
<h1>변명 게시판</h1>           // 태그 사이 → 글자(텍스트)
<PostList posts="MOCK_POSTS"/> // 따옴표 → 글자 "MOCK_POSTS" (11글자)
<PostList posts={MOCK_POSTS}/> // 중괄호 → "JS 표현식으로 평가해 결과값을 써라"
```
`{}` = 역참조 연산자 아님. **"이 안은 JS니까 실행해서 나온 값을 넣어줘"** 라는 구획 표시.

### "JS로 해석" > "변수로 해석" (변수는 한 경우일 뿐)
`{}` 안엔 **어떤 JS 표현식이든** 가능:
```tsx
{MOCK_POSTS}        // 변수 → 그 값(배열)
{1 + 1}             // → 2
{posts.length}      // → 3
{posts.filter(...)} // 함수 호출 결과
{isLoading ? "로딩중" : "완료"}  // 삼항식
```
React는 `{}` 안을 **평가(evaluate)해서 결과값**만 씀. "변수냐 함수냐" 미리 구분 안 함. → 정확한 말은 "**표현식으로 평가**"(변수로 해석은 너무 좁음).

### "역참조 어떻게 인식?" → 인식 안 함, 그냥 JS 기본 규칙
JS에선 변수 이름을 쓰면 그 자리에 값이 들어감(어디서나):
```js
const MOCK_POSTS = [1,2,3];
console.log(MOCK_POSTS);  // [1,2,3]
const x = MOCK_POSTS;     // 그 배열
```
`{MOCK_POSTS}`도 동일. C 포인터 `*p` 같은 역참조와 무관. "변수 이름 = 그 값"이라는 기본 규칙일 뿐.

---

## 10. 이거 구조분해 아니야? — `{}` 삼형제 구분

**`{MOCK_POSTS}`는 구조분해가 아니라 JSX 표현식(§9).** 같은 중괄호지만 **자리에 따라 역할이 완전히 다름.**

| 종류 | 예 | 하는 일 | 방향 |
|---|---|---|---|
| ① 구조분해 | `function PostCard({ post })` / `const {post} = props` | 객체에서 필드 **꺼냄** | 밖으로 |
| ② JSX 표현식 | `<PostList posts={MOCK_POSTS}/>` | JS 평가해 값 **넣음** | 안으로 |
| ③ 객체 리터럴 | `const obj = {id:"p1"}` | 새 객체 **만듦** | 생성 |

**자리로 구분:**
- `=` 왼쪽 / 함수 매개변수 자리 → 구조분해(꺼내기)
- JSX 태그 안 props 값 자리 → 표현식 평가(넣기)
- `=` 오른쪽에서 `키:값` → 객체 만들기

동시에 나오는 함정:
```tsx
function PostList({ posts }) {       // ① 구조분해(꺼내기)
  return <div>{posts.length}</div>;  // ② JSX 표현식(넣기)
}
```
같은 기호, 다른 자리, 다른 일.

---

## 11. PostListPage는 왜 인자가 없어?

컴포넌트의 인자 = **props(부모가 넘기는 데이터)**. 그러니 "인자 있다/없다" = "밖에서 데이터 받느냐".

| | 인자 | 데이터 출처 |
|---|---|---|
| `PostCard({post})` | 있음 | 부모(PostList)가 props로 줌 |
| `PostList({posts})` | 있음 | 부모(페이지)가 props로 줌 |
| `PostListPage()` | **없음** | **현재 단계에선 자기가 직접 import** |

- 페이지는 라우터가 `<PostListPage/>`로 **props 없이** 부름 → 받을 게 없어 인자 없음.
- 데이터는 위에서 `import {MOCK_POSTS}`로 직접 조달(§1의 역할 분리).
- 다만 이건 "페이지는 원래 무조건 인자 없음"이 아니라, **지금 만든 이 페이지가 그런 구조**라는 뜻. 나중엔 props/context/훅 결과를 함께 쓸 수도 있다.

> 규칙: **위에서 import로 직접 가져오면 → 인자 없음. 부모가 `<태그 x={}/>`로 넘기면 → 인자 있음.**

---

## 12. Tailwind 클래스 (`mx-auto max-w-2xl px-4 py-8`) — 어떻게 찾아 써?

> ⚠️ 이번 주 범위는 **"읽고 붙이는" 수준만.** 직접 디자인 설계는 나중.

미리 만들어진 작은 클래스 조합으로 스타일링(클래스 1개 = CSS 한두 줄).
```
mx-auto    → margin 좌우 auto (가로 가운데)
max-w-2xl  → 최대 너비 제한 (2xl ≈ 672px)
px-4       → padding 좌우
py-8       → padding 상하
```
→ "가운데 정렬된, 적당히 좁고, 안쪽 여백 있는 박스".

### 읽을 때는 "쪼개서 읽기"가 핵심
Tailwind 클래스는 **모든 게 딱 하나의 공식으로 통일되는 건 아니다.** 대신 지금 단계에선 자주 보는 조각만 읽으면 충분하다.

- `m` / `p` = margin / padding
- `x` / `y` / `t` / `b` = 좌우 / 상하 / 위 / 아래
- 숫자 `4`, `8` = spacing 크기 단계 (`4`는 보통 16px, `8`은 32px 정도로 읽으면 됨)
- `max-w-2xl` = 최대 너비를 `2xl` 크기로 제한
- `text-2xl` = 글자 크기 키움
- `font-bold` = 글자 굵게

즉:
- `px-4` = padding x 4 = 좌우 안쪽 여백
- `py-8` = padding y 8 = 위아래 안쪽 여백
- `mb-4` = margin bottom 4 = 아래 바깥 여백

### 찾는 법 (외우지 말고)
1. 공식 문서 tailwindcss.com 검색
2. VS Code "Tailwind CSS IntelliSense" 확장 → 자동완성 + 값(px) 표시
3. 클래스에 마우스 올리면 실제 CSS 보여줌 ← 읽을 땐 이거면 끝
4. 잘 된 기존 코드 복붙해 살짝 수정 ← 우리 학습 범위

---

## 13. `mb`는? (방향별 여백)

`mb` = **margin-bottom (아래 바깥 여백)**. 방향은 한 쪽씩 지정 가능:

| 클래스 | 방향 |
|---|---|
| `mt` | top(위) |
| `mb` | bottom(아래) |
| `ml` | left |
| `mr` | right |
| `mx` | 좌우 |
| `my` | 상하 |

`t/b/l/r` = top/bottom/left/right 첫 글자. padding도 동일(`pt/pb/pl/pr`).

예:
```tsx
<h1 className="mb-4 text-2xl font-bold">변명 게시판</h1>
// mb-4 = 제목 아래 여백 16px / text-2xl = 큰 글자 / font-bold = 굵게
```
읽는 법: **`m`/`p` + `t/b/l/r/x/y` + 숫자**로 분해. `mb-4` = margin, bottom, 4단계.

---

## 14. 오늘 핵심 3줄 요약

1. `PostListPage`는 **현재 단계에서** 데이터를 직접 가져와 `PostList`를 조립하는 페이지 컴포넌트다.
2. `<PostList posts={MOCK_POSTS} />`는 함수를 직접 호출하는 게 아니라, React에게 넘기는 **JSX 엘리먼트 주문서**다.
3. 훅은 React가 컴포넌트를 호출하는 흐름 안에서만 안전하게 동작하므로, `PostList()`를 직접 부르지 않고 `<PostList />`처럼 React에게 호출권을 넘긴다.

---

## 다음 세션 할 일
- `App.tsx`에 `<Routes>` + `<Route path="/" element={<PostListPage />} />` 추가 (BrowserRouter는 main.tsx에 이미 있음)
- `cd frontend && npm run dev` 로 브라우저에서 카드 목록 확인
- 그 다음 6단계: `api/posts.ts` (fetchPosts/fetchPostById/createPost) — 여기서 async/await, 그 뒤 7단계에서 useEffect/useParams 실전
