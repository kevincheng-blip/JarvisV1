/**
 * AggregateRisk Component
 * 
 * Macro Layer - Aggregate Risk Overview
 * 
 * 顯示總曝險、多空曝險、淨曝險、槓桿等風險指標
 */

import { useAggregateRisk } from '../../../hooks/war-room/useRisk';

export function AggregateRisk() {
  const { data, isLoading, isError, error } = useAggregateRisk();

  if (isLoading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          總曝險概覽
        </h3>
        <div className="space-y-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-6 bg-gray-200 dark:bg-gray-700 animate-pulse rounded" />
          ))}
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          總曝險概覽
        </h3>
        <div className="text-red-500 dark:text-red-400">
          無法載入風險資料，請稍後重試
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          總曝險概覽
        </h3>
        <div className="text-gray-500 dark:text-gray-400">
          目前沒有風險資料
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        總曝險概覽
      </h3>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <div className="text-sm text-gray-600 dark:text-gray-400">總曝險</div>
          <div className="text-2xl font-bold text-gray-900 dark:text-white">
            {(data.gross_exposure * 100).toFixed(1)}%
          </div>
        </div>
        <div>
          <div className="text-sm text-gray-600 dark:text-gray-400">淨曝險</div>
          <div className={`text-2xl font-bold ${
            data.net_exposure >= 0
              ? 'text-green-600 dark:text-green-400'
              : 'text-red-600 dark:text-red-400'
          }`}>
            {(data.net_exposure * 100).toFixed(1)}%
          </div>
        </div>
        <div>
          <div className="text-sm text-gray-600 dark:text-gray-400">多頭曝險</div>
          <div className="text-xl font-semibold text-green-600 dark:text-green-400">
            {(data.long_exposure * 100).toFixed(1)}%
          </div>
        </div>
        <div>
          <div className="text-sm text-gray-600 dark:text-gray-400">空頭曝險</div>
          <div className="text-xl font-semibold text-red-600 dark:text-red-400">
            {(data.short_exposure * 100).toFixed(1)}%
          </div>
        </div>
        {data.beta_exposure !== undefined && (
          <div>
            <div className="text-sm text-gray-600 dark:text-gray-400">Beta 曝險</div>
            <div className="text-xl font-semibold text-blue-600 dark:text-blue-400">
              {data.beta_exposure.toFixed(2)}
            </div>
          </div>
        )}
        {data.var_95 !== undefined && (
          <div>
            <div className="text-sm text-gray-600 dark:text-gray-400">VaR (95%)</div>
            <div className="text-xl font-semibold text-yellow-600 dark:text-yellow-400">
              {(data.var_95 * 100).toFixed(2)}%
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

