/**
 * SignalConflictMap Component
 * 
 * Micro Layer - Signal Conflict Map
 * 
 * 顯示多策略衝突偵測
 */

import { useWarRoomStore } from '../../../store/warRoomStore';

export function SignalConflictMap() {
  const { selectedSymbol } = useWarRoomStore();

  // Placeholder data structure
  // In future, this should come from SignalConflict API
  const conflicts = selectedSymbol
    ? [
        { symbol: selectedSymbol, strategy: 'Strategy A', signal: 'BUY', score: 0.8 },
        { symbol: selectedSymbol, strategy: 'Strategy B', signal: 'SELL', score: 0.6 },
        { symbol: selectedSymbol, strategy: 'Strategy C', signal: 'BUY', score: 0.7 },
      ]
    : [];

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        策略衝突偵測
        {selectedSymbol && (
          <span className="ml-2 text-sm text-gray-500 dark:text-gray-400">
            ({selectedSymbol})
          </span>
        )}
      </h3>
      {!selectedSymbol ? (
        <div className="text-gray-500 dark:text-gray-400 text-center py-8">
          請先選擇一檔股票
        </div>
      ) : conflicts.length === 0 ? (
        <div className="text-gray-500 dark:text-gray-400 text-center py-8">
          無策略衝突
        </div>
      ) : (
        <div className="space-y-3">
          {conflicts.map((conflict, idx) => (
            <div
              key={idx}
              className="p-3 rounded-lg border border-yellow-500 bg-yellow-50 dark:bg-yellow-900/20"
            >
              <div className="flex justify-between items-center">
                <div>
                  <div className="font-semibold text-gray-900 dark:text-white">
                    {conflict.strategy}
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    {conflict.symbol}
                  </div>
                </div>
                <div className="text-right">
                  <div
                    className={`font-bold ${
                      conflict.signal === 'BUY'
                        ? 'text-green-600 dark:text-green-400'
                        : 'text-red-600 dark:text-red-400'
                    }`}
                  >
                    {conflict.signal}
                  </div>
                  <div className="text-sm text-gray-500 dark:text-gray-500">
                    Score: {conflict.score.toFixed(2)}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

