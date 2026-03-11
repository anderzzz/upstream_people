import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Layout } from "./components/shared/Layout.tsx";
import { Lobby } from "./pages/Lobby.tsx";
import { TableRoom } from "./pages/TableRoom.tsx";
import { Lab } from "./pages/Lab.tsx";
import { RangeRoom } from "./pages/RangeRoom.tsx";
import { StrategyMap } from "./pages/StrategyMap.tsx";

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Lobby />} />
          <Route path="table" element={<TableRoom />} />
          <Route path="lab" element={<Lab />} />
          <Route path="ranges" element={<RangeRoom />} />
          <Route path="strategy" element={<StrategyMap />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
