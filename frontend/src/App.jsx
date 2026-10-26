import { Routes, Route } from "react-router-dom";
import HomePage from "./pages/HomePage.jsx";
import TripDetailPage from "./pages/TripDetailPage.jsx";

function App() {
  return (
    <div className="app-shell">
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/trips/:tripId" element={<TripDetailPage />} />
      </Routes>
    </div>
  );
}

export default App;
