/**
 * FinalOrders Component
 * 
 * Macro Layer - Final Orders
 * 
 * 顯示今日最終指令清單
 */

import { useFinalOrders } from '../../../hooks/war-room/useOrders';
import { useWarRoomStore } from '../../../store/warRoomStore';

export function FinalOrders() {
  const { selectedRunId } = useWarRoomStore();
  const { data: orders, isLoading, isError, error } = useFinalOrders();

  if (isLoading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          今日最終指令
        </h3>
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
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
          今日最終指令
        </h3>
        <div className="text-red-500 dark:text-red-400">
          錯誤: {error instanceof Error ? error.message : '未知錯誤'}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        今日最終指令
        {selectedRunId && (
          <span className="ml-2 text-sm text-gray-500 dark:text-gray-400">
            ({selectedRunId.substring(0, 8)}...)
          </span>
        )}
      </h3>
      {!orders || orders.length === 0 ? (
        <div className="text-gray-500 dark:text-gray-400 text-center py-8">
          目前沒有待執行指令
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 dark:border-gray-700">
                <th className="text-left py-2 text-gray-600 dark:text-gray-400">股票</th>
                <th className="text-left py-2 text-gray-600 dark:text-gray-400">方向</th>
                <th className="text-right py-2 text-gray-600 dark:text-gray-400">數量</th>
                <th className="text-right py-2 text-gray-600 dark:text-gray-400">信心度</th>
                <th className="text-right py-2 text-gray-600 dark:text-gray-400">Final Score</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((order, idx) => (
                <tr key={idx} className="border-b border-gray-200 dark:border-gray-700">
                  <td className="py-2">
                    <div className="font-mono text-gray-900 dark:text-white">{order.symbol}</div>
                    <div className="text-xs text-gray-500 dark:text-gray-500">{order.name}</div>
                  </td>
                  <td className={`py-2 font-semibold ${
                    order.side === 'buy'
                      ? 'text-green-600 dark:text-green-400'
                      : order.side === 'sell'
                      ? 'text-red-600 dark:text-red-400'
                      : 'text-gray-600 dark:text-gray-400'
                  }`}>
                    {order.side.toUpperCase()}
                  </td>
                  <td className="py-2 text-right text-gray-900 dark:text-white">{order.size}</td>
                  <td className="py-2 text-right">
                    <span className={`font-semibold ${
                      order.confidence >= 0.7
                        ? 'text-green-600 dark:text-green-400'
                        : order.confidence >= 0.5
                        ? 'text-yellow-600 dark:text-yellow-400'
                        : 'text-red-600 dark:text-red-400'
                    }`}>
                      {(order.confidence * 100).toFixed(0)}%
                    </span>
                  </td>
                  <td className="py-2 text-right text-gray-900 dark:text-white">
                    {order.final_score.toFixed(2)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

