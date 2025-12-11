/**
 * AbTestSummaryCard Component
 * 
 * War Room V2 - AB Test Summary
 * 
 * 顯示最新的 Decision AB Test 結果
 */

import { useRecentDecisionAbReports } from "../../hooks/useDecisionAbTest";
import type { DecisionABTestReport } from "../../types/decisionAb";

export function AbTestSummaryCard() {
  const { data: reports, isLoading, isError, error } = useRecentDecisionAbReports(1);

  const handleViewABTest = () => {
    // Dispatch custom event for navigation
    window.dispatchEvent(new CustomEvent("navigation", {
      detail: { page: "decision-ab-test" }
    }));
  };

  if (isLoading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          AB Test 摘要
        </h3>
        <div className="h-64 bg-gray-200 dark:bg-gray-700 animate-pulse rounded" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          AB Test 摘要
        </h3>
        <div className="text-red-500 dark:text-red-400 text-sm">
          載入失敗: {error instanceof Error ? error.message : '未知錯誤'}
        </div>
      </div>
    );
  }

  const latestReport = reports?.[0] as DecisionABTestReport | undefined;

  if (!latestReport) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          AB Test 摘要
        </h3>
        <div className="text-gray-500 dark:text-gray-400 text-center py-8">
          <p className="mb-4">尚未執行 AB Test</p>
          <button
            onClick={handleViewABTest}
            className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
          >
            前往 AB Test 儀表板
          </button>
        </div>
      </div>
    );
  }

  const getRecommendationBadge = (rec: string) => {
    switch (rec) {
      case "V2_PREFERRED":
        return { text: "V2 推薦", color: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200" };
      case "V1_PREFERRED":
        return { text: "V1 推薦", color: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200" };
      case "V2_NOT_RECOMMENDED":
        return { text: "V2 不建議", color: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200" };
      default:
        return { text: "無顯著差異", color: "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200" };
    }
  };

  const badge = getRecommendationBadge(latestReport.recommendation);

  // Prepare equity curve data
  const variantCurve = latestReport.variant?.equity_curve || [];
  const baselineCurve = latestReport.baseline?.equity_curve || [];

  // Calculate chart dimensions
  const allEquities = [
    ...variantCurve.map(p => p.equity),
    ...baselineCurve.map(p => p.equity)
  ];
  const maxEquity = allEquities.length > 0 ? Math.max(...allEquities) : 1;
  const minEquity = allEquities.length > 0 ? Math.min(...allEquities) : 0;
  const range = maxEquity - minEquity || 1;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          AB Test 摘要
        </h3>
        <button
          onClick={handleViewABTest}
          className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
        >
          查看全部 →
        </button>
      </div>

      {/* Recommendation Badge */}
      <div className="mb-4">
        <span className={`inline-block px-3 py-1 text-sm rounded ${badge.color}`}>
          {badge.text}
        </span>
      </div>

      {/* Metrics Comparison */}
      <div className="grid grid-cols-3 gap-4 mb-4">
        <div>
          <div className="text-sm text-gray-500 dark:text-gray-400">Sharpe Δ</div>
          <div className={`text-xl font-bold ${
            latestReport.sharpe_delta > 0 ? "text-green-600 dark:text-green-400" :
            latestReport.sharpe_delta < 0 ? "text-red-600 dark:text-red-400" :
            "text-gray-600 dark:text-gray-400"
          }`}>
            {latestReport.sharpe_delta > 0 ? "+" : ""}{latestReport.sharpe_delta.toFixed(2)}
          </div>
        </div>

        <div>
          <div className="text-sm text-gray-500 dark:text-gray-400">MaxDD Δ</div>
          <div className={`text-xl font-bold ${
            latestReport.max_drawdown_delta < 0 ? "text-green-600 dark:text-green-400" :
            latestReport.max_drawdown_delta > 0 ? "text-red-600 dark:text-red-400" :
            "text-gray-600 dark:text-gray-400"
          }`}>
            {latestReport.max_drawdown_delta > 0 ? "+" : ""}{latestReport.max_drawdown_delta.toFixed(2)}%
          </div>
        </div>

        <div>
          <div className="text-sm text-gray-500 dark:text-gray-400">Return Δ</div>
          <div className={`text-xl font-bold ${
            latestReport.return_delta > 0 ? "text-green-600 dark:text-green-400" :
            latestReport.return_delta < 0 ? "text-red-600 dark:text-red-400" :
            "text-gray-600 dark:text-gray-400"
          }`}>
            {latestReport.return_delta > 0 ? "+" : ""}{(latestReport.return_delta * 100).toFixed(1)}%
          </div>
        </div>
      </div>

      {/* Mini Equity Curve */}
      {(variantCurve.length > 0 || baselineCurve.length > 0) && (
        <div className="mt-4">
          <div className="text-sm text-gray-500 dark:text-gray-400 mb-2">Equity Curve</div>
          <div className="h-32 relative border border-gray-200 dark:border-gray-700 rounded p-2 bg-gray-50 dark:bg-gray-900">
            <svg width="100%" height="100%" className="overflow-visible">
              {/* V1 Baseline */}
              {baselineCurve.length > 0 && (
                <polyline
                  points={baselineCurve.map((p, i) => {
                    const x = (i / (baselineCurve.length - 1 || 1)) * 100;
                    const y = 100 - ((p.equity - minEquity) / range) * 100;
                    return `${x},${y}`;
                  }).join(" ")}
                  fill="none"
                  stroke="#ef4444"
                  strokeWidth="2"
                  strokeDasharray="4,4"
                />
              )}
              {/* V2 Variant */}
              {variantCurve.length > 0 && (
                <polyline
                  points={variantCurve.map((p, i) => {
                    const x = (i / (variantCurve.length - 1 || 1)) * 100;
                    const y = 100 - ((p.equity - minEquity) / range) * 100;
                    return `${x},${y}`;
                  }).join(" ")}
                  fill="none"
                  stroke="#10b981"
                  strokeWidth="2"
                />
              )}
            </svg>
            <div className="absolute bottom-0 right-0 text-xs text-gray-500 dark:text-gray-400 flex gap-2 p-2">
              <span className="flex items-center gap-1">
                <span className="w-3 h-0.5 bg-red-500 inline-block" style={{ borderTop: "2px dashed #ef4444" }} />
                V1
              </span>
              <span className="flex items-center gap-1">
                <span className="w-3 h-0.5 bg-green-500 inline-block" />
                V2
              </span>
            </div>
          </div>
        </div>
      )}

      {/* CTA Button */}
      <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
        <button
          onClick={handleViewABTest}
          className="w-full px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
        >
          前往 AB Test 儀表板
        </button>
      </div>
    </div>
  );
}
