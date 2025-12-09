/**
 * FinalOrders Component
 * 
 * Macro Layer - Final Orders
 * 
 * 顯示今日最終指令清單
 */

import { useWarRoomStore } from '../../../store/warRoomStore';

export function FinalOrders() {
  const { selectedRunId } = useWarRoomStore();

  // Placeholder data structure
  // In future, this should come from FinalOrders API
  const orders = [
    { symbol: '2330', side: 'BUY', quantity: 100, price: 580.0, status: 'PENDING' },
    { symbol: '2317', side: 'SELL', quantity: 50, price: 105.0, status: 'FILLED' },
  ];

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
      {orders.length === 0 ? (
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
                <th className="text-right py-2 text-gray-600 dark:text-gray-400">價格</th>
                <th className="text-left py-2 text-gray-600 dark:text-gray-400">狀態</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((order, idx) => (
                <tr key={idx} className="border-b border-gray-200 dark:border-gray-700">
                  <td className="py-2 font-mono text-gray-900 dark:text-white">{order.symbol}</td>
                  <td className={`py-2 font-semibold ${
                    order.side === 'BUY'
                      ? 'text-green-600 dark:text-green-400'
                      : 'text-red-600 dark:text-red-400'
                  }`}>
                    {order.side}
                  </td>
                  <td className="py-2 text-right text-gray-900 dark:text-white">{order.quantity}</td>
                  <td className="py-2 text-right text-gray-900 dark:text-white">${order.price.toFixed(2)}</td>
                  <td className={`py-2 ${
                    order.status === 'FILLED'
                      ? 'text-green-600 dark:text-green-400'
                      : 'text-yellow-600 dark:text-yellow-400'
                  }`}>
                    {order.status}
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

