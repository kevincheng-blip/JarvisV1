/**
 * PositionHealthPanel Component
 * 
 * Anomaly Layer - Position Health Panel
 * 
 * 顯示部位健康度
 */

export function PositionHealthPanel() {
  // Placeholder data structure
  // In future, this should come from PositionHealth API
  const positions = [
    { symbol: '2330', side: 'LONG', health: 0.85, pnl: 5000, pnl_pct: 0.05 },
    { symbol: '2317', side: 'SHORT', health: 0.65, pnl: -2000, pnl_pct: -0.02 },
    { symbol: '2454', side: 'LONG', health: 0.45, pnl: -5000, pnl_pct: -0.08 },
  ];

  const getHealthColor = (health: number) => {
    if (health >= 0.8) return 'text-green-600 dark:text-green-400';
    if (health >= 0.6) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-red-600 dark:text-red-400';
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        部位健康度
      </h3>
      {positions.length === 0 ? (
        <div className="text-gray-500 dark:text-gray-400 text-center py-8 text-sm">
          目前沒有持倉
        </div>
      ) : (
        <div className="space-y-3">
          {positions.map((pos, idx) => (
            <div
              key={idx}
              className="p-3 rounded-lg border border-gray-200 dark:border-gray-700"
            >
              <div className="flex justify-between items-center mb-2">
                <div className="flex items-center gap-2">
                  <span className="font-mono font-semibold text-gray-900 dark:text-white">
                    {pos.symbol}
                  </span>
                  <span
                    className={`text-xs px-2 py-1 rounded ${
                      pos.side === 'LONG'
                        ? 'bg-green-100 dark:bg-green-900/20 text-green-700 dark:text-green-400'
                        : 'bg-red-100 dark:bg-red-900/20 text-red-700 dark:text-red-400'
                    }`}
                  >
                    {pos.side}
                  </span>
                </div>
                <div className={`text-sm font-semibold ${getHealthColor(pos.health)}`}>
                  {(pos.health * 100).toFixed(0)}%
                </div>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600 dark:text-gray-400">PnL:</span>
                <span
                  className={`font-semibold ${
                    pos.pnl >= 0
                      ? 'text-green-600 dark:text-green-400'
                      : 'text-red-600 dark:text-red-400'
                  }`}
                >
                  ${pos.pnl >= 0 ? '+' : ''}
                  {pos.pnl.toLocaleString()} ({pos.pnl_pct >= 0 ? '+' : ''}
                  {(pos.pnl_pct * 100).toFixed(2)}%)
                </span>
              </div>
              <div className="mt-2 w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
                <div
                  className={`h-1.5 rounded-full ${
                    pos.health >= 0.8
                      ? 'bg-green-500'
                      : pos.health >= 0.6
                      ? 'bg-yellow-500'
                      : 'bg-red-500'
                  }`}
                  style={{ width: `${pos.health * 100}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

