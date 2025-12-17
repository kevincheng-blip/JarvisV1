// @ts-nocheck
/**
 * PredictionStabilityCard Component
 * 
 * War Room V2 - Prediction Stability Metrics
 * 
 * 顯示預測穩定性指標（標準差、最大日間變化、趨勢斜率、穩定性等級）
 */

import { useQuery } from "@tanstack/react-query";
import { api } from "../../api/client";

interface PredictionStabilityData {
  symbol: string;
  n_points: number;
  score_std: number;
  max_abs_delta: number;
  trend_slope: number;
  stability_grade: "NO_DATA" | "STABLE" | "WATCH" | "VOLATILE";
  thresholds: {
    std_threshold_stable: number;
    delta_threshold_stable: number;
    std_threshold_watch: number;
    delta_threshold_watch: number;
    min_points: number;
  };
}

function usePredictionStability(symbol: string | null, enabled: boolean = true) {
  return useQuery<PredictionStabilityData>({
    queryKey: ["predictionStability", symbol],
    queryFn: async () => {
      if (!symbol) throw new Error("Symbol is required");
      return await api.getPredictionStability(symbol, 60);
    },
    enabled: enabled && !!symbol,
    staleTime: 60000, // 1 minute
    refetchOnWindowFocus: false,
  });
}

export function PredictionStabilityCard({ symbol }: { symbol: string | null }) {
  const { data, isLoading, isError, error } = usePredictionStability(symbol, !!symbol);

  if (isLoading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          預測穩定性
        </h3>
        <div className="h-32 bg-gray-200 dark:bg-gray-700 animate-pulse rounded" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          預測穩定性
        </h3>
        <div className="text-red-500 dark:text-red-400 text-sm">
          載入失敗: {error instanceof Error ? error.message : '未知錯誤'}
        </div>
      </div>
    );
  }

  if (!data || data.stability_grade === "NO_DATA") {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          預測穩定性
        </h3>
        <div className="text-gray-500 dark:text-gray-400 text-center py-8">
          {symbol ? `暫無 ${symbol} 的預測資料` : "請選擇股票代號"}
        </div>
      </div>
    );
  }

  // Grade badge color mapping
  const getGradeColor = (grade: string) => {
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

  const getGradeLabel = (grade: string) => {
    switch (grade) {
      case "STABLE":
        return "穩定";
      case "WATCH":
        return "觀察";
      case "VOLATILE":
        return "波動";
      default:
        return grade;
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          預測穩定性
        </h3>
        <span className={`px-3 py-1 text-sm font-semibold rounded ${getGradeColor(data.stability_grade)}`}>
          {getGradeLabel(data.stability_grade)}
        </span>
      </div>

      <div className="space-y-3">
        {/* Symbol */}
        <div className="text-sm text-gray-600 dark:text-gray-400">
          標的: <span className="font-medium text-gray-900 dark:text-white">{data.symbol}</span>
        </div>

        {/* Metrics */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">資料點數</div>
            <div className="text-lg font-semibold text-gray-900 dark:text-white">
              {data.n_points}
            </div>
          </div>
          <div>
            <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">標準差</div>
            <div className="text-lg font-semibold text-gray-900 dark:text-white">
              {data.score_std.toFixed(4)}
            </div>
          </div>
          <div>
            <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">最大日間變化</div>
            <div className="text-lg font-semibold text-gray-900 dark:text-white">
              {data.max_abs_delta.toFixed(4)}
            </div>
          </div>
          <div>
            <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">趨勢斜率</div>
            <div className={`text-lg font-semibold ${
              data.trend_slope > 0 
                ? "text-green-600 dark:text-green-400" 
                : data.trend_slope < 0
                ? "text-red-600 dark:text-red-400"
                : "text-gray-900 dark:text-white"
            }`}>
              {data.trend_slope > 0 ? "+" : ""}{data.trend_slope.toFixed(4)}
            </div>
          </div>
        </div>

        {/* Thresholds info (collapsible) */}
        <details className="text-xs text-gray-500 dark:text-gray-400 mt-4">
          <summary className="cursor-pointer hover:text-gray-700 dark:hover:text-gray-300">
            閾值設定
          </summary>
          <div className="mt-2 space-y-1 pl-2">
            <div>穩定: std ≤ {data.thresholds.std_threshold_stable}, delta ≤ {data.thresholds.delta_threshold_stable}</div>
            <div>觀察: std ≤ {data.thresholds.std_threshold_watch}, delta ≤ {data.thresholds.delta_threshold_watch}</div>
            <div>最少資料點: {data.thresholds.min_points}</div>
          </div>
        </details>
      </div>
    </div>
  );
}

