/**
 * DoctrineAlertPanel Component
 * 
 * Anomaly Layer - Doctrine Alert Panel
 * 
 * 顯示 Doctrine 紅線警示
 */

import { useDoctrineAlerts } from '../../../hooks/war-room/useDoctrineAlerts';

export function DoctrineAlertPanel() {
  const { data: alerts, isLoading, isError, error } = useDoctrineAlerts();

  const getAlertColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'border-red-500 bg-red-50 dark:bg-red-900/20';
      case 'warning':
        return 'border-yellow-500 bg-yellow-50 dark:bg-yellow-900/20';
      case 'info':
        return 'border-blue-500 bg-blue-50 dark:bg-blue-900/20';
      default:
        return 'border-gray-500 bg-gray-50 dark:bg-gray-900/20';
    }
  };

  if (isLoading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Doctrine 紅線警示
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
          Doctrine 紅線警示
        </h3>
        <div className="text-red-500 dark:text-red-400 text-sm">
          錯誤: {error instanceof Error ? error.message : '未知錯誤'}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        Doctrine 紅線警示
      </h3>
      {!alerts || alerts.length === 0 ? (
        <div className="text-gray-500 dark:text-gray-400 text-center py-8 text-sm">
          目前沒有違反 Doctrine 風控規則的即時警報。
        </div>
      ) : (
        <div className="space-y-3 max-h-64 overflow-y-auto">
          {alerts.map((alert) => (
            <div
              key={alert.id}
              className={`p-3 rounded-lg border-l-4 ${getAlertColor(alert.severity)}`}
            >
              <div className="flex justify-between items-start mb-1">
                <span
                  className={`text-xs font-semibold px-2 py-1 rounded ${
                    alert.severity === 'critical'
                      ? 'bg-red-500 text-white'
                      : alert.severity === 'warning'
                      ? 'bg-yellow-500 text-white'
                      : 'bg-blue-500 text-white'
                  }`}
                >
                  {alert.severity.toUpperCase()}
                </span>
                <span className="text-xs text-gray-500 dark:text-gray-500">
                  {alert.rule_id}
                </span>
              </div>
              <div className="text-sm text-gray-900 dark:text-white">
                {alert.message}
              </div>
              {alert.symbol && (
                <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                  股票: {alert.symbol}
                </div>
              )}
              <div className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                {new Date(alert.created_at).toLocaleString('zh-TW')}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

