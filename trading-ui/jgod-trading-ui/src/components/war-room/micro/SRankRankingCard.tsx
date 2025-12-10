/**
 * S-Rank Ranking Card
 * 
 * War Room Micro Layer widget displaying strategy rankings.
 */

import { useState } from "react";
import { useSRankLatestFactors, useSRankStrategyHistory } from "../../../hooks/useSRankFactors";
import type { SRankFactor, RankLevel } from "../../../types/sRank";

export function SRankRankingCard() {
  const [selectedStrategy, setSelectedStrategy] = useState<string | null>(null);
  
  const { data: factors, isLoading, isError, error } = useSRankLatestFactors();
  
  // Calculate date range for history (last 30 days)
  const endDate = new Date().toISOString().split('T')[0];
  const startDate = new Date();
  startDate.setDate(startDate.getDate() - 30);
  const startDateStr = startDate.toISOString().split('T')[0];
  
  const { data: historyData } = useSRankStrategyHistory(
    selectedStrategy,
    startDateStr,
    endDate,
    !!selectedStrategy
  );
  
  const getRankBadgeClass = (rank: RankLevel) => {
    switch (rank) {
      case "S":
        return "bg-purple-500 text-white";
      case "A":
        return "bg-blue-500 text-white";
      case "B":
        return "bg-green-500 text-white";
      case "C":
        return "bg-yellow-500 text-white";
      case "D":
        return "bg-red-500 text-white";
      default:
        return "bg-gray-500 text-white";
    }
  };
  
  // TODO: Detect rank degradation (A/S -> C/D)
  // const hasRankDegradation = factors?.some((f, idx) => {
  //   const prevRank = previousFactors?.find(pf => pf.strategy_id === f.strategy_id);
  //   if (!prevRank) return false;
  //   const rankOrder = { "S": 5, "A": 4, "B": 3, "C": 2, "D": 1 };
  //   return rankOrder[prevRank.rank_level] >= 4 && rankOrder[f.rank_level] <= 2;
  // });
  
  if (isLoading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
          S-Rank 策略排行榜
        </h3>
        <div className="text-gray-500 dark:text-gray-400">載入中...</div>
      </div>
    );
  }
  
  if (isError) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
          S-Rank 策略排行榜
        </h3>
        <div className="text-red-500">
          錯誤: {error instanceof Error ? error.message : "未知錯誤"}
        </div>
      </div>
    );
  }
  
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          S-Rank 策略排行榜
        </h3>
        {/* TODO: Add rank degradation warning badge */}
      </div>
      
      {factors && factors.length > 0 ? (
        <>
          <div className="overflow-x-auto mb-4">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-700">
                  <th className="px-3 py-2 text-left">Strategy ID</th>
                  <th className="px-3 py-2 text-left">Rank</th>
                  <th className="px-3 py-2 text-left">S-Rank Score</th>
                  <th className="px-3 py-2 text-left">Sharpe</th>
                  <th className="px-3 py-2 text-left">MaxDD</th>
                </tr>
              </thead>
              <tbody>
                {factors.map((factor) => (
                  <tr
                    key={factor.strategy_id}
                    onClick={() => setSelectedStrategy(
                      selectedStrategy === factor.strategy_id ? null : factor.strategy_id
                    )}
                    className={`border-b border-gray-200 dark:border-gray-700 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50 ${
                      selectedStrategy === factor.strategy_id ? "bg-blue-50 dark:bg-blue-900/20" : ""
                    }`}
                  >
                    <td className="px-3 py-2 font-semibold">{factor.strategy_id}</td>
                    <td className="px-3 py-2">
                      <span className={`px-2 py-1 text-xs rounded font-semibold ${getRankBadgeClass(factor.rank_level)}`}>
                        {factor.rank_level}
                      </span>
                    </td>
                    <td className="px-3 py-2">
                      <span className="font-semibold">{factor.s_rank_score.toFixed(3)}</span>
                    </td>
                    <td className="px-3 py-2">{factor.performance_snapshot.sharpe_ratio.toFixed(2)}</td>
                    <td className="px-3 py-2">
                      {(factor.performance_snapshot.max_drawdown * 100).toFixed(2)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          {/* History Chart (Expandable) */}
          {selectedStrategy && (
            <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-700/50 rounded">
              <h4 className="font-semibold mb-2 text-gray-900 dark:text-white">
                {selectedStrategy} 歷史 S-Rank 走勢
              </h4>
              {historyData && historyData.length > 0 ? (
                <div className="space-y-2">
                  {historyData.slice(0, 10).map((factor) => (
                    <div
                      key={factor.calculated_at}
                      className="flex justify-between items-center text-sm"
                    >
                      <span className="text-gray-600 dark:text-gray-400">
                        {new Date(factor.calculated_at).toLocaleDateString("zh-TW")}
                      </span>
                      <div className="flex items-center gap-4">
                        <span className="font-semibold">{factor.s_rank_score.toFixed(3)}</span>
                        <span className={`px-2 py-1 text-xs rounded ${getRankBadgeClass(factor.rank_level)}`}>
                          {factor.rank_level}
                        </span>
                      </div>
                    </div>
                  ))}
                  {historyData.length > 10 && (
                    <div className="text-xs text-gray-500 text-center mt-2">
                      顯示最近 10 筆，共 {historyData.length} 筆
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-sm text-gray-500 dark:text-gray-400">
                  無歷史資料（TODO: 未來可整合圖表視覺化）
                </div>
              )}
            </div>
          )}
        </>
      ) : (
        <div className="text-gray-500 dark:text-gray-400 text-center py-4 text-sm">
          目前沒有 S-Rank 資料，請先執行計算
        </div>
      )}
    </div>
  );
}

