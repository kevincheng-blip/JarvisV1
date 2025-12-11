/**
 * SRankTrendCard Component
 * 
 * War Room V2 - S-Rank Trend Chart
 * 
 * 顯示 S-Rank 分佈趨勢（堆疊柱狀圖）
 */

import { useSRankDistributionHistory } from "../../hooks/useObserver";

export function SRankTrendCard() {
  const { data: distributionHistory, isLoading, isError, error } = useSRankDistributionHistory(30);

  if (isLoading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          S-Rank 分佈趨勢
        </h3>
        <div className="h-64 bg-gray-200 dark:bg-gray-700 animate-pulse rounded" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          S-Rank 分佈趨勢
        </h3>
        <div className="text-red-500 dark:text-red-400 text-sm">
          載入失敗: {error instanceof Error ? error.message : '未知錯誤'}
        </div>
      </div>
    );
  }

  if (!distributionHistory || distributionHistory.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          S-Rank 分佈趨勢
        </h3>
        <div className="text-gray-500 dark:text-gray-400 text-center py-8">暫無資料</div>
      </div>
    );
  }

  // Get last entry for current distribution summary
  const latestDistribution = distributionHistory[distributionHistory.length - 1];

  // Calculate max value for scaling
  const maxValue = Math.max(
    ...distributionHistory.map(d =>
      d.distribution.S + d.distribution.A + d.distribution.B + d.distribution.C + d.distribution.D
    )
  ) || 1;

  // Get last 14 days for display (or all if less than 14)
  const displayData = distributionHistory.slice(-14);

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          S-Rank 分佈趨勢
        </h3>
        <div className="text-xs text-gray-500 dark:text-gray-400">
          目前: S:{latestDistribution.distribution.S} A:{latestDistribution.distribution.A} 
          B:{latestDistribution.distribution.B} C:{latestDistribution.distribution.C} 
          D:{latestDistribution.distribution.D}
        </div>
      </div>

      <div className="space-y-4">
        {/* Chart */}
        <div className="h-64 flex items-end justify-between gap-1">
          {displayData.map((item, index) => {
            const total = item.distribution.S + item.distribution.A + item.distribution.B +
                         item.distribution.C + item.distribution.D;
            const heightPercent = total > 0 ? (total / maxValue) * 100 : 0;

            return (
              <div key={index} className="flex-1 flex flex-col items-center" style={{ height: "100%" }}>
                <div className="w-full flex flex-col-reverse" style={{ height: `${heightPercent}%`, minHeight: "4px" }}>
                  {/* D (Red) */}
                  {item.distribution.D > 0 && (
                    <div
                      className="bg-red-600 dark:bg-red-700"
                      style={{
                        height: `${(item.distribution.D / (total || 1)) * 100}%`,
                      }}
                      title={`D: ${item.distribution.D}`}
                    />
                  )}
                  {/* C (Red) */}
                  {item.distribution.C > 0 && (
                    <div
                      className="bg-red-500 dark:bg-red-600"
                      style={{
                        height: `${(item.distribution.C / (total || 1)) * 100}%`,
                      }}
                      title={`C: ${item.distribution.C}`}
                    />
                  )}
                  {/* B (Yellow) */}
                  {item.distribution.B > 0 && (
                    <div
                      className="bg-yellow-500 dark:bg-yellow-600"
                      style={{
                        height: `${(item.distribution.B / (total || 1)) * 100}%`,
                      }}
                      title={`B: ${item.distribution.B}`}
                    />
                  )}
                  {/* A (Green) */}
                  {item.distribution.A > 0 && (
                    <div
                      className="bg-green-500 dark:bg-green-600"
                      style={{
                        height: `${(item.distribution.A / (total || 1)) * 100}%`,
                      }}
                      title={`A: ${item.distribution.A}`}
                    />
                  )}
                  {/* S (Green) */}
                  {item.distribution.S > 0 && (
                    <div
                      className="bg-green-600 dark:bg-green-700"
                      style={{
                        height: `${(item.distribution.S / (total || 1)) * 100}%`,
                      }}
                      title={`S: ${item.distribution.S}`}
                    />
                  )}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400 mt-1 transform -rotate-45 origin-left whitespace-nowrap">
                  {new Date(item.date).toLocaleDateString("zh-TW", { month: "short", day: "numeric" })}
                </div>
              </div>
            );
          })}
        </div>

        {/* Legend */}
        <div className="flex justify-center gap-4 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-green-600 dark:bg-green-700 rounded" />
            <span className="text-gray-700 dark:text-gray-300">S/A</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-yellow-500 dark:bg-yellow-600 rounded" />
            <span className="text-gray-700 dark:text-gray-300">B</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-red-500 dark:bg-red-600 rounded" />
            <span className="text-gray-700 dark:text-gray-300">C/D</span>
          </div>
        </div>
      </div>
    </div>
  );
}
