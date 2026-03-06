import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "@/components/Layout";
import Dashboard from "@/pages/Dashboard";
import Feed from "@/pages/Feed";
import Board from "@/pages/Board";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/feed" element={<Feed />} />
          <Route path="/board" element={<Board />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
