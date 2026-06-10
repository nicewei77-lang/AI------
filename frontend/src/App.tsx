/* 라우트와 페이지를 import한다. */
import {Routes, Route} from "react-router-dom";
import PostListPage from "./pages/PostListPage";
import PostDetailPage from "./pages/PostDetailPage";
// ⚠️ [임시 채움 — 코치] 아래 import 3줄과 /login·/new 라우트는 8~9단계 복습 때 직접 작성할 부분입니다.
import LoginPage from "./pages/LoginPage";
import PostCreatePage from "./pages/PostCreatePage";
import ProtectedRoute from "./components/ProtectedRoute";

/* PostListPage를 라우팅한다. */
function App() {
  return (
    <Routes>
      <Route path="/" element={<PostListPage/>} />
      <Route path="/posts/:id" element={<PostDetailPage/>}/>
      {/* ⚠️ [임시 채움 — 코치] 8~9단계 복습 때 직접 작성 */}
      <Route path="/login" element={<LoginPage/>}/>
      <Route path="/new" element={<ProtectedRoute><PostCreatePage/></ProtectedRoute>}/>
    </Routes>
  );
}

export default App;