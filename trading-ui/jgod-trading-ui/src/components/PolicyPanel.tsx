/**
 * PolicyPanel Component
 * 
 * 顯示 AI Policy Service 建議的最佳實驗和風險配置
 */

import { useState, useEffect } from 'react';

interface PolicySuggestion {
  run_id: string;
  created_at: string;
  source_log_path: string;
  start_date: string;
  end_date: string;
  score: number;
  sharpe_ratio: number;
  max_drawdown: number;
  total_return: number;
  win_rate: number;
  num_days: number;
  num_trades: number;
  long_budget: number;
  short_budget: number;
  max_weight_per_symbol: number;
  min_score: number;
  allow_short: boolean;
}

interface RiskConfig {
  long_budget: number;
  short_budget: number;
  max_weight_per_symbol: number;
  min_score: number;
  allow_short: boolean;
}

interface PolicyResponse {
  suggestion: PolicySuggestion;
  config: RiskConfig;
}

export function PolicyPanel() {
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<PolicyResponse | null>(null);
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');

  const fetchPolicySuggestion = async () => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);

      const url = `http://localhost:8000/api/v1/policy/risk-config/suggest?${params.toString()}`;
      const response = await fetch(url);

      if (response.status === 404) {
        setError('目前沒有有效的回測實驗結果，請先執行 Path A v1 或放寬篩選條件。');
        setData(null);
        return;
      }

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const result: PolicyResponse = await response.json();
      setData(result);
    } catch (err) {
      console.error('Failed to fetch policy suggestion:', err);
      setError('無法載入 Policy 建議，請稍後重試。');
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // 載入時自動取得建議
    fetchPolicySuggestion();
  }, []);

  const handleReload = () => {
    fetchPolicySuggestion();
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
          AI Policy 建議
        </h2>
        <button
          onClick={handleReload}
          disabled={loading}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? '載入中...' : '重新載入'}
        </button>
      </div>

      {/* Date Filters */}
      <div className="mb-4 grid grid-cols-2 gap-4">
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
      </div>

      {/* Loading State */}
      {loading && (
        <div className="text-center py-8 text-gray-500 dark:text-gray-400">
          載入中...
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md p-4 text-red-700 dark:text-red-400">
          {error}
        </div>
      )}

      {/* Data Display */}
      {!loading && !error && data && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Section A: Best Experiment */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
              最佳實驗
            </h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Run ID:</span>
                <span className="font-mono text-gray-900 dark:text-white text-xs">
                  {data.suggestion.run_id.substring(0, 8)}...
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Sharpe Ratio:</span>
                <span className="font-semibold text-gray-900 dark:text-white">
                  {data.suggestion.sharpe_ratio.toFixed(4)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Max Drawdown:</span>
                <span className="font-semibold text-gray-900 dark:text-white">
                  {(data.suggestion.max_drawdown * 100).toFixed(2)}%
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Total Return:</span>
                <span className="font-semibold text-gray-900 dark:text-white">
                  {(data.suggestion.total_return * 100).toFixed(2)}%
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Win Rate:</span>
                <span className="font-semibold text-gray-900 dark:text-white">
                  {(data.suggestion.win_rate * 100).toFixed(2)}%
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Days:</span>
                <span className="font-semibold text-gray-900 dark:text-white">
                  {data.suggestion.num_days}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Trades:</span>
                <span className="font-semibold text-gray-900 dark:text-white">
                  {data.suggestion.num_trades}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Score:</span>
                <span className="font-semibold text-green-600 dark:text-green-400">
                  {data.suggestion.score.toFixed(4)}
                </span>
              </div>
            </div>
          </div>

          {/* Section B: Suggested RiskConfig */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
              建議風險配置
            </h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Long Budget:</span>
                <span className="font-semibold text-gray-900 dark:text-white">
                  {(data.config.long_budget * 100).toFixed(1)}%
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Short Budget:</span>
                <span className="font-semibold text-gray-900 dark:text-white">
                  {(data.config.short_budget * 100).toFixed(1)}%
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Max Weight/Symbol:</span>
                <span className="font-semibold text-gray-900 dark:text-white">
                  {(data.config.max_weight_per_symbol * 100).toFixed(1)}%
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Min Score:</span>
                <span className="font-semibold text-gray-900 dark:text-white">
                  {data.config.min_score.toFixed(2)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Allow Short:</span>
                <span className={`font-semibold ${data.config.allow_short ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                  {data.config.allow_short ? '是' : '否'}
                </span>
              </div>
              <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  <div>日期區間: {data.suggestion.start_date} ~ {data.suggestion.end_date}</div>
                  <div className="mt-1">Created: {new Date(data.suggestion.created_at).toLocaleString('zh-TW')}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

