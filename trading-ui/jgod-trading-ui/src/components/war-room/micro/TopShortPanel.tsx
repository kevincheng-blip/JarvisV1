/**
 * TopShortPanel Component
 * 
 * Micro Layer - Top N Short Predictions
 * 
 * 顯示 Final Score 空頭排行榜
 * 點擊股票可選擇 selectedSymbol
 */

import { useTopShortPredictions } from '../../../hooks/war-room/usePredictions';
import { useWarRoomStore } from '../../../store/warRoomStore';

export function TopShortPanel() {
  const { data: predictions, isLoading, isError, error } = useTopShortPredictions(30);
  const { selectedSymbol, setSelectedSymbol } = useWarRoomStore();

  if (isLoading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Top 30 空頭排行榜
        </h3>
        <div className="space-y-2">
          {Array.from({ length: 10 }).map((_, i) => (
            <div key={i} className="h-12 bg-gray-200 dark:bg-gray-700 animate-pulse rounded" />
          ))}
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Top 30 空頭排行榜
        </h3>
        <div className="text-red-500">
          錯誤: {error instanceof Error ? error.message : '未知錯誤'}
        </div>
      </div>
    );
  }

  if (!predictions || predictions.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Top 30 空頭排行榜
        </h3>
        <div className="text-gray-500 dark:text-gray-400 text-center py-8">
          目前沒有空頭預測資料
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        Top 30 空頭排行榜
      </h3>
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {predictions.map((pred, idx) => (
          <div
            key={pred.symbol}
            onClick={() => setSelectedSymbol(pred.symbol)}
            className={`p-3 rounded-lg border cursor-pointer transition-colors ${
              selectedSymbol === pred.symbol
                ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                : 'border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700'
            }`}
          >
            <div className="flex justify-between items-center">
              <div className="flex items-center gap-3">
                <span className="text-sm font-semibold text-gray-500 dark:text-gray-400 w-6">
                  #{idx + 1}
                </span>
                <div>
                  <div className="font-mono font-semibold text-gray-900 dark:text-white">
                    {pred.symbol}
                  </div>
                  {pred.name_zh && (
                    <div className="text-xs text-gray-600 dark:text-gray-400">
                      {pred.name_zh}
                    </div>
                  )}
                </div>
              </div>
              <div className="text-right">
                <div className="text-lg font-bold text-red-600 dark:text-red-400">
                  {pred.final_score.toFixed(2)}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-500">
                  Raw: {pred.raw_score.toFixed(2)}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

