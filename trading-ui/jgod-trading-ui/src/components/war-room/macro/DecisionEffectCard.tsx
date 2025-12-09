/**
 * DecisionEffectCard Component
 * 
 * Macro Layer - Decision Effect Card
 * 
 * 顯示 Doctrine 介入後的策略表現差異（RAW_ONLY vs DECISION_ON）
 */

import { useDecisionAbRecent } from "../../../hooks/useDecisionAbReport";

export function DecisionEffectCard() {
  const { data: abResults, isLoading, isError, error, refetch } = useDecisionAbRecent(1);

  // Loading state
  if (isLoading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Decision Layer 效果評估
        </h3>
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-4 bg-gray-200 dark:bg-gray-700 animate-pulse rounded" />
          ))}
        </div>
      </div>
    );
  }

  // Error state
  if (isError) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Decision Layer 效果評估
        </h3>
        <div className="text-red-500 dark:text-red-400 text-center py-8">
          <div className="mb-4">無法取得 AB 測試報告</div>
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

  // Empty state
  if (!abResults || abResults.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Decision Layer 效果評估
        </h3>
        <div className="text-gray-500 dark:text-gray-400 text-center py-8 text-sm">
          尚未有 Decision Layer AB Test 結果，請先執行回測腳本。
        </div>
      </div>
    );
  }

  // Display latest result
  const latestResult = abResults[0];

  const formatDelta = (delta: number, isPercent: boolean = false, reverseColor: boolean = false) => {
    const isPositive = delta > 0;
    const color = reverseColor
      ? (isPositive ? "text-red-600 dark:text-red-400" : "text-green-600 dark:text-green-400")
      : (isPositive ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400");
    const arrow = isPositive ? "▲" : "▼";
    const value = isPercent ? `${(delta * 100).toFixed(2)}%` : delta.toFixed(4);
    return (
      <span className={color}>
        {arrow} {value}
      </span>
    );
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        Decision Layer 效果評估
      </h3>

      {/* Experiment Info */}
      <div className="mb-4 pb-4 border-b border-gray-200 dark:border-gray-700">
        <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">
          實驗 ID
        </div>
        <div className="font-mono text-sm text-gray-900 dark:text-white">
          {latestResult.experiment_id}
        </div>
        <div className="text-xs text-gray-500 dark:text-gray-500 mt-1">
          {latestResult.raw_only.start_date} ~ {latestResult.raw_only.end_date}
        </div>
      </div>

      {/* Metrics Comparison */}
      <div className="space-y-4">
        {/* Sharpe Ratio */}
        <div>
          <div className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-2">
            Sharpe Ratio
          </div>
          <div className="grid grid-cols-3 gap-2 text-sm">
            <div className="text-gray-700 dark:text-gray-300">
              RAW: <span className="font-mono">{latestResult.raw_only.metrics.sharpe.toFixed(4)}</span>
            </div>
            <div className="text-gray-700 dark:text-gray-300">
              DECISION: <span className="font-mono">{latestResult.decision_on.metrics.sharpe.toFixed(4)}</span>
            </div>
            <div className="font-semibold">
              Delta: {formatDelta(latestResult.delta_sharpe)}
            </div>
          </div>
        </div>

        {/* Max Drawdown */}
        <div>
          <div className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-2">
            最大回撤 (Max Drawdown)
          </div>
          <div className="grid grid-cols-3 gap-2 text-sm">
            <div className="text-gray-700 dark:text-gray-300">
              RAW: <span className="font-mono">{(latestResult.raw_only.metrics.max_drawdown * 100).toFixed(2)}%</span>
            </div>
            <div className="text-gray-700 dark:text-gray-300">
              DECISION: <span className="font-mono">{(latestResult.decision_on.metrics.max_drawdown * 100).toFixed(2)}%</span>
            </div>
            <div className="font-semibold">
              Delta: {formatDelta(latestResult.delta_max_drawdown, true, true)}
            </div>
          </div>
        </div>

        {/* Total Return */}
        <div>
          <div className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-2">
            總報酬率 (Total Return)
          </div>
          <div className="grid grid-cols-3 gap-2 text-sm">
            <div className="text-gray-700 dark:text-gray-300">
              RAW: <span className="font-mono">{(latestResult.raw_only.metrics.total_return * 100).toFixed(2)}%</span>
            </div>
            <div className="text-gray-700 dark:text-gray-300">
              DECISION: <span className="font-mono">{(latestResult.decision_on.metrics.total_return * 100).toFixed(2)}%</span>
            </div>
            <div className="font-semibold">
              Delta: {formatDelta(latestResult.delta_total_return, true)}
            </div>
          </div>
        </div>

        {/* Win Rate */}
        <div>
          <div className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-2">
            勝率 (Win Rate)
          </div>
          <div className="grid grid-cols-3 gap-2 text-sm">
            <div className="text-gray-700 dark:text-gray-300">
              RAW: <span className="font-mono">{(latestResult.raw_only.metrics.win_rate * 100).toFixed(2)}%</span>
            </div>
            <div className="text-gray-700 dark:text-gray-300">
              DECISION: <span className="font-mono">{(latestResult.decision_on.metrics.win_rate * 100).toFixed(2)}%</span>
            </div>
            <div className="font-semibold">
              Delta: {formatDelta(latestResult.delta_win_rate, true)}
            </div>
          </div>
        </div>
      </div>

      {/* Additional Info */}
      <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700 text-xs text-gray-500 dark:text-gray-500">
        測試時間: {new Date(latestResult.created_at).toLocaleString("zh-TW")}
      </div>
    </div>
  );
}

