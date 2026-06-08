/* 라우트와 페이지를 import한다. */
import {Routes, Route} from "react-router-dom";
import PostListPage from "./pages/PostListPage";

/* PostListPage를 라우팅한다. */
function App() {
  return (
    <Routes>
      <Route path="/" element={<PostListPage/>} />
    </Routes>
  );
}

export default App;