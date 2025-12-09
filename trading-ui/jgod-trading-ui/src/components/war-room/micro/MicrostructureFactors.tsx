/**
 * MicrostructureFactors Component
 * 
 * Micro Layer - Microstructure Factors
 * 
 * 顯示微觀結構因子
 */

import { useWarRoomStore } from '../../../store/warRoomStore';

export function MicrostructureFactors() {
  const { selectedSymbol } = useWarRoomStore();

  // Placeholder data structure
  // In future, this should come from MicrostructureFactors API
  const factors = selectedSymbol
    ? [
        { name: 'Order Flow', value: 0.65, trend: 'up' },
        { name: 'Bid-Ask Spread', value: 0.02, trend: 'down' },
        { name: 'Volume Profile', value: 0.78, trend: 'up' },
        { name: 'Tick Direction', value: 0.55, trend: 'neutral' },
      ]
    : [];

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        微觀結構因子
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
      ) : factors.length === 0 ? (
        <div className="text-gray-500 dark:text-gray-400 text-center py-8">
          目前沒有微觀結構因子資料
        </div>
      ) : (
        <div className="space-y-4">
          {factors.map((factor, idx) => (
            <div key={idx}>
              <div className="flex justify-between mb-1">
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  {factor.name}
                </span>
                <span className="text-sm font-semibold text-gray-900 dark:text-white">
                  {factor.value.toFixed(2)}
                  {factor.trend === 'up' && ' ↗️'}
                  {factor.trend === 'down' && ' ↘️'}
                  {factor.trend === 'neutral' && ' →'}
                </span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${
                    factor.trend === 'up'
                      ? 'bg-green-500'
                      : factor.trend === 'down'
                      ? 'bg-red-500'
                      : 'bg-gray-500'
                  }`}
                  style={{ width: `${factor.value * 100}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

