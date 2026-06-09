/* 라우트와 페이지를 import한다. */
import {Routes, Route} from "react-router-dom";
import PostListPage from "./pages/PostListPage";
import PostDetailPage from "./pages/PostDetailPage";

/* PostListPage를 라우팅한다. */
function App() {
  return (
    <Routes>
      <Route path="/" element={<PostListPage/>} />
      <Route path="/posts/:id" element={<PostDetailPage/>}/>
    </Routes>
  );
}

export default App;