/**
 * ErrorReplayViewer Component
 * 
 * Displays error replay report with:
 * - Price chart
 * - Factor/Score chart
 * - Trade markers
 * - Diagnostic information
 */

import { useErrorReplay } from "../../../hooks/useErrorReplay";
import { useWarRoomStore } from "../../../store/warRoomStore";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";

export function ErrorReplayViewer() {
  const { selectedErrorId } = useWarRoomStore();
  const { data: report, isLoading, isError, error, refetch } = useErrorReplay(selectedErrorId);

  // Loading state
  if (!selectedErrorId) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          錯誤回放
        </h3>
        <div className="text-gray-500 dark:text-gray-400 text-center py-8 text-sm">
          請先在錯誤列表中選擇一筆錯誤，才能啟動回放。
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          錯誤回放
        </h3>
        <div className="text-gray-500 dark:text-gray-400 text-center py-8 text-sm">
          載入回放資料中…
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          錯誤回放
        </h3>
        <div className="text-red-500 dark:text-red-400 text-center py-8">
          <div className="mb-4">無法載入錯誤回放資料</div>
          <div className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            {error instanceof Error ? error.message : "未知錯誤"}
          </div>
          <button
            onClick={() => refetch()}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm"
          >
            重試
          </button>
        </div>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          錯誤回放
        </h3>
        <div className="text-gray-500 dark:text-gray-400 text-center py-8 text-sm">
          無回放資料
        </div>
      </div>
    );
  }

  // Prepare chart data
  const priceChartData = report.price_series.map((point) => ({
    ts: new Date(point.ts).toLocaleString("zh-TW", {
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    }),
    close: point.close,
    high: point.high,
    low: point.low,
    open: point.open,
    volume: point.volume,
  }));

  const factorChartData = report.factor_series.map((point) => ({
    ts: new Date(point.ts).toLocaleString("zh-TW", {
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    }),
    raw_score: point.raw_score ?? null,
    final_score: point.final_score ?? null,
  }));

  // Prepare trade markers
  const tradesByTime = new Map<string, { action: string; price: number; quantity: number }>();
  report.trades.forEach((trade) => {
    const tsKey = new Date(trade.ts).toLocaleString("zh-TW", {
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
    tradesByTime.set(tsKey, {
      action: trade.action,
      price: trade.price,
      quantity: trade.quantity,
    });
  });

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        錯誤回放：{report.meta.symbol} ({report.meta.date})
      </h3>

      {/* Charts Section */}
      <div className="space-y-6 mb-6">
        {/* Price Chart */}
        {report.price_series.length > 0 ? (
          <div>
            <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              價格走勢
            </h4>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={priceChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="ts" stroke="#6b7280" fontSize={12} />
                <YAxis stroke="#6b7280" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#1f2937",
                    border: "1px solid #374151",
                    borderRadius: "4px",
                  }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="close"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  name="收盤價"
                  dot={false}
                />
              {report.trades.map((trade, idx) => {
                const tsKey = new Date(trade.ts).toLocaleString("zh-TW", {
                  month: "2-digit",
                  day: "2-digit",
                  hour: "2-digit",
                  minute: "2-digit",
                });
                return (
                  <ReferenceLine
                    key={idx}
                    x={tsKey}
                    stroke={trade.action === "BUY" ? "#10b981" : "#ef4444"}
                    strokeWidth={2}
                    strokeDasharray="5 5"
                    label={{
                      value: trade.action,
                      position: "top",
                      fill: trade.action === "BUY" ? "#10b981" : "#ef4444",
                      fontSize: 10,
                    }}
                  />
                );
              })}
              </LineChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="text-gray-500 dark:text-gray-400 text-center py-8 text-sm">
            目前缺少價格資料，無法繪製圖表。
          </div>
        )}

        {/* Factor/Score Chart */}
        {report.factor_series.length > 0 ? (
          <div>
            <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              分數變化
            </h4>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={factorChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="ts" stroke="#6b7280" fontSize={12} />
                <YAxis stroke="#6b7280" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#1f2937",
                    border: "1px solid #374151",
                    borderRadius: "4px",
                  }}
                />
                <Legend />
                {report.factor_series.some((f) => f.raw_score !== null) && (
                  <Line
                    type="monotone"
                    dataKey="raw_score"
                    stroke="#f59e0b"
                    strokeWidth={2}
                    name="Raw Score"
                    dot={false}
                  />
                )}
                {report.factor_series.some((f) => f.final_score !== null) && (
                  <Line
                    type="monotone"
                    dataKey="final_score"
                    stroke="#8b5cf6"
                    strokeWidth={2}
                    name="Final Score"
                    dot={false}
                  />
                )}
              </LineChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="text-gray-500 dark:text-gray-400 text-center py-4 text-sm">
            因子資料缺失
          </div>
        )}
      </div>

      {/* Diagnosis Section */}
      <div className="border-t border-gray-200 dark:border-gray-700 pt-6">
        <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">
          診斷分析
        </h4>

        {/* Root Cause */}
        <div className="mb-4">
          <div className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
            根本原因
          </div>
          <div className="text-sm text-gray-900 dark:text-white bg-gray-50 dark:bg-gray-900 p-3 rounded">
            {report.diagnosis.root_cause}
          </div>
        </div>

        {/* Contributing Factors */}
        {report.diagnosis.contributing_factors.length > 0 && (
          <div className="mb-4">
            <div className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
              影響因素
            </div>
            <ul className="list-disc list-inside text-sm text-gray-700 dark:text-gray-300 space-y-1">
              {report.diagnosis.contributing_factors.map((factor, idx) => (
                <li key={idx}>{factor}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Missed Signals */}
        {report.diagnosis.missed_signals.length > 0 && (
          <div className="mb-4">
            <div className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
              錯過的訊號
            </div>
            <ul className="list-disc list-inside text-sm text-gray-700 dark:text-gray-300 space-y-1">
              {report.diagnosis.missed_signals.map((signal, idx) => (
                <li key={idx}>{signal}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Doctrine References */}
        {report.diagnosis.doctrine_refs.length > 0 && (
          <div>
            <div className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-2">
              Doctrine 參考
            </div>
            <div className="flex flex-wrap gap-2">
              {report.diagnosis.doctrine_refs.map((ref, idx) => (
                <span
                  key={idx}
                  className="px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 text-xs rounded"
                >
                  {ref}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

