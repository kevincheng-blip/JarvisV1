/**
 * PositionHealthPanel Component
 * 
 * Anomaly Layer - Position Health Panel
 * 
 * 顯示部位健康度
 */

import { usePositionHealth } from '../../../hooks/war-room/usePositionHealth';

export function PositionHealthPanel() {
  const { data: health, isLoading, isError, error } = usePositionHealth();

  const getRiskColor = (risk: number) => {
    if (risk <= 0.3) return 'text-green-600 dark:text-green-400';
    if (risk <= 0.6) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-red-600 dark:text-red-400';
  };

  if (isLoading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          部位健康度
        </h3>
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="h-20 bg-gray-200 dark:bg-gray-700 animate-pulse rounded" />
          ))}
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          部位健康度
        </h3>
        <div className="text-red-500 dark:text-red-400 text-sm">
          錯誤: {error instanceof Error ? error.message : '未知錯誤'}
        </div>
      </div>
    );
  }

  if (!health) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          部位健康度
        </h3>
        <div className="text-gray-500 dark:text-gray-400 text-center py-8 text-sm">
          目前沒有持倉
        </div>
      </div>
    );
  }

  const riskItems = [
    { name: '集中度風險', value: health.concentration_risk },
    { name: '流動性風險', value: health.liquidity_risk },
    { name: '槓桿風險', value: health.leverage_risk },
  ];

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        部位健康度
      </h3>
      <div className="space-y-4">
        {riskItems.map((item, idx) => (
          <div key={idx}>
            <div className="flex justify-between mb-1">
              <span className="text-sm text-gray-600 dark:text-gray-400">
                {item.name}
              </span>
              <span className={`text-sm font-semibold ${getRiskColor(item.value)}`}>
                {(item.value * 100).toFixed(0)}%
              </span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div
                className={`h-2 rounded-full ${
                  item.value <= 0.3
                    ? 'bg-green-500'
                    : item.value <= 0.6
                    ? 'bg-yellow-500'
                    : 'bg-red-500'
                }`}
                style={{ width: `${item.value * 100}%` }}
              />
            </div>
          </div>
        ))}
      </div>
      {health.comments && health.comments.length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          <div className="text-sm font-semibold text-gray-900 dark:text-white mb-2">
            提示:
          </div>
          <ul className="list-disc list-inside text-sm text-gray-600 dark:text-gray-400 space-y-1">
            {health.comments.map((comment, idx) => (
              <li key={idx}>{comment}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

