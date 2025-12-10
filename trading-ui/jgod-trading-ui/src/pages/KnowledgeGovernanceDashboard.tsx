/**
 * Knowledge Governance Dashboard
 * 
 * War Room - Knowledge Governance monitoring dashboard
 */

import { useGovernanceSummary, useStabilityAlerts, useSRankDistributionHistory } from "../hooks/useObserver";

export function KnowledgeGovernanceDashboard() {
  const { data: summary, isLoading: summaryLoading } = useGovernanceSummary();
  const { data: alerts, isLoading: alertsLoading } = useStabilityAlerts();
  const { data: distributionHistory, isLoading: historyLoading } = useSRankDistributionHistory(30);

  if (summaryLoading || alertsLoading || historyLoading) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-bold mb-6 text-gray-900 dark:text-white">
          知識治理監控面板
        </h1>
        <div className="text-gray-500 dark:text-gray-400">載入中...</div>
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-bold mb-6 text-gray-900 dark:text-white">
          知識治理監控面板
        </h1>
        <div className="text-red-500">無法載入治理數據</div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
        知識治理監控面板
      </h1>

      {/* Quick Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* 治理瓶頸 */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4 border-l-4 border-yellow-500">
          <div className="text-sm font-semibold text-gray-600 dark:text-gray-400 mb-1">
            治理瓶頸
          </div>
          <div className="text-3xl font-bold text-gray-900 dark:text-white">
            {summary.pending_review_count}
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            待審核條目
          </div>
        </div>

        {/* 系統風險 */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4 border-l-4 border-red-500">
          <div className="text-sm font-semibold text-gray-600 dark:text-gray-400 mb-1">
            系統風險
          </div>
          <div className="text-3xl font-bold text-gray-900 dark:text-white">
            {summary.critical_alerts_active}
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            CRITICAL 警報
          </div>
        </div>

        {/* 修正成功率 */}
        <div
          className={`bg-white dark:bg-gray-800 rounded-lg shadow-md p-4 border-l-4 ${
            summary.sim_approve_rate_30d >= 0.9
              ? "border-green-500"
              : summary.sim_approve_rate_30d >= 0.5
              ? "border-yellow-500"
              : "border-red-500"
          }`}
        >
          <div className="text-sm font-semibold text-gray-600 dark:text-gray-400 mb-1">
            修正成功率
          </div>
          <div className="text-3xl font-bold text-gray-900 dark:text-white">
            {(summary.sim_approve_rate_30d * 100).toFixed(1)}%
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            Rule Sim 批准率 (30天)
          </div>
        </div>

        {/* 策略健康度 */}
        <div
          className={`bg-white dark:bg-gray-800 rounded-lg shadow-md p-4 border-l-4 ${
            summary.s_rank_strategy_degradation_7d === 0
              ? "border-green-500"
              : summary.s_rank_strategy_degradation_7d <= 1
              ? "border-yellow-500"
              : "border-red-500"
          }`}
        >
          <div className="text-sm font-semibold text-gray-600 dark:text-gray-400 mb-1">
            策略健康度
          </div>
          <div className="text-3xl font-bold text-gray-900 dark:text-white">
            {summary.s_rank_strategy_degradation_7d}
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            策略退化 (7天)
          </div>
        </div>
      </div>

      {/* Stability Alerts */}
      {alerts && alerts.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <h2 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
            穩定性警報
          </h2>
          <div className="space-y-2">
            {alerts.map((alert, idx) => (
              <div
                key={idx}
                className={`p-3 rounded border-l-4 ${
                  alert.severity === "CRITICAL"
                    ? "border-red-500 bg-red-50 dark:bg-red-900/20"
                    : alert.severity === "WARNING"
                    ? "border-yellow-500 bg-yellow-50 dark:bg-yellow-900/20"
                    : "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
                }`}
              >
                <div className="flex items-center gap-2 mb-1">
                  <span
                    className={`px-2 py-1 text-xs rounded font-semibold ${
                      alert.severity === "CRITICAL"
                        ? "bg-red-500 text-white"
                        : alert.severity === "WARNING"
                        ? "bg-yellow-500 text-white"
                        : "bg-blue-500 text-white"
                    }`}
                  >
                    {alert.severity}
                  </span>
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    {new Date(alert.timestamp).toLocaleString("zh-TW")}
                  </span>
                </div>
                <div className="text-sm text-gray-900 dark:text-white">
                  {alert.message}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* S-Rank Distribution Chart */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h2 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
          S-Rank 策略分佈歷史 (過去 30 天)
        </h2>
        {distributionHistory && distributionHistory.length > 0 ? (
          <div className="space-y-2">
            {/* Simple stacked bar chart representation */}
            {distributionHistory.slice(-14).map((item) => {
              const total = Object.values(item.distribution).reduce((a, b) => a + b, 0);
              if (total === 0) return null;
              
              return (
                <div key={item.date} className="flex items-center gap-4">
                  <div className="w-24 text-xs text-gray-600 dark:text-gray-400">
                    {new Date(item.date).toLocaleDateString("zh-TW", {
                      month: "short",
                      day: "numeric",
                    })}
                  </div>
                  <div className="flex-1 flex h-6 rounded overflow-hidden">
                    {["S", "A", "B", "C", "D"].map((rank) => {
                      const count = item.distribution[rank as keyof typeof item.distribution] || 0;
                      const percentage = total > 0 ? (count / total) * 100 : 0;
                      return (
                        <div
                          key={rank}
                          className={`${
                            rank === "S"
                              ? "bg-purple-500"
                              : rank === "A"
                              ? "bg-blue-500"
                              : rank === "B"
                              ? "bg-green-500"
                              : rank === "C"
                              ? "bg-yellow-500"
                              : "bg-red-500"
                          } text-white text-xs flex items-center justify-center`}
                          style={{ width: `${percentage}%` }}
                          title={`${rank}: ${count}`}
                        >
                          {count > 0 && percentage > 10 ? rank : ""}
                        </div>
                      );
                    })}
                  </div>
                  <div className="w-16 text-xs text-gray-600 dark:text-gray-400 text-right">
                    總計: {total}
                  </div>
                </div>
              );
            })}
            {/* Legend */}
            <div className="flex gap-4 mt-4 text-xs">
              {["S", "A", "B", "C", "D"].map((rank) => (
                <div key={rank} className="flex items-center gap-1">
                  <div
                    className={`w-3 h-3 rounded ${
                      rank === "S"
                        ? "bg-purple-500"
                        : rank === "A"
                        ? "bg-blue-500"
                        : rank === "B"
                        ? "bg-green-500"
                        : rank === "C"
                        ? "bg-yellow-500"
                        : "bg-red-500"
                    }`}
                  />
                  <span className="text-gray-600 dark:text-gray-400">{rank}級</span>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="text-gray-500 dark:text-gray-400 text-center py-8 text-sm">
            無歷史數據
          </div>
        )}
      </div>

      {/* Additional Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4">
          <div className="text-sm font-semibold text-gray-600 dark:text-gray-400 mb-2">
            Doctrine 條文總數
          </div>
          <div className="text-2xl font-bold text-gray-900 dark:text-white">
            {summary.total_sections}
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4">
          <div className="text-sm font-semibold text-gray-600 dark:text-gray-400 mb-2">
            過去 7 天修改次數
          </div>
          <div className="text-2xl font-bold text-gray-900 dark:text-white">
            {summary.sections_modified_last_7d}
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4">
          <div className="text-sm font-semibold text-gray-600 dark:text-gray-400 mb-2">
            過去 30 天模擬次數
          </div>
          <div className="text-2xl font-bold text-gray-900 dark:text-white">
            {summary.simulations_last_30d}
          </div>
        </div>
      </div>
    </div>
  );
}

