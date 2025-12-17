// @ts-nocheck
/**
 * FinalOrders Component
 * 
 * Macro Layer - Final Orders
 * 
 * 顯示今日最終指令清單
 */

import { useFinalOrders } from '../../../hooks/war-room/useOrders';
import { useWarRoomStore } from '../../../store/warRoomStore';
import type { FinalOrder } from '../../../types/warRoom';

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
                <th className="text-left py-2 text-gray-600 dark:text-gray-400">動作</th>
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
                  <td className="py-2">
                    <div className={`font-semibold ${
                      order.action === 'BUY'
                        ? 'text-green-600 dark:text-green-400'
                        : order.action === 'SELL'
                        ? 'text-red-600 dark:text-red-400'
                        : 'text-gray-600 dark:text-gray-400'
                    }`}>
                      {order.action}
                    </div>
                    {order.status && (
                      <div className={`text-xs mt-1 px-2 py-0.5 rounded inline-block ${
                        order.status === 'EXECUTED'
                          ? 'bg-green-100 dark:bg-green-900/20 text-green-700 dark:text-green-400'
                          : order.status === 'PENDING'
                          ? 'bg-yellow-100 dark:bg-yellow-900/20 text-yellow-700 dark:text-yellow-400'
                          : 'bg-gray-100 dark:bg-gray-900/20 text-gray-700 dark:text-gray-400'
                      }`}>
                        {order.status}
                      </div>
                    )}
                  </td>
                  <td className="py-2 text-right text-gray-900 dark:text-white">{order.quantity}</td>
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
                  <td className="py-2 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <span className="text-gray-900 dark:text-white">
                        {order.final_score.toFixed(2)}
                      </span>
                      {/* Doctrine Flags Icon */}
                      {order.doctrine_flags && order.doctrine_flags.length > 0 && (
                        <div className="relative group">
                          <div className={`w-3 h-3 rounded-full ${
                            order.doctrine_flags.some(f => f.severity === 'critical')
                              ? 'bg-red-500'
                              : order.doctrine_flags.some(f => f.severity === 'warning')
                              ? 'bg-yellow-500'
                              : 'bg-blue-500'
                          }`} />
                          {/* Tooltip */}
                          <div className="absolute right-0 top-full mt-2 w-64 p-2 bg-gray-900 text-white text-xs rounded-lg shadow-lg opacity-0 group-hover:opacity-100 transition-opacity z-10">
                            <div className="font-semibold mb-1">Doctrine 警示:</div>
                            {order.doctrine_flags.slice(0, 2).map((flag, flagIdx) => (
                              <div key={flagIdx} className="mb-1">
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

