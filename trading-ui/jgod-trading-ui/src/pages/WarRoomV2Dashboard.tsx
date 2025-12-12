/**
 * WarRoomV2Dashboard Page
 * 
 * J-GOD War Room V2 - Unified Control Center
 * 
 * 整合四大核心：
 * 1. Decision Layer V2 (Top N Predictions)
 * 2. Knowledge Observer (治理監控)
 * 3. Doctrine Patch Queue
 * 4. Decision AB Test Dashboard
 */

import { useState } from "react";
import { ExecutiveSummary } from "../components/war-room-v2/ExecutiveSummary";
import { TopPredictionsPanel } from "../components/war-room-v2/TopPredictionsPanel";
import { SRankTrendCard } from "../components/war-room-v2/SRankTrendCard";
import { PatchQueueCard } from "../components/war-room-v2/PatchQueueCard";
import { AbTestSummaryCard } from "../components/war-room-v2/AbTestSummaryCard";
import { PredictionStabilityCard } from "../components/war-room-v2/PredictionStabilityCard";
import { useFinalScoreV2 } from "../hooks/war-room/usePredictions";
import type { TopLongItem, TopShortItem } from "../types/warRoom";

/**
 * Decision Context V2 Side Drawer
 */
function DecisionContextDrawer({
  isOpen,
  onClose,
  symbol,
  item,
}: {
  isOpen: boolean;
  onClose: () => void;
  symbol: string | null;
  item: (TopLongItem | TopShortItem) | null;
}) {
  const today = new Date().toISOString().split('T')[0];
  const { 
    data: contextData, 
    isLoading: contextLoading, 
    isError: contextError 
  } = useFinalScoreV2(symbol, today, isOpen && !!symbol);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black bg-opacity-50"
        onClick={onClose}
      />

      {/* Drawer */}
      <div className="absolute right-0 top-0 h-full w-96 bg-white dark:bg-gray-800 shadow-xl overflow-y-auto">
        <div className="p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Decision Context V2
            </h2>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 text-2xl leading-none"
            >
              ×
            </button>
          </div>

          {contextLoading ? (
            <div className="space-y-4">
              <div className="h-4 bg-gray-200 dark:bg-gray-700 animate-pulse rounded w-24" />
              <div className="h-8 bg-gray-200 dark:bg-gray-700 animate-pulse rounded w-32" />
              <div className="h-4 bg-gray-200 dark:bg-gray-700 animate-pulse rounded w-24" />
            </div>
          ) : contextError ? (
            <div className="text-red-500 dark:text-red-400 text-sm">
              載入 Decision Context 失敗，顯示基本資訊
            </div>
          ) : null}

          <div className="space-y-4">
            {/* Symbol & Name */}
            <div>
              <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                標的代碼
              </h3>
              <p className="text-lg font-semibold text-gray-900 dark:text-white">
                {item?.symbol || symbol} - {item?.name || "N/A"}
              </p>
            </div>

            {/* Final Score */}
            <div>
              <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                Final Score
              </h3>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {contextData?.final_score?.toFixed(2) ?? item?.final_score.toFixed(2) ?? "N/A"}
              </p>
            </div>

            {/* Raw Score */}
            <div>
              <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                Raw Score
              </h3>
              <p className="text-lg text-gray-900 dark:text-white">
                {contextData?.raw_score?.toFixed(2) ?? item?.raw_score.toFixed(2) ?? "N/A"}
              </p>
            </div>

            {/* S-Rank */}
            {contextData?.s_rank_level && (
              <div>
                <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                  S-Rank
                </h3>
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-1 text-sm font-semibold rounded ${
                    contextData.s_rank_level === 'S' || contextData.s_rank_level === 'A' 
                      ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
                      : contextData.s_rank_level === 'B'
                      ? "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200"
                      : "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200"
                  }`}>
                    {contextData.s_rank_level}
                  </span>
                  {contextData.s_rank_weighted_score !== undefined && (
                    <span className="text-sm text-gray-600 dark:text-gray-400">
                      ({contextData.s_rank_weighted_score.toFixed(2)})
                    </span>
                  )}
                </div>
              </div>
            )}

            {/* Strategy Scores */}
            {contextData?.strategy_scores && Object.keys(contextData.strategy_scores).length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
                  Strategy Scores
                </h3>
                <div className="space-y-1">
                  {Object.entries(contextData.strategy_scores).map(([strategy, score]) => (
                    <div key={strategy} className="flex justify-between text-sm">
                      <span className="text-gray-700 dark:text-gray-300">{strategy}:</span>
                      <span className="font-medium text-gray-900 dark:text-white">{score.toFixed(2)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Conflict Summary */}
            {contextData?.conflict_summary && (
              <div>
                <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                  Conflict Summary
                </h3>
                <p className="text-sm text-gray-700 dark:text-gray-300 bg-yellow-50 dark:bg-yellow-900/20 p-2 rounded">
                  {contextData.conflict_summary}
                </p>
              </div>
            )}

            {/* Doctrine Alerts */}
            {(contextData?.doctrine_alerts && contextData.doctrine_alerts.length > 0) || 
             (item?.doctrine_flags && item.doctrine_flags.length > 0) ? (
              <div>
                <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
                  Doctrine Alerts
                </h3>
                <div className="space-y-2">
                  {contextData?.doctrine_alerts?.map((alert, i) => (
                    <div
                      key={i}
                      className={`p-2 rounded text-xs ${
                        alert.severity === 'critical' 
                          ? "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200"
                          : alert.severity === 'warning'
                          ? "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200"
                          : "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200"
                      }`}
                    >
                      <div className="font-medium">{alert.type}</div>
                      <div>{alert.message}</div>
                      {alert.rule_id && (
                        <div className="text-xs opacity-75 mt-1">Rule: {alert.rule_id}</div>
                      )}
                    </div>
                  ))}
                  {!contextData?.doctrine_alerts && item?.doctrine_flags?.map((flag, i) => (
                    <span
                      key={i}
                      className="inline-block px-2 py-1 text-xs bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200 rounded mr-2 mb-2"
                    >
                      {typeof flag === 'string' ? flag : String(flag)}
                    </span>
                  ))}
                </div>
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
}

export function WarRoomV2Dashboard() {
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null);
  const [selectedItem, setSelectedItem] = useState<(TopLongItem | TopShortItem) | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  const handlePredictionClick = (symbol: string, item: TopLongItem | TopShortItem) => {
    setSelectedSymbol(symbol);
    setSelectedItem(item);
    setIsDrawerOpen(true);
  };

  const handleCloseDrawer = () => {
    setIsDrawerOpen(false);
    setSelectedSymbol(null);
    setSelectedItem(null);
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Page Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            War Room V2 Dashboard
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            統一的控制中心 - Decision V2 + Observer + Doctrine Patch + AB Test
          </p>
        </div>

        {/* Executive Summary Row */}
        <ExecutiveSummary />

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Top Predictions */}
          <div className="lg:col-span-2">
            <TopPredictionsPanel onPredictionClick={handlePredictionClick} />
          </div>

          {/* Right Column - Observer & Governance */}
          <div className="space-y-6">
            <SRankTrendCard />
            <PredictionStabilityCard symbol={selectedSymbol || "2330"} />
            <PatchQueueCard />
            <AbTestSummaryCard />
          </div>
        </div>
      </div>

      {/* Decision Context Side Drawer */}
      <DecisionContextDrawer
        isOpen={isDrawerOpen}
        onClose={handleCloseDrawer}
        symbol={selectedSymbol}
        item={selectedItem}
      />
    </div>
  );
}
