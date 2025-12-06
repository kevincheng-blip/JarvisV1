/**
 * Dashboard Page
 * 
 * Main dashboard with Watchlist, Prediction Summary, and Coverage Heatmap panels
 */

import { useState } from "react";
import { useTranslation } from "react-i18next";
import { CoverageHeatmapPanel } from "../components/CoverageHeatmapPanel";
import { PredictionSummaryPanel } from "../components/PredictionSummaryPanel";
import { PredictionTimelinePanel } from "../components/PredictionTimelinePanel";
import { SmartWatchlist } from "../components/SmartWatchlist";
import { WatchlistPanel } from "../components/WatchlistPanel";
import { api } from "../api/client";
import type { CoverageResponse, Prediction } from "../types";

export function DashboardPage() {
  const { t } = useTranslation();
  
  // Default to today
  const [selectedDate, setSelectedDate] = useState(() => {
    const today = new Date();
    return today.toISOString().split("T")[0];
  });
  
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [coverage, setCoverage] = useState<CoverageResponse | undefined>();
  const [loading, setLoading] = useState(false);
  const [selectedSymbol, setSelectedSymbol] = useState<string>("2330");
  const [timelineSymbol, setTimelineSymbol] = useState<string>("2330");

  const handleLoad = async () => {
    setLoading(true);
    try {
      // Load predictions
      const preds = await api.getPredictions(selectedDate);
      setPredictions(preds);
      console.log("Predictions loaded:", preds);
      
      // Load coverage (last 30 days)
      const fromDate = new Date();
      fromDate.setDate(fromDate.getDate() - 30);
      const cov = await api.getCoverage(
        "tw_top50_2024",
        fromDate.toISOString().split("T")[0],
        selectedDate
      );
      setCoverage(cov);
      console.log("Coverage loaded:", cov);
      
    } catch (error) {
      console.error("Error loading data:", error);
      alert("Failed to load data. Make sure API server is running on http://localhost:8000");
    } finally {
      setLoading(false);
    }
  };

  const selectedPrediction = predictions.find((p) => p.symbol === selectedSymbol);

  return (
    <div style={{ padding: "20px", fontFamily: "Arial, sans-serif" }}>
      <div style={{ marginBottom: "20px", padding: "12px", background: "#f0f0f0", borderRadius: "8px" }}>
        <h1>J-GOD Trading Command Center</h1>
        <p style={{ color: "#666", fontSize: "14px" }}>
          {t("label.simulation_only")}
        </p>
      </div>

      <div style={{ marginBottom: "20px", display: "flex", gap: "12px", alignItems: "center" }}>
        <label>
          {t("label.date")}:
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            style={{ marginLeft: "8px", padding: "4px 8px" }}
          />
        </label>
        <button
          onClick={handleLoad}
          disabled={loading}
          style={{ padding: "8px 16px", cursor: loading ? "not-allowed" : "pointer" }}
        >
          {loading ? t("label.loading") : t("label.load")}
        </button>
      </div>

      <div style={{ display: "flex", gap: "16px", marginBottom: "16px" }}>
        {/* Left: Smart Watchlist */}
        <div style={{ width: "256px", flexShrink: 0 }}>
          <SmartWatchlist
            selectedSymbol={timelineSymbol}
            onSelectSymbol={setTimelineSymbol}
          />
        </div>

        {/* Right: Main Content */}
        <div style={{ flex: 1 }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginBottom: "16px" }}>
            <div>
              <WatchlistPanel
                predictions={predictions}
                loading={loading}
              />
              {predictions.length > 0 && (
                <div style={{ marginTop: "8px", fontSize: "12px", color: "#666" }}>
                  Click on a symbol to view details (coming soon)
                </div>
              )}
            </div>
            
            <PredictionSummaryPanel
              prediction={selectedPrediction}
              loading={loading}
            />
          </div>

          <div>
            <CoverageHeatmapPanel />
          </div>

          <div style={{ marginTop: "20px" }}>
            <PredictionTimelinePanel
              symbol={timelineSymbol}
              startDate="2024-01-01"
              endDate="2024-12-31"
            />
          </div>
        </div>
      </div>

      <div style={{ marginTop: "20px", padding: "12px", background: "#fff3cd", borderRadius: "8px", fontSize: "12px" }}>
        <strong>Note:</strong> This is a minimal skeleton UI. Full features (K-line charts, order ticket, etc.) 
        will be implemented in future versions. Current version focuses on data loading and basic display.
      </div>
    </div>
  );
}

