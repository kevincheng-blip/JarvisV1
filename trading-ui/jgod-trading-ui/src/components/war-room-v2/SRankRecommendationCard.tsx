/**
 * SRankRecommendationCard Component
 * 
 * War Room V2 - S-Rank Engine V2 Strategy Recommendation
 * 
 * 顯示策略推薦：Top strategies + weights + rationale
 */

import { useState } from "react";
import { useSRankV2Recommendation } from "../../hooks/useSRankV2";
import { useStrategyPerfLatest, useRecomputeStrategyPerf } from "../../hooks/useStrategyPerf";

interface SRankRecommendationCardProps {
  symbol: string | null;
}

export function SRankRecommendationCard({ symbol }: SRankRecommendationCardProps) {
  const { data, isLoading, isError, error, refetch } = useSRankV2Recommendation(
    symbol,
    60,
    5,
    "performance", // Default to performance mode
    !!symbol
  );
  const { data: perfData } = useStrategyPerfLatest(symbol, !!symbol);
  const recomputePerf = useRecomputeStrategyPerf();
  const [actionMessage, setActionMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const getStabilityGradeColor = (grade: string) => {
    switch (grade) {
      case "STABLE":
        return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200";
      case "WATCH":
        return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200";
      case "VOLATILE":
        return "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200";
      default:
        return "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200";
    }
  };

  const getStrategyName = (strategy: string) => {
    const names: Record<string, string> = {
      trend_follow: "趨勢跟隨",
      mean_reversion: "均值回歸",
      breakout: "突破",
      risk_off: "風險規避",
      momentum: "動量",
    };
    return names[strategy] || strategy;
  };

  if (isLoading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          策略推薦 (S-Rank V2)
        </h3>
        <div className="space-y-2">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="h-16 bg-gray-200 dark:bg-gray-700 animate-pulse rounded" />
          ))}
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          策略推薦 (S-Rank V2)
        </h3>
        <div className="text-red-500 dark:text-red-400 text-sm">
          載入失敗: {error instanceof Error ? error.message : '未知錯誤'}
        </div>
      </div>
    );
  }

  if (!data || data.metrics.stability_grade === "NO_DATA" || data.items.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          策略推薦 (S-Rank V2)
        </h3>
        <div className="text-gray-500 dark:text-gray-400 text-center py-8">
          {symbol ? `目前沒有 ${symbol} 的策略推薦資料` : "請選擇股票代碼"}
        </div>
      </div>
    );
  }

  const handleRecomputePerf = async () => {
    if (!symbol) return;
    
    setActionMessage(null);
    try {
      await recomputePerf.mutateAsync({ symbol, limit: 60, window: 20 });
      setActionMessage({ type: "success", text: "績效重新計算成功" });
      // Refetch recommendation and perf
      refetch();
      setTimeout(() => setActionMessage(null), 3000);
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || "操作失敗";
      setActionMessage({ type: "error", text: errorMsg });
      setTimeout(() => setActionMessage(null), 5000);
    }
  };

  // Get performance metrics for a strategy
  const getPerfMetrics = (strategy: string) => {
    if (!perfData || !perfData.items) return null;
    return perfData.items.find(item => item.strategy_id === strategy);
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <div className="flex justify-between items-center mb-4">
        <div className="flex items-center gap-2">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            策略推薦 (S-Rank V2)
          </h3>
          <span className="px-2 py-1 text-xs rounded bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
            Performance-driven
          </span>
        </div>
        <span className={`px-2 py-1 text-xs rounded ${getStabilityGradeColor(data.metrics.stability_grade)}`}>
          {data.metrics.stability_grade}
        </span>
      </div>

      {/* Action Message */}
      {actionMessage && (
        <div className={`mb-4 p-3 rounded text-sm ${
          actionMessage.type === "success"
            ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
            : "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200"
        }`}>
          {actionMessage.text}
        </div>
      )}

      {/* Recompute Perf Button */}
      <div className="mb-4">
        <button
          onClick={handleRecomputePerf}
          disabled={recomputePerf.isPending || !symbol}
          className="px-3 py-1.5 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {recomputePerf.isPending ? "計算中..." : "Recompute Perf"}
        </button>
      </div>

      {/* Metrics Summary */}
      <div className="grid grid-cols-2 gap-2 mb-4 text-xs text-gray-600 dark:text-gray-400">
        <div>
          <span className="font-medium">資料點數:</span> {data.metrics.n_points}
        </div>
        <div>
          <span className="font-medium">趨勢斜率:</span> {data.metrics.trend_slope.toFixed(4)}
        </div>
        <div>
          <span className="font-medium">標準差:</span> {data.metrics.score_std.toFixed(4)}
        </div>
        <div>
          <span className="font-medium">最大變化:</span> {data.metrics.max_abs_delta.toFixed(4)}
        </div>
      </div>

      {/* Top Strategies */}
      <div className="space-y-3">
        <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">
          推薦策略 (Top {data.items.length})
        </h4>
        {data.items.map((item, index) => {
          const perfMetrics = getPerfMetrics(item.strategy);
          return (
            <div
              key={item.strategy}
              className="p-3 border border-gray-200 dark:border-gray-700 rounded"
            >
              <div className="flex justify-between items-start mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-medium text-gray-500 dark:text-gray-400">
                    #{index + 1}
                  </span>
                  <span className="font-semibold text-gray-900 dark:text-white">
                    {getStrategyName(item.strategy)}
                  </span>
                </div>
                <span className="text-lg font-bold text-blue-600 dark:text-blue-400">
                  {(item.weight * 100).toFixed(1)}%
                </span>
              </div>
              
              {/* Performance Metrics (if available) */}
              {perfMetrics && perfMetrics.grade !== "NO_DATA" && (
                <div className="grid grid-cols-4 gap-2 mt-2 text-xs text-gray-600 dark:text-gray-400">
                  <div>
                    <span className="font-medium">Sharpe:</span> {perfMetrics.sharpe_proxy.toFixed(2)}
                  </div>
                  <div>
                    <span className="font-medium">MDD:</span> {(perfMetrics.max_drawdown_proxy * 100).toFixed(1)}%
                  </div>
                  <div>
                    <span className="font-medium">Turnover:</span> {(perfMetrics.turnover_proxy * 100).toFixed(1)}%
                  </div>
                  <div>
                    <span className="font-medium">Decay:</span> {perfMetrics.decay_slope.toFixed(3)}
                  </div>
                </div>
              )}
              
              {/* Rationale */}
              {data.rationale[item.strategy] && (
                <p className="text-xs text-gray-600 dark:text-gray-400 mt-1 line-clamp-2">
                  {data.rationale[item.strategy]}
                </p>
              )}
            </div>
          );
        })}
      </div>

      {/* Date Range */}
      {data.start_date && data.end_date && (
        <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700 text-xs text-gray-500 dark:text-gray-400">
          資料期間: {data.start_date} ~ {data.end_date}
        </div>
      )}
    </div>
  );
}

