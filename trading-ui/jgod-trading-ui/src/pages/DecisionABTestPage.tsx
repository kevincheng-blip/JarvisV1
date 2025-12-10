/**
 * Decision AB Test Dashboard Page
 * 
 * Complete dashboard for Decision Layer V1 vs V2 AB testing
 */

import { useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import {
  useRunDecisionAbTest,
  useRecentDecisionAbReports,
  useDecisionAbReport,
} from "../hooks/useDecisionAbTest";
import type { DecisionRecommendation } from "../types/decisionAb";

export function DecisionABTestPage() {
  const [selectedExperimentId, setSelectedExperimentId] = useState<string | null>(null);
  const [startDate, setStartDate] = useState<string>("");
  const [endDate, setEndDate] = useState<string>("");
  const [capital, setCapital] = useState<number>(1_000_000);
  const [pathAConfig, setPathAConfig] = useState<string>("path_a_tw_basic_v1");
  const [note, setNote] = useState<string>("");
  
  const runAbTestMutation = useRunDecisionAbTest();
  const { data: recentReports } = useRecentDecisionAbReports(20);
  const { data: selectedReport, isLoading: reportLoading } = useDecisionAbReport(
    selectedExperimentId,
    !!selectedExperimentId
  );
  
  const handleRunExperiment = () => {
    if (!startDate || !endDate) {
      alert("請選擇開始和結束日期");
      return;
    }
    
    runAbTestMutation.mutate(
      {
        start_date: startDate,
        end_date: endDate,
        capital,
        path_a_config_name: pathAConfig,
        note: note || undefined,
      },
      {
        onSuccess: (report) => {
          setSelectedExperimentId(report.experiment_id);
          alert(`實驗已建立: ${report.experiment_id}`);
        },
        onError: (error) => {
          alert(`實驗建立失敗: ${error instanceof Error ? error.message : "未知錯誤"}`);
        },
      }
    );
  };
  
  const getRecommendationBadge = (recommendation: DecisionRecommendation) => {
    switch (recommendation) {
      case "V2_PREFERRED":
        return (
          <span className="px-3 py-1 bg-green-500 text-white rounded font-semibold text-sm">
            ✓ V2 推薦：顯著優勢
          </span>
        );
      case "V1_PREFERRED":
      case "V2_NOT_RECOMMENDED":
        return (
          <span className="px-3 py-1 bg-red-500 text-white rounded font-semibold text-sm">
            ✗ V2 不推薦：績效惡化
          </span>
        );
      case "NO_SIGNIFICANT_CHANGE":
        return (
          <span className="px-3 py-1 bg-yellow-500 text-white rounded font-semibold text-sm">
            ○ 無顯著差異
          </span>
        );
      default:
        return null;
    }
  };
  
  const formatDelta = (value: number, isPercentage: boolean = false) => {
    const sign = value > 0 ? "+" : "";
    if (isPercentage) {
      return `${sign}${(value * 100).toFixed(2)}%`;
    }
    return `${sign}${value.toFixed(4)}`;
  };
  
  const getDeltaColor = (value: number, isRiskMetric: boolean = false) => {
    if (isRiskMetric) {
      // For risk metrics (MaxDD, Volatility, Turnover), lower is better
      return value < 0 ? "text-green-600" : value > 0 ? "text-red-600" : "text-gray-600";
    } else {
      // For performance metrics (Sharpe, Return, Win Rate), higher is better
      return value > 0 ? "text-green-600" : value < 0 ? "text-red-600" : "text-gray-600";
    }
  };
  
  const getDeltaArrow = (value: number, isRiskMetric: boolean = false) => {
    if (isRiskMetric) {
      return value < 0 ? "↓" : value > 0 ? "↑" : "→";
    } else {
      return value > 0 ? "↑" : value < 0 ? "↓" : "→";
    }
  };
  
  // Prepare equity curve chart data
  const equityChartData = selectedReport
    ? selectedReport.baseline.equity_curve.map((point, idx) => {
        const variantPoint = selectedReport.variant.equity_curve[idx];
        return {
          date: point.date,
          "V1 (Baseline)": point.equity,
          "V2 (Variant)": variantPoint?.equity || point.equity,
        };
      })
    : [];
  
  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
        Decision AB Test Dashboard
      </h1>
      
      {/* (A) 啟動實驗區 */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h2 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
          啟動 V1 vs V2 AB Test
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              開始日期
            </label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              結束日期
            </label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              初始資金
            </label>
            <input
              type="number"
              value={capital}
              onChange={(e) => setCapital(Number(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Path A 配置名稱
            </label>
            <select
              value={pathAConfig}
              onChange={(e) => setPathAConfig(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
            >
              <option value="path_a_tw_basic_v1">path_a_tw_basic_v1</option>
              <option value="path_a_tw_conservative_v1">path_a_tw_conservative_v1</option>
              <option value="path_a_tw_aggressive_v1">path_a_tw_aggressive_v1</option>
            </select>
          </div>
          
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              備註（可選）
            </label>
            <input
              type="text"
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="實驗說明..."
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
            />
          </div>
        </div>
        
        <button
          onClick={handleRunExperiment}
          disabled={runAbTestMutation.isPending}
          className="mt-4 px-6 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          {runAbTestMutation.isPending ? "執行中..." : "啟動 V1 vs V2 AB Test"}
        </button>
      </div>
      
      {/* (B) 淨值曲線比較 */}
      {selectedReport && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              淨值曲線比較
            </h2>
            {getRecommendationBadge(selectedReport.recommendation)}
          </div>
          
          {equityChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={equityChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 12 }}
                  angle={-45}
                  textAnchor="end"
                  height={80}
                />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="V1 (Baseline)"
                  stroke="#8884d8"
                  strokeWidth={2}
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="V2 (Variant)"
                  stroke="#82ca9d"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              無淨值曲線資料
            </div>
          )}
        </div>
      )}
      
      {/* (C) KPI 對比表 & Recommendation */}
      {selectedReport && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <h2 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
            核心績效指標比較
          </h2>
          
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-700">
                  <th className="px-4 py-2 text-left">指標</th>
                  <th className="px-4 py-2 text-right">V1 (Baseline)</th>
                  <th className="px-4 py-2 text-right">V2 (Variant)</th>
                  <th className="px-4 py-2 text-right">Δ (Delta)</th>
                </tr>
              </thead>
              <tbody>
                {/* Sharpe Ratio */}
                <tr className="border-b border-gray-200 dark:border-gray-700">
                  <td className="px-4 py-2 font-medium">Sharpe Ratio</td>
                  <td className="px-4 py-2 text-right">{selectedReport.baseline.sharpe_ratio.toFixed(4)}</td>
                  <td className="px-4 py-2 text-right">{selectedReport.variant.sharpe_ratio.toFixed(4)}</td>
                  <td className={`px-4 py-2 text-right font-semibold ${getDeltaColor(selectedReport.sharpe_delta)}`}>
                    {getDeltaArrow(selectedReport.sharpe_delta)} {formatDelta(selectedReport.sharpe_delta)}
                  </td>
                </tr>
                
                {/* Total Return */}
                <tr className="border-b border-gray-200 dark:border-gray-700">
                  <td className="px-4 py-2 font-medium">Total Return (%)</td>
                  <td className="px-4 py-2 text-right">{(selectedReport.baseline.total_return * 100).toFixed(2)}%</td>
                  <td className="px-4 py-2 text-right">{(selectedReport.variant.total_return * 100).toFixed(2)}%</td>
                  <td className={`px-4 py-2 text-right font-semibold ${getDeltaColor(selectedReport.return_delta)}`}>
                    {getDeltaArrow(selectedReport.return_delta)} {formatDelta(selectedReport.return_delta, true)}
                  </td>
                </tr>
                
                {/* Max Drawdown */}
                <tr className="border-b border-gray-200 dark:border-gray-700">
                  <td className="px-4 py-2 font-medium">Max Drawdown (%)</td>
                  <td className="px-4 py-2 text-right">{(selectedReport.baseline.max_drawdown * 100).toFixed(2)}%</td>
                  <td className="px-4 py-2 text-right">{(selectedReport.variant.max_drawdown * 100).toFixed(2)}%</td>
                  <td className={`px-4 py-2 text-right font-semibold ${getDeltaColor(selectedReport.max_drawdown_delta, true)}`}>
                    {getDeltaArrow(selectedReport.max_drawdown_delta, true)} {formatDelta(selectedReport.max_drawdown_delta, true)}
                  </td>
                </tr>
                
                {/* Volatility */}
                <tr className="border-b border-gray-200 dark:border-gray-700">
                  <td className="px-4 py-2 font-medium">Volatility (%)</td>
                  <td className="px-4 py-2 text-right">{(selectedReport.baseline.volatility * 100).toFixed(2)}%</td>
                  <td className="px-4 py-2 text-right">{(selectedReport.variant.volatility * 100).toFixed(2)}%</td>
                  <td className={`px-4 py-2 text-right font-semibold ${getDeltaColor(selectedReport.volatility_delta, true)}`}>
                    {getDeltaArrow(selectedReport.volatility_delta, true)} {formatDelta(selectedReport.volatility_delta, true)}
                  </td>
                </tr>
                
                {/* Win Rate */}
                <tr className="border-b border-gray-200 dark:border-gray-700">
                  <td className="px-4 py-2 font-medium">Win Rate (%)</td>
                  <td className="px-4 py-2 text-right">{(selectedReport.baseline.win_rate * 100).toFixed(2)}%</td>
                  <td className="px-4 py-2 text-right">{(selectedReport.variant.win_rate * 100).toFixed(2)}%</td>
                  <td className={`px-4 py-2 text-right font-semibold ${getDeltaColor(selectedReport.win_rate_delta)}`}>
                    {getDeltaArrow(selectedReport.win_rate_delta)} {formatDelta(selectedReport.win_rate_delta, true)}
                  </td>
                </tr>
                
                {/* Turnover */}
                <tr>
                  <td className="px-4 py-2 font-medium">Turnover</td>
                  <td className="px-4 py-2 text-right">{selectedReport.baseline.turnover.toFixed(4)}</td>
                  <td className="px-4 py-2 text-right">{selectedReport.variant.turnover.toFixed(4)}</td>
                  <td className={`px-4 py-2 text-right font-semibold ${getDeltaColor(selectedReport.turnover_delta, true)}`}>
                    {getDeltaArrow(selectedReport.turnover_delta, true)} {formatDelta(selectedReport.turnover_delta)}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}
      
      {/* 實驗列表 */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h2 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
          最近執行的實驗
        </h2>
        
        {recentReports && recentReports.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-700">
                  <th className="px-3 py-2 text-left">建立時間</th>
                  <th className="px-3 py-2 text-left">Path A 配置</th>
                  <th className="px-3 py-2 text-right">Sharpe Δ</th>
                  <th className="px-3 py-2 text-right">Return Δ</th>
                  <th className="px-3 py-2 text-right">MaxDD Δ</th>
                  <th className="px-3 py-2 text-center">推薦</th>
                </tr>
              </thead>
              <tbody>
                {recentReports.map((report) => (
                  <tr
                    key={report.experiment_id}
                    onClick={() => setSelectedExperimentId(report.experiment_id)}
                    className={`border-b border-gray-200 dark:border-gray-700 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50 ${
                      selectedExperimentId === report.experiment_id
                        ? "bg-blue-50 dark:bg-blue-900/20"
                        : ""
                    }`}
                  >
                    <td className="px-3 py-2">
                      {new Date(report.created_at).toLocaleString("zh-TW")}
                    </td>
                    <td className="px-3 py-2 font-mono text-xs">{report.path_a_config_name}</td>
                    <td className={`px-3 py-2 text-right ${getDeltaColor(report.sharpe_delta)}`}>
                      {formatDelta(report.sharpe_delta)}
                    </td>
                    <td className={`px-3 py-2 text-right ${getDeltaColor(report.return_delta)}`}>
                      {formatDelta(report.return_delta, true)}
                    </td>
                    <td className={`px-3 py-2 text-right ${getDeltaColor(report.max_drawdown_delta, true)}`}>
                      {formatDelta(report.max_drawdown_delta, true)}
                    </td>
                    <td className="px-3 py-2 text-center">
                      {getRecommendationBadge(report.recommendation)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400 text-sm">
            尚無實驗記錄
          </div>
        )}
      </div>
    </div>
  );
}

