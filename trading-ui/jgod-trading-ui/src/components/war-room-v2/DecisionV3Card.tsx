/**
 * DecisionV3Card Component
 * 
 * War Room V2 - Decision Engine V3
 * 
 * 顯示決策結果：主要策略、風險狀態、信心度、決策理由
 */

import { useState } from "react";
import { useDecisionV3 } from "../../hooks/useDecisionV3";
import {
  useDecisionV3Latest,
  useRecomputeDecisionV3,
  useDecisionV3SnapshotList,
} from "../../hooks/useDecisionV3Snapshots";
import {
  useDecisionV3EvalLatest,
  useRecomputeDecisionV3Eval,
  useDecisionV3EvalList,
} from "../../hooks/useDecisionV3Eval";

interface DecisionV3CardProps {
  symbol: string | null;
}

export function DecisionV3Card({ symbol }: DecisionV3CardProps) {
  const { data, isLoading, isError, error, refetch } = useDecisionV3(symbol, "performance", 60, 5, !!symbol);
  const { data: latestData } = useDecisionV3Latest(symbol, !!symbol);
  const { data: snapshotList } = useDecisionV3SnapshotList(symbol, 5, !!symbol);
  const recomputeDecision = useRecomputeDecisionV3();
  const [actionMessage, setActionMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);
  
  // Evaluation hooks
  const { data: evalLatest } = useDecisionV3EvalLatest(symbol || "");
  const { data: evalList } = useDecisionV3EvalList(symbol || "", 5);
  const recomputeEval = useRecomputeDecisionV3Eval(symbol || "");
  const [evalActionMessage, setEvalActionMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const getRiskStateColor = (state: string) => {
    switch (state) {
      case "RISK_ON":
        return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200";
      case "CAUTION":
        return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200";
      case "RISK_OFF":
        return "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200";
      default:
        return "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200";
    }
  };

  const getRiskStateLabel = (state: string) => {
    switch (state) {
      case "RISK_ON":
        return "正常操作";
      case "CAUTION":
        return "謹慎操作";
      case "RISK_OFF":
        return "暫停操作";
      default:
        return state;
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

  const getVerdictColor = (verdict: string) => {
    switch (verdict) {
      case "IMPROVED":
        return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200";
      case "NEUTRAL":
        return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200";
      case "REGRESSED":
        return "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200";
      case "NO_DATA":
        return "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200";
      default:
        return "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200";
    }
  };

  const getVerdictLabel = (verdict: string) => {
    switch (verdict) {
      case "IMPROVED":
        return "改善";
      case "NEUTRAL":
        return "中性";
      case "REGRESSED":
        return "衰退";
      case "NO_DATA":
        return "無資料";
      default:
        return verdict;
    }
  };

  const handleRecomputeEval = async () => {
    if (!symbol) return;
    
    setEvalActionMessage(null);
    try {
      await recomputeEval.mutateAsync({ mode: "performance", limit: 60, k: 5, window: 20 });
      setEvalActionMessage({ type: "success", text: "評估重新計算成功" });
      setTimeout(() => setEvalActionMessage(null), 3000);
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || "操作失敗";
      setEvalActionMessage({ type: "error", text: errorMsg });
      setTimeout(() => setEvalActionMessage(null), 5000);
    }
  };

  if (isLoading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Decision V3
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
          Decision V3
        </h3>
        <div className="text-red-500 dark:text-red-400 text-sm">
          載入失敗: {error instanceof Error ? error.message : '未知錯誤'}
        </div>
      </div>
    );
  }

  const handleRecompute = async () => {
    if (!symbol) return;
    
    setActionMessage(null);
    try {
      await recomputeDecision.mutateAsync({ symbol, mode: "performance", limit: 60, k: 5 });
      setActionMessage({ type: "success", text: "決策重新計算成功" });
      // Refetch all related data
      refetch();
      setTimeout(() => setActionMessage(null), 3000);
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || "操作失敗";
      setActionMessage({ type: "error", text: errorMsg });
      setTimeout(() => setActionMessage(null), 5000);
    }
  };

  if (!data || !data.selected_primary_strategy) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Decision V3
        </h3>
        <div className="text-gray-500 dark:text-gray-400 text-center py-8">
          {symbol ? `Decision V3 暫無 ${symbol} 的決策資料` : "請選擇股票代碼"}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Decision V3
        </h3>
        <span className={`px-2 py-1 text-xs rounded ${getRiskStateColor(data.risk_plan.risk_state)}`}>
          {getRiskStateLabel(data.risk_plan.risk_state)}
        </span>
      </div>

      {/* Latest Snapshot Info */}
      {latestData && latestData.snapshot_id && (
        <div className="mb-3 text-xs text-gray-500 dark:text-gray-400">
          最新快照: {new Date(latestData.created_at).toLocaleString("zh-TW")}
        </div>
      )}

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

      {/* Recompute Button */}
      <div className="mb-4">
        <button
          onClick={handleRecompute}
          disabled={recomputeDecision.isPending || !symbol}
          className="px-3 py-1.5 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {recomputeDecision.isPending ? "計算中..." : "Recompute"}
        </button>
      </div>

      {/* Primary Strategy */}
      <div className="mb-4">
        <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">主要策略</div>
        <div className="text-lg font-semibold text-gray-900 dark:text-white">
          {getStrategyName(data.selected_primary_strategy)}
        </div>
        {data.selected_secondary_strategies.length > 0 && (
          <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            輔助: {data.selected_secondary_strategies.map(s => getStrategyName(s)).join(", ")}
          </div>
        )}
      </div>

      {/* Risk Plan & Confidence */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">建議倉位</div>
          <div className="text-lg font-semibold text-gray-900 dark:text-white">
            {(data.risk_plan.position_scale * 100).toFixed(0)}%
          </div>
        </div>
        <div>
          <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">信心度</div>
          <div className={`text-lg font-semibold ${
            data.confidence >= 0.7
              ? "text-green-600 dark:text-green-400"
              : data.confidence >= 0.4
              ? "text-yellow-600 dark:text-yellow-400"
              : "text-red-600 dark:text-red-400"
          }`}>
            {(data.confidence * 100).toFixed(0)}%
          </div>
        </div>
      </div>

      {/* Top Weights */}
      {data.weights.length > 0 && (
        <div className="mb-4">
          <div className="text-xs text-gray-500 dark:text-gray-400 mb-2">策略權重 (Top 3)</div>
          <div className="space-y-1">
            {data.weights.slice(0, 3).map((w, index) => (
              <div key={w.strategy_id} className="flex justify-between text-sm">
                <span className="text-gray-700 dark:text-gray-300">
                  #{index + 1} {getStrategyName(w.strategy_id)}
                </span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {(w.weight * 100).toFixed(1)}%
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Risk Reasons */}
      {data.risk_plan.reasons.length > 0 && (
        <div className="mb-4">
          <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">風險理由</div>
          <ul className="text-xs text-gray-600 dark:text-gray-400 list-disc list-inside">
            {data.risk_plan.reasons.map((reason, i) => (
              <li key={i}>{reason}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Explanation */}
      {data.explain && (
        <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          <div className="text-xs text-gray-500 dark:text-gray-400 mb-2">決策說明</div>
          <div className="text-xs text-gray-700 dark:text-gray-300 whitespace-pre-line">
            {data.explain}
          </div>
        </div>
      )}

      {/* Recent Snapshots */}
      {snapshotList && snapshotList.items.length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          <div className="text-xs text-gray-500 dark:text-gray-400 mb-2">最近快照 ({snapshotList.total})</div>
          <div className="space-y-1">
            {snapshotList.items.slice(0, 5).map((item) => (
              <div key={item.snapshot_id} className="flex justify-between text-xs">
                <div className="text-gray-600 dark:text-gray-400">
                  {new Date(item.created_at).toLocaleString("zh-TW", {
                    month: "2-digit",
                    day: "2-digit",
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                  {item.primary_strategy && ` • ${getStrategyName(item.primary_strategy)}`}
                </div>
                <div className="text-gray-700 dark:text-gray-300">
                  {(item.confidence * 100).toFixed(0)}%
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Evaluation Section */}
      <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
        <div className="flex justify-between items-center mb-3">
          <h4 className="text-sm font-semibold text-gray-900 dark:text-white">評估 (Evaluation)</h4>
          <button
            onClick={handleRecomputeEval}
            disabled={recomputeEval.isPending || !symbol}
            className="px-2 py-1 text-xs bg-purple-600 text-white rounded hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {recomputeEval.isPending ? "計算中..." : "Run Evaluation"}
          </button>
        </div>

        {/* Eval Action Message */}
        {evalActionMessage && (
          <div className={`mb-3 p-2 rounded text-xs ${
            evalActionMessage.type === "success"
              ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
              : "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200"
          }`}>
            {evalActionMessage.text}
          </div>
        )}

        {/* Latest Evaluation */}
        {evalLatest && evalLatest.evaluation && evalLatest.evaluation.metrics.verdict !== "NO_DATA" ? (
          <>
            {/* Verdict Badge */}
            <div className="mb-3">
              <span className={`px-2 py-1 text-xs rounded ${getVerdictColor(evalLatest.evaluation.metrics.verdict)}`}>
                {getVerdictLabel(evalLatest.evaluation.metrics.verdict)}
              </span>
              {evalLatest.created_at && (
                <span className="ml-2 text-xs text-gray-500 dark:text-gray-400">
                  {new Date(evalLatest.created_at).toLocaleString("zh-TW")}
                </span>
              )}
            </div>

            {/* Metrics Grid */}
            <div className="grid grid-cols-2 gap-2 mb-3">
              <div>
                <div className="text-xs text-gray-500 dark:text-gray-400">命中率</div>
                <div className="text-sm font-semibold text-gray-900 dark:text-white">
                  {(evalLatest.evaluation.metrics.hit_rate_proxy * 100).toFixed(1)}%
                </div>
              </div>
              <div>
                <div className="text-xs text-gray-500 dark:text-gray-400">平均報酬</div>
                <div className={`text-sm font-semibold ${
                  evalLatest.evaluation.metrics.avg_return_proxy > 0
                    ? "text-green-600 dark:text-green-400"
                    : "text-red-600 dark:text-red-400"
                }`}>
                  {(evalLatest.evaluation.metrics.avg_return_proxy * 100).toFixed(2)}%
                </div>
              </div>
              <div>
                <div className="text-xs text-gray-500 dark:text-gray-400">最大回撤</div>
                <div className="text-sm font-semibold text-gray-900 dark:text-white">
                  {(evalLatest.evaluation.metrics.max_drawdown_proxy * 100).toFixed(1)}%
                </div>
              </div>
              <div>
                <div className="text-xs text-gray-500 dark:text-gray-400">一致性</div>
                <div className="text-sm font-semibold text-gray-900 dark:text-white">
                  {(evalLatest.evaluation.metrics.decision_consistency * 100).toFixed(0)}%
                </div>
              </div>
            </div>

            {/* Recommendation */}
            {evalLatest.evaluation.metrics.recommendation_next_step && (
              <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
                <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">建議</div>
                <div className="text-xs text-gray-700 dark:text-gray-300 whitespace-pre-line">
                  {evalLatest.evaluation.metrics.recommendation_next_step}
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="text-xs text-gray-500 dark:text-gray-400 text-center py-4">
            暫無評估資料
          </div>
        )}

        {/* Recent Evaluations */}
        {evalList && evalList.items.length > 0 && (
          <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
            <div className="text-xs text-gray-500 dark:text-gray-400 mb-2">最近評估 ({evalList.total})</div>
            <div className="space-y-1">
              {evalList.items.slice(0, 3).map((item) => (
                <div key={item.eval_id} className="flex justify-between text-xs">
                  <div className="text-gray-600 dark:text-gray-400">
                    {new Date(item.created_at).toLocaleString("zh-TW", {
                      month: "2-digit",
                      day: "2-digit",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </div>
                  <span className={`px-1.5 py-0.5 rounded text-xs ${getVerdictColor(item.verdict)}`}>
                    {getVerdictLabel(item.verdict)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

