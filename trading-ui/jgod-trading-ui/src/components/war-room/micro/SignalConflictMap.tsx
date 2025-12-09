/**
 * SignalConflictMap Component
 * 
 * Micro Layer - Signal Conflict Map
 * 
 * 顯示多策略衝突偵測
 */

import { useSignalConflicts } from '../../../hooks/war-room/useConflicts';
import { useWarRoomStore } from '../../../store/warRoomStore';

export function SignalConflictMap() {
  const { selectedSymbol } = useWarRoomStore();
  const { data: conflictItem, isLoading, isError, error } = useSignalConflicts();

  if (!selectedSymbol) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          策略衝突偵測
        </h3>
        <div className="text-gray-500 dark:text-gray-400 text-center py-8 text-sm">
          請先選擇一檔股票
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          策略衝突偵測
          <span className="ml-2 text-sm text-gray-500 dark:text-gray-400">
            ({selectedSymbol})
          </span>
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
          策略衝突偵測
          <span className="ml-2 text-sm text-gray-500 dark:text-gray-400">
            ({selectedSymbol})
          </span>
        </h3>
        <div className="text-red-500 dark:text-red-400 text-sm">
          錯誤: {error instanceof Error ? error.message : '未知錯誤'}
        </div>
      </div>
    );
  }

  if (!conflictItem || conflictItem.conflict_level === 'none' || conflictItem.signals.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          策略衝突偵測
          <span className="ml-2 text-sm text-gray-500 dark:text-gray-400">
            ({selectedSymbol})
          </span>
        </h3>
        <div className="text-gray-500 dark:text-gray-400 text-center py-8 text-sm">
          目前策略看法一致，未發現顯著衝突。
        </div>
      </div>
    );
  }

  const getConflictColor = (level: string) => {
    switch (level) {
      case 'severe':
        return 'border-red-500 bg-red-50 dark:bg-red-900/20';
      case 'mild':
        return 'border-yellow-500 bg-yellow-50 dark:bg-yellow-900/20';
      default:
        return 'border-gray-500 bg-gray-50 dark:bg-gray-900/20';
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        策略衝突偵測
        <span className="ml-2 text-sm text-gray-500 dark:text-gray-400">
          ({selectedSymbol})
        </span>
      </h3>
      <div className="mb-3">
        <div className="text-sm text-gray-600 dark:text-gray-400">
          共識分數: <span className="font-semibold">{conflictItem.consensus_score.toFixed(2)}</span>
        </div>
        <div className="text-sm text-gray-600 dark:text-gray-400">
          衝突等級: <span className="font-semibold">{conflictItem.conflict_level}</span>
        </div>
      </div>
      <div className="space-y-3">
        {conflictItem.signals.map((signal, idx) => (
          <div
            key={idx}
            className={`p-3 rounded-lg border ${getConflictColor(conflictItem.conflict_level)}`}
          >
            <div className="flex justify-between items-center">
              <div>
                <div className="font-semibold text-gray-900 dark:text-white">
                  {signal.strategy_id}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  {conflictItem.symbol} - {conflictItem.name}
                </div>
              </div>
              <div className="text-right">
                <div
                  className={`font-bold ${
                    signal.signal === 'long'
                      ? 'text-green-600 dark:text-green-400'
                      : signal.signal === 'short'
                      ? 'text-red-600 dark:text-red-400'
                      : 'text-gray-600 dark:text-gray-400'
                  }`}
                >
                  {signal.signal.toUpperCase()}
                </div>
                <div className="text-sm text-gray-500 dark:text-gray-500">
                  Score: {signal.score.toFixed(2)}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

