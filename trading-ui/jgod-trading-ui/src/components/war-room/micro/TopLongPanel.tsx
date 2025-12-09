/**
 * TopLongPanel Component
 * 
 * Micro Layer - Top N Long Predictions
 * 
 * 顯示 Final Score 多頭排行榜
 * 點擊股票可選擇 selectedSymbol
 */

import { useTopLongPredictions } from '../../../hooks/war-room/usePredictions';
import { useWarRoomStore } from '../../../store/warRoomStore';

export function TopLongPanel() {
  const { data: predictions, isLoading, isError, error } = useTopLongPredictions(30);
  const { selectedSymbol, setSelectedSymbol } = useWarRoomStore();
  const { selectedSymbol, setSelectedSymbol } = useWarRoomStore();

  if (isLoading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Top 30 多頭排行榜
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
          Top 30 多頭排行榜
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
          Top 30 多頭排行榜
        </h3>
        <div className="text-gray-500 dark:text-gray-400 text-center py-8 text-sm">
          目前尚無 Final Score 排名，可能尚未完成 Decision Layer 計算。
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        Top 30 多頭排行榜
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
                  {pred.name && (
                    <div className="text-xs text-gray-600 dark:text-gray-400">
                      {pred.name}
                    </div>
                  )}
                </div>
              </div>
              <div className="text-right">
                <div className="flex items-center gap-2">
                  <div className="text-lg font-bold text-green-600 dark:text-green-400">
                    {pred.final_score.toFixed(2)}
                  </div>
                  {/* Doctrine Flags Icon */}
                  {pred.doctrine_flags && pred.doctrine_flags.length > 0 && (
                    <div className="relative group">
                      <div className={`w-4 h-4 rounded-full ${
                        pred.doctrine_flags.some(f => f.severity === 'critical')
                          ? 'bg-red-500'
                          : pred.doctrine_flags.some(f => f.severity === 'warning')
                          ? 'bg-yellow-500'
                          : 'bg-blue-500'
                      }`} />
                      {/* Tooltip */}
                      <div className="absolute right-0 top-full mt-2 w-64 p-2 bg-gray-900 text-white text-xs rounded-lg shadow-lg opacity-0 group-hover:opacity-100 transition-opacity z-10">
                        <div className="font-semibold mb-1">Doctrine 警示:</div>
                        {pred.doctrine_flags.slice(0, 3).map((flag, idx) => (
                          <div key={idx} className="mb-1">
                            <div className="font-medium">{flag.message}</div>
                            {flag.doctrine_refs && flag.doctrine_refs.length > 0 && (
                              <div className="text-gray-400 text-xs">
                                {flag.doctrine_refs.slice(0, 2).join(', ')}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-500">
                  Raw: {pred.raw_score.toFixed(2)}
                  {pred.win_prob !== undefined && ` | Win: ${(pred.win_prob * 100).toFixed(0)}%`}
                </div>
                {pred.risk_level && (
                  <div className={`text-xs mt-1 ${
                    pred.risk_level === 'low'
                      ? 'text-green-600 dark:text-green-400'
                      : pred.risk_level === 'mid'
                      ? 'text-yellow-600 dark:text-yellow-400'
                      : 'text-red-600 dark:text-red-400'
                  }`}>
                    Risk: {pred.risk_level.toUpperCase()}
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

