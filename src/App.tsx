import { BrowserRouter, Routes, Route } from "react-router-dom";

import Sidebar from "./Sidebar";
import Dashboard from "./Dashboard";
import ImageProcessing from "./ImageProcessing";
import TigerDatabase from "./TigerDatabase";
import TigerProfile from "./TigerProfile";
import MovementMap from "./MovementMap";
import Alerts from "./Alerts";
import HumanReview from "./HumanReview";
import ModelPerformance from "./ModelPerformance";

function App() {
  return (
    <BrowserRouter>
      <div className="flex min-h-screen bg-[#08120e] text-white">
        <Sidebar />

        <main className="flex-1 overflow-auto p-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/processing" element={<ImageProcessing />} />
            <Route path="/tigers" element={<TigerDatabase />} />
            <Route path="/tigers/:id" element={<TigerProfile />} />
            <Route path="/movement" element={<MovementMap />} />
            <Route path="/alerts" element={<Alerts />} />
            <Route path="/review" element={<HumanReview />} />
            <Route path="/model" element={<ModelPerformance />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
