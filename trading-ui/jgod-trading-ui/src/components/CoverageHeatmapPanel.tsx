/**
 * Coverage Heatmap Panel (E1)
 * 
 * 資料覆蓋 / 背填狀態面板
 */

import React, { useEffect, useState } from "react";
import { api } from "../api/client";
import type { CoverageSummary, CoverageItem } from "../types";

interface CoverageHeatmapPanelProps {
  defaultStartDate?: string;
  defaultEndDate?: string;
}

const coverageToColor = (coverage: number): string => {
  // 簡單版：紅 → 黃 → 綠
  if (coverage >= 0.99) return "#16a34a"; // 綠
  if (coverage >= 0.7) return "#eab308";  // 黃
  if (coverage > 0.0) return "#dc2626";   // 紅
  return "#4b5563"; // 完全沒資料：灰
};

export const CoverageHeatmapPanel: React.FC<CoverageHeatmapPanelProps> = ({
  defaultStartDate = "2024-01-01",
  defaultEndDate = "2024-12-31",
}) => {
  const [startDate, setStartDate] = useState(defaultStartDate);
  const [endDate, setEndDate] = useState(defaultEndDate);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState<CoverageSummary | null>(null);

  const loadCoverage = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getCoverage(startDate, endDate);
      setSummary(data);
    } catch (err: any) {
      console.error(err);
      setError(err?.message || "Failed to load coverage");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // 初次載入
    loadCoverage();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleRefresh = () => {
    loadCoverage();
  };

  return (
    <div className="p-4 rounded-2xl border border-gray-700 bg-slate-900 text-slate-100 shadow-lg h-full flex flex-col">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h2 className="text-lg font-semibold">
            指標覆蓋率面板 Coverage Heatmap
          </h2>
          <p className="text-xs text-slate-400">
            Interval: {startDate} → {endDate}
          </p>
          {summary && (
            <p className="text-xs text-slate-400 mt-1">
              Symbols: {summary.total_symbols} ·
              Completed ≥99.9%: {summary.completed_symbols} ·
              Avg Coverage: {(summary.average_coverage * 100).toFixed(1)}%
            </p>
          )}
        </div>
        <div className="flex items-center gap-2">
          <div className="flex flex-col text-[10px] text-slate-400 mr-2">
            <span>
              <span className="inline-block w-3 h-3 mr-1 rounded bg-[#16a34a]" /> ≥99.9%
            </span>
            <span>
              <span className="inline-block w-3 h-3 mr-1 rounded bg-[#eab308]" /> 70%~99.9%
            </span>
            <span>
              <span className="inline-block w-3 h-3 mr-1 rounded bg-[#dc2626]" /> 0%~70%
            </span>
          </div>
          <button
            onClick={handleRefresh}
            className="px-3 py-1 rounded-full text-xs bg-sky-600 hover:bg-sky-500 disabled:bg-slate-600"
            disabled={loading}
          >
            {loading ? "Refreshing..." : "Refresh"}
          </button>
        </div>
      </div>

      <div className="flex items-center gap-2 mb-3 text-xs">
        <label className="flex items-center gap-1">
          Start:
          <input
            type="date"
            className="bg-slate-800 border border-slate-600 rounded px-2 py-1 text-xs"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
          />
        </label>
        <label className="flex items-center gap-1">
          End:
          <input
            type="date"
            className="bg-slate-800 border border-slate-600 rounded px-2 py-1 text-xs"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
          />
        </label>
      </div>

      {error && (
        <div className="text-xs text-red-400 mb-2">
          Error: {error}
        </div>
      )}

      <div className="flex-1 overflow-auto border border-slate-700 rounded-xl">
        <table className="w-full text-xs">
          <thead className="bg-slate-800 sticky top-0">
            <tr>
              <th className="px-2 py-1 text-left">Symbol</th>
              <th className="px-2 py-1 text-left">Name</th>
              <th className="px-2 py-1 text-right">Bars</th>
              <th className="px-2 py-1 text-right">IndDays</th>
              <th className="px-2 py-1 text-right">Coverage</th>
              <th className="px-2 py-1 text-left">Status</th>
            </tr>
          </thead>
          <tbody>
            {summary?.items.map((item) => {
              const pct = item.coverage * 100;
              const color = coverageToColor(item.coverage);
              return (
                <tr key={item.symbol} className="border-t border-slate-800">
                  <td className="px-2 py-1 font-mono">{item.symbol}</td>
                  <td className="px-2 py-1">{item.name}</td>
                  <td className="px-2 py-1 text-right">{item.bar_days}</td>
                  <td className="px-2 py-1 text-right">{item.indicator_days}</td>
                  <td className="px-2 py-1 text-right">
                    {pct.toFixed(1)}%
                  </td>
                  <td className="px-2 py-1">
                    <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
                      <div
                        className="h-2 rounded-full"
                        style={{
                          width: `${Math.min(100, pct)}%`,
                          backgroundColor: color,
                        }}
                      />
                    </div>
                  </td>
                </tr>
              );
            })}
            {!summary && !loading && (
              <tr>
                <td
                  colSpan={6}
                  className="px-2 py-3 text-center text-slate-400"
                >
                  No data loaded yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
