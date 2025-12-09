/**
 * Main App Component
 */

import { useState } from "react";
import "./i18n";
import { DashboardPage } from "./pages/DashboardPage";
import { WarRoomPage } from "./pages/WarRoomPage";

type Page = "dashboard" | "war-room";

function App() {
  const [currentPage, setCurrentPage] = useState<Page>("dashboard");

  return (
    <div className="App">
      {/* Navigation */}
      <nav className="bg-gray-800 dark:bg-gray-900 border-b border-gray-700 px-4 py-2">
        <div className="flex gap-4">
          <button
            onClick={() => setCurrentPage("dashboard")}
            className={`px-4 py-2 rounded ${
              currentPage === "dashboard"
                ? "bg-blue-600 text-white"
                : "text-gray-300 hover:bg-gray-700"
            }`}
          >
            Dashboard
          </button>
          <button
            onClick={() => setCurrentPage("war-room")}
            className={`px-4 py-2 rounded ${
              currentPage === "war-room"
                ? "bg-blue-600 text-white"
                : "text-gray-300 hover:bg-gray-700"
            }`}
          >
            War Room
          </button>
        </div>
      </nav>

      {/* Page Content */}
      {currentPage === "dashboard" && <DashboardPage />}
      {currentPage === "war-room" && <WarRoomPage />}
    </div>
  );
}

export default App;

