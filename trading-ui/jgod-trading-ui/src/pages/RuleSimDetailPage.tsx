/**
 * Rule Simulation Detail Page
 * 
 * Displays detailed results of a rule simulation experiment.
 */

import { useRuleSimReport } from "../hooks/useRuleSim";
import type { RuleSimRecommendation } from "../types/ruleSim";

interface RuleSimDetailPageProps {
  experimentId: string;
  onBack?: () => void;
}

export function RuleSimDetailPage({ experimentId, onBack }: RuleSimDetailPageProps) {
  const { data: report, isLoading, isError, error } = useRuleSimReport(experimentId);
  
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
  
  if (isLoading) {
    return <div className="p-6">載入中...</div>;
  }
  
  if (isError || !report) {
    return (
      <div className="p-6">
        <div className="text-red-500">
          錯誤: {error instanceof Error ? error.message : "未知錯誤"}
        </div>
      </div>
    );
  }
  
  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold">
          Rule Simulation Report: {experimentId.substring(0, 8)}...
        </h1>
        {onBack && (
          <button
            onClick={onBack}
            className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
          >
            返回列表
          </button>
        )}
      </div>
      
      {/* Recommendation Badge */}
      <div className="mb-6">
        <div className={`inline-block px-6 py-3 rounded-lg text-lg font-semibold ${getRecommendationColor(report.recommendation)}`}>
          建議: {report.recommendation}
        </div>
      </div>
      
      {/* Config Section */}
      <div className="mb-6 p-4 bg-gray-100 dark:bg-gray-800 rounded">
        <h2 className="text-lg font-semibold mb-2">實驗配置</h2>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <strong>Target Ruleset:</strong> {report.config.target_ruleset?.id || "N/A"}
          </div>
          <div>
            <strong>Type:</strong> {report.config.target_ruleset?.type || "N/A"}
          </div>
          <div>
            <strong>Start Date:</strong> {report.config.start_date}
          </div>
          <div>
            <strong>End Date:</strong> {report.config.end_date}
          </div>
          <div>
            <strong>Universe:</strong> {report.config.universe.length > 0 ? report.config.universe.join(", ") : "Default"}
          </div>
          <div>
            <strong>Baseline Version:</strong> {report.config.baseline_version_id || "Production"}
          </div>
          <div>
            <strong>Variant Version:</strong> {report.config.variant_version_id || "N/A"}
          </div>
          <div>
            <strong>Status:</strong> {report.status.status}
          </div>
        </div>
      </div>
      
      {/* Metrics Comparison Table */}
      <div className="mb-6">
        <h2 className="text-lg font-semibold mb-2">指標比較</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full bg-white dark:bg-gray-800 rounded-lg shadow">
            <thead>
              <tr className="bg-gray-100 dark:bg-gray-700">
                <th className="px-4 py-2 text-left">指標</th>
                <th className="px-4 py-2 text-left">Baseline</th>
                <th className="px-4 py-2 text-left">Variant</th>
                <th className="px-4 py-2 text-left">Delta</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-gray-200 dark:border-gray-700">
                <td className="px-4 py-2 font-semibold">Sharpe Ratio</td>
                <td className="px-4 py-2">{report.baseline_metrics.sharpe.toFixed(3)}</td>
                <td className="px-4 py-2">{report.variant_metrics.sharpe.toFixed(3)}</td>
                <td className={`px-4 py-2 font-semibold ${report.deltas.sharpe_delta >= 0 ? "text-green-600" : "text-red-600"}`}>
                  {report.deltas.sharpe_delta >= 0 ? "+" : ""}
                  {report.deltas.sharpe_delta.toFixed(3)}
                </td>
              </tr>
              <tr className="border-b border-gray-200 dark:border-gray-700">
                <td className="px-4 py-2 font-semibold">Max Drawdown</td>
                <td className="px-4 py-2">{(report.baseline_metrics.max_drawdown * 100).toFixed(2)}%</td>
                <td className="px-4 py-2">{(report.variant_metrics.max_drawdown * 100).toFixed(2)}%</td>
                <td className={`px-4 py-2 font-semibold ${report.deltas.max_drawdown_delta <= 0 ? "text-green-600" : "text-red-600"}`}>
                  {report.deltas.max_drawdown_delta >= 0 ? "+" : ""}
                  {(report.deltas.max_drawdown_delta * 100).toFixed(2)}%
                </td>
              </tr>
              <tr className="border-b border-gray-200 dark:border-gray-700">
                <td className="px-4 py-2 font-semibold">Total Return</td>
                <td className="px-4 py-2">{(report.baseline_metrics.total_return * 100).toFixed(2)}%</td>
                <td className="px-4 py-2">{(report.variant_metrics.total_return * 100).toFixed(2)}%</td>
                <td className={`px-4 py-2 font-semibold ${report.deltas.total_return_delta >= 0 ? "text-green-600" : "text-red-600"}`}>
                  {report.deltas.total_return_delta >= 0 ? "+" : ""}
                  {(report.deltas.total_return_delta * 100).toFixed(2)}%
                </td>
              </tr>
              <tr className="border-b border-gray-200 dark:border-gray-700">
                <td className="px-4 py-2 font-semibold">Win Rate</td>
                <td className="px-4 py-2">{(report.baseline_metrics.win_rate * 100).toFixed(2)}%</td>
                <td className="px-4 py-2">{(report.variant_metrics.win_rate * 100).toFixed(2)}%</td>
                <td className={`px-4 py-2 font-semibold ${report.deltas.win_rate_delta >= 0 ? "text-green-600" : "text-red-600"}`}>
                  {report.deltas.win_rate_delta >= 0 ? "+" : ""}
                  {(report.deltas.win_rate_delta * 100).toFixed(2)}%
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      
      {/* Key Findings */}
      <div className="mb-6">
        <h2 className="text-lg font-semibold mb-2">關鍵發現</h2>
        <ul className="list-disc list-inside space-y-1">
          {report.key_findings.map((finding, idx) => (
            <li key={idx} className="text-sm">{finding}</li>
          ))}
        </ul>
      </div>
      
      {/* Status Info */}
      {report.status.started_at && (
        <div className="text-sm text-gray-600 dark:text-gray-400">
          <div>開始時間: {new Date(report.status.started_at).toLocaleString("zh-TW")}</div>
          {report.status.finished_at && (
            <div>完成時間: {new Date(report.status.finished_at).toLocaleString("zh-TW")}</div>
          )}
          {report.status.error_message && (
            <div className="text-red-500 mt-2">錯誤: {report.status.error_message}</div>
          )}
        </div>
      )}
    </div>
  );
}

