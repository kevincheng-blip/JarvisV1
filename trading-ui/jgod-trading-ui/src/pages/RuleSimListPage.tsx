/**
 * Rule Simulation List Page
 * 
 * Displays recent rule simulation experiments.
 */

import { useRuleSimExperiments } from "../hooks/useRuleSim";
import type { RuleSimRecommendation } from "../types/ruleSim";

export function RuleSimListPage() {
  const { data, isLoading, isError, error } = useRuleSimExperiments(20);
  
  const getRecommendationColor = (rec: RuleSimRecommendation) => {
    switch (rec) {
      case "APPROVE":
        return "bg-green-500 text-white";
      case "CAUTION":
        return "bg-yellow-500 text-white";
      case "REJECT":
        return "bg-red-500 text-white";
      default:
        return "bg-gray-500 text-white";
    }
  };
  
  const getStatusColor = (status: string) => {
    switch (status) {
      case "SUCCESS":
        return "text-green-600";
      case "FAILED":
        return "text-red-600";
      case "RUNNING":
        return "text-blue-600";
      case "PENDING":
        return "text-gray-600";
      default:
        return "text-gray-600";
    }
  };
  
  if (isLoading) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-bold mb-4">Rule Simulation Experiments</h1>
        <div className="text-gray-500">載入中...</div>
      </div>
    );
  }
  
  if (isError) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-bold mb-4">Rule Simulation Experiments</h1>
        <div className="text-red-500">
          錯誤: {error instanceof Error ? error.message : "未知錯誤"}
        </div>
      </div>
    );
  }
  
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Rule Simulation Experiments</h1>
      
      {data && data.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="min-w-full bg-white dark:bg-gray-800 rounded-lg shadow">
            <thead>
              <tr className="bg-gray-100 dark:bg-gray-700">
                <th className="px-4 py-2 text-left">Experiment ID</th>
                <th className="px-4 py-2 text-left">Target Ruleset</th>
                <th className="px-4 py-2 text-left">Created At</th>
                <th className="px-4 py-2 text-left">Status</th>
                <th className="px-4 py-2 text-left">Baseline Sharpe</th>
                <th className="px-4 py-2 text-left">Variant Sharpe</th>
                <th className="px-4 py-2 text-left">Sharpe Delta</th>
                <th className="px-4 py-2 text-left">Recommendation</th>
                <th className="px-4 py-2 text-left">操作</th>
              </tr>
            </thead>
            <tbody>
              {data.map((experiment) => (
                <tr
                  key={experiment.experiment_id}
                  className="border-b border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50"
                >
                  <td className="px-4 py-2 font-mono text-sm">
                    {experiment.experiment_id.substring(0, 8)}...
                  </td>
                  <td className="px-4 py-2">
                    <div>
                      <div className="font-semibold">{experiment.target_ruleset.id}</div>
                      <div className="text-xs text-gray-500">{experiment.target_ruleset.type}</div>
                    </div>
                  </td>
                  <td className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400">
                    {new Date(experiment.created_at).toLocaleString("zh-TW")}
                  </td>
                  <td className="px-4 py-2">
                    <span className={`text-sm ${getStatusColor(experiment.status)}`}>
                      {experiment.status}
                    </span>
                  </td>
                  <td className="px-4 py-2 text-sm">{experiment.baseline_sharpe.toFixed(3)}</td>
                  <td className="px-4 py-2 text-sm">{experiment.variant_sharpe.toFixed(3)}</td>
                  <td className="px-4 py-2">
                    <span
                      className={`text-sm font-semibold ${
                        experiment.sharpe_delta >= 0 ? "text-green-600" : "text-red-600"
                      }`}
                    >
                      {experiment.sharpe_delta >= 0 ? "+" : ""}
                      {experiment.sharpe_delta.toFixed(3)}
                    </span>
                  </td>
                  <td className="px-4 py-2">
                    <span className={`px-2 py-1 text-xs rounded ${getRecommendationColor(experiment.recommendation)}`}>
                      {experiment.recommendation}
                    </span>
                  </td>
                  <td className="px-4 py-2">
                    <button
                      onClick={() => {
                        window.dispatchEvent(new CustomEvent('ruleSim:navigate', {
                          detail: { page: 'detail', experimentId: experiment.experiment_id }
                        }));
                      }}
                      className="px-2 py-1 bg-blue-500 text-white text-xs rounded hover:bg-blue-600"
                    >
                      查看詳情
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="text-gray-500 text-center py-8">
          目前沒有任何 Rule Simulation 實驗
        </div>
      )}
    </div>
  );
}

