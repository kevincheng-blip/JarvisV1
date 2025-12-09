/**
 * MicrostructureFactors Component
 * 
 * Micro Layer - Microstructure Factors
 * 
 * 顯示微觀結構因子
 */

import { useMicrostructureFactors } from '../../../hooks/war-room/useMicrostructure';
import { useWarRoomStore } from '../../../store/warRoomStore';

export function MicrostructureFactors() {
  const { selectedSymbol } = useWarRoomStore();
  const { data: factors, isLoading, isError, error } = useMicrostructureFactors();

  if (!selectedSymbol) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          微觀結構因子
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
          微觀結構因子
          <span className="ml-2 text-sm text-gray-500 dark:text-gray-400">
            ({selectedSymbol})
          </span>
        </h3>
        <div className="space-y-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i}>
              <div className="h-4 bg-gray-200 dark:bg-gray-700 animate-pulse rounded mb-2" />
              <div className="h-2 bg-gray-200 dark:bg-gray-700 animate-pulse rounded" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (isError) {
    // Handle 404 gracefully (as per SPEC 12.2)
    if (error && typeof error === 'object' && 'response' in error && (error as any).response?.status === 404) {
      return (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            微觀結構因子
            <span className="ml-2 text-sm text-gray-500 dark:text-gray-400">
              ({selectedSymbol})
            </span>
          </h3>
          <div className="text-gray-500 dark:text-gray-400 text-center py-8 text-sm">
            目前無法取得此股票的微觀數據，可能未在當前觀察清單中。
          </div>
        </div>
      );
    }
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          微觀結構因子
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

  if (!factors) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          微觀結構因子
          <span className="ml-2 text-sm text-gray-500 dark:text-gray-400">
            ({selectedSymbol})
          </span>
        </h3>
        <div className="text-gray-500 dark:text-gray-400 text-center py-8 text-sm">
          目前沒有微觀結構因子資料
        </div>
      </div>
    );
  }

  const factorItems = [
    { name: 'Bid-Ask Spread', value: factors.spread_bps, unit: ' bps', trend: factors.spread_bps !== undefined ? (factors.spread_bps < 5 ? 'good' : 'bad') : undefined },
    { name: 'Order Imbalance', value: factors.order_imbalance, unit: '', trend: factors.order_imbalance !== undefined ? (factors.order_imbalance > 0 ? 'up' : 'down') : undefined },
    { name: 'Liquidity Score', value: factors.liquidity_score, unit: '', trend: factors.liquidity_score !== undefined ? (factors.liquidity_score > 0.7 ? 'up' : factors.liquidity_score > 0.5 ? 'neutral' : 'down') : undefined },
    { name: 'Volatility (1d)', value: factors.volatility_1d, unit: '%', trend: undefined },
    { name: 'Volatility (5d)', value: factors.volatility_5d, unit: '%', trend: undefined },
  ].filter((item) => item.value !== undefined);

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        微觀結構因子
        <span className="ml-2 text-sm text-gray-500 dark:text-gray-400">
          ({selectedSymbol})
        </span>
      </h3>
      {factorItems.length === 0 ? (
        <div className="text-gray-500 dark:text-gray-400 text-center py-8 text-sm">
          目前沒有微觀結構因子資料
        </div>
      ) : (
        <div className="space-y-4">
          {factorItems.map((item, idx) => (
            <div key={idx}>
              <div className="flex justify-between mb-1">
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  {item.name}
                </span>
                <span className="text-sm font-semibold text-gray-900 dark:text-white">
                  {typeof item.value === 'number' ? item.value.toFixed(2) : '-'}
                  {item.unit}
                  {item.trend === 'up' && ' ↗️'}
                  {item.trend === 'down' && ' ↘️'}
                  {item.trend === 'good' && ' ✓'}
                  {item.trend === 'bad' && ' ⚠️'}
                </span>
              </div>
              {item.value !== undefined && typeof item.value === 'number' && item.value >= 0 && item.value <= 1 && (
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${
                      item.trend === 'up' || item.trend === 'good'
                        ? 'bg-green-500'
                        : item.trend === 'down' || item.trend === 'bad'
                        ? 'bg-red-500'
                        : 'bg-gray-500'
                    }`}
                    style={{ width: `${item.value * 100}%` }}
                  />
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

