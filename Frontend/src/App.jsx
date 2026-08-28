import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";

import Dashboard from "./pages/Dashboard";
import Missions from "./pages/Missions";
import Drones from "./pages/Drones";
import LiveMap from "./pages/LiveMap";
import Perception from "./pages/Perception";

import "./App.css";

function App() {
  return (
    <BrowserRouter>
      <div className="app">

        {/* TOP BAR */}
        <header className="topbar">

          <div className="brand">
            <div className="brand-logo">✦</div>

            <div>
              <h1>VayuNetra</h1>
              <p>Wings of Hope</p>
            </div>
          </div>

          {/* NAVIGATION */}
          <nav className="navigation">

            <NavLink
              to="/"
              end
              className="nav-item"
            >
              Dashboard
            </NavLink>

            <NavLink
              to="/missions"
              className="nav-item"
            >
              Missions
            </NavLink>

            <NavLink
              to="/drones"
              className="nav-item"
            >
              Drones
            </NavLink>

            <NavLink
              to="/map"
              className="nav-item"
            >
              Live Map
            </NavLink>

            <NavLink
              to="/perception"
              className="nav-item"
            >
              Perception
            </NavLink>

          </nav>

          {/* SYSTEM STATUS */}
          <div className="system-status">
            <span className="status-dot"></span>
            SYSTEM ONLINE
          </div>

        </header>

        {/* PAGE ROUTES */}
        <Routes>

          <Route
            path="/"
            element={<Dashboard />}
          />

          <Route
            path="/missions"
            element={<Missions />}
          />

          <Route
            path="/drones"
            element={<Drones />}
          />

          <Route
            path="/map"
            element={<LiveMap />}
          />

          <Route
            path="/perception"
            element={<Perception />}
          />

        </Routes>

      </div>
    </BrowserRouter>
  );
}

export default App;