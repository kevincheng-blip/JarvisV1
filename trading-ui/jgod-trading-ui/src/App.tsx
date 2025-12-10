/**
 * Main App Component
 */

import { useState, useEffect } from "react";
import "./i18n";
import { DashboardPage } from "./pages/DashboardPage";
import { WarRoomPage } from "./pages/WarRoomPage";
import { DMCPage } from "./pages/DMCPage";
import { DMCReviewPage } from "./pages/DMCReviewPage";
import { DMCEditPage } from "./pages/DMCEditPage";
import { RuleSimListPage } from "./pages/RuleSimListPage";
import { RuleSimDetailPage } from "./pages/RuleSimDetailPage";

type Page = "dashboard" | "war-room" | "dmc" | "dmc-review" | "dmc-edit" | "rule-sim-list" | "rule-sim-detail";

interface DMCRouteState {
  page: "review" | "edit";
  sectionId: string;
  versionId?: string;
}

interface RuleSimRouteState {
  page: "detail";
  experimentId: string;
}

function App() {
  const [currentPage, setCurrentPage] = useState<Page>("dashboard");
  const [dmcRouteState, setDmcRouteState] = useState<DMCRouteState | null>(null);
  const [ruleSimRouteState, setRuleSimRouteState] = useState<RuleSimRouteState | null>(null);
  
  // Listen for DMC navigation events
  useEffect(() => {
    const handleNavigate = (e: Event) => {
      const customEvent = e as CustomEvent;
      const { page, sectionId, versionId, status } = customEvent.detail;
      if (page === "review") {
        setCurrentPage("dmc-review");
        setDmcRouteState({ page: "review", sectionId, versionId });
      } else if (page === "edit") {
        setCurrentPage("dmc-edit");
        setDmcRouteState({ page: "edit", sectionId });
      } else if (page === "list") {
        setCurrentPage("dmc");
        setDmcRouteState(null);
      }
    };
    
    const handleRuleSimNavigate = (e: Event) => {
      const customEvent = e as CustomEvent;
      const { page, experimentId } = customEvent.detail;
      if (page === "detail") {
        setCurrentPage("rule-sim-detail");
        setRuleSimRouteState({ page: "detail", experimentId });
      } else if (page === "list") {
        setCurrentPage("rule-sim-list");
        setRuleSimRouteState(null);
      }
    };
    
    window.addEventListener("dmc:navigate", handleNavigate);
    window.addEventListener("ruleSim:navigate", handleRuleSimNavigate);
    return () => {
      window.removeEventListener("dmc:navigate", handleNavigate);
      window.removeEventListener("ruleSim:navigate", handleRuleSimNavigate);
    };
  }, []);

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
          <button
            onClick={() => setCurrentPage("dmc")}
            className={`px-4 py-2 rounded ${
              currentPage.startsWith("dmc")
                ? "bg-blue-600 text-white"
                : "text-gray-300 hover:bg-gray-700"
            }`}
          >
            DMC
          </button>
          <button
            onClick={() => setCurrentPage("rule-sim-list")}
            className={`px-4 py-2 rounded ${
              currentPage.startsWith("rule-sim")
                ? "bg-blue-600 text-white"
                : "text-gray-300 hover:bg-gray-700"
            }`}
          >
            Rule Sim
          </button>
        </div>
      </nav>

      {/* Page Content */}
      {currentPage === "dashboard" && <DashboardPage />}
      {currentPage === "war-room" && <WarRoomPage />}
      {currentPage === "dmc" && <DMCPage />}
      {currentPage === "dmc-review" && dmcRouteState && (
        <DMCReviewPage
          sectionId={dmcRouteState.sectionId}
          versionId={dmcRouteState.versionId || ""}
          onBack={() => setCurrentPage("dmc")}
        />
      )}
      {currentPage === "dmc-edit" && dmcRouteState && (
        <DMCEditPage
          sectionId={dmcRouteState.sectionId}
          onBack={() => setCurrentPage("dmc")}
        />
      )}
      {currentPage === "rule-sim-list" && <RuleSimListPage />}
      {currentPage === "rule-sim-detail" && ruleSimRouteState && (
        <RuleSimDetailPage
          experimentId={ruleSimRouteState.experimentId}
          onBack={() => setCurrentPage("rule-sim-list")}
        />
      )}
    </div>
  );
}

export default App;

